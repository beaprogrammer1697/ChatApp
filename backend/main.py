from fastapi import FastAPI, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from uuid import UUID
from typing import Dict, List, Any
import json
import asyncio

import models, schemas, crud, auth, fcm
from database import engine, get_db

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Chat Application API")

# ---------------------------------------------------------
# WebSocket Manager
# ---------------------------------------------------------
class ConnectionManager:
    def __init__(self):
        # Maps user_id (str) to their active WebSocket connection
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        self.active_connections[user_id] = websocket

    def disconnect(self, user_id: str):
        if user_id in self.active_connections:
            del self.active_connections[user_id]

    async def send_personal_message(self, message: dict, user_id: str):
        if user_id in self.active_connections:
            websocket = self.active_connections[user_id]
            await websocket.send_json(message)

manager = ConnectionManager()

# ---------------------------------------------------------
# Authentication Endpoints
# ---------------------------------------------------------
@app.post("/register", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user_email = crud.get_user_by_email(db, email=user.email)
    db_user_username = crud.get_user_by_username(db, username=user.username)
    if db_user_email or db_user_username:
        raise HTTPException(status_code=400, detail="Email or Username already registered")
    return crud.create_user(db=db, user=user)

@app.post("/token", response_model=schemas.Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = crud.get_user_by_username(db, username=form_data.username)
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = auth.create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/users/me/fcm", response_model=schemas.UserResponse)
def update_fcm(
    token_data: schemas.FCMTokenUpdate, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(auth.get_current_user)
):
    return crud.update_fcm_token(db, current_user.id, token_data.fcm_token)

@app.get("/users/me", response_model=schemas.UserResponse)
def read_users_me(current_user: models.User = Depends(auth.get_current_user)):
    return current_user

# ---------------------------------------------------------
# Group Endpoints
# ---------------------------------------------------------
@app.post("/groups", response_model=schemas.GroupResponse)
def create_group(
    group: schemas.GroupCreate, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(auth.get_current_user)
):
    return crud.create_group(db, group, current_user.id)

@app.post("/groups/{group_id}/members")
def add_member_to_group(
    group_id: UUID, 
    member: schemas.GroupMemberCreate, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(auth.get_current_user)
):
    # Depending on rules, you might want to verify if current_user is admin or in the group
    crud.add_group_member(db, group_id, member.user_id)
    return {"status": "success"}

# ---------------------------------------------------------
# Chat Endpoints
# ---------------------------------------------------------
@app.post("/messages", response_model=schemas.MessageCreateResponse)
async def send_message(
    msg: schemas.MessageSend,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    if not msg.receiver_id and not msg.group_id:
        raise HTTPException(status_code=400, detail="Must specify receiver_id or group_id")
    
    # 1. Save message to DB
    db_msg = crud.create_message(db, msg, current_user.id)
    
    # 2. Serialize message for WebSocket and FCM
    msg_data = {
        "id": str(db_msg.id),
        "sender_id": str(db_msg.sender_id),
        "content": db_msg.content,
        "receiver_id": str(db_msg.receiver_id) if db_msg.receiver_id else None,
        "group_id": str(db_msg.group_id) if db_msg.group_id else None,
        "created_at": db_msg.created_at.isoformat()
    }

    # 3. Route Real-time via WebSocket and push notification via FCM
    if msg.group_id:
        members = crud.get_group_members(db, msg.group_id)
        for member in members:
            member_id_str = str(member.user_id)
            if member_id_str != str(current_user.id):
                # Send WebSocket
                await manager.send_personal_message(msg_data, member_id_str)
                # Send FCM Notification
                target_user = db.query(models.User).filter(models.User.id == member.user_id).first()
                if target_user and target_user.fcm_token:
                    fcm.send_push_notification(
                        token=target_user.fcm_token,
                        title=f"New message in Group",
                        body=db_msg.content[:50]
                    )
    elif msg.receiver_id:
        receiver_id_str = str(msg.receiver_id)
        # Send WebSocket
        await manager.send_personal_message(msg_data, receiver_id_str)
        # Send FCM Notification
        target_user = db.query(models.User).filter(models.User.id == msg.receiver_id).first()
        if target_user and target_user.fcm_token:
             fcm.send_push_notification(
                  token=target_user.fcm_token,
                  title=f"New message from {current_user.username}",
                  body=db_msg.content[:50]
             )
                
    return db_msg

@app.get("/messages", response_model=List[schemas.MessageCreateResponse])
def get_messages(
    other_user_id: UUID = None,
    group_id: UUID = None,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    return crud.get_messages(db, current_user.id, other_user_id, group_id, limit)

# ---------------------------------------------------------
# WebSocket Endpoint
# ---------------------------------------------------------
@app.websocket("/ws/{token}")
async def websocket_endpoint(websocket: WebSocket, token: str, db: Session = Depends(get_db)):
    """
    Simplified auth for websocket: Passing the JWT token in URL path.
    """
    try:
        user = await auth.get_current_user(token=token, db=db)
    except Exception:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    user_id_str = str(user.id)
    await manager.connect(websocket, user_id_str)
    try:
        while True:
            data = await websocket.receive_text()
            # In a real app, clients might send typing indicators or read receipts here
            pass
    except WebSocketDisconnect:
        manager.disconnect(user_id_str)
