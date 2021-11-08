import uvicorn
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db import engine, Base
from app.api import courses

origins = ["*"]
courses.set_engine(engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(courses.router, prefix="/courses", tags=["courses"])

if __name__ == '__main__':
    Base.metadata.create_all(engine)
    uvicorn.run(app, host='0.0.0.0', port=8000)
