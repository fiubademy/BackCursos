from pydantic import BaseModel, Field
from uuid import UUID
from typing import List, Optional
from fastapi import Query


class CourseBase(BaseModel):
    sub_level: Optional[int] = Field(None, ge=0, le=2)
    latitude: Optional[float] = Field(None, ge=-180, le=180)
    longitude: Optional[float] = Field(None, ge=-90, le=90)
    category: Optional[str]


class Hashtags(BaseModel):
    tags: List[str] = Field(..., min_len=1)


class CourseCreate(CourseBase):
    name: str
    owner: UUID
    description: Optional[str] = ""
    hashtags: Optional[List] = []


class CourseUpdate(CourseBase):
    name: Optional[str]
    owner: Optional[UUID]
    description: Optional[str]


class CourseFilter:
    def __init__(
        self,
        id: Optional[UUID] = None,
        name: Optional[str] = None,
        owner: Optional[UUID] = None,
        description: Optional[str] = None,
        sub_level: Optional[int] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        student: Optional[UUID] = None,
        collaborator: Optional[UUID] = None,
        hashtags: Optional[List[str]] = Query(None),
        minRating: Optional[int] = None,
        category: Optional[str] = None
    ):
        self.id = id
        self.name = name
        self.owner = owner
        self.description = description
        self.sub_level = sub_level
        self.latitude = latitude
        self.longitude = longitude
        self.student = student
        self.collaborator = collaborator
        self.hashtags = hashtags
        self.minRating = minRating
        self.category = category


class ContentCreate(BaseModel):
    name: str
    link: str


class ReviewCreate(BaseModel):
    user_id: UUID
    description: Optional[str] = Field(None, max_length=500)
    rating: int = Field(..., ge=1, le=5)
