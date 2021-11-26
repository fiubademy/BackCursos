from uuid import UUID
from fastapi import status, APIRouter, Depends
from typing import List
from starlette.responses import JSONResponse
from sqlalchemy.orm import sessionmaker

from api.models import CourseCreate, CourseUpdate, CourseFilter
from db import Course, Student, Teacher, Hashtag, Content

PER_PAGE = 5


router = APIRouter()

session = None
engine = None


def set_engine(engine_rcvd):
    global engine
    global session
    engine = engine_rcvd
    session = sessionmaker(bind=engine)()
    return session


@router.get('/all/{page_num}')
async def get_courses(
    page_num: int,
    filter: CourseFilter = Depends()
):
    query = session.query(Course)
    if filter.name:
        query = query.filter(Course.name.ilike(f'%{filter.name}%'))
    if filter.owner:
        query = query.filter(Course.owner == filter.owner)
    if filter.description:
        query = query.filter(
            Course.description.ilike(f'%{filter.description}%'))
    if filter.sub_level:
        query = query.filter(Course.sub_level == filter.sub_level)
    if filter.latitude:
        query = query.filter(Course.latitude == filter.latitude)
    if filter.longitude:
        query = query.filter(Course.longitude == filter.longitude)
    count = query.count()
    query = query.limit(PER_PAGE).offset((page_num-1)*PER_PAGE)
    if (count/PER_PAGE - int(count/PER_PAGE) == 0):
        num_pages = int(count/PER_PAGE)
    else:
        num_pages = int(count/PER_PAGE)+1
    return {'num_pages': num_pages, 'content': [{
        'id': str(course.id),
        'name': course.name,
        'description': course.description,
        'sub_level': course.sub_level,
        'latitude': course.latitude,
        'longitude': course.longitude,
        'hashtags': [hashtag.tag for hashtag in course.hashtags],
        'time_created': course.time_created
    } for course in query]}


@ router.get('/{id}')
async def get_by_id(id: UUID):
    course = session.get(Course, id)
    if course is None:
        return JSONResponse(status_code=404, content='Course ' + str(id) + ' not found.')
    return {'id': str(course.id),
            'name': course.name,
            'description': course.description,
            'sub_level': course.sub_level,
            'latitude': course.latitude,
            'longitude': course.longitude,
            'hashtags': [hashtag.tag for hashtag in course.hashtags],
            'time_created': course.time_created
            }


@ router.get('/student/{userId}')
async def get_by_student(userId: UUID):
    user = session.get(Student, userId)
    if user is None:
        return JSONResponse(status_code=404, content="No courses found")
    return [{'id': str(course.id)} for course in user.courses],


@ router.get('/collaborator/{userId}')
async def get_by_collaborator(userId: UUID):
    user = session.get(Teacher, userId)
    if user is None:
        return JSONResponse(status_code=404, content="No courses found")
    return [{'id': str(course.id)} for course in user.courses],


@ router.get('/hashtag/{tag}')
async def get_by_hashtag(tag: str):
    courses = session.query(Course).filter(
        Course.hashtags.any(tag=tag))
    return [{'id': str(course.id)} for course in courses],


@ router.post('')
async def create(request: CourseCreate):
    new = Course(**request.dict(exclude_unset=True, exclude={"hashtags"}))
    for tag in request.hashtags:
        hashtag = session.query(Hashtag).filter(Hashtag.tag == tag).first()
        if hashtag is None:
            new.hashtags.append(Hashtag(tag=tag))
        elif hashtag not in new.hashtags:
            new.hashtags.append(hashtag)

    session.add(new)
    session.commit()
    return {'id': str(new.id)}


@ router.delete('/{id}')
async def delete(id: UUID):
    course = session.get(Course, id)
    if course is None:
        return JSONResponse(status_code=404, content='Course ' + str(id) + ' not found and will not be deleted.')
    session.delete(course)
    session.commit()
    return JSONResponse(status_code=status.HTTP_202_ACCEPTED, content='Course ' + str(id) + ' was deleted succesfully.')


@ router.patch('/{id}')
async def update(id: UUID, request: CourseUpdate):
    course = session.get(Course, id)
    if course is None:
        return JSONResponse(status_code=404, content='Course ' + str(id) + ' not found and will not be updated.')

    attributes = request.dict(exclude_unset=True, exclude_none=True)
    for att, value in attributes.items():
        setattr(course, att, value)

    session.merge(course)
    session.commit()
    return JSONResponse(status_code=status.HTTP_202_ACCEPTED, content='Course ' + str(id) + ' was updated succesfully.')


@ router.get('/{courseId}/students')
async def get_students(courseId: UUID):
    course = session.get(Course, courseId)
    if course is None:
        return JSONResponse(status_code=404, content='Course ' + str(courseId) + ' not found.')
    return [{'id': user.user_id} for user in course.students],



@ router.post('/{courseId}/add_student/{userId}')
async def add_student(courseId: UUID, userId: UUID):
    course = session.get(Course, courseId)
    if course is None:
        return JSONResponse(status_code=404, content='Course ' + str(courseId) + ' not found.')
    student = session.get(Student, userId)
    if student is None:
        course.students.append(Student(user_id=userId))
    elif student not in course.students:
        course.students.append(student)
    return JSONResponse(status_code=status.HTTP_201_CREATED, content='Student ' + str(userId) + ' added succesfully.')


@ router.delete('/{courseId}/remove_student/{userId}')
async def remove_student(courseId: UUID, userId: UUID):
    removed = False
    course = session.get(Course, courseId)
    if course is None:
        return JSONResponse(status_code=404, content='Course ' + str(courseId) + ' not found.')

    for student in course.students:
        if student.user_id == userId:
            course.students.remove(student)
            removed = True
            break
    if not removed:
        return JSONResponse(status_code=404, content='No student found.')

    session.commit()
    return JSONResponse(status_code=status.HTTP_202_ACCEPTED, content='Student ' + str(userId) + ' was removed succesfully.')


@ router.get('/{courseId}/collaborators')
async def get_collaborators(courseId: UUID):
    course = session.get(Course, courseId)
    if course is None:
        return JSONResponse(status_code=404, content='Course ' + str(courseId) + ' not found.')
    return [{'id': user.user_id} for user in course.teachers],



@ router.post('/{courseId}/add_collaborator/{userId}')
async def add_collaborator(courseId: UUID, userId: UUID):
    course = session.get(Course, courseId)
    if course is None:
        return JSONResponse(status_code=404, content='Course ' + str(courseId) + ' not found.')

    teacher = session.get(Teacher, userId)
    if teacher is None:
        course.teachers.append(Teacher(user_id=userId))
    elif teacher not in course.teachers:
        course.teachers.append(teacher)
    return JSONResponse(status_code=status.HTTP_201_CREATED, content='Collaborator ' + str(userId) + ' added succesfully.')


@ router.delete('/{courseId}/remove_collaborator/{userId}')
async def remove_collaborator(courseId: UUID, userId: UUID):
    removed = False
    course = session.get(Course, courseId)
    if course is None:
        return JSONResponse(status_code=404, content='Course ' + str(courseId) + ' not found.')

    for teacher in course.teachers:
        if teacher.user_id == userId:
            course.teachers.remove(teacher)
            removed = True
            break
    if not removed:
        return JSONResponse(status_code=404, content='No collaborator found.')
    session.commit()
    return JSONResponse(status_code=status.HTTP_202_ACCEPTED, content='Collaborator ' + str(userId) + ' was removed succesfully.')


@ router.get('/{courseId}/hashtags')
async def get_hashtags(courseId: UUID):
    course = session.get(Course, courseId)
    if course is None:
        return JSONResponse(
            status_code=404, content='Course ' + str(courseId) + ' not found.')
    return [{'hashtag': hashtag.tag} for hashtag in course.hashtags],



@ router.post('/{courseId}/add_hashtags')
async def add_hashtags(courseId: UUID, tags: List[str]):
    course = session.get(Course, courseId)
    if course is None:
        return JSONResponse(status_code=404, content='Course ' + str(courseId) + ' not found.')

    for tag in tags:
        hashtag = session.query(Hashtag).filter(Hashtag.tag == tag).first()
        if hashtag is None:
            course.hashtags.append(Hashtag(tag=tag))
        elif hashtag not in course.hashtags:
            course.hashtags.append(hashtag)

    session.commit()
    return JSONResponse(status_code=status.HTTP_201_CREATED, content='Hashtags added succesfully.')


@ router.delete('/{courseId}/remove_hashtags')
async def remove_hashtags(courseId: UUID, tags: List[str]):
    response = ""
    course = session.get(Course, courseId)
    if course is None:
        return JSONResponse(status_code=404, content='Course ' + str(courseId) + ' not found.')

    for tag in tags:
        for hashtag in course.hashtags:
            if hashtag.tag == tag:
                course.hashtags.remove(hashtag)
                response += f'\'{tag}\', '
                break
    if response == "":
        return JSONResponse(status_code=404, content='No hashtags found.')
    session.commit()
    return JSONResponse(status_code=status.HTTP_202_ACCEPTED, content='Hashtags ' + response + 'were removed succesfully.')


@ router.get('/{courseId}/owner')
async def get_owner(courseId: UUID):
    course = session.get(Course, courseId)
    if course is None:
        return JSONResponse(status_code=404, content='Course ' + str(courseId) + ' not found.')
    return {"ownerId": course.owner}


@ router.put('/{courseId}/block')
async def set_block(courseId: UUID, block: bool = True):
    course = session.get(Course, courseId)
    if course is None:
        return JSONResponse(status_code=404, content='Course ' + str(courseId) + ' not found.')
    course.blocked = block
    session.commit()
    if block is True:
        return JSONResponse(status_code=status.HTTP_202_ACCEPTED, content='Course ' + str(courseId) + ' was blocked succesfully.')
    else:
        return JSONResponse(status_code=status.HTTP_202_ACCEPTED, content='Course ' + str(courseId) + ' was unblocked succesfully.')


@ router.put('/{courseId}/status')
async def set_status(courseId: UUID, in_edition: bool):
    course = session.get(Course, courseId)
    if course is None:
        return JSONResponse(status_code=404, content='Course ' + str(courseId) + ' not found.')
    course.in_edition = in_edition
    session.commit()
    return JSONResponse(status_code=status.HTTP_202_ACCEPTED, content='Course ' + str(courseId) + ' status was updated succesfully.')
