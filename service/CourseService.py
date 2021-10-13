from fastapi import FastAPI, status
from typing import List, Optional
from pydantic.main import BaseModel
from starlette.responses import JSONResponse
import uvicorn
import uuid

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


class Course:
    def __init__(self, id: str, courseName: str):
        self.courseId = id
        self.courseName = courseName
        self.description = ""
        self.students = []
        self.hashtags = []
        self.subscription = None
        self.teachers = []
        self.content = None


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


if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8000)
