"""
Script to clear all users and messages from the database.
This will remove all existing data to start fresh.
"""

import asyncio
from app.database import connect_to_mongo, close_mongo_connection
from app import database as db_module


async def clear_database():
    """Delete all users and messages from the database"""
    print("Connecting to database...")
    await connect_to_mongo()
    
    if db_module.database is None:
        print("Error: Database not initialized")
        return
    
    try:
        # Delete all messages
        messages_result = await db_module.database.messages.delete_many({})
        print(f"Deleted {messages_result.deleted_count} messages")
        
        # Delete all message requests
        requests_result = await db_module.database.message_requests.delete_many({})
        print(f"Deleted {requests_result.deleted_count} message requests")
        
        # Delete all users
        users_result = await db_module.database.users.delete_many({})
        print(f"Deleted {users_result.deleted_count} users")
        
        print("\n[SUCCESS] Database cleared successfully!")
        print("You can now register new users and start fresh.")
        
    except Exception as e:
        print(f"Error clearing database: {e}")
    finally:
        await close_mongo_connection()


if __name__ == "__main__":
    print("[WARNING] This will delete ALL users and messages!")
    print("Press Ctrl+C to cancel, or wait 3 seconds to continue...")
    
    try:
        import time
        time.sleep(3)
    except KeyboardInterrupt:
        print("\n[CANCELLED]")
        exit(0)
    
    asyncio.run(clear_database())

