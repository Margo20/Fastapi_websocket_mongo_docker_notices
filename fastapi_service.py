import base64
import os
import logging
from typing import List, Dict

from fastapi import FastAPI, HTTPException, WebSocket
from pydantic.main import BaseModel
from hash_password import fastapi_crypt_pass
from pymongo import MongoClient
from fastapi.responses import HTMLResponse

salt_bytes = base64.b64decode(os.getenv('SALT_BASE64').encode())
hash_bytes = base64.b64decode(os.getenv('HASH_BASE64').encode())


client = MongoClient("mongodb://localhost:27017/")
db = client["storage_db_msg"]
msg_collection = db["db_messages"]

class Db_msg(BaseModel):
    user_id: int
    sent: bool

class Api_msg(BaseModel):
    user_id: int
    password: str

api = FastAPI()

class Connection_Manager():
    def __init__(self):
        self.connections: Dict[str, WebSocket] = {}
    def send_message(self,user_id:int):
        user_id_str = str(user_id)
        websocket = self.connections[user_id_str] # достать из connection по ключу user_id  значение websocket
        sent = False
        if websocket:
            self.send_to_websocket(websocket)
            sent = True
        db_msg = Db_msg(user_id=user_id, sent=sent)
        msg_collection.insert_one(db_msg.dict())

    def connected(self, websocket:WebSocket, user_id:str):
        self.connections[user_id]=websocket# положить в connection по ключу user_id  значение websocket
        x = db.users.find ({'user_id': user_id, 'sent': 'False'})
        for i in x:
            self.send_to_websocket(websocket)

    def send_to_websocket(self, websocket):
        websocket.send_text("Сделка состоялась")


connection_manager = Connection_Manager()

@api.post("/send_user_id")
async def send_user_id(msg: Api_msg):
    logging.info("New user_id: %s" % (msg.user_id))
    hash_from_clients = fastapi_crypt_pass(msg.password, salt_bytes)

    if hash_from_clients==hash_bytes:
        connection_manager.send_message(msg.user_id)
    else:
        logging.warning("Password not valid")
        raise HTTPException(status_code=401, detail="wrong password")


@api.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await websocket.accept()
    connection_manager.connected(websocket, user_id)


html = """
<!DOCTYPE html>
<html>
    <head>
        <title>WebSocket message</title>
    </head>
    <body>
        <h3>WebSocket message for buyer and seller about trade</h3>

        <ul id='messages'>
        </ul>
        <script>
            var ws = new WebSocket("ws://localhost:8888/ws");
            ws.onmessage = function(event) {
                var messages = document.getElementById('messages')
                var message = document.createElement('li')
                var content = document.createTextNode(event.data)
                message.appendChild(content)
                messages.appendChild(message)
            };
        </script>
    </body>
</html>
"""

@api.get("/")
async def get():
    return HTMLResponse(html)
