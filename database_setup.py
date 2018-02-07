import os
import sys
from sqlalchemy import Column, ForeignKey, Integer, String

from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy.orm import relationship

from sqlalchemy import create_engine

Base = declarative_base()


# class to store user info
class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)
    image = Column(String(250))
    provider = Column(String(25))


# class for Movies Database
class MoviesDB(Base):
    __tablename__ = "movies"

    id = Column(Integer, primary_key=True)
    movieName = Column(String(250), nullable=False)
    director = Column(String(250), nullable=False)
    trailerUrl = Column(String(450), nullable=False)
    description = Column(String(), nullable=False)
    category = Column(String(100), nullable=False)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
        # return movie data in serializable format
        return {
            'id': self.id,
            'name': self.movieName,
            'director': self.director,
            'genre': self.category,
            'trailerUrl': self.trailerUrl,
            'description': self.description
        }

engine = create_engine('sqlite:///MoviesCatalog.db')
Base.metadata.create_all(engine)