from time import sleep
from fastapi import FastAPI

# from application.base.database import database, db_models
from application.router import PT_IDA_routes
# from application.base.core import web_utils

app = FastAPI()

app.include_router(PT_IDA_routes.router)
