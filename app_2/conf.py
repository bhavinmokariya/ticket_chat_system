from dotenv import load_dotenv
import os

load_dotenv()

class Settings:
    __slots__ = ()
    mongo_uri: str = os.environ.get("MONGO_URI", "")
    collection: str = "tickets"

settings = Settings()
