from pydantic import BaseModel, Field
import uuid
from typing import List, Optional


class CourseRequest(BaseModel):
    name: str
    owner: uuid.UUID
    description: Optional[str] = ""


class CourseResponse(BaseModel):
    id: str
    name: str


class CourseDetailResponse(CourseResponse):
    description: str
    students: List
    hashtags: List
    teachers: List
    content: List

    class Config:
        orm_mode = True
