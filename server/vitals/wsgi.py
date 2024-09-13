import dataclasses
import os
import flask
import flask_login
import json

login_manager = flask_login.LoginManager()

from . import album_match
from . import db
from . import encode
from . import user


class DataclassJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if dataclasses.is_dataclass(obj):
            return dataclasses.asdict(obj)
        return super().default(obj)


class App(flask.Flask):
    json_encoder = DataclassJSONEncoder


class PrefixMiddleware:
    def __init__(self, wsgi_app, prefix):
        self.wsgi_app = wsgi_app
        self.prefix = prefix

    def __call__(self, environ, start_response):
        if environ['PATH_INFO'].startswith(self.prefix):
            environ['PATH_INFO'] = environ['PATH_INFO'][len(self.prefix):]
            environ['SCRIPT_NAME'] = self.prefix
            return self.wsgi_app(environ, start_response)
        else:
            start_response('404', [('Content-Type', 'text/plain')])
            return [b'this url does not belong to the app']


def create_app():
    # check db.env
    if os.getenv('VITALS_PSQL_HOSTNAME') is None:
        raise RuntimeError('source db.env')

    app = App(
        __name__,
        # set files used by the server to a special folder (flask.current_app.instance_path)
        instance_relative_config=True,
    )

    login_manager.init_app(app)
    app.test_client_class = flask_login.FlaskLoginClient

    album_match.init_app(app)
    db.init_app(app)
    encode.init_app(app)
    user.init_app(app)

    if app.debug:
        secret_key = 'development'
    else:
        secret_key = os.getenv('VITALS_SECRET_KEY')

    app.config.from_mapping(
        SECRET_KEY=secret_key,
        APPLICATION_ROOT='/api/v1',
    )
    app.wsgi_app = PrefixMiddleware(app.wsgi_app, app.config['APPLICATION_ROOT'])
    return app
