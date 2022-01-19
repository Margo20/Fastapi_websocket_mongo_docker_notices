import base64
import os
import logging
from fastapi import FastAPI, HTTPException
from pydantic.main import BaseModel


api = FastAPI()

@api.post("/my_send_notice")
async def enqueue_add():
    pass
