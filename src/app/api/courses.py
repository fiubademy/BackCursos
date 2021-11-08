from fastapi import status, APIRouter
from typing import List, Optional
from fastapi.param_functions import Query
from starlette.responses import JSONResponse
from sqlalchemy.exc import DataError
from sqlalchemy.orm import sessionmaker

from app.api.models import CourseRequest, CourseResponse, CourseDetailResponse
from app.db import Course


router = APIRouter()

session = None
engine = None


def set_engine(engine_rcvd):
    global engine
    global session
    engine = engine_rcvd
    session = sessionmaker(bind=engine)()
    return session


@router.get('', response_model=List[CourseResponse])
async def getCourses(nameFilter: Optional[str] = ''):
    mensaje = []
    courses = session.query(Course).filter(
        Course.name.ilike("%"+nameFilter+"%"))
    if courses.first() is None:
        return JSONResponse(status_code=404, content="No courses found")
    for course in courses:
        mensaje.append(
            {'id': str(course.id), 'name': course.name})
    return mensaje


@router.get('/{id}', response_model=CourseResponse)
async def getCourse(id: str = Query(...)):
    try:
        course = session.get(Course, id)
    except DataError:
        session.rollback()
        return JSONResponse(
            status_code=400, content='Invalid id.')
    if course is None:
        return JSONResponse(
            status_code=404, content='Course ' + id + ' not found.')
    return {'name': course.name, 'id': str(course.id)}


@router.post('', response_model=CourseResponse, status_code=status.HTTP_201_CREATED)
async def createCourse(request: CourseRequest):
    new = Course(**request.dict(exclude_unset=True))
    session.add(new)
    session.commit()
    return {'id': str(new.id), 'name': new.name}


@ router.delete('/{id}')
async def deleteCourse(id: str):
    try:
        course = session.get(Course, id)
    except DataError:
        session.rollback()
        return JSONResponse(status_code=400, content='Invalid id.')
    if course is None:
        return JSONResponse(status_code=404, content='Course ' +
                            id + ' not found and will not be deleted.')
    session.delete(course)
    session.commit()
    return JSONResponse(status_code=status.HTTP_202_ACCEPTED, content='Course ' + id + ' was deleted succesfully.')


@ router.put('/{id}')
async def updateCourse(id: str, request: CourseRequest):
    try:
        course = session.get(Course, id)
    except DataError:
        session.rollback()
        return JSONResponse(status_code=400, content='Invalid id.')
    if course is None:
        return JSONResponse(status_code=404, content='Course ' +
                            id + ' not found and will not be deleted.')
    attributes = request.dict(exclude_unset=True)
    attributes['id'] = course.id
    course = Course(**attributes)
    session.merge(course)
    session.commit()
    return {'course_id': course.id, 'name': course.name}
