from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import Base, MoviesDB, User

engine = create_engine('sqlite:///MovieCatalog.db')
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

# Sample movies data
movie1 = MoviesDB(movieName="Bahubali2",
               director="S.S. Rajamouli",
               trilerUrl="""https://www.youtube.com/
               watch?v=G62HrubdD6o""",
               description="When Shiva, the son of Bahubali,"
               "learns about his heritage, he begins to look"
               "for answers. His story is juxtaposed with past"
               "events that unfolded in the Mahishmati Kingdom.", 
               category="Fantasy", user_id=1)

session.add(movie1)
session.commit()

movie2 = MoviesDB(movieName="300",
               director="Zack Snyder",
               trilerUrl="""https://www.youtube.com/watch?v=UrIbxk7idYA""",
               description="King Leonidas of Sparta and a force of 300 men" 
               " fight the Persians at Thermopylae in 480 B.C.",
               category="Action", user_id=1)

session.add(movie2)
session.commit()

movie3 = MoviesDB(movieName="The Great Wall",
               director="Yimou Zhang",
               trilerUrl="""https://books.google.com/books/content/
               images/frontcover/xE15t_pAG34C?fife=w300-rw""",
               description="European mercenaries searching for black"
               " powder become embroiled in the defense of the Great"
               " Wall of China against a horde of monstrous creatures.", 
               category="Adventure", user_id=1)

session.add(movie3)
session.commit()

movie4 = MoviesDB(movieName="Home Alone",
               director="Chris Columbus",
               trilerUrl="""https://www.youtube.com/
               watch?v=CK2Btk6Ybm0""",
               description="An eight-year-old troublemaker"
               " must protect his house from a pair of burglars"
               " when he is accidentally left home alone by his"
               " family during Christmas vacation.",
               category="Family", user_id=1)

session.add(movie4)
session.commit()

movie5 = MoviesDB(movieName="Rio",
               director="Carlos Saldanha",
               trilerUrl="""https://www.youtube.com/
               watch?v=P1GRO31ve5Q""",
               description="When Blu, a domesticated macaw"
               " from small-town Minnesota, meets the fiercely"
               " independent Jewel, he takes off on an adventure"
               " to Rio de Janeiro with the bird of his dreams.", 
               category="Animation", user_id=1)

session.add(movie5)
session.commit()


print "added Movies!"