from pydantic import BaseModel, Field

from typing import List, Optional


class CourseRequest(BaseModel):
    name: str
    owner: str
    description: Optional[str] = ""
    students: Optional[List] = []
    hashtags: Optional[List] = []
    teachers: Optional[List] = []
    content: Optional[List] = []


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
