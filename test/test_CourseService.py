import pytest
import asyncio
from fastapi import status

from service import CourseService


@pytest.mark.asyncio
async def post(courseName: str):
    return await CourseService.createCourse(courseName)


@pytest.mark.asyncio
async def delete(courseId: str):
    return await CourseService.deleteCourse(courseId)


@pytest.mark.asyncio
async def get_by_id(courseId: str):
    return await CourseService.getCourse(courseId)


@pytest.mark.asyncio
async def get_all(courseName: str = ''):
    return await CourseService.getCourses(courseName)


@pytest.mark.asyncio
async def patch(courseId: str, courseName: str = None, courseDescription: str = None):
    return await CourseService.patchCourse(courseId=courseId, courseName=courseName, courseDescription=courseDescription)


def test_post_and_get_by_id():
    name = 'curso-test'
    courseId = asyncio.run(post(name))["courseId"]
    course_obtained = asyncio.run(get_by_id(courseId))
    asyncio.run(delete(courseId))

    assert course_obtained["courseId"] == courseId
    assert course_obtained["courseName"] == name


def test_post_and_get_by_name():
    name = 'curso-test'
    courseId = asyncio.run(post(name))["courseId"]
    courses = asyncio.run(get_all(name))
    asyncio.run(delete(courseId))

    assert len(courses) == 1
    assert courses[0]["courseId"] == courseId
    assert courses[0]["courseName"] == name


def test_delete_correctly():
    name = 'curso-test'
    courseId = asyncio.run(post(name))["courseId"]
    asyncio.run(delete(courseId))

    assert asyncio.run(get_by_id(courseId)
                       ).status_code == status.HTTP_404_NOT_FOUND


def test_patch_course_correctly():
    name = 'name'
    newName = 'newname'
    courseId = asyncio.run(post(name))["courseId"]
    asyncio.run(patch(courseId, newName))
    course_obtained = asyncio.run(get_by_id(courseId))
    asyncio.run(delete(courseId))

    assert course_obtained["courseId"] == courseId
    assert course_obtained["courseName"] == newName


def test_get_all_courses():
    courseId1 = asyncio.run(post('curso1'))["courseId"]
    courseId2 = asyncio.run(post('curso2'))["courseId"]
    coursesObtained = asyncio.run(get_all())
    asyncio.run(delete(courseId1))
    asyncio.run(delete(courseId2))

    assert len(coursesObtained) == 2
    assert coursesObtained[0]["courseId"] == courseId1
    assert coursesObtained[1]["courseId"] == courseId2


def test_get_by_wrong_id_returns_404():
    wrongId = 'abc123'
    assert asyncio.run(get_by_id(wrongId)
                       ).status_code == status.HTTP_404_NOT_FOUND


def test_get_all_on_empty_db_returns_404():
    assert asyncio.run(get_all()).status_code == status.HTTP_404_NOT_FOUND


def test_delete_wrong_id_returns_404():
    wrongId = 'abc123'
    assert asyncio.run(
        delete(wrongId)).status_code == status.HTTP_404_NOT_FOUND


def test_patch_wrong_id_returns_404():
    wrongId = 'abc123'
    assert asyncio.run(patch(wrongId, courseName='name')
                       ).status_code == status.HTTP_404_NOT_FOUND
