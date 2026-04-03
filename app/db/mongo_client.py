from pymongo import AsyncMongoClient
from app.config.conf import settings
from fastapi import HTTPException
from pymongo.errors import PyMongoError

class MongoDB():
    client: AsyncMongoClient = None
    db = None
    
db_manager = MongoDB()

async def connect_to_mongo():
    try:
        db_manager.client = AsyncMongoClient(settings.MONGO_URI, serverSelectionTimeoutMS=5000, uuidRepresentation = "standard")
        db_manager.db = db_manager.client['app']
        await db_manager.client.admin.command('ping')
        print('Connected to MongoDB successfull.')
    except Exception as e:
        print('Connection Unsuccessfull with error ', e)
        
async def disconnect_to_mongo():
    if db_manager.client is not None:
        await db_manager.client.close()
        print('Connection to MongoDB closed Successfully.')
        
def get_mongo_db():
    try:
        yield db_manager.db
    except PyMongoError as e:
        print('MongoDB Error', e)
        raise HTTPException(
            status_code = 500,
            detail = 'Database Error'
        )

def get_mongo_db_direct():
    return db_manager.db