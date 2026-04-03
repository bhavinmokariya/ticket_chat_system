from dotenv import load_dotenv
from datetime import timedelta
import os

load_dotenv()

class settings:
    MONGO_URI : str = os.environ.get('MONGO_URI',None)
    REDIS_HOST: str = os.environ.get('REDIS_HOST',None)
    REDIS_PORT: int = os.environ.get('REDIS_PORT',6379)
    REDIS_DB: int = os.environ.get('REDIS_DB',0)