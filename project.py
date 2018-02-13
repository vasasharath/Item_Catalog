from functools import wraps

from flask import Flask, render_template, redirect, url_for, flash, request, jsonify
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, User, Category, Movies

from flask import session as login_session
import random
import string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
from flask import make_response, jsonify
import httplib2
import json
import requests

app = Flask(__name__)

engine = create_engine('sqlite:///movie-catalog.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

# Google+ client id and application name
CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Movie-Catalog"


def createUser(login_session):
    u = User(
        name=login_session['username'],
        email=login_session['email'],
        picture=login_session['picture'])
    session.add(u)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except BaseException:
        return None


def user_allowed_to_browse():
    return 'email' in login_session


def user_allowed_to_edit(m):
    return ('user_id' in login_session and
            m.user_id == login_session['user_id'])


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'email' in login_session:
            return f(*args, **kwargs)
        else:
            flash('You are not allowed to access there', 'danger')
            return redirect('/login')

    return decorated_function


@app.context_processor
def inject_user_logged_in():
    return dict(user_logged_in=user_allowed_to_browse())


@app.route('/login')
def showLogin():
    """
    Open login page contains google signin button
    """
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    # return "The current session state is %s" % login_session['state']
    return render_template('login.html', STATE=state)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    """
    Connect google account.
    """
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(
            json.dumps('Current user is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['email'] = data['email']
    login_session['picture'] = data['picture']

    # see if user exists, if it doesn't make a new one
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += """
        " style = "width: 80px; height: 80px;border-radius: 50%;
         -webkit-border-radius: 50%;-moz-border-radius: 50%;"> '
         """
    flash("Welcome, you are now logged in as %s." %
          login_session['username'], 'success')
    print "done!"
    return output


@app.route('/gdisconnect')
def gdisconnect():
    """
    Log out from google.
    """
    access_token = login_session['access_token']
    print 'In gdisconnect access token is %s', access_token
    print 'User name is: '
    print login_session['username']
    if access_token is None:
        print 'Access Token is None'
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = ('https://accounts.google.com/o/oauth2/revoke?token=%s'
           % login_session['access_token'])
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print 'result is '
    print result
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        response = make_response(
            json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


@app.route('/')
def index():
    """
    List all of the categories, and latest movies
    """
    categories = session.query(Category).all()
    latest_movies = session.query(Movies).order_by(Movies.id.desc()).all()
    return render_template('home.html',
                           categories=categories,
                           movies=latest_movies)


@app.route('/catalog/<int:category_id>')
@app.route('/category/<int:category_id>')
def view_category(category_id):
    """
    Show details of selected category
    """
    categories = session.query(Category).all()
    try:
        category = session.query(Category).filter_by(id=category_id).one()
    except BaseException:
        flash('Sorry, something went wrong.', 'danger')
        return redirect(url_for('index'))

    category_movies = session.query(Movies).filter_by(category_id=category.id)
    return render_template('view_category.html',
                           categories=categories,
                           category=category,
                           movies=category_movies)


@app.route('/movie/<int:movie_id>')
def view_movie(movie_id):
    """
    Show details of selected movie
    """
    try:
        movie = session.query(Movies).filter_by(id=movie_id).one()
    except BaseException:
        flash('Sorry, something went wrong.', 'danger')
        return redirect(url_for('index'))

    return render_template('view_movie.html',
                           movie=movie)


@app.route('/movie/new', methods=['GET', 'POST'])
@login_required
def new_movie():
    """
    Allow logged users to create new movie
    """
    # # check user logged in
    # if not user_allowed_to_browse():
    #     flash('You need to login!', 'danger')
    #     return redirect(url_for('showLogin'))

    if request.method == 'POST':
        image_url = str(request.form['image_url'])
        if image_url == "":
            image_url = "https://placehold.it/300x200"

        movie = Movies(name=request.form['name'],
                       description=request.form['description'],
                       image_url=image_url,
                       category_id=request.form['category_id'],
                       user=getUserInfo(login_session['user_id']))
        session.add(movie)
        try:
            session.commit()
            flash('New movie added!', 'success')
            return redirect(url_for('view_movie', movie_id=movie.id))
        except Exception as e:
            flash('Something went wrong. {}'.format(e), 'danger')
            return redirect(url_for('index'))
    else:
        categories = session.query(Category).all()
        movie = {
            'id': None,
            'name': "",
            'description': "",
            'image_url': "",
            'category_id': None,
        }

        return render_template('edit_movie.html',
                               categories=categories,
                               movie=movie,
                               form_action=url_for('new_movie'))


@app.route('/movie/<int:movie_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_movie(movie_id):
    """
    Allow logged users to edit a movie
    """
    # # check user logged in
    # if not user_allowed_to_browse():
    #     flash('You need to login!', 'danger')
    #     return redirect(url_for('showLogin'))

    movie = session.query(Movies).filter_by(id=movie_id).one()

    # check user is owner of the item
    if not user_allowed_to_edit(movie):
        flash(
            'You are not authorized to edit this movie, '
            'but you can always create yours and then edit them if you want.',
            'danger')
        return redirect(url_for('index'))

    if request.method == 'POST':
        image_url = str(request.form['image_url'])
        if image_url == "":
            image_url = "https://placehold.it/300x200"

        movie.name = request.form['name']
        movie.description = request.form['description']
        movie.image_url = image_url
        movie.category_id = request.form['category_id']
        session.add(movie)
        try:
            session.commit()
            flash('Update Movies `%s` Successfully.' % movie.name, 'success')
        except Exception as e:
            flash(
                'Update Movies `%s` Unsuccessfully. %s' %
                (movie.name, e), 'danger')

        return redirect(url_for('view_movie', movie_id=movie.id))
    else:
        categories = session.query(Category).all()

        return render_template('edit_movie.html',
                               categories=categories,
                               movie=movie)


@app.route('/movies/<int:movie_id>/delete', methods=['GET', 'POST'])
@login_required
def delete_movie(movie_id):
    """
    Allow logged users to add a delete
    """
    # # check user logged in
    # if not user_allowed_to_browse():
    #     flash('You need to login!', 'danger')
    #     return redirect(url_for('showLogin'))

    movie = session.query(Movies).filter_by(id=movie_id).one()

    # check user is owner of the item
    if not user_allowed_to_edit(movie):
        flash(
            'You are not authorized to edit this movie, '
            'but you can always create yours and then delete them if you want.',
            'danger')
        return redirect(url_for('index'))

    if request.method == 'POST':
        category = session.query(Category).filter_by(
            id=movie.category_id).one()
        session.delete(movie)
        try:
            session.commit()
            flash('Delete Movies `%s` Successfully.' % movie.name, 'success')
            return redirect(url_for('view_category', category_id=category.id))
        except Exception as e:
            flash('Something went wrong. {}'.format(e), 'danger')
            return redirect(url_for('view_movie', movie_id=movie.id))
    else:
        return render_template('delete_movie.html', movie=movie)


@app.route('/catalog.json')
@app.route('/categories.json')
def api_categories():
    """
    API JSON Format: List all of the categories
    """
    categories = session.query(Category).all()
    return jsonify(categories=[c.serialize for c in categories])


@app.route('/catalog/<int:category_id>/JSON')
@app.route('/category/<int:category_id>/JSON')
def api_view_category(category_id):
    """
    API JSON Format: Show details of selected category
    """
    category = session.query(Category).filter_by(id=category_id).one()
    return jsonify(category.serialize)


@app.route('/movies.json')
def api_movies():
    """
    API JSON Format: List all of the movies
    """
    movies = session.query(Movies).all()
    return jsonify(movies=[c.serialize for c in movies])


@app.route('/movie/<int:movie_id>/JSON')
def api_view_movie(movie_id):
    """
    API JSON Format: Show details of selected movie
    """
    movie = session.query(Movies).filter_by(id=movie_id).one()
    return jsonify(movie.serialize)


if __name__ == '__main__':
    app.secret_key = 'secret'
    app.debug = True
    app.run(host='0.0.0.0', port=8000)
