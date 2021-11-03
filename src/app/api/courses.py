from fastapi import status, HTTPException, APIRouter
from typing import List, Optional
from fastapi.param_functions import Query
from starlette.responses import JSONResponse

from sqlalchemy.exc import DataError

from api.models import CourseRequest, CourseResponse, CourseDetailResponse
from db import Course, session


router = APIRouter()


@router.get('', response_model=List[CourseResponse])
async def getCourses(nameFilter: Optional[str] = ''):
    mensaje = []
    courses = session.query(Course).filter(
        Course.name.ilike("%"+nameFilter+"%"))
    if courses.first() is None:
        raise HTTPException(status_code=404, detail="No courses found")
    for course in courses:
        mensaje.append(
            {'courseId': str(course.id), 'courseName': course.name})

    # Podria devolver un CourseResponse. No estoy usando la estructura
    return mensaje


@router.get('/{courseId}', response_model=CourseResponse)
# Usar Path obligatorio en lugar de hacer chequeo manual
async def getCourse(courseId: str = Query(...)):
    try:
        course = session.get(Course, courseId)
    except DataError:
        raise HTTPException(
            status_code=404, detail='Course ' + courseId + ' not found.')
    if course is None:
        raise HTTPException(
            status_code=404, detail='Course ' + courseId + ' not found.')
    return {'courseName': course.name, 'courseId': str(course.id)}


@router.post('', response_model=CourseResponse, status_code=status.HTTP_201_CREATED)
async def createCourse(request: CourseRequest):
    newCourse = Course(name=request.courseName,
                       description=request.description)  # CREAR CON TODOS LOS ATRIBUTOS
    session.add(newCourse)
    session.commit()
    return {'courseId': str(newCourse.id), 'courseName': newCourse.name}


@router.delete('/{courseId}')
async def deleteCourse(courseId: str):
    try:
        course = session.get(Course, courseId)
    except DataError:
        raise HTTPException(status_code=404, detail='Course ' +
                            courseId + ' not found and will not be deleted.')
    if course is None:
        raise HTTPException(status_code=404, detail='Course ' +
                            courseId + ' not found and will not be deleted.')
    session.delete(course)
    session.commit()
    return JSONResponse(status_code=status.HTTP_202_ACCEPTED, content='Course ' + courseId + ' was deleted succesfully.')


@router.patch('/{courseId}')
async def patchCourse(courseId: str, request: CourseRequest):
    # AGREGAR QUE SE MODIFIQUEN SOLO LOS CAMPOS PRESENTES EN newCourse
    try:
        course = session.get(Course, courseId)
    except DataError:
        raise HTTPException(status_code=404, detail='Course ' +
                            courseId + ' not found and will not be patched.')
    if course is None:
        raise HTTPException(status_code=404, detail='Course ' +
                            courseId + ' not found and will not be deleted.')

    updated_course = Course(name=request.courseName,
                            description=request.description)  # CREAR CON TODOS LOS ATRIBUTOS, constructor de copia
    session.add(updated_course)
    session.commit()
    return {'course_id': courseId, 'course_name': updated_course.name}
