from uuid import UUID
from fastapi import status, APIRouter, File, UploadFile
from typing import List, Optional
from starlette.responses import JSONResponse, StreamingResponse
from sqlalchemy.orm import sessionmaker

from api.models import CourseRequest, CourseUpdate
from db import Course, Student, Teacher, Hashtag, Content

router = APIRouter()

session = None
engine = None


def set_engine(engine_rcvd):
    global engine
    global session
    engine = engine_rcvd
    session = sessionmaker(bind=engine)()
    return session


@router.get('')
async def get_all(nameFilter: Optional[str] = ''):
    response = []
    if nameFilter != '':
        courses = session.query(Course).filter(
            Course.name.ilike("%"+nameFilter+"%"))
    else:
        courses = session.query(Course)
    for course in courses:
        response.append({'id': str(course.id)})
    return response


@router.get('/{id}')
async def get_by_id(id: UUID):
    course = session.get(Course, id)
    if course is None:
        return JSONResponse(status_code=404, content='Course ' + str(id) + ' not found.')
    return {'id': str(course.id),
            'ownerId': str(course.owner),
            'name': course.name,
            'description': course.description,
            'sub_level': course.sub_level,
            'latitude': course.latitude,
            'longitude': course.longitude,
            'hashtags': [hashtag.tag for hashtag in course.hashtags],
            'time_created': course.time_created
            }


@router.get('/student/{userId}')
async def get_by_student(userId: UUID):
    userCourses = []
    user = session.get(Student, userId)
    if user is None:
        return JSONResponse(status_code=404, content="No user found")
    for course in user.courses:
        userCourses.append(
            {'id': str(course.id)})
    return userCourses


@router.post('')
async def create(request: CourseRequest):
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
    students = []
    course = session.get(Course, courseId)
    if course is None:
        return JSONResponse(status_code=404, content='Course ' + str(courseId) + ' not found.')
    for user in course.students:
        students.append({'id': user.user_id})
    return students


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
    collaborators = []
    course = session.get(Course, courseId)
    if course is None:
        return JSONResponse(status_code=404, content='Course ' + str(courseId) + ' not found.')
    for user in course.teachers:
        collaborators.append({'id': user.user_id})
    return collaborators


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
    hashtags = []
    course = session.get(Course, courseId)
    if course is None:
        return JSONResponse(
            status_code=404, content='Course ' + str(courseId) + ' not found.')
    for hashtag in course.hashtags:
        hashtags.append({'hashtag': hashtag.tag})
    return hashtags


@ router.post('/{courseId}/add_hashtag/{tag}')
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


@ router.get('/hashtag/{tag}')
async def get_by_hashtag(tag: str):
    response = []
    courses = session.query(Course).filter(
        Course.hashtags.any(tag=tag))
    for course in courses:
        response.append(
            {'id': str(course.id)})
    return response


@router.get('/{courseId}/owner')
async def get_owner(courseId: UUID):
    course = session.get(Course, courseId)
    if course is None:
        return JSONResponse(status_code=404, content='Course ' + str(courseId) + ' not found.')
    return {"ownerId": course.owner}


@router.put('/{courseId}/block')
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


@router.put('/{courseId}/status')
async def set_status(courseId: UUID, in_edition: bool):
    course = session.get(Course, courseId)
    if course is None:
        return JSONResponse(status_code=404, content='Course ' + str(courseId) + ' not found.')
    course.in_edition = in_edition
    session.commit()
    return JSONResponse(status_code=status.HTTP_202_ACCEPTED, content='Course ' + str(courseId) + ' status was updated succesfully.')


@ router.post('/{courseId}/add_content')
async def add_content(courseId: UUID, file: UploadFile = File(...)):
    course = session.get(Course, courseId)
    if course is None:
        return JSONResponse(status_code=404, content='Course ' + str(courseId) + ' not found.')

    if file.content_type != "video/mp4":
        return JSONResponse(status_code=400, content='Wrong filetype: expected video/mp4.')
    content = session.query(Content).filter(
        Content.name == file.filename).first()
    if content is None:
        file_bytes = await file.read()
        course.content.append(Content(content=file_bytes, name=file.filename))
    elif content not in course.content:
        course.content.append(content)

    session.commit()
    return {'contentId': content.id}


@ router.post('/{courseId}/get_content_list')
async def get_content_list(courseId: UUID):
    course = session.get(Course, courseId)
    if course is None:
        return JSONResponse(status_code=404, content='Course ' + str(courseId) + ' not found.')
    return [{'id': content.id} for content in course.content]


def iterfile(file):  # usar lambda
    yield from file


@ router.post('{courseId}/get_content/{contentId}')
async def get_content(contentId: UUID):
    content = session.get(Content, contentId)
    if content is None:
        return JSONResponse(status_code=404, content='Content ' + str(contentId) + ' not found.')

    # https://github.com/mpimentel04/rtsp_fastapi/blob/617d7f693151999d96901ec5d15f252478c96891/webstreaming.py#L46
    return StreamingResponse(iterfile(content.content), media_type="multipart/x-mixed-replace;boundary=frame")


@ router.delete('/remove_content/{contentId}')
async def remove_content(courseId: UUID, contentId: UUID):
    removed = False
    course = session.get(Course, courseId)
    if course is None:
        return JSONResponse(status_code=404, content='Course ' + str(courseId) + ' not found.')
    content = session.get(Content, contentId)
    if content is None:
        return JSONResponse(status_code=404, content='content ' + str(contentId) + ' not found.')

    for content in course.content:
        if content.id == contentId:
            course.content.remove(content)
            removed = True
            break
    if not removed:
        return JSONResponse(status_code=404, content='No content found.')
    session.commit()
    return JSONResponse(status_code=status.HTTP_202_ACCEPTED, content='Content ' + str(contentId) + ' was deleted succesfully.')
