from fastapi import WebSocket, HTTPException, WebSocketDisconnect
from app.db.redis_client import get_redis_db_direct
import logging
import json
# from app.schemas.messages import CreateMessage, AcceptMessage



# class NotificationManager:
#     """
#     This is the Notification Manager class which will handle each individual websocket connection along with each individual pubsub object
    
#     Methods:
#         - connect
#         - disconnect
#         - listen_channel
#         - listen
#     """
    
#     live_channel = "live-tickets"
#     accept_channel = "accept-tickets"

#     def __init__(self, websocket: WebSocket):       
#         self.redis_db = get_redis_db_direct()
#         self.pubsub = self.redis_db.pubsub()
#         self.websocket: WebSocket = websocket

#     async def connect(self):
#         """
#         Accept the connection and subscribe the initialized pubsub object to the live and accept channel.
#         """
        
#         try:
#             await self.websocket.accept()
#             await self.pubsub.subscribe(NotificationManager.live_channel, NotificationManager.accept_channel)
#         except Exception as e:
#             raise HTTPException(status_code=500, detail="Error Connecting.")

#     async def disconnect(self):
#         """
#         Disconnect to the pubsub object and close the connection
#         """
        
#         await self.pubsub.unsubscribe()
#         await self.pubsub.aclose()

#     async def listen_channel(self):
#         """
#         Keep on listening to the incoming messages from the channel and yield along with channel name and the message
        
#         Output:
#             - dictionary containing channel name and the msg
#         """
        
#         try:
#             async for data in self.pubsub.listen():
#                 if data['type'] == 'message':
#                     print(f"{data['data']}--{data['channel']}")
#                     yield {"channel": data["channel"], "msg": json.loads(data["data"])}
#         except Exception as e:
#             logging.exception(f"Function: {self.listen_channel.__name__}")

#     async def listen(self):
#         """
#         Send message via the websocket to the client
#         Perform graceful cleanup after closing of the Websocket Connection
#         """
        
#         try:
#             async for payload in self.listen_channel():
#                 await self.websocket.send_json(json.dumps(payload))
#         except WebSocketDisconnect:
#             pass
#         except Exception as e:
#             logging.exception(f"Function: {self.listen.__name__}")
#             raise HTTPException(status_code=500, detail="Unknown Error Occured")
#         finally:
#            await self.disconnect() 



class NotificationManager:
    """
    This is the Notification Manager class which will handle each individual websocket connection along with each individual pubsub object
    
    Methods:
        - connect
        - disconnect
        - listen_channel
        - listen
    """
    
    live_channel = "live-tickets"
    accept_channel = "accept-tickets"

    def __init__(self):       
        self.redis_db = get_redis_db_direct()
        self.pubsub = self.redis_db.pubsub()

    async def connect(self,websocket: WebSocket):
        """
        Accept the connection and subscribe the initialized pubsub object to the live and accept channel.
        """
        
        try:
            await websocket.accept()
            await self.pubsub.subscribe(NotificationManager.live_channel, NotificationManager.accept_channel)
        except Exception as e:
            raise HTTPException(status_code=500, detail="Error Connecting.")

    async def disconnect(self):
        """
        Disconnect to the pubsub object and close the connection
        """
        
        await self.pubsub.unsubscribe()
        await self.pubsub.aclose()

    async def listen_channel(self):
        """
        Keep on listening to the incoming messages from the channel and yield along with channel name and the message
        
        Output:
            - dictionary containing channel name and the msg
        """
        
        try:
            async for data in self.pubsub.listen():
                if data['type'] == 'message':
                    print(f"{data['data']}--{data['channel']}")
                    yield {"channel": data["channel"], "msg": json.loads(data["data"])}
        except Exception as e:
            logging.exception(f"Function: {self.listen_channel.__name__}")

    async def listen(self, websocket: WebSocket):
        """
        Send message via the websocket to the client
        Perform graceful cleanup after closing of the Websocket Connection
        """
        
        try:
            async for payload in self.listen_channel():
                await websocket.send_json(json.dumps(payload))
        except WebSocketDisconnect:
            pass
        except Exception as e:
            logging.exception(f"Function: {self.listen.__name__}")
            raise HTTPException(status_code=500, detail="Unknown Error Occured")
        finally:
           await self.disconnect()