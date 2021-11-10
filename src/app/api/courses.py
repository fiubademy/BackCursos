from fastapi import status, APIRouter
from typing import List, Optional
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
    response = []
    if nameFilter != '':
        courses = session.query(Course).filter(
            Course.name.ilike("%"+nameFilter+"%"))
    else:
        courses = session.query(Course)
    if courses.first() is None:
        return JSONResponse(status_code=404, content="No courses found")
    for course in courses:
        response.append({'id': str(course.id), 'name': course.name})
    return response


@router.get('/{id}', response_model=CourseResponse)
async def get_by_id(id: str):
    try:
        course = session.get(Course, id)
    except DataError:
        session.rollback()
        return JSONResponse(status_code=400, content='Invalid id.')
    if course is None:
        return JSONResponse(status_code=404, content='Course ' + id + ' not found.')
    return {'name': course.name, 'id': str(course.id)}


@router.get('/student/{userId}', response_model=List[CourseResponse])
async def get_by_student(userId: str):
    userCourses = []
    try:
        user = session.get(Student, userId)
    except DataError:
        session.rollback()
        return JSONResponse(status_code=400, content='Invalid user id.')
    if user is None:
        return JSONResponse(status_code=404, content="No courses found")
    for course in user.courses:
        userCourses.append(
            {'id': str(course.id), 'name': course.name})
    if len(userCourses) == 0:
        return JSONResponse(status_code=404, content="No courses found")
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
        return JSONResponse(status_code=404, content='Course ' + id + ' not found and will not be deleted.')
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
        return JSONResponse(status_code=404, content='Course ' + id + ' not found and will not be updated.')
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
        return JSONResponse(status_code=400, content='Invalid id.')
    if course is None:
        return JSONResponse(status_code=404, content='Course ' + courseId + ' not found.')
    if len(course.students) == 0:
        return JSONResponse(status_code=404, content='No users found.')
    for user in course.students:
        students.append({'id': user.user_id})
    return students


@ router.post('/{courseId}/add_student/{userId}')
async def add_student(courseId: str, userId: str):
    try:
        course = session.get(Course, courseId)
    except DataError:
        session.rollback()
        return JSONResponse(status_code=400, content='Invalid course id.')
    if course is None:
        return JSONResponse(status_code=404, content='Course ' + courseId + ' not found.')

    try:
        student = session.get(Student, userId)
    except DataError:
        session.rollback()
        return JSONResponse(status_code=400, content='Invalid user id.')
    if student is None:
        course.students.append(Student(user_id=userId))
    elif student not in course.students:
        course.students.append(student)
    return JSONResponse(status_code=status.HTTP_201_CREATED, content='Student ' + userId + ' added succesfully.')


@ router.delete('/{courseId}/remove_student/{userId}')
async def remove_student(courseId: str, userId: str):
    try:
        course = session.get(Course, courseId)
    except DataError:
        session.rollback()
        return JSONResponse(status_code=400, content='Invalid course id.')
    if course is None:
        return JSONResponse(status_code=404, content='Course ' + id + ' not found.')

    for student in course.students:
        if student.user_id == userId:
            course.students.remove(student)
            break
    session.commit()
    return JSONResponse(status_code=status.HTTP_202_ACCEPTED, content='Student ' + userId + ' was removed succesfully.')


@ router.get('/{courseId}/collaborators')
async def get_collaborators(courseId: str):
    collaborators = []
    try:
        course = session.get(Course, courseId)
    except DataError:
        session.rollback()
        return JSONResponse(status_code=400, content='Invalid id.')
    if course is None:
        return JSONResponse(status_code=404, content='Course ' + courseId + ' not found.')
    if len(course.teachers) == 0:
        return JSONResponse(status_code=404, content='No collaborators found.')
    for user in course.teachers:
        collaborators.append({'id': user.user_id})
    return collaborators


@ router.post('/{courseId}/add_collaborator/{userId}')
async def add_collaborator(courseId: str, userId: str):
    try:
        course = session.get(Course, courseId)
    except DataError:
        session.rollback()
        return JSONResponse(status_code=400, content='Invalid course id.')
    if course is None:
        return JSONResponse(status_code=404, content='Course ' + courseId + ' not found.')

    try:
        teacher = session.get(Teacher, userId)
    except DataError:
        session.rollback()
        return JSONResponse(status_code=400, content='Invalid user id.')
    if teacher is None:
        course.teachers.append(Teacher(user_id=userId))
    elif teacher not in course.teachers:
        course.teachers.append(teacher)
    return JSONResponse(status_code=status.HTTP_201_CREATED, content='Collaborator ' + userId + ' added succesfully.')


@ router.delete('/{courseId}/remove_collaborator/{userId}')
async def remove_collaborator(courseId: str, userId: str):
    try:
        course = session.get(Course, courseId)
    except DataError:
        session.rollback()
        return JSONResponse(status_code=400, content='Invalid course id.')
    if course is None:
        return JSONResponse(status_code=404, content='Course ' + id + ' not found.')

    for teacher in course.teachers:
        if teacher.user_id == userId:
            course.teachers.remove(teacher)
            break
    session.commit()
    return JSONResponse(status_code=status.HTTP_202_ACCEPTED, content='Collaborator ' + userId + ' was removed succesfully.')


@ router.get('/{courseId}/hashtags')
async def get_hashtags(courseId: str):
    hashtags = []
    try:
        course = session.get(Course, courseId)
    except DataError:
        session.rollback()
        return JSONResponse(status_code=400, content='Invalid id.')
    if course is None:
        return JSONResponse(
            status_code=404, content='Course ' + courseId + ' not found.')
    if len(course.hashtags) == 0:
        return JSONResponse(status_code=404, content='No hashtags found.')
    for hashtag in course.hashtags:
        hashtags.append({'hashtag': hashtag.tag})
    return hashtags


@ router.post('/{courseId}/add_hashtag/{tag}')
async def add_hashtags(courseId: str, tags: List[str]):
    try:
        course = session.get(Course, courseId)
    except DataError:
        session.rollback()
        return JSONResponse(status_code=400, content='Invalid course id.')
    if course is None:
        return JSONResponse(status_code=404, content='Course ' + courseId + ' not found.')

    for tag in tags:
        hashtag = session.query(Hashtag).filter(Hashtag.tag == tag).first()
        if hashtag is None:
            course.hashtags.append(Hashtag(tag=tag))
        elif hashtag not in course.hashtags:
            course.hashtags.append(hashtag)
    return JSONResponse(status_code=status.HTTP_201_CREATED, content='Hashtags added succesfully.')


@ router.delete('/{courseId}/remove_hashtag/{tag}')
async def remove_hashtag(courseId: str, tag: str):
    try:
        course = session.get(Course, courseId)
    except DataError:
        session.rollback()
        return JSONResponse(status_code=400, content='Invalid course id.')
    if course is None:
        return JSONResponse(status_code=404, content='Course ' + id + ' not found.')

    for hashtag in course.hashtags:
        if hashtag.tag == tag:
            course.hashtags.remove(hashtag)
            break
    session.commit()
    return JSONResponse(status_code=status.HTTP_202_ACCEPTED, content='Hashtag \'' + tag + '\' was removed succesfully.')


@router.get('/hashtag/{tag}')
async def get_by_hashtag(tag: str):
    response = []
    courses = session.query(Course).filter(
        Course.hashtags.any(tag=tag))
    if courses.first() is None:
        return JSONResponse(status_code=404, content="No courses found")
    for course in courses:
        response.append(
            {'id': str(course.id), 'name': course.name})
    return response


@router.get('/{courseId}/owner')
async def get_owner(courseId: str):
    try:
        course = session.get(Course, courseId)
    except DataError:
        session.rollback()
        return JSONResponse(status_code=400, content='Invalid course id.')
    if course is None:
        return JSONResponse(status_code=404, content='Course ' + id + ' not found.')
    return {"ownerId": course.owner}


@router.put('/{courseId}/block')
async def block(courseId: str, block: bool = True):
    try:
        course = session.get(Course, courseId)
    except DataError:
        session.rollback()
        return JSONResponse(status_code=400, content='Invalid course id.')
    if course is None:
        return JSONResponse(status_code=404, content='Course ' + id + ' not found.')
    course.blocked = block
    if block is True:
        return JSONResponse(status_code=status.HTTP_202_ACCEPTED, content='Course ' + courseId + ' was blocked succesfully.')
    else:
        return JSONResponse(status_code=status.HTTP_202_ACCEPTED, content='Course ' + courseId + ' was unblocked succesfully.')


@router.put('/{courseId}/status')
async def change_status(courseId: str, in_edition: bool):
    try:
        course = session.get(Course, courseId)
    except DataError:
        session.rollback()
        return JSONResponse(status_code=400, content='Invalid course id.')
    if course is None:
        return JSONResponse(status_code=404, content='Course ' + id + ' not found.')
    course.in_edition = in_edition
    return JSONResponse(status_code=status.HTTP_202_ACCEPTED, content='Course ' + courseId + ' status was updated succesfully.')
