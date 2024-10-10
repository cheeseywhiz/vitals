import pathlib
import flask
import pytest
import vitals

resources = pathlib.Path(__file__).parent / 'resources'


@pytest.fixture
def app():
    return vitals.wsgi.create_app(vitals_testing=True)


@pytest.fixture
def runner(app):
    return app.test_cli_runner()


@pytest.fixture
def client(app):
    with app.test_client() as client:
        yield client


@pytest.fixture
def fresh_db(runner):
    runner.invoke(vitals.db.db_reset, catch_exceptions=False)
    runner.invoke(vitals.db.db_load_test_data, catch_exceptions=False)
    vitals.db.close_db()


def user_client(username, password, app, setup=False):
    with app.test_client() as client:
        with app.app_context():
            url = flask.url_for('user.user_login')
            response = client.post(url, json=dict(username=username, password=password))
            assert response.status_code == 200

            if setup:
                yield client
                # do more setup then pass back

        yield client


@pytest.fixture
def testuser_client(app):
    yield from user_client('testuser', 'password', app)


@pytest.fixture
def emptyuser_client(app):
    yield from user_client('emptyuser', 'empty', app)


@pytest.fixture
def current_album_client(app):
    client_manager = user_client('testuser', 'password', app, setup=True)
    client = next(client_manager)
    url = flask.url_for('user.user_album', catalog='TPLP101')
    response = client.post(url)
    assert response.status_code == 200
    yield from client_manager


@pytest.fixture
def helpers():
    return Helpers()


class Helpers:
    @staticmethod
    def validate_static_file_exists(url):
        if not url.startswith('/static/'):
            raise RuntimeError(f'url is not a static file: {url}')
        file_path = url[len('/static/'):]
        if not file_path:
            raise RuntimeError(f'invalid static url: {url}')
        if not (vitals.utils.static_files() / file_path).is_file():
            raise RuntimeError(f'static file does not exist: {url}')
