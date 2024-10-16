import dataclasses
import datetime
import flask
import flask_login
import psycopg
import werkzeug
from . import db as vitals_db
from . import wsgi
from . import utils

# Boilerplate


user_routes = flask.Blueprint('user', __name__)


def init_app(app):
    app.register_blueprint(user_routes)


@dataclasses.dataclass
class User(flask_login.UserMixin):
    username: str
    password: str
    created: datetime.datetime
    current_album: str
    current_side: int

    def get_id(self):
        return self.username


@wsgi.login_manager.user_loader
def get_user(username):
    cur = vitals_db.get_db().cursor(row_factory=psycopg.rows.class_row(User))
    user = cur.execute('SELECT * FROM users WHERE username = %s', (username, )).fetchone()
    return user


@wsgi.login_manager.unauthorized_handler
def unauthorized_handler():
    return utils.jsonify_error('unauthorized', status=401)


# Routes


@user_routes.route('/user/me', methods=['GET'])
@flask_login.login_required
def user_me():
    return utils.jsonify()(username=flask_login.current_user.username)


@user_routes.route('/user/login', methods=['POST'])
def user_login():
    flask.session.clear()
    if 'username' not in flask.request.json:
        return utils.jsonify_error('username not provided', status=400)
    if 'password' not in flask.request.json:
        return utils.jsonify_error('password not provided', status=400)
    username = flask.request.json['username']
    password = flask.request.json['password']
    user_row = vitals_db.get_db().execute('SELECT password FROM users WHERE username = %s', (username, )).fetchone()
    if user_row is None:
        return utils.jsonify_error('bad username', status=403, username=username)
    if not werkzeug.security.check_password_hash(user_row.password, password):
        return utils.jsonify_error('bad password', status=403)
    user = get_user(username)
    if user is None:
        return utils.jsonify_error('assertion error: could not retrieve user', status=500, username=username)
    flask_login.login_user(user, remember=flask.request.json.get('remember_me', False))
    return utils.jsonify_error('successfully logged in user', status=200, username=username)


@user_routes.route('/user/logout', methods=['POST'])
def user_logout():
    flask.session.clear()
    return utils.jsonify_error('successfully logged out user', status=200)


@user_routes.route('/user/sign_up', methods=['POST'])
def user_sign_up():
    if flask_login.current_user.is_authenticated:
        return utils.jsonify_error('already logged in', status=409)
    if 'username' not in flask.request.json:
        return utils.jsonify_error('username not provided', status=400)
    if 'password' not in flask.request.json:
        return utils.jsonify_error('password not provided', status=400)
    username = flask.request.json['username']
    if not username:
        return utils.jsonify_error('username not valid', status=400, username=username)
    password = flask.request.json['password']
    if not password:
        return utils.jsonify_error('password not valid', status=400, password=password)
    user_row = vitals_db.get_db().execute('SELECT 1 as exists FROM users WHERE username = %s', (username, )).fetchone()
    if user_row is not None:
        return utils.jsonify_error('username already exists', status=409, username=username)
    pw_hashed = werkzeug.security.generate_password_hash(password)
    vitals_db.get_db().execute('INSERT INTO users(username, password) VALUES (%s, %s);', (username, pw_hashed))
    return utils.jsonify_error('successfully signed up user', status=200, username=username)


@user_routes.route('/user/album', methods=['GET', 'POST', 'DELETE'])
@flask_login.login_required
def user_album():
    if flask.request.method == 'GET':
        catalog = flask_login.current_user.current_album

        if catalog is not None:
            album = vitals_db.Album.load(catalog).serialize()
        else:
            album = None

        return utils.jsonify()(album=album, side=flask_login.current_user.current_side)

    username = flask_login.current_user.username

    if flask.request.method == 'DELETE':
        vitals_db.get_db().execute('UPDATE users SET current_album = NULL WHERE username = %s', (username, ))
        return flask.Response(status=204)

    # POST

    # validate album
    if 'catalog' not in flask.request.args:
        return utils.jsonify_error('catalog not provided', status=400)
    catalog = flask.request.args['catalog']
    if not catalog:
        return utils.jsonify_error('catalog not valid', status=400, catalog=catalog)
    collection_row = vitals_db.get_db().execute(
        'SELECT 1 as exists FROM collections WHERE username = %s AND catalog = %s',
        (username, catalog)).fetchone()
    if collection_row is None:
        return utils.jsonify_error('album is not in collection', status=400, catalog=catalog)

    # validate side
    if 'side' not in flask.request.args:
        return utils.jsonify_error('side not provided', status=400)

    try:
        side = int(flask.request.args['side'])
    except ValueError:
        return utils.jsonify_error(f'side is not int: {side}', status=400)

    album = vitals_db.Album.load(catalog)
    if not (side < 2 * album.num_discs):
        return utils.jsonify_error(f'side {side} is not in release {album}', status=400)

    # set the currently playing album
    vitals_db.get_db().execute('UPDATE users SET current_album = %s, current_side = %s WHERE username = %s',
                               (catalog, side, username))

    # track history
    vitals_db.add_listening_history(username, album, side)

    return utils.jsonify()({})
