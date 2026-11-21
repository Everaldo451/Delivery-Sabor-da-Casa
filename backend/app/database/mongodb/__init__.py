import os

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

load_dotenv()

# tz_aware=True: datas voltam do Mongo com fuso (UTC), o app Flutter converte pro horario local
client = AsyncIOMotorClient(os.getenv("MONGO_URL", "mongodb://localhost:27017"), tz_aware=True)
db = client[os.getenv("MONGO_DB", "sabordacasa")]


def get_mongo_db() -> AsyncIOMotorDatabase:
    return db
