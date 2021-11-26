import asyncio
import uuid
from fastapi import status
from app.api import courses
from app.api.models import CourseCreate, CourseUpdate, CourseFilter


async def post(request: CourseCreate):
    return await courses.create(request)


async def delete(courseId: str):
    return await courses.delete(courses.check_course(courseId))


async def get(filter: CourseFilter):
    return await courses.get_courses(page_num=1, filter=filter)


async def update(courseId: str, request: CourseUpdate):
    return await courses.update(request, courses.check_course(courseId))


async def get_students(courseId: str):
    return await courses.get_students(courses.check_course(courseId))


async def add_student(courseId: str, userId: str):
    return await courses.add_student(userId, courses.check_course(courseId))


async def get_collaborators(courseId: str):
    return await courses.get_collaborators(courses.check_course(courseId))


async def add_collaborator(courseId: str, userId: str):
    return await courses.add_collaborator(userId, courses.check_course(courseId))


async def add_hashtags(courseId: str, tag: str):
    return await courses.add_hashtags(tag, courses.check_course(courseId))


def test_post_and_get_by_id():
    name = 'test_post_and_get_by_id'
    description = 'descripcion'
    ownerId = str(uuid.uuid4())
    new = CourseCreate(name=name, owner=ownerId, description=description)

    courseId = asyncio.run(post(new))['courseId']
    courseObtained = asyncio.run(get(CourseFilter(id=courseId)))['content'][0]

    assert courseObtained["id"] == courseId
    assert courseObtained["name"] == name

    asyncio.run(delete(courseId))


def test_get_by_id_inexistent_course_returns_empty():
    inexistentId = str(uuid.uuid4())
    assert asyncio.run(get(CourseFilter(id=inexistentId)))['content'] == []


def test_post_and_get_by_name():
    name = 'test_post_and_get_by_name'
    ownerId = str(uuid.uuid4())
    request = CourseCreate(owner=ownerId, name=name,
                           description='descripcion')

    courseId = asyncio.run(post(request))['courseId']
    courses = asyncio.run(get(CourseFilter(name=name)))['content']

    assert courses[0]['id'] == courseId

    asyncio.run(delete(courseId))


def test_delete_correctly():
    name = 'test_delete_correctly'
    ownerId = str(uuid.uuid4())
    request = CourseCreate(owner=ownerId, name=name)

    courseId = asyncio.run(post(request))['courseId']
    asyncio.run(delete(courseId))

    assert asyncio.run(get(CourseFilter(id=courseId)))['content'] == []


def test_update_course_correctly():
    name = 'test_update_course_correctly'
    ownerId = str(uuid.uuid4())
    request = CourseCreate(owner=ownerId, name=name)
    courseId = asyncio.run(post(request))["courseId"]

    newName = 'new_name'
    ownerId = str(uuid.uuid4())
    request = CourseUpdate(owner=ownerId, name=newName)
    asyncio.run(update(courseId, request))

    courseObtained = asyncio.run(get(CourseFilter(id=courseId)))['content'][0]

    assert courseObtained['id'] == courseId
    assert courseObtained['name'] == newName

    asyncio.run(delete(courseId))


def test_get_all_courses():
    try:
        initialLen = len(asyncio.run(get())['content'])
    except TypeError:
        initialLen = 0
    ownerId = str(uuid.uuid4())
    courseId1 = asyncio.run(post(request=CourseCreate(owner=ownerId, name='curso1')
                                 ))["courseId"]
    courseId2 = asyncio.run(post(request=CourseCreate(owner=ownerId, name='curso1')
                                 ))["courseId"]

    courseId3 = asyncio.run(post(request=CourseCreate(owner=ownerId, name='curso2')
                                 ))["courseId"]
    newLen = len(asyncio.run(get(CourseFilter()))['content'])

    assert newLen == initialLen + 3

    asyncio.run(delete(courseId1))
    asyncio.run(delete(courseId2))
    asyncio.run(delete(courseId3))


def test_get_by_user_inexistent_returns_empty():
    name = 'test_get_by_user_inexistent_returns_empty'
    ownerId = str(uuid.uuid4())
    userId1 = str(uuid.uuid4())
    userId2 = str(uuid.uuid4())
    courseId = asyncio.run(
        post(CourseCreate(owner=ownerId, name=name)))["courseId"]
    asyncio.run(add_student(courseId, userId1))

    assert asyncio.run(get(CourseFilter(id=userId2)))['content'] == []

    asyncio.run(delete(courseId))


def test_add_and_get_students():
    ownerId = str(uuid.uuid4())
    courseId = asyncio.run(
        post(CourseCreate(owner=ownerId, name='test_add_and_get_students')))["courseId"]
    userId1 = str(uuid.uuid4())
    userId2 = str(uuid.uuid4())
    asyncio.run(add_student(courseId, userId1))
    asyncio.run(add_student(courseId, userId2))

    students = asyncio.run(get_students(courseId))

    assert userId1 in students
    assert userId2 in students

    asyncio.run(delete(courseId))


def test_add_and_get_collaborators():
    ownerId = str(uuid.uuid4())
    courseId = asyncio.run(
        post(CourseCreate(owner=ownerId, name='test_add_and_get_collaborators')))["courseId"]
    userId1 = str(uuid.uuid4())
    userId2 = str(uuid.uuid4())
    asyncio.run(add_collaborator(courseId, userId1))
    asyncio.run(add_collaborator(courseId, userId2))

    collaborators = asyncio.run(get_collaborators(courseId))

    assert userId1 in collaborators
    assert userId2 in collaborators

    asyncio.run(delete(courseId))


def test_add_and_get_hashtags():
    ownerId = str(uuid.uuid4())
    courseId = asyncio.run(
        post(CourseCreate(owner=ownerId, name='test_add_and_get_hashtags')))["courseId"]
    responseAdd = asyncio.run(add_hashtags(courseId, ['tag1', 'tag2']))

    course = asyncio.run(get(CourseFilter(id=courseId)))['content'][0]

    assert responseAdd.status_code == status.HTTP_201_CREATED
    assert 'tag1' in course['hashtags']
    assert 'tag2' in course['hashtags']

    asyncio.run(delete(courseId))


def test_get_by_hashtag():
    name = 'test_get_by_hashtag'
    ownerId = str(uuid.uuid4())
    tag = 'testTag'
    courseId = asyncio.run(
        post(CourseCreate(owner=ownerId, name=name)))["courseId"]
    asyncio.run(add_hashtags(courseId, [tag]))

    courses = asyncio.run(get(CourseFilter(hashtag=tag)))['content'][0]

    assert courseId == courses['id']

    asyncio.run(delete(courseId))


def test_get_by_hashtag_two_courses():
    name1 = 'test_get_by_hashtag1'
    name2 = 'test_get_by_hashtag2'
    ownerId = str(uuid.uuid4())
    tag = 'testTag'
    courseId1 = asyncio.run(
        post(CourseCreate(owner=ownerId, name=name1)))["courseId"]
    asyncio.run(add_hashtags(courseId1, [tag]))

    courseId2 = asyncio.run(
        post(CourseCreate(owner=ownerId, name=name2)))["courseId"]
    asyncio.run(add_hashtags(courseId2, [tag]))

    courses = asyncio.run(get(CourseFilter(hashtag=tag)))

    foundCourse1 = False
    foundCourse2 = False
    for course in courses['content']:
        if course['id'] == courseId1:
            foundCourse1 = True
        elif course['id'] == courseId2:
            foundCourse2 = True
    assert foundCourse1
    assert foundCourse2

    asyncio.run(delete(courseId1))
    asyncio.run(delete(courseId2))
