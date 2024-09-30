import flask
import functools


def debug(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception:
            import pdb
            import sys
            pdb.post_mortem(sys.exc_info()[2])
            raise

    return wrapper


def jsonify(status=200):
    def wrapper(*args, **kwargs):
        response = flask.jsonify(*args, **kwargs)
        response.status_code = status
        return response

    return wrapper


def jsonify_error(message=None, status=500, **kwargs):
    response = {
        'status': status,
        **kwargs,
    }
    if message is not None:
        response['message'] = message
    return jsonify(status)(response)


def url_for(endpoint, *args, _external=None, **kwargs):
    """generate a url that is not associated with a named route"""
    if not endpoint.startswith('/'):
        return flask.url_for(endpoint, *args, **kwargs)
    if _external is None:
        _external = bool(flask.request)
    return endpoint if not _external else get_server_name() + endpoint


def get_server_name():
    server_name = flask.current_app.config.get('SERVER_NAME')
    if server_name is not None:
        return server_name
    if not flask.request:
        raise RuntimeError('get_server_name must be called from a request context if SERVER_NAME is not set')
    host = flask.request.headers.get('Host')
    if host is None:
        raise RuntimeError('get_server_name must have the Host header set')
    return 'http://' + host


def slow(*, seconds=5):
    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            import time
            time.sleep(seconds)
            return f(*args, **kwargs)

        return wrapper

    return decorator


def static_files():
    return flask.current_app.config['STATIC_FILES']
