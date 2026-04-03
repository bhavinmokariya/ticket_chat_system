from fastapi import FastAPI, Depends
from app.socket import routes
from contextlib import asynccontextmanager
from app.db.mongo_client import connect_to_mongo, disconnect_to_mongo
from app.db.redis_client import connect_to_redis, disconnect_to_redis
# from app.models.celery_client import connect_to_celery
import asyncio


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    All the startup code including connections to mongo,redis and celery is kept here to be executed only once 
    at startup.
    """
    await connect_to_mongo()
    await connect_to_redis()
    # connect_to_celery()
    try:
        yield
    except asyncio.CancelledError:
        pass
    finally:
        await disconnect_to_mongo()
        await disconnect_to_redis()
    

app = FastAPI(lifespan = lifespan)

for route in routes:
    app.include_router(route)