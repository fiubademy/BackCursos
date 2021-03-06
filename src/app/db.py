from sqlalchemy import (
    Column,
    Table,
    ForeignKey,
    create_engine
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relation, relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.sql.expression import null
from sqlalchemy.sql.sqltypes import Boolean, DateTime, Float, LargeBinary, String, Integer
import uuid


DATABASE_URL = "postgresql://jhveahofefzvsq:eb0250343f5b7772d0db89b4c6ac263c7d1c891b956d4f38527acfc2ba0e88b6@ec2-3-221-100-217.compute-1.amazonaws.com:5432/d9bj3e61otop9n"
engine = create_engine(DATABASE_URL)

TEST_DATABASE_URL = "postgresql://iegxsavpkkbzlf:7bc34cff38335a7e9c09dcde83b44d3ce6cfc903157deba12999d8a7ea58af2f@ec2-3-218-92-146.compute-1.amazonaws.com:5432/d9li5u0oq3rjhe"
test_engine = create_engine(TEST_DATABASE_URL)

Base = declarative_base()


course_students = Table('course_students', Base.metadata,
                        Column('course_id', ForeignKey(
                            'courses.id'), primary_key=True),
                        Column('student_id', ForeignKey(
                            'students.user_id'), primary_key=True)
                        )

course_hashtags = Table('course_hashtags', Base.metadata,
                        Column('course_id', ForeignKey(
                            'courses.id'), primary_key=True),
                        Column('hashtag_id', ForeignKey(
                            'hashtags.id'), primary_key=True)
                        )

course_favs = Table('course_favs', Base.metadata,
                        Column('course_id', ForeignKey(
                            'courses.id'), primary_key=True),
                        Column('user_id', ForeignKey(
                            'users.user_id'), primary_key=True)
                        )


class Course(Base):
    __tablename__ = "courses"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    description = Column(String)
    owner = Column(UUID(as_uuid=True), nullable=False)
    in_edition = Column(Boolean, default=True)
    blocked = Column(Boolean, default=False)
    time_created = Column(DateTime(timezone=True), default=func.now())
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    sub_level = Column(Integer, nullable=True)
    rating = Column(Float, nullable=False, default=0)
    category = Column(String)

    content = relationship('Content', back_populates="course",
                           cascade="all, delete, delete-orphan")
    reviews = relationship('Review', back_populates="course",
                           cascade="all, delete, delete-orphan")
    collaborators = relationship('Collaborator', back_populates='course',
                           cascade="all, delete, delete-orphan")
    students = relationship('Student',
                            secondary=course_students,
                            back_populates='courses')
    hashtags = relationship('Hashtag',
                            secondary=course_hashtags,
                            back_populates='courses')
    faved_by = relationship('User',
                            secondary=course_favs,
                            back_populates='favs')


class Student(Base):  # many to many relationship
    __tablename__ = "students"
    user_id = Column(UUID(as_uuid=True), primary_key=True)
    courses = relationship('Course',
                           secondary=course_students,
                           back_populates='students')


class Collaborator(Base):
    __tablename__ = "course_collaborators"
    course_id = Column(UUID(as_uuid=True), ForeignKey('courses.id'), primary_key=True)
    user_id = Column(UUID(as_uuid=True), primary_key=True)
    accepted = Column(Boolean, nullable=False, default=False)
    course = relationship("Course", back_populates="collaborators")


class Hashtag(Base):  # many to many relationship
    __tablename__ = "hashtags"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tag = Column(String(140), nullable=False, unique=True)
    courses = relationship('Course',
                           secondary=course_hashtags,
                           back_populates='hashtags')


class Content(Base):  # one to many relationship
    __tablename__ = "content"
    id = Column(Integer, primary_key=True)
    link = Column(String, nullable=False)
    name = Column(String, nullable=False)
    course_id = Column(UUID(as_uuid=True), ForeignKey('courses.id'))
    course = relationship("Course", back_populates="content")


class Review(Base):
    __tablename__ = "reviews"
    id = Column(Integer, primary_key=True)
    rating = Column(Integer, nullable=False)
    description = Column(String(500), nullable=True)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    course_id = Column(UUID(as_uuid=True), ForeignKey('courses.id'))
    course = relationship("Course", back_populates="reviews")


class User(Base):  # many to many relationship
    __tablename__ = "users"
    user_id = Column(UUID(as_uuid=True), primary_key=True)
    favs = relationship('Course',
                           secondary=course_favs,
                           back_populates='faved_by')

