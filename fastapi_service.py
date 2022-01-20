import base64
import os
import logging
from fastapi import FastAPI, HTTPException
from pydantic.main import BaseModel
from hash_password import fastapi_crypt_pass
from pymongo import MongoClient
from bson import ObjectId

class Db_msg(BaseModel):
    _id: ObjectId
    user_id: int
    sent: bool

class User_msg(BaseModel):
    _id: ObjectId
    user_id: int
    sent: bool

salt_bytes = base64.b64decode(os.getenv('SALT_BASE64').encode())
hash_bytes = base64.b64decode(os.getenv('HASH_BASE64').encode())


client = MongoClient()
db = client[database_name]

client = MongoClient()
db = client.test

class Api_msg(BaseModel):
    user_id: int
    password: str

api = FastAPI()

@api.post("/my_send_notice")
async def save_to_mongodb(msg: Api_msg):
    logging.info("New user_id: %s" % (msg.user_id))
    hash_from_clients = fastapi_crypt_pass(msg.password, salt_bytes)

    if hash_from_clients==hash_bytes:
        save_to_mongodb
    else:
        logging.warning("Password not valid")
        raise HTTPException(status_code=401, detail="wrong password")
