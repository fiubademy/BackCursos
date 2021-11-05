import asyncio
import uuid
from fastapi import status

from app.api import courses
from app.api.models import CourseRequest


async def post(request: CourseRequest):
    return await courses.create(request)


async def delete(courseId: str):
    return await courses.delete(courseId)


async def get_by_id(courseId: str):
    return await courses.get_by_id(courseId)


async def get_all(courseName: str = ''):
    return await courses.get_all(courseName)


async def get_by_user(userId: str):
    return await courses.get_by_user(userId)


async def update(courseId: str, request: CourseRequest):
    return await courses.update(courseId, request)


async def get_students(courseId: str):
    return await courses.get_students(courseId)


async def add_student(courseId: str, userId: str):
    return await courses.add_student(courseId, userId)


def test_post_and_get_by_id():
    name = 'test_post_and_get_by_id'
    description = 'descripcion'
    request = CourseRequest(name=name, description=description)

    courseId = asyncio.run(post(request))["id"]
    courseObtained = asyncio.run(get_by_id(courseId))

    assert courseObtained["id"] == courseId
    assert courseObtained["name"] == name

    asyncio.run(delete(courseId))


def test_get_by_bad_id_returns_400():
    badId = 'abc123'
    assert asyncio.run(
        get_by_id(badId)).status_code == status.HTTP_400_BAD_REQUEST


def test_post_and_get_by_name():
    name = 'test_post_and_get_by_name'
    teacherId = str(uuid.uuid4())
    userId = str(uuid.uuid4())
    request = CourseRequest(name=name, description='descripcion', teachers=[
                            teacherId], students=[userId], hashtags=['cursos'])

    courseId = asyncio.run(post(request))['id']
    courses = asyncio.run(get_all(name))

    assert courses[-1]["name"] == name

    asyncio.run(delete(courseId))


def test_delete_correctly():
    name = 'test_delete_correctly'
    request = CourseRequest(name=name)

    courseId = asyncio.run(post(request))["id"]
    asyncio.run(delete(courseId))

    assert asyncio.run(get_by_id(courseId)
                       ).status_code == status.HTTP_404_NOT_FOUND


def test_delete_bad_id_returns_400():
    badId = 'abc123'
    assert asyncio.run(
        delete(badId)).status_code == status.HTTP_400_BAD_REQUEST


def test_put_course_correctly():
    name = 'test_put_course_correctly'
    request = CourseRequest(name=name)
    courseId = asyncio.run(post(request))["id"]

    newName = 'new_name'
    request = CourseRequest(name=newName)
    asyncio.run(update(courseId, request))

    courseObtained = asyncio.run(get_by_id(courseId))
    asyncio.run(delete(courseId))

    assert courseObtained["id"] == courseId
    assert courseObtained["name"] == newName

    asyncio.run(delete(courseId))


def test_put_bad_id_returns_400():
    badId = 'abc123'
    name = 'test_put_bad_id_returns_404'
    request = CourseRequest(name=name)
    assert asyncio.run(
        update(badId, request)).status_code == status.HTTP_400_BAD_REQUEST


def test_get_all_courses():
    try:
        initialLen = len(asyncio.run(get_all()))
    except TypeError:
        initialLen = 0

    courseId1 = asyncio.run(post(request=CourseRequest(name='curso1')
                                 ))["id"]
    courseId2 = asyncio.run(post(request=CourseRequest(name='curso1')
                                 ))["id"]
    coursesObtained = asyncio.run(get_all())

    assert len(coursesObtained) == initialLen + 2

    asyncio.run(delete(courseId1))
    asyncio.run(delete(courseId2))


def test_get_by_user():
    name = 'test_get_by_user'
    userId = str(uuid.uuid4())
    courseId = asyncio.run(
        post(CourseRequest(name=name, students=[userId])))["id"]

    courses = asyncio.run(get_by_user(userId))
    course = {
        'id': courseId,
        'name': name
    }
    assert course in courses

    asyncio.run(delete(courseId))


# def test_get_students():


def test_add_student():
    courseId = asyncio.run(post(CourseRequest(name='test_add_student')))["id"]
    userId = str(uuid.uuid4())
    asyncio.run(add_student(courseId, userId))

    students = asyncio.run(get_students(courseId))
    user = {
        'id': userId
    }
    assert user in students

    asyncio.run(delete(courseId))
