import csv
import os
import discogs_client
import flask
import flask_login
from . import wsgi
from . import utils

discogs_routes = flask.Blueprint('discogs', __name__)


def init_app(app):
    app.register_blueprint(discogs_routes)


def get_discogs(key=None):
    if 'discogs' not in flask.g or key is not None:
        if not os.path.isfile('discogs.csv.secret'):
            raise RuntimeError('discogs auth not enabled: discogs.csv.secret not found')
        with open('discogs.csv.secret') as f:
            vars, data = csv.reader(f)
        secrets = {
            var: datum
            for var, datum in zip(vars, data)
        }

        if key == 'csv':
            token = secrets['session_token']
            secret = secrets['session_secret']
        elif key is not None:
            token, secret = key
        else:
            token, secret = get_discogs_key()

        flask.g.discogs = discogs_client.Client(
            wsgi.USER_AGENT,
            consumer_key=secrets['consumer_key'],
            consumer_secret=secrets['consumer_secret'],
            token=token,
            secret=secret,
        )

    return flask.g.discogs


def store_discogs_key(token, secret):
    # TODO: encrypt this
    flask.session['discogs_key'] = token, secret


def get_discogs_key():
    # TODO: descrypt this
    if 'discogs_key' not in flask.session:
        return None, None
    return flask.session['discogs_key']


def logout_discogs():
    flask.session.pop('discogs_key', None)


@discogs_routes.route('/discogs/login')
@flask_login.login_required
def login_with_discogs():
    vitals_callback = flask.request.args.get('vitals_callback', utils.url_for('/', _external=True))
    if is_discogs_authenticated():
        return flask.redirect(vitals_callback)

    # step 1: instantiate the client with the consumer key and secret
    discogs = get_discogs()
    redirect_url = flask.url_for('discogs.discogs_oauth_callback', vitals_callback=vitals_callback, _external=True)

    # step 2: get authorization url
    req_token, req_secret, auth_url = discogs.get_authorize_url(redirect_url)
    store_discogs_key(req_token, req_secret)

    # step 3: the user logs in with discogs
    return flask.redirect(auth_url)


@discogs_routes.route('/discogs/callback')
@flask_login.login_required
def discogs_oauth_callback():
    """if there was an error then see if we are already authenticated. on success, redirect to vitals."""
    vitals_callback = flask.request.args.get('vitals_callback', '/')
    error = discogs_oauth_callback_impl()
    if error is not None and not is_discogs_authenticated():
        return flask.redirect(flask.url_for('discogs.my_discogs_auth_error_page', error=error,
                                            vitals_callback=vitals_callback))
    return flask.redirect(vitals_callback)


def discogs_oauth_callback_impl():
    """process the oauth callback. returns an error or None on success."""
    # validate request
    oauth_token = flask.request.args.get('oauth_token')
    if oauth_token is None:
        return 'discogs did not send an oauth token'
    verifier = flask.request.args.get('oauth_verifier')
    if verifier is None:
        return 'discogs did not send an oauth verifier'
    req_token, req_secret = get_discogs_key()
    if req_token != oauth_token:
        return 'discogs ooauth request mismatch'

    # step 4: get access token
    discogs = get_discogs((req_token, req_secret))

    try:
        discogs_token, discogs_secret = discogs.get_access_token(verifier)
    except discogs_client.exceptions.HTTPError:
        logout_discogs()
        return 'stale discogs oauth verifier'

    # step 5: validate access
    if not is_discogs_authenticated(discogs):
        logout_discogs()
        return 'discogs authentication failed'

    # step 6: save access
    store_discogs_key(discogs_token, discogs_secret)
    return None


def is_discogs_authenticated(discogs=None):
    """returns identity or None"""
    if discogs is None:
        token, secret = get_discogs_key()
        if token is None or secret is None:
            return None

        discogs = get_discogs()

    try:
        return discogs.identity()
    except discogs_client.exceptions.HTTPError:
        return None


@discogs_routes.route('/discogs/error_page')
def my_discogs_auth_error_page():
    return utils.jsonify_error(
        message=flask.request.args.get('error', ''),
        status=500,
        vitals_callback=flask.request.args.get('vitals_callback', ''),
    )


@discogs_routes.route('/discogs/identity')
@flask_login.login_required
def discogs_identity():
    discogs_identity = is_discogs_authenticated()

    if discogs_identity is not None:
        serialized = dict(
            username=discogs_identity.username,
        )
    else:
        serialized = None

    return utils.jsonify()(
        loginUrl=flask.url_for('discogs.login_with_discogs'),
        discogsIdentity=serialized,
    )
