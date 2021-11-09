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


async def get_by_student(userId: str):
    return await courses.get_by_student(userId)


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


def test_get_by_id_inexistent_course_returns_404():
    inexistentId = str(uuid.uuid4())
    assert asyncio.run(
        get_by_id(inexistentId)).status_code == status.HTTP_404_NOT_FOUND


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

    courseId3 = asyncio.run(post(request=CourseRequest(name='curso2')
                                 ))["id"]
    newLen = len(asyncio.run(get_all()))

    assert newLen == initialLen + 3

    asyncio.run(delete(courseId1))
    asyncio.run(delete(courseId2))
    asyncio.run(delete(courseId3))


def test_get_by_student():
    name = 'test_get_by_student'
    userId = str(uuid.uuid4())
    courseId = asyncio.run(
        post(CourseRequest(name=name, students=[userId])))["id"]

    courses = asyncio.run(get_by_student(userId))
    course = {
        'id': courseId,
        'name': name
    }
    assert course in courses

    asyncio.run(delete(courseId))


def test_get_by_user_inexistent_returns_404():
    name = 'test_get_by_user_inexistent_returns_404'
    userId1 = str(uuid.uuid4())
    userId2 = str(uuid.uuid4())
    courseId = asyncio.run(
        post(CourseRequest(name=name, students=[userId1])))["id"]

    assert asyncio.run(get_by_student(
        userId2)).status_code == status.HTTP_404_NOT_FOUND

    asyncio.run(delete(courseId))


def test_add_and_get_students():
    courseId = asyncio.run(post(CourseRequest(name='test_add_student')))["id"]
    userId1 = str(uuid.uuid4())
    userId2 = str(uuid.uuid4())
    asyncio.run(add_student(courseId, userId1))
    asyncio.run(add_student(courseId, userId2))

    students = asyncio.run(get_students(courseId))
    user1 = {'id': userId1}
    user2 = {'id': userId2}
    assert user1 in students
    assert user2 in students

    asyncio.run(delete(courseId))


def test_get_students_on_empty_course_returns_404():
    courseId = asyncio.run(post(CourseRequest(name='test_add_student')))["id"]

    assert asyncio.run(get_students(courseId)
                       ).status_code == status.HTTP_404_NOT_FOUND

    asyncio.run(delete(courseId))
