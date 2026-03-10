import firebase_admin
from firebase_admin import credentials, messaging
import os
import logging

logger = logging.getLogger(__name__)

# Initialize Firebase App
# In a real environment, provide the path to your service account key JSON file
FIREBASE_SERVICE_ACCOUNT_KEY = os.environ.get("FIREBASE_CREDENTIALS", "firebase-adminsdk.json")

try:
    if os.path.exists(FIREBASE_SERVICE_ACCOUNT_KEY):
        cred = credentials.Certificate(FIREBASE_SERVICE_ACCOUNT_KEY)
        firebase_admin.initialize_app(cred)
        logger.info("Firebase Admin initialized successfully.")
    else:
        logger.warning("Firebase credentials not found. Notifications will be mocked or fail.")
except Exception as e:
    logger.error(f"Error initializing Firebase Admin: {e}")

def send_push_notification(token: str, title: str, body: str, data: dict = None):
    """
    Sends a push notification to a specific device using its FCM token.
    """
    if not token:
        logger.warning("No FCM token provided, skipping notification.")
        return False

    if not firebase_admin._apps:
         logger.warning("Firebase not initialized. Cannot send notification.")
         return False

    try:
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            data=data or {},
            token=token,
        )

        response = messaging.send(message)
        logger.info(f"Successfully sent message: {response}")
        return True
    except Exception as e:
        logger.error(f"Error sending push notification: {e}")
        return False
