from redis.asyncio import Redis
from app.config.conf import settings
from fastapi import HTTPException
from redis.exceptions import RedisError

class RedisDb():
    client: Redis = None

redis_manager = RedisDb()

async def connect_to_redis():
    try:
        redis_manager.client = Redis(
            host = settings.REDIS_HOST, 
            port = settings.REDIS_PORT, 
            db = settings.REDIS_DB,
            decode_responses = True,
            socket_connect_timeout = 5
        )
        await redis_manager.client.ping()
        print('Connection to Redis established Successfully.')
    except Exception as e:
        print('Connection to Redis Failed with error ', e)
        
async def disconnect_to_redis():
    if redis_manager.client is not None:
        await redis_manager.client.aclose()
        print('Connection to Redis closed Successfully.')
        
def get_redis_db():
    try:
        yield redis_manager.client
    except RedisError as e:
        print('Redis Operation Error', e)
        raise HTTPException(
            status_code = 500,
            detail = 'Redis Db Error'
        )
        
def get_redis_db_direct():
    return redis_manager.client