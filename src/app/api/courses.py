from uuid import UUID
import math
from fastapi import status, APIRouter, Depends, HTTPException
from fastapi.param_functions import Path, Optional
from starlette.responses import JSONResponse
from sqlalchemy.orm import sessionmaker

from api.models import CourseCreate, CourseUpdate, CourseFilter, Hashtags, ReviewCreate, ContentCreate
from db import Course, Student, Teacher, Hashtag, Content, Review, User

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
    if filter.id is not None:
        query = query.filter(Course.id == filter.id)
    if filter.name is not None:
        query = query.filter(Course.name.ilike(f'%{filter.name}%'))
    if filter.owner is not None:
        query = query.filter(Course.owner == filter.owner)
    if filter.description is not None:
        query = query.filter(
            Course.description.ilike(f'%{filter.description}%'))
    if filter.sub_level is not None:
        query = query.filter(Course.sub_level == filter.sub_level)
    if filter.latitude is not None:
        query = query.filter(Course.latitude == filter.latitude)
    if filter.longitude is not None:
        query = query.filter(Course.longitude == filter.longitude)
    if filter.student is not None:
        query = query.filter(
            Course.students.any(user_id=filter.student))
    if filter.collaborator is not None:
        query = query.filter(
            Course.teachers.any(user_id=filter.collaborator))
    if filter.hashtags is not None:
        for tag in filter.hashtags:
            query = query.filter(
                Course.hashtags.any(tag=tag))
    if filter.minRating is not None:
        query = query.filter(Course.rating >= filter.minRating)
    if filter.category is not None:
        query = query.filter(Course.category == filter.category)
    if filter.faved_by is not None:
        query = query.filter(Course.faved_by.any(user_id=filter.faved_by))

    num_pages = math.ceil(query.count()/COURSES_PER_PAGE)
    query = query.limit(COURSES_PER_PAGE).offset((page_num-1)*COURSES_PER_PAGE)
    return {'num_pages': num_pages, 'content': [{
        'id': str(course.id),
        'name': course.name,
        'description': course.description,
        'ownerId': course.owner,
        'sub_level': course.sub_level,
        'category': course.category,
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


@ router.get('/{courseId}/get_content_list')
async def get_content_list(course=Depends(check_course)):
    return [{'id': content.id, 'name': content.name, 'link': content.link} for content in course.content]


@ router.patch('/{courseId}')
async def update(request: CourseUpdate, course=Depends(check_course)):
    attributes = request.dict(exclude_unset=True, exclude_none=True, exclude={'hashtags'})
    for att, value in attributes.items():
        setattr(course, att, value)
    if request.hashtags is not None:
        course.hashtags[:] = []
        for tag in request.hashtags:
            hashtag = session.query(Hashtag).filter(Hashtag.tag == tag).first()
            if hashtag is None:
                course.hashtags.append(Hashtag(tag=tag))
            else:
                course.hashtags.append(hashtag)
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


@ router.post('/{courseId}/add_content')
async def add_content(new: ContentCreate, course=Depends(check_course)):
    for content in course.content:
        if content.link == new.link or content.name == new.name:
            return JSONResponse(status_code=status.HTTP_409_CONFLICT, content='Content already exists.')

    course.content.append(Content(**new.dict()))
    session.commit()
    return JSONResponse(status_code=status.HTTP_201_CREATED, content='Content added succesfully.')


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


@ router.delete('/remove_content/{contentId}')
async def remove_content(contentId: str):
    content = session.get(Content, contentId)
    if content is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='Content not found.')
    session.delete(content)
    session.commit()
    return JSONResponse(status_code=status.HTTP_202_ACCEPTED, content='Content deleted succesfully.')


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


@ router.put('/new_fav/{userId}/{courseId}/{fav}')
async def fav_course(fav: bool, userId: UUID, course=Depends(check_course)):
    user = session.get(User, userId)
    if fav is True:
        if user is None:
            course.faved_by.append(User(user_id=userId))
        elif user not in course.faved_by:
            course.faved_by.append(user)
    else:
        for user in course.faved_by:
            if user.user_id == userId:
                course.faved_by.remove(user)
                break
    session.commit()
    return JSONResponse(status_code=status.HTTP_202_ACCEPTED, content='Fav updated succesfully.')
