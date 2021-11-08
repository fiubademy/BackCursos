from fastapi import status, APIRouter
from typing import List, Optional
from fastapi.param_functions import Query
from starlette.responses import JSONResponse
from sqlalchemy.exc import DataError
from sqlalchemy.orm import sessionmaker

from api.models import CourseRequest, CourseResponse, CourseDetailResponse
from db import Course, Student, Teacher, Hashtag

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
async def get_all(nameFilter: Optional[str] = ''):
    mensaje = []
    if nameFilter != '':
        courses = session.query(Course).filter(
            Course.name.ilike("%"+nameFilter+"%"))
    else:
        courses = session.query(Course)
    if courses.first() is None:
        return JSONResponse(status_code=404, content="No courses found")
    for course in courses:
        mensaje.append(
            {'id': str(course.id), 'name': course.name})
    return mensaje


@router.get('/{id}', response_model=CourseResponse)
async def get_by_id(id: str = Query(...)):
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


@router.get('/user/{userId}', response_model=List[CourseResponse])
async def get_by_user(userId: str = Query(...)):
    userCourses = []
    try:
        user = session.get(Student, userId)
    except DataError:
        session.rollback()
        return JSONResponse(
            status_code=400, content='Invalid user id.')
    if user is None:
        return JSONResponse(status_code=404, content="No courses found")
    for course in user.courses:
        userCourses.append(
            {'id': str(course.id), 'name': course.name})
    return userCourses


@router.post('', response_model=CourseResponse, status_code=status.HTTP_201_CREATED)
async def create(request: CourseRequest):
    new = Course(**request.dict(exclude_unset=True))
    session.add(new)
    session.commit()
    return {'id': str(new.id), 'name': new.name}


@ router.delete('/{id}')
async def delete(id: str):
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
async def update(id: str, request: CourseRequest):
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
    return {'id': course.id, 'name': course.name}


@ router.get('/{courseId}/students')
async def get_students(courseId: str):
    students = []
    try:
        course = session.get(Course, courseId)
    except DataError:
        session.rollback()
        return JSONResponse(
            status_code=400, content='Invalid id.')
    if course is None:
        return JSONResponse(
            status_code=404, content='Course ' + courseId + ' not found.')
    if len(course.students) == 0:
        return JSONResponse(status_code=404, content='No users found.')
    for user in course.students:
        students.append({'id': user.userId})
    return students


@ router.post('/{courseId}/add_student/{userId}')
async def add_student(courseId: str, userId: str):
    # No se valida que el id de usuario sea correcto
    try:
        course = session.get(Course, courseId)
    except DataError:
        session.rollback()
        return JSONResponse(
            status_code=400, content='Invalid course id.')
    if course is None:
        return JSONResponse(
            status_code=404, content='Course ' + courseId + ' not found.')
    course.students.append(Student(userId=userId))
    return {'courseId': course.id, 'name': course.name}


@ router.get('/{courseId}/colaborators')
async def get_colaborators(courseId: str):
    colaborators = []
    try:
        course = session.get(Course, courseId)
    except DataError:
        session.rollback()
        return JSONResponse(
            status_code=400, content='Invalid id.')
    if course is None:
        return JSONResponse(
            status_code=404, content='Course ' + courseId + ' not found.')
    if len(course.teachers) == 0:
        return JSONResponse(status_code=404, content='No colaborators found.')
    for user in course.teachers:
        colaborators.append({'id': user.userId})
    return colaborators


@ router.post('/{courseId}/add_colaborator/{userId}')
async def add_colaborator(courseId: str, userId: str):
    # No se valida que el id de usuario sea correcto
    try:
        course = session.get(Course, courseId)
    except DataError:
        session.rollback()
        return JSONResponse(
            status_code=400, content='Invalid course id.')
    if course is None:
        return JSONResponse(
            status_code=404, content='Course ' + courseId + ' not found.')
    course.teachers.append(Teacher(userId=userId))
    return {'courseId': course.id, 'name': course.name}


@ router.get('/{courseId}/hashtags')
async def get_hashtags(courseId: str):
    hashtags = []
    try:
        course = session.get(Course, courseId)
    except DataError:
        session.rollback()
        return JSONResponse(
            status_code=400, content='Invalid id.')
    if course is None:
        return JSONResponse(
            status_code=404, content='Course ' + courseId + ' not found.')
    if len(course.hashtags) == 0:
        return JSONResponse(status_code=404, content='No hashtags found.')
    for hashtag in course.hashtags:
        hashtags.append({'hashtag': hashtag.tag})
    return hashtags


@ router.post('/{courseId}/add_hashtag/{tag}')
async def add_hashtag(courseId: str, tag: str):
    try:
        course = session.get(Course, courseId)
    except DataError:
        session.rollback()
        return JSONResponse(
            status_code=400, content='Invalid course id.')
    if course is None:
        return JSONResponse(
            status_code=404, content='Course ' + courseId + ' not found.')
    course.hashtags.append(Hashtag(tag=tag))
    return {'courseId': course.id, 'name': course.name}
