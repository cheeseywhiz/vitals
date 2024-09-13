import pathlib
import flask
import pytest
import vitals

resources = pathlib.Path(__file__).parent / 'resources'


@pytest.fixture
def app():
    app = vitals.wsgi.create_app()
    app.config.update({
        'TESTING': True,
    })
    return app


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


def user_client(username, password, app):
    with app.test_client() as client:
        with app.app_context():
            url = flask.url_for('user.user_login')
            response = client.post(url, json=dict(username=username, password=password))
            assert response.status_code == 200

        yield client


@pytest.fixture
def testuser_client(app):
    yield from user_client('testuser', 'password', app)
