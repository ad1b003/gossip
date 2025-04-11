import datetime
from typing import Dict, List, Optional
from uuid import uuid4
import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud.firestore_v1.client import Client
from google.cloud.firestore_v1.query import Query
from werkzeug.security import generate_password_hash, check_password_hash

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)
db: Client = firestore.client()


def addUser(name: str, username: str, password: str) -> Optional[bool]:
    try:
        user: Query = db.collection("users").document(username).get()
        if user.exists:
            return None
        user_info = {"username": username,
                     "password": generate_password_hash(password),
                     "name": name,
                     "online": None
                     }
        db.collection("users").document(username).set(user_info)
        return True
    except Exception as e:
        print(f"Error while adding the user: {e}")
        return None


def authenticate(username: str, password: str) -> Optional[Dict]:
    try:
        user: Query = db.collection("users").document(username).get()
        if user.exists:
            user_data = user.to_dict()
            if check_password_hash(user_data["password"], password):
                return user_data
        return None
    except Exception as e:
        print(f"Error while authenticating: {e}")
        return None


def fetchUser(username: str) -> Optional[Dict]:
    try:
        docs: Query = db.collection("users").where(
            "username", "==", username).get()
        if docs:
            for doc in docs:
                user_data = doc.to_dict()
                return user_data
        else:
            return None
    except Exception as e:
        print(f"Error fetching the user: {e}")
        return None


def fetchAllUsers(username: str) -> Optional[List]:
    try:
        docs: Query = db.collection("users").stream()
        all_users = [doc.to_dict() for doc in docs if doc.id != username]
        return all_users
    except Exception as e:
        print(f"Error fetching all users: {e}")
        return None


def setUserLastSeen(username: str):
    try:
        db.collection("users").document(username).update(
            {"online": firestore.SERVER_TIMESTAMP})
        return True
    except Exception as e:
        print(f"Error setting last seen: {e}")
        return None

def isUserOnline(username: str) -> Optional[bool]:
    try:
        user: Query = db.collection("users").document(username).get()
        if user.exists:
            user_data = user.to_dict()
            time_diff = datetime.datetime.now(datetime.timezone.utc) - user_data["online"].to_datetime()
            return time_diff.total_seconds() < 123
        return None
    except Exception as e:
        print(f"Error while checking online status: {e}")
        return None

def createNewChatRoom(sender: str, receiver: str):
    if not isUserOnline(receiver):
        return None
    chat_room_id: str = str(uuid4())
    try:
        chat_room = {"chat_room_id": chat_room_id,
                     "members": [sender, receiver],
                     "messages": []}
        db.collection("chat-rooms").document(chat_room_id).set(chat_room)
        return chat_room_id
    except Exception as e:
        print(f"Error while creating the new chat room: {e}")
        return None


def getChatRoomId(sender: str, receiver: str) -> Optional[str]:
    try:
        docs = db.collection("chat-rooms").where(
            "members", "array_contains", sender).stream()
        if docs:
            for chat in docs:
                chat_data = chat.to_dict()
                if receiver in chat_data.get("members", []):
                    return chat.id
                else:
                    return createNewChatRoom(sender, receiver)
        else:
            return createNewChatRoom(sender, receiver)
    except Exception as e:
        print(f"Error while getting the chat room id: {e}")
        return None


def fetchAllMessages(sender: str, receiver: str) -> Optional[List]:
    chat_room_id: str = getChatRoomId(sender, receiver)
    if chat_room_id is None:
        return []
    else:
        try:
            doc: Query = db.collection(
                "chat-rooms").document(chat_room_id).get()
            if doc.exists:
                chat_room_data = doc.to_dict()
                return chat_room_data.get("messages", [])
        except Exception as e:
            print(f"Error while fetching all messages: {e}")
            return None


def saveMessage(sender: str, receiver: str, message: str) -> Optional[bool]:
    chat_room_id: str = getChatRoomId(sender, receiver)
    try:
        if chat_room_id is None:
            return None
        # timestamp = firestore.SERVER_TIMESTAMP
        db.collection("chat-rooms").document(chat_room_id).update(
            {"messages": firestore.ArrayUnion([
                # "timestamp": firestore.SERVER_TIMESTAMP
                {
                    "sender": sender,
                    "message": message,
                    "timestamp": datetime.datetime.now(datetime.timezone.utc)
                    }
                ])
                }
        )
        return True
    except Exception as e:
        print(f"Error saving message in the database: {e}")
        return None
