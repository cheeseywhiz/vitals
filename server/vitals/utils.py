import flask


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
