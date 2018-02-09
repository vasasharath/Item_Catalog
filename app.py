from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import Base, MoviesDB, User

engine = create_engine('sqlite:///MoviesCatalog.db')
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
session = DBSession()

# Create dummy user
User1 = User(name="admin", email="sharathvasa@gmail.com")
session.add(User1)
session.commit()

def clear_data(session):
    meta = db.metadata
    for table in reversed(meta.sorted_tables):
        print 'Clear table %s' % table
        session.execute(table.delete())
    session.commit()