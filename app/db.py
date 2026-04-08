from pymongo import AsyncMongoClient


MONGO_URI = "mongodb://localhost:27017"
DB_NAME = "chatbot_db"

client = AsyncMongoClient(MONGO_URI)
db = client[DB_NAME]

ticket_collection = db["tickets"]