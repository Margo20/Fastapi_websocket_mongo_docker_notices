import asyncio
import base64
import os
import logging
from asyncio import Queue
from typing import List, Dict

import uvicorn
from fastapi import FastAPI, HTTPException, WebSocket
from pydantic.main import BaseModel
from websockets.exceptions import WebSocketException

from hash_password import fastapi_crypt_pass
from pymongo import MongoClient
from fastapi.responses import HTMLResponse

logger = logging.getLogger("fastapiService")

salt_bytes = base64.b64decode(os.getenv('SALT_BASE64').encode())
hash_bytes = base64.b64decode(os.getenv('HASH_BASE64').encode())

client = MongoClient("mongodb://mongodb:27017/")
db = client["storage_db_msg"]
msg_collection = db["db_messages"]


class Db_msg(BaseModel):
    user_id: int
    sent: bool

class Api_msg(BaseModel):
    user_id: int
    password: str


api = FastAPI()
connections: Dict[str, WebSocket] = {}
queue_users_id = Queue()

@api.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await websocket.accept()
    try:
        db_msgs = msg_collection.find({'user_id': int(user_id), 'sent': False})
        logger.info("FOUND new %s MESSAGES for user_id %s" % (db_msgs, user_id))
        for db_msg in db_msgs:
            logger.info("New %s message for user_id %s" % (db_msg, user_id))
            await websocket.send_text("Сделка состоялась")
            msg_collection.update_one({'_id': db_msg['_id']}, {'$set': {'sent': True}})
    except WebSocketException:
        logging.error("leave: user_id: %s" % (user_id))
        return
    else:
       logger.info("Send success user_id: %s" % (user_id)) # todo add information about message
    while True:
        msg = await queue_users_id.get()  # todo 1.check if msg is already sent 2.
        # todo send msg to websocket
        await asyncio.sleep(100000000)


@api.post("/send_user_id")
async def send_user_id(msg: Api_msg):
    user_id = msg.user_id
    logger.info("New user_id: %s" % (user_id))
    hash_from_clients = fastapi_crypt_pass(msg.password, salt_bytes)
    if hash_from_clients == hash_bytes:
        db_msg = Db_msg(user_id=user_id, sent=False)
        insertion_result = await msg_collection.insert_one(db_msg.dict())
        if insertion_result.acknowledged:
            logger.info("db_msg add to db: %s" % (db_msg))
            queue_users_id.put_nowait(db_msg)
        else:
            logger.error("not added to db: %s" % (db_msg))
            raise HTTPException(status_code=500, detail="see servers' logs")
    else:
        logger.warning("Password not valid")
        raise HTTPException(status_code=401, detail="wrong password")


html = """
<!DOCTYPE html>
<html lang="en">
    <head>
        <title>WebSocket message</title>
        <script>
        var ws;
        window.onbeforeunload = function() {
            ws && ws.close("Client closed window");
        };
        function createWebsocket() { 
            ws = new WebSocket("ws://"+location.host+"/ws/"+document.querySelector("#user_id_text").value);
            document.querySelector("#connection_status").style.display="inline";
            document.querySelector("#btn_connect").setAttribute('disabled', '');
            ws.onmessage = function(event) {
                var messages = document.getElementById('messages')
                var message = document.createElement('li')
                var content = document.createTextNode(event.data)
                message.appendChild(content)
                messages.appendChild(message)
            };
        }
        </script>
    </head>
    <body>
        <h3>WebSocket message for buyer and seller about trade</h3>
            <label for="user_id_text">Your user_id</label>
            <input type="text" id="user_id_text"/>
            <button id="btn_connect" onclick="createWebsocket()">Connect</button>
            <div><label id="connection_status" style='display: none'>You are connected</label></div>
            <ul id='messages'> </ul>
        
    </body>
</html>
"""


@api.get("/")
async def get():
    return HTMLResponse(html)

# if __name__ == "__main__":
#     uvicorn.run(api, host="0.0.0.0", port=8080)