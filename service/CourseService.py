import enum
from fastapi import FastAPI, status
from typing import List, Optional
from pydantic.main import BaseModel
from starlette.responses import JSONResponse
import uvicorn
import uuid

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Table, Column, ForeignKey, Integer, String
from sqlalchemy import create_engine, insert
from sqlalchemy.orm import relation, sessionmaker, relationship
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.dialects.postgresql import UUID
from fastapi.middleware.cors import CORSMiddleware

origins = ["*"]

DATABASE_URL = "postgresql://jhveahofefzvsq:eb0250343f5b7772d0db89b4c6ac263c7d1c891b956d4f38527acfc2ba0e88b6@ec2-3-221-100-217.compute-1.amazonaws.com:5432/d9bj3e61otop9n"

engine = create_engine(DATABASE_URL)
Base = declarative_base()
Session = sessionmaker(bind=engine)
session = Session()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class CourseRequest(BaseModel):
    courseName: str
    courseId: str
    Description: Optional[str] = ""
    Students: Optional[List] = []
    Hashtags: Optional[List] = []
    Teachers: Optional[List] = []
    Content: Optional[str] = None


class CourseResponse(BaseModel):
    courseId: str
    courseName: str


class Course(Base):
    __tablename__ = "courses"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    description = Column(String)


@app.get('/courses', response_model=List[CourseResponse], status_code=status.HTTP_200_OK)
async def getCourses(courseNameFilter: Optional[str] = ''):
    mensaje = []
    try:
        courses = session.query(Course).filter(
            Course.name.like("%"+courseNameFilter+"%"))
    except NoResultFound:
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content='No users found in the database.')
    if (courses.count() == 0):
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content='No users found in the database.')
    for course in courses:
        mensaje.append({'courseId': str(course.id), 'courseName': course.name})
    return mensaje


@ app.get('/courses/{courseId}', response_model=CourseResponse, status_code=status.HTTP_200_OK)
async def getCourse(courseId: str = ''):
    if courseId == '':
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content='Cannot search for null courses.')
    try:
        course = session.query(Course).get(courseId)
    except NoResultFound:
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content='Course ' + courseId + ' not found.')
    return {'courseName': course.name, 'courseId': str(course.id)}


@ app.post('/courses', response_model=CourseResponse, status_code=status.HTTP_201_CREATED)
async def createCourse(courseName: str, courseDescription: str = ''):
    newCourse = Course(name=courseName, description=courseDescription)
    session.add(newCourse)
    session.commit()
    return {'courseId': str(newCourse.id), 'courseName': newCourse.name}


@ app.delete('/courses/{courseId}', status_code=status.HTTP_202_ACCEPTED)
async def deleteCourse(courseId: str):
    try:
        course = session.query(Course).get(courseId)
    except NoResultFound:
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content='Course ' + courseId + ' not found and will not be deleted.')
    session.delete(course)
    session.commit()
    return JSONResponse(status_code=status.HTTP_202_ACCEPTED, content='Course ' + courseId + ' was deleted succesfully.')


@ app.patch('/courses/{courseId}')
async def patchCourse(courseId: str, courseName: Optional[str] = None):
    try:
        course = session.query(Course).get(courseId)
    except NoResultFound:
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content='Course ' + courseId + ' not found and will not be patched.')
    if(courseName is not None):
        course.name = courseName
    session.add(course)
    session.commit()
    return {'course_id': courseId, 'course_name': courseName}


if __name__ == '__main__':
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    uvicorn.run(app, host='0.0.0.0', port=8000)
