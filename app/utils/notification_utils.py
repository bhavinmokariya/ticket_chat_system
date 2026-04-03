from app.db.redis_client import get_redis_db_direct
from app.db.mongo_client import get_mongo_db_direct
import logging
import json
import asyncio
from contextlib import asynccontextmanager
# from app.schemas.messages import CreateMessage, AcceptMessage 



class BackgroundManager:
    """
    This class defines methods for initializing the mongo and redis db once.
    
    Functions:
        - __init__
        - watch_tickets_insertion
        - watch_tickets_assignment
        - publish_message_on_create
        - publish_acknowledgement_on_accept
        
    Approach:
    
    This particular approach implemented here utilizes the asyncronous watch functionality of pymongo Async client along with redis pubsub manager 
    There can be 4 different ways to implement this:
        1) Start the watcher the publisher in a complete different process decoupled from fastapi app
        2) Each worker will have its own watch stream as well redis db
        3) Remove redis completely migrate to local connection manager storing connection websockets in python itself and even if multiple workers are there each having
        its own watch stream would not create any problem
        4) Have only 1 watch stream, no redis pubsub, local connection manager but works only if there is one process
        
    Here the approach is per worker different watch stream, different redis connection 
    Alternative can be 1 watch stream using redis pubsub for each individual worker and also managing active_connections in python (Optimised)
    Current approach is simple but creates multiple mongo streams per workers, redis pubsub objects per websocket connection but because of 
    the use case should not make much difference
    
    If in future requirements changes, migration to the optmised version can be done easily.
    """
    
    
    def __init__(self):
        self.collection = get_mongo_db_direct()['tickets']
        self.redis_db = get_redis_db_direct()
        self.live_channel = "live-tickets"
        self.accept_channel = "accept-tickets"

    async def watch_tickets_insertion(self):
        """
        Watches for insertion tasks on tickets collection in mongodb
        
        Works:
        The watcher works in background constantly looking for any insert operations on the tickets collection 
        Managed by the watch context manager as well as message/document yielding whenever any insert operation is performed
        Keeps on working and the connection is not closed unless and until, an error or exception occurs
        
        pipeline defined here matches for the required fields and filters out the rest
                
        Output:
            - yield the inserted ticket entire document 
        """
        
        pipeline = [{"$match": {"operationType": "insert"}}]
        try:
            print('Watch tickets started')
            async with await self.collection.watch(pipeline,full_document='updateLookup') as stream:
                async for input in stream:
                    # print(input)
                    ticket = input.get("fullDocument")
                    # print(ticket)
                    yield ticket
        except Exception as e:
            logging.exception("Exception occured watching insert tickets")

    async def watch_tickets_assignment(self):
        """
        Watches for update tasks on tickets collection in mongodb.
        Not all update tasks are output here, only those update tasks which have the assigned_engineer_id as an updated field in it are.
        
        Works:
        The watcher works in background constantly looking for any specific update operations on the tickets collection 
        Managed by the watch context manager as well as message/document yielding whenever any specific operation is performed
        Keeps on working and the connection is not closed unless and until, an error or exception occurs
        
        pipeline defined here matches for the required fields and filters out the rest
                
        Output:
            - yield the document id (_id) of the updated document
        """
        pipeline = [
            {
                "$match": {
                    "operationType": "update",
                    "updateDescription.updatedFields.assigned_engineer_id": {"$exists": True},
                }
            }
        ]

        try:
            async with await self.collection.watch(pipeline,full_document='updateLookup') as stream:
                async for input in stream:
                    id = input.get("documentKey")
                    yield str(id)
        except Exception as e:
            logging.exception("Exception occured watching tickets assignment")

    async def publish_message_on_create(self):
        """
        Utilizes redis publish and subscribe functionality
        publishes the entire ticket data to the redis "live-tickets" channel 
        
        Note: Data has to be converted to json serializable type before pushing it 
        Better would be to preprocess data, using pydantic schema and convert it to json serializable.
        """
        
        try:
            async for ticket in self.watch_tickets_insertion():
                print(ticket)
                ticket['_id'] = str(ticket['_id'])
                await self.redis_db.publish(self.live_channel, json.dumps(ticket))
        except Exception as e:
            # logging.exception(f"Function: {self.send_message_create.__name__}")
            pass

    async def publish_acknowledgement_on_accept(self):
        """
        Publish Acknowledgement message to the accept-tickets channel along with the ticket id.
        """
        
        try:
            async for id in self.watch_tickets_assignment():
                print(id)
                await self.redis_db.publish(self.accept_channel, json.dumps(id))
        except Exception as e:
            # logging.exception(
            #     f"Function: {send_acknowledgement_on_accept.__name__}"
            print(e)
            # )
            pass
    

