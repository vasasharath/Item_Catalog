import json

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, User, Category, Movies

engine = create_engine('sqlite:///movie-catalog.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

current_user = User(name='admin', email='sharathvasa@gmail.com')
session.add(current_user)
session.commit()

fixtures = json.loads(open('fixtures.json', 'rb').read())

for t in fixtures['categories']:
    category = Category(name=t['name'],
                        description=t['description'])
    session.add(category)
    session.commit()

for c in fixtures['movies']:
    movie = Movies(name=c['name'],
                    description=c['description'],
                    image_url=c['image_url'],
                    category_id=c['category_id'],
                    user=current_user)
    session.add(movie)
    session.commit()