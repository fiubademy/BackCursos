from fastapi import FastAPI
import uvicorn

from fastapi.middleware.cors import CORSMiddleware

from db import engine, Base
from api import courses

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