from pydantic import BaseModel, validator
from uuid import UUID
from typing import List, Optional


class CourseBase(BaseModel):
    sub_level: Optional[int]
    latitude: Optional[float]
    longitude: Optional[float]

    @validator('sub_level')
    def sub_level_valid(cls, v):
        if v > 2 or v < 0:
            raise ValueError(
                'valid subscription levels are 0 (Free), 1 (Standard), 2 (Premium)')
        return v

    @validator('latitude')
    def latitude_valid(cls, latitude):
        if latitude > 90 or latitude < -90:
            raise ValueError(
                'No a valid latitude. It must be between -90 and 90')
        return latitude

    @validator('longitude')
    def longitude_valid(cls, longitude):
        if longitude > 180 or longitude < -180:
            raise ValueError(
                'No a valid longitude. It must be between 180 and -180')
        return longitude


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
        hashtag: Optional[str] = None
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
        self.hashtag = hashtag
