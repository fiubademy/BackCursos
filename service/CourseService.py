from fastapi import FastAPI, status
from typing import List, Optional
from pydantic.main import BaseModel
from starlette.responses import JSONResponse
import uvicorn
import uuid

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import insert
from sqlalchemy.orm.exc import NoResultFound

DATABASE_URL = "postgresql://jhveahofefzvsq:eb0250343f5b7772d0db89b4c6ac263c7d1c891b956d4f38527acfc2ba0e88b6@ec2-3-221-100-217.compute-1.amazonaws.com:5432/d9bj3e61otop9n"
engine = create_engine(DATABASE_URL)
Base = declarative_base()

app = FastAPI()

courses = {}


class CourseRequest(BaseModel):
    courseName: str
    courseId: str
    Description: Optional[str] = ""
    Students: Optional[List] = []
    Hashtags: Optional[List] = []
    Subscription: Optional[str] = None #TO DO class subscription
    Teachers: Optional[List] = []
    Content: Optional[str] = None #TO DO class content


class CourseResponse(BaseModel):
    courseId: str
    courseName: str


class Course(Base):
    __tablename__ = "courses"
    course_id = Column(String, primary_key=True, nullable=False)
    course_name = Column(String, nullable=False)
    description = Column(String)

# Para relacionar un estudiante a un curso
class StudentsInCourse(Base):
    __tablename__ = "students_in_course"
    user_id = Column(String(500), primary_key = True, nullable = False)
    course_id = Column(String, primary_key=True, nullable=False)
    sub_type = Column(String, nullable=False)

class Hashtags(Base):
    __tablename__ = "hashtags"
    #No se que va aca, yo te armo un modelo mas o menos

class TeachersInCourse(Base):
    __tablename__ = "teachers_in_course"
    user_id = Columns(String(500), primary_key = True, nullable=False)
    course_id = Column(String, primary_key=True, nullable=False)

class ContentInCourse(Base):
    __tablename__ = "content_in_course"
    course_id = Column(String, primary_key=True, nullable=False)
    content_id = column(String, primary_key=True, nullable=False)
    #Agregar lo necesario para el contenido, los IDs son para identificar univocamente a cada contenido...

#class Course:
#    def __init__(self, id: str, courseName: str):
#        self.courseId = id
#        self.courseName = courseName
#        self.description = ""
#        self.students = []
#        self.hashtags = []
#        self.subscription = None
#        self.teachers = []
#        self.content = None

# TODO: Lo que es de aca para abajo hay que modificar todo para adaptarlo al esquema de base.
@app.get('/courses', response_model=List[CourseResponse], status_code=status.HTTP_200_OK)
async def getCourses(courseNameFilter: Optional[str] = None):
    if len(courses) == 0:
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content='No courses found in the database.')
    mensaje = []
    for courseId, course in courses.items():
        if(courseNameFilter is None or not course.courseName.startswith(courseNameFilter)):
            mensaje.append(
                {'courseId': courseId, 'courseName': course.courseName})
    return mensaje


@app.get('/courses/{courseId}', response_model=CourseResponse, status_code=status.HTTP_200_OK)
async def getCourse(courseId=None):
    if courseId is None:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content='Cannot search for null courses.')
    if (courseId not in courses):
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content='Course ' + courseId + ' not found.')
    return {'courseName': courses[courseId].courseName, 'courseId': courses[courseId].courseId}


@app.post('/courses', response_model=CourseResponse, status_code=status.HTTP_201_CREATED)
async def createCourse(courseName):
    courseId = str(uuid.uuid4())
    courses[courseId] = Course(id=courseId, courseName=courseName)
    return {'courseId': courseId, 'courseName': courseName}


@app.delete('/courses/{courseId}', status_code=status.HTTP_202_ACCEPTED)
async def deleteCourse(courseId):
    if (courseId not in courses):
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content='Course ' + courseId + ' not found and will not be deleted.')
    courses.pop(courseId)
    return JSONResponse(status_code=status.HTTP_202_ACCEPTED, content='Course ' + courseId + 'was deleted succesfully.')


@app.patch('/courses/{courseId}')
async def patchCourse(courseId: str, courseName: Optional[str] = None):
    if(courses[courseId] == None):
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content='Course ' + courseId + ' not found and will not be patched.')
    if(courseName is not None):
        courses[courseId].courseName = courseName
    return {'courseId': courseId, 'courseName': courses[courseId].courseName}

Session = sessionmaker(bind=engine)
session = Session()

if __name__ == '__main__':
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    uvicorn.run(app, host='0.0.0.0', port=8000)
