import dataclasses
import os
import flask
import json
from . import album_match


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
    app = App(
        __name__,
        # set files used by the server to a special folder (flask.current_app.instance_path)
        instance_relative_config=True,
    )

    album_match.init_app(app)

    if app.debug:
        secret_key = 'development'
    else:
        secret_key = os.getenv('APP_SECRET_KEY')

    app.config.from_mapping(
        SECRET_KEY=secret_key,
        APPLICATION_ROOT='/api/v1',
    )
    app.wsgi_app = PrefixMiddleware(app.wsgi_app, app.config['APPLICATION_ROOT'])
    return app
