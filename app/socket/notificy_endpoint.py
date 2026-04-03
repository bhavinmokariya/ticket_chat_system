from fastapi import APIRouter, WebSocket, Depends
from app.socket.notification_manger import NotificationManager
from app.utils.notification_utils import BackgroundManager
import asyncio
from contextlib import asynccontextmanager



@asynccontextmanager
async def lifespan(app):
    """
    This is a lifespan event for notify route
    
    It will start the publish message on create and publish acknowledge on accept as separate background task which will keep on running until stopped
    Here as we are currently using only 1 worker only 1 watch stream will be created.
    """
    
    bg_manager = BackgroundManager()
    # notification_manager = NotificationManager()
    task1 = asyncio.create_task(bg_manager.publish_message_on_create())
    task2 = asyncio.create_task(bg_manager.publish_acknowledgement_on_accept())
    print('Background process started.')
    try:
        yield
    except asyncio.CancelledError:
        pass
    finally:
        task1.cancel()
        task2.cancel()
        print('Background Tasks Closed Successfully.')



notify_rt = APIRouter(
    prefix='/notify',
    lifespan=lifespan
)

@notify_rt.websocket('/live-tickets')
async def live_tickets(websocket: WebSocket):
    manager = NotificationManager()
    await manager.connect(websocket)
    await manager.listen(websocket)
        