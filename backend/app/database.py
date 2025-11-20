from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings

client: AsyncIOMotorClient = None
database = None


async def connect_to_mongo():
    """Create database connection"""
    global client, database
    client = AsyncIOMotorClient(settings.mongo_url)
    database = client[settings.mongo_db_name]
    print(f"Connected to MongoDB: {settings.mongo_db_name}")


async def close_mongo_connection():
    """Close database connection"""
    global client
    if client:
        client.close()
        print("Disconnected from MongoDB")

