import asyncio
from fastapi import status

from app.api import courses, models


async def post(request: models.CourseRequest):
    return await courses.createCourse(request)


async def delete(courseId: str):
    return await courses.deleteCourse(courseId)


async def get_by_id(courseId: str):
    return await courses.getCourse(courseId)


async def get_all(courseName: str = ''):
    return await courses.getCourses(courseName)


async def update(courseId: str, request: models.CourseRequest):
    return await courses.updateCourse(courseId, request)


def test_post_and_get_by_id():
    name = 'test_post_and_get_by_id'
    description = 'descripcion'
    request = models.CourseRequest(name=name, description=description)

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
    request = models.CourseRequest(name=name)

    courseId = asyncio.run(post(request))['id']
    courses = asyncio.run(get_all(name))

    assert courses[-1]["name"] == name

    asyncio.run(delete(courseId))


def test_delete_correctly():
    name = 'test_delete_correctly'
    request = models.CourseRequest(name=name)

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
    request = models.CourseRequest(name=name)
    courseId = asyncio.run(post(request))["id"]

    newName = 'new_name'
    request = models.CourseRequest(name=newName)
    asyncio.run(update(courseId, request))

    courseObtained = asyncio.run(get_by_id(courseId))
    asyncio.run(delete(courseId))

    assert courseObtained["id"] == courseId
    assert courseObtained["name"] == newName

    asyncio.run(delete(courseId))


def test_put_bad_id_returns_400():
    badId = 'abc123'
    name = 'test_put_bad_id_returns_404'
    request = models.CourseRequest(name=name)
    assert asyncio.run(
        update(badId, request)).status_code == status.HTTP_400_BAD_REQUEST


def test_get_all_courses():
    try:
        initialLen = len(asyncio.run(get_all()))
    except TypeError:
        initialLen = 0

    courseId1 = asyncio.run(post(request=models.CourseRequest(name='curso1')
                                 ))["id"]
    courseId2 = asyncio.run(post(request=models.CourseRequest(name='curso1')
                                 ))["id"]
    coursesObtained = asyncio.run(get_all())

    assert len(coursesObtained) == initialLen + 2

    asyncio.run(delete(courseId1))
    asyncio.run(delete(courseId2))
