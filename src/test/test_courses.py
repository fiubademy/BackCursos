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


async def get_collaborators(courseId: str):
    return await courses.get_collaborators(courseId)


async def add_collaborator(courseId: str, userId: str):
    return await courses.add_collaborator(courseId, userId)


async def get_hashtags(courseId: str):
    return await courses.get_hashtags(courseId)


async def add_hashtags(courseId: str, tag: str):
    return await courses.add_hashtags(courseId, tag)


async def get_by_hashtag(tag: str):
    return await courses.get_by_hashtag(tag)


def test_post_and_get_by_id():
    name = 'test_post_and_get_by_id'
    description = 'descripcion'
    ownerId = str(uuid.uuid4())
    request = CourseRequest(name=name, owner=ownerId, description=description)

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
    ownerId = str(uuid.uuid4())
    request = CourseRequest(owner=ownerId, name=name,
                            description='descripcion')

    courseId = asyncio.run(post(request))['id']
    courses = asyncio.run(get_all(name))

    assert courses[0]["id"] == courseId

    asyncio.run(delete(courseId))


def test_delete_correctly():
    name = 'test_delete_correctly'
    ownerId = str(uuid.uuid4())
    request = CourseRequest(owner=ownerId, name=name)

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
    ownerId = str(uuid.uuid4())
    request = CourseRequest(owner=ownerId, name=name)
    courseId = asyncio.run(post(request))["id"]

    newName = 'new_name'
    ownerId = str(uuid.uuid4())
    request = CourseRequest(owner=ownerId, name=newName)
    asyncio.run(update(courseId, request))

    courseObtained = asyncio.run(get_by_id(courseId))
    asyncio.run(delete(courseId))

    assert courseObtained["id"] == courseId
    assert courseObtained["name"] == newName

    asyncio.run(delete(courseId))


def test_put_bad_id_returns_400():
    badId = 'abc123'
    name = 'test_put_bad_id_returns_404'
    ownerId = str(uuid.uuid4())
    request = CourseRequest(owner=ownerId, name=name)
    assert asyncio.run(
        update(badId, request)).status_code == status.HTTP_400_BAD_REQUEST


def test_get_all_courses():
    try:
        initialLen = len(asyncio.run(get_all()))
    except TypeError:
        initialLen = 0
    ownerId = str(uuid.uuid4())
    courseId1 = asyncio.run(post(request=CourseRequest(owner=ownerId, name='curso1')
                                 ))["id"]
    courseId2 = asyncio.run(post(request=CourseRequest(owner=ownerId, name='curso1')
                                 ))["id"]

    courseId3 = asyncio.run(post(request=CourseRequest(owner=ownerId, name='curso2')
                                 ))["id"]
    newLen = len(asyncio.run(get_all()))

    assert newLen == initialLen + 3

    asyncio.run(delete(courseId1))
    asyncio.run(delete(courseId2))
    asyncio.run(delete(courseId3))


def test_get_by_student():
    name = 'test_get_by_student'
    ownerId = str(uuid.uuid4())
    userId = str(uuid.uuid4())
    courseId = asyncio.run(
        post(CourseRequest(owner=ownerId, name=name)))["id"]
    asyncio.run(add_student(courseId, userId))

    courses = asyncio.run(get_by_student(userId))

    assert {'id': courseId} in courses

    asyncio.run(delete(courseId))


def test_get_by_user_inexistent_returns_404():
    name = 'test_get_by_user_inexistent_returns_404'
    ownerId = str(uuid.uuid4())
    userId1 = str(uuid.uuid4())
    userId2 = str(uuid.uuid4())
    courseId = asyncio.run(
        post(CourseRequest(owner=ownerId, name=name)))["id"]
    asyncio.run(add_student(courseId, userId1))

    assert asyncio.run(get_by_student(
        userId2)).status_code == status.HTTP_404_NOT_FOUND

    asyncio.run(delete(courseId))


def test_add_and_get_students():
    ownerId = str(uuid.uuid4())
    courseId = asyncio.run(
        post(CourseRequest(owner=ownerId, name='test_add_and_get_students')))["id"]
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


def test_add_and_get_collaborators():
    ownerId = str(uuid.uuid4())
    courseId = asyncio.run(
        post(CourseRequest(owner=ownerId, name='test_add_and_get_collaborators')))["id"]
    userId1 = str(uuid.uuid4())
    userId2 = str(uuid.uuid4())
    asyncio.run(add_collaborator(courseId, userId1))
    asyncio.run(add_collaborator(courseId, userId2))

    collaborators = asyncio.run(get_collaborators(courseId))
    user1 = {'id': userId1}
    user2 = {'id': userId2}
    assert user1 in collaborators
    assert user2 in collaborators

    asyncio.run(delete(courseId))


def test_add_and_get_hashtags():
    ownerId = str(uuid.uuid4())
    courseId = asyncio.run(
        post(CourseRequest(owner=ownerId, name='test_add_and_get_hashtags')))["id"]
    responseAdd = asyncio.run(add_hashtags(courseId, ['tag1', 'tag2']))

    hashtags = asyncio.run(get_hashtags(courseId))
    tag1 = {'hashtag': 'tag1'}
    tag2 = {'hashtag': 'tag2'}

    assert responseAdd.status_code == status.HTTP_201_CREATED
    assert tag1 in hashtags
    assert tag2 in hashtags

    asyncio.run(delete(courseId))


def test_get_by_hashtag():
    name = 'test_get_by_hashtag'
    ownerId = str(uuid.uuid4())
    tag = 'testTag'
    courseId = asyncio.run(
        post(CourseRequest(owner=ownerId, name=name)))["id"]
    asyncio.run(add_hashtags(courseId, [tag]))

    courses = asyncio.run(get_by_hashtag(tag))

    assert {'id': courseId} in courses

    asyncio.run(delete(courseId))


def test_get_by_hashtag_two_courses():
    name1 = 'test_get_by_hashtag1'
    name2 = 'test_get_by_hashtag2'
    ownerId = str(uuid.uuid4())
    tag = 'testTag'
    courseId1 = asyncio.run(
        post(CourseRequest(owner=ownerId, name=name1)))["id"]
    asyncio.run(add_hashtags(courseId1, [tag]))

    courseId2 = asyncio.run(
        post(CourseRequest(owner=ownerId, name=name2)))["id"]
    asyncio.run(add_hashtags(courseId2, [tag]))

    courses = asyncio.run(get_by_hashtag(tag))

    assert {'id': courseId1} in courses
    assert {'id': courseId2} in courses

    asyncio.run(delete(courseId1))
    asyncio.run(delete(courseId2))
