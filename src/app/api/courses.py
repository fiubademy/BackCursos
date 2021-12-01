from uuid import UUID
import math
from fastapi import status, APIRouter, Depends, HTTPException
from fastapi.param_functions import Path, Optional
from starlette.responses import JSONResponse
from sqlalchemy.orm import sessionmaker

from api.models import CourseCreate, CourseUpdate, CourseFilter, Hashtags, ReviewCreate
from db import Course, Student, Teacher, Hashtag, Content, Review

COURSES_PER_PAGE = 5
REVIEWS_PER_PAGE = 5

router = APIRouter()

session = None
engine = None


def set_engine(engine_rcvd):
    global engine
    global session
    engine = engine_rcvd
    session = sessionmaker(bind=engine)()
    return session


def check_course(courseId: UUID):
    course = session.get(Course, courseId)
    if course is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='Course not found.')
    return course


@router.get('/all/{page_num}')
async def get_courses(
    page_num: int = Path(..., gt=0),
    filter: CourseFilter = Depends()
):
    query = session.query(Course)
    if filter.id:
        query = query.filter(Course.id == filter.id)
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
    if filter.student:
        query = query.filter(
            Course.students.any(user_id=filter.student))
    if filter.collaborator:
        query = query.filter(
            Course.teachers.any(user_id=filter.collaborator))
    if filter.hashtags:
        for tag in filter.hashtags:
            query = query.filter(
                Course.hashtags.any(tag=tag))
    if filter.minRating:
        query = query.filter(Course.rating >= filter.minRating)

    num_pages = math.ceil(query.count()/COURSES_PER_PAGE)
    query = query.limit(COURSES_PER_PAGE).offset((page_num-1)*COURSES_PER_PAGE)
    return {'num_pages': num_pages, 'content': [{
        'id': str(course.id),
        'name': course.name,
        'description': course.description,
        'ownerId': course.owner,
        'sub_level': course.sub_level,
        'latitude': course.latitude,
        'longitude': course.longitude,
        'hashtags': [hashtag.tag for hashtag in course.hashtags],
        'time_created': course.time_created,
        'blocked': course.blocked,
        'in_edition': course.in_edition,
        'ratingCount': len(course.reviews),
        'ratingAvg': course.rating
    } for course in query]}


@ router.get('/{courseId}/students')
async def get_students(course=Depends(check_course)):
    return [user.user_id for user in course.students]


@ router.get('/{courseId}/collaborators')
async def get_collaborators(course=Depends(check_course)):
    return [user.user_id for user in course.teachers]


@ router.get('/{courseId}/owner')
async def get_owner(course=Depends(check_course)):
    return {"ownerId": course.owner}


@ router.get('/{courseId}/review/{userId}')
async def get_review(userId: UUID, course=Depends(check_course)):
    try:
        review = next(
            review for review in course.reviews if review.user_id == userId)
        return {'rating': review.rating, 'description': review.description}
    except StopIteration:
        return {'rating': None, 'description': None}


@ router.get('/{courseId}/all_reviews/{pagenum}')
async def get_all_reviews(pagenum: int = Path(..., gt=0), course=Depends(check_course)):
    reviews = course.reviews[REVIEWS_PER_PAGE *
                             (pagenum-1):REVIEWS_PER_PAGE*(pagenum)]
    num_pages = math.ceil(len(course.reviews)/REVIEWS_PER_PAGE)
    return {'num_pages': num_pages, 'content': [{
        'userId': review.user_id,
        'rating': review.rating,
        'description': review.description
    } for review in reviews]}


@ router.patch('/{courseId}')
async def update(request: CourseUpdate, course=Depends(check_course)):
    attributes = request.dict(exclude_unset=True, exclude_none=True)
    for att, value in attributes.items():
        setattr(course, att, value)
    session.merge(course)
    session.commit()
    return JSONResponse(status_code=status.HTTP_202_ACCEPTED, content='Course updated succesfully.')


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
    return {'courseId': str(new.id)}


@ router.post('/{courseId}/add_student/{userId}')
async def add_student(userId: UUID, course=Depends(check_course)):
    student = session.get(Student, userId)
    if student is None:
        course.students.append(Student(user_id=userId))
    elif student not in course.students:
        course.students.append(student)
    else:
        return JSONResponse(status_code=status.HTTP_409_CONFLICT, content='Student already existed.')
    return JSONResponse(status_code=status.HTTP_201_CREATED, content='Student added succesfully.')


@ router.post('/{courseId}/add_collaborator/{userId}')
async def add_collaborator(userId: UUID, course=Depends(check_course)):
    teacher = session.get(Teacher, userId)
    if teacher is None:
        course.teachers.append(Teacher(user_id=userId))
    elif teacher not in course.teachers:
        course.teachers.append(teacher)
    else:
        return JSONResponse(status_code=status.HTTP_409_CONFLICT, content='Collaborator already existed.')
    return JSONResponse(status_code=status.HTTP_201_CREATED, content='Collaborator added succesfully.')


@ router.post('/{courseId}/add_hashtags')
async def add_hashtags(tags: Hashtags, course=Depends(check_course)):
    response = ""
    for tag in tags.tags:
        hashtag = session.query(Hashtag).filter(Hashtag.tag == tag).first()
        if hashtag is None:
            course.hashtags.append(Hashtag(tag=tag))
            response += f'\'{tag}\', '
        elif hashtag not in course.hashtags:
            course.hashtags.append(hashtag)
            response += f'\'{tag}\', '
    if response == "":
        return JSONResponse(status_code=status.HTTP_409_CONFLICT, content='Tags already existed.')
    session.commit()
    return JSONResponse(status_code=status.HTTP_201_CREATED, content=f'Hashtag {response[:-2]} added succesfully.')


@ router.delete('/{courseId}', summary='Delete course')
async def delete(course=Depends(check_course)):
    session.delete(course)
    session.commit()
    return JSONResponse(status_code=status.HTTP_202_ACCEPTED, content='Course deleted succesfully.')


@ router.delete('/{courseId}/remove_student/{userId}')
async def remove_student(userId: UUID, course=Depends(check_course)):
    removed = False
    for student in course.students:
        if student.user_id == userId:
            course.students.remove(student)
            removed = True
            break
    if not removed:
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content='No student found.')
    session.commit()
    return JSONResponse(status_code=status.HTTP_202_ACCEPTED, content='Student was removed succesfully.')


@ router.delete('/{courseId}/remove_collaborator/{userId}')
async def remove_collaborator(userId: UUID, course=Depends(check_course)):
    removed = False
    for teacher in course.teachers:
        if teacher.user_id == userId:
            course.teachers.remove(teacher)
            removed = True
            break
    if not removed:
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content='No collaborator found.')
    session.commit()
    return JSONResponse(status_code=status.HTTP_202_ACCEPTED, content='Collaborator was removed succesfully.')


@ router.delete('/{courseId}/remove_hashtags')
async def remove_hashtags(tags: Hashtags, course=Depends(check_course)):
    response = ""
    for tag in tags.tags:
        for hashtag in course.hashtags:
            if hashtag.tag == tag:
                course.hashtags.remove(hashtag)
                response += f'\'{tag}\', '
                break
    if response == "":
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content='No hashtags found.')
    session.commit()
    return JSONResponse(status_code=status.HTTP_202_ACCEPTED, content=f'Hashtag {response[:-2]} removed succesfully.')


@ router.put('/{courseId}/block')
async def set_block(block: bool = True, course=Depends(check_course)):
    course.blocked = block
    session.commit()
    return JSONResponse(status_code=status.HTTP_202_ACCEPTED, content='Course block status updated succesfully.')


@ router.put('/{courseId}/status')
async def set_status(in_edition: bool, course=Depends(check_course)):
    course.in_edition = in_edition
    session.commit()
    return JSONResponse(status_code=status.HTTP_202_ACCEPTED, content='Course edition status updated succesfully.')


@ router.put('/{courseId}/review')
async def add_review(new: ReviewCreate, course=Depends(check_course)):
    new = Review(**new.dict())
    new.course_id = course.id
    try:
        new.id = next(
            review for review in course.reviews if review.user_id == new.user_id).id
    except StopIteration:
        pass

    course.rating = (sum([r.rating for r in course.reviews]
                         ) + new.rating)/(len(course.reviews) + 1)
    session.merge(new)
    session.commit()
    return JSONResponse(status_code=status.HTTP_202_ACCEPTED, content='Review added succesfully.')
