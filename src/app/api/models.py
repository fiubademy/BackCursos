from pydantic import BaseModel, validator
import uuid
from typing import List, Optional


class CourseRequest(BaseModel):
    name: str
    owner: uuid.UUID
    description: Optional[str] = ""
    sub_level: Optional[int]
    latitude: Optional[float]
    longitude: Optional[float]
    hashtags: Optional[List] = []


class CourseUpdate(BaseModel):
    name: Optional[str]
    owner: Optional[uuid.UUID]
    description: Optional[str]
    sub_level: Optional[int]
    latitude: Optional[float]
    longitude: Optional[float]

    @validator('sub_level')
    def sub_level_valid(cls, v):
        if v > 2 or v < 0:
            raise ValueError(
                'valid subscription levels are 0 (Free), 1 (Standard), 2 (Premium)')
        return v
