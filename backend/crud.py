from sqlalchemy.orm import Session
from uuid import UUID
import models, schemas
from auth import get_password_hash

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = get_password_hash(user.password)
    db_user = models.User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_fcm_token(db: Session, user_id: UUID, token: str):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if db_user:
        db_user.fcm_token = token
        db.commit()
        db.refresh(db_user)
    return db_user

def create_group(db: Session, group: schemas.GroupCreate, creator_id: UUID):
    db_group = models.Group(
        name=group.name,
        description=group.description,
        created_by=creator_id
    )
    db.add(db_group)
    db.commit()
    db.refresh(db_group)
    
    # Add creator as a starting member
    add_group_member(db, db_group.id, creator_id)
    return db_group

def add_group_member(db: Session, group_id: UUID, user_id: UUID):
    db_member = models.GroupMember(group_id=group_id, user_id=user_id)
    db.add(db_member)
    db.commit()
    db.refresh(db_member)
    return db_member

def get_group_members(db: Session, group_id: UUID):
    return db.query(models.GroupMember).filter(models.GroupMember.group_id == group_id).all()

def create_message(db: Session, msg: schemas.MessageSend, sender_id: UUID):
    db_msg = models.Message(
        sender_id=sender_id,
        receiver_id=msg.receiver_id,
        group_id=msg.group_id,
        content=msg.content
    )
    db.add(db_msg)
    db.commit()
    db.refresh(db_msg)
    return db_msg

def get_messages(db: Session, user_id: UUID, other_user_id: UUID = None, group_id: UUID = None, limit: int = 50):
    if group_id:
        return db.query(models.Message).filter(models.Message.group_id == group_id).order_by(models.Message.created_at.desc()).limit(limit).all()
    elif other_user_id:
        return db.query(models.Message).filter(
            ((models.Message.sender_id == user_id) & (models.Message.receiver_id == other_user_id)) |
            ((models.Message.sender_id == other_user_id) & (models.Message.receiver_id == user_id))
        ).order_by(models.Message.created_at.desc()).limit(limit).all()
    return []
