#!/bin/bash

uvicorn fastapi_service:api --host 0.0.0.0 --port 8080
