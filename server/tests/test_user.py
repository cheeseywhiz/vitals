import flask


class TestLogin:
    def post_login(client=None, username='testuser', password='password', remember_me=None):
        json = {}
        if username is not None:
            json['username'] = username
        if password is not None:
            json['password'] = password
        if remember_me is not None:
            json['remember_me'] = remember_me
        url = flask.url_for('user.user_login')
        return client.post(url, json=json)

    def test_Login_EmptyReq_Returns415(self, client):
        """/login should return HTTP 415 if the request body is empty"""
        url = flask.url_for('user.user_login')
        response = client.post(url)
        assert response.status_code == 415

    def test_Login_EmptyJson_Returns400(self, client):
        """/login should return HTTP 400 if neither username now password were provided."""
        response = TestLogin.post_login(client, username=None, password=None)
        assert response.status_code == 400

    def test_Login_NoPassword_Returns400(self, client):
        """/login should return HTTP 400 if the password was not provided"""
        response = TestLogin.post_login(password=None, client=client)
        assert response.status_code == 400

    def test_Login_BadUsername_Returns403(self, client):
        """/login should return HTTP 403 if the username was not found"""
        response = TestLogin.post_login(username='BadUsername', password='BadPassword', client=client)
        assert response.status_code == 403

    def test_Login_BadPassword_Returns403(self, client):
        """/login should return HTTP 403 if the password was the wrong password"""
        response = TestLogin.post_login(password='BadPassword', client=client)
        assert response.status_code == 403

    def test_Login_GoodLoginData_SuccessJson(self, client):
        """/login should return success if the username and password were correct"""
        response = TestLogin.post_login(client)
        assert response.status_code == 200
        assert response.json is not None

    def test_Login_GoodLoginData_ReturnsCorrectUsername(self, client):
        """/login should return the username of the user that logged in"""
        response = TestLogin.post_login(client)
        assert response.status_code == 200  # smoke test
        assert 'username' in response.json
        assert response.json['username'] == 'testuser'

    def test_Login_GoodLoginData_UserInSession(self, client):
        """/login should store the user in the session if successfully logged in"""
        TestLogin.post_login(client)
        assert '_user_id' in flask.session
        assert flask.session['_user_id'] == 'testuser'

    def test_Login_RememberMe_Success(self, client):
        """/login should return success if the remember me parameter was provided."""
        response = TestLogin.post_login(remember_me=True, client=client)
        assert response.status_code == 200

    def test_Login_DoNotRememberMe_Success(self, client):
        """/login should return success if the remember me parameter was provided and the value was false."""
        response = TestLogin.post_login(remember_me=False, client=client)
        assert response.status_code == 200

    def test_Login_SecretsInSession_BadPassword_SessionIsCleared(self, client):
        """/login should clear the session even if there are errors in the login process"""
        secret_name = 'MyTestSecret'
        with client.session_transaction() as session:
            session[secret_name] = 'shhh'
        TestLogin.post_login(password='BadPassword', client=client)
        assert secret_name not in flask.session

    def test_Login_SecretsInSession_GoodLoginData_SessionIsCleared(self, client):
        """/login should clear the session"""
        secret_name = 'MyTestSecret'
        with client.session_transaction() as session:
            session[secret_name] = 'shhh'
        TestLogin.post_login(client)
        assert secret_name not in flask.session

    def test_Login_UserAlreadyLoggedIn_GoodLoginData_Success(self, testuser_client):
        """if the user is already logged in then /login should return success"""
        response = TestLogin.post_login(testuser_client)
        assert response.status_code == 200
        assert '_user_id' in flask.session
        assert flask.session['_user_id'] == 'testuser'


class TestLogout:
    def logout(client):
        url = flask.url_for('user.user_logout')
        response = client.post(url)
        return response

    def test_Logout_UserNotLoggedIn_Success(self, client):
        """if no user is logged in then /logout should return success"""
        TestLogout.logout(client)

    def test_Logout_UserNotLoggedIn_SessionIsCleared(self, client):
        """if no user is logged in then /logout should clear the session"""
        secret_name = 'MyTestSecret'
        with client.session_transaction() as session:
            session[secret_name] = 'shhh'
        TestLogout.logout(client)
        assert secret_name not in flask.session

    def test_Logout_UserLoggedIn_Success(self, testuser_client):
        """if a user is logged in then /logout should return success"""
        TestLogout.logout(testuser_client)

    def test_Logout_UserLoggedIn_SessionIsCleared(self, testuser_client):
        """if a user is logged in then /logout should clear the session"""
        secret_name = 'MyTestSecret'
        with testuser_client.session_transaction() as session:
            session[secret_name] = 'shhh'
        TestLogout.logout(testuser_client)
        assert secret_name not in flask.session


class TestSignUp:
    USERNAME = 'signupuser'
    PASSWORD = 'signuppassword'

    def post_sign_up(client=None, username=USERNAME, password=PASSWORD):
        json = {}
        if username is not None:
            json['username'] = username
        if password is not None:
            json['password'] = password
        url = flask.url_for('user.user_sign_up')
        return client.post(url, json=json)

    def post_login(client=None):
        return TestLogin.post_login(client, username=TestSignUp.USERNAME, password=TestSignUp.PASSWORD)

    def test_SignUp_UserLoggedIn_Invalid(self, testuser_client):
        """if a user is logged in then /sign_up should return an error"""
        response = TestSignUp.post_sign_up(testuser_client)
        assert response.status_code == 409

    def test_SignUp_EmptyReq_Invalid(self, client):
        """/sign_up should return an error if the request body is empty"""
        url = flask.url_for('user.user_sign_up')
        response = client.post(url)
        assert response.status_code == 415

    def test_SignUp_EmptyJson_Invalid(self, client):
        """/sign_up should return an error if neither the username nor the password were provided"""
        response = TestSignUp.post_sign_up(username=None, password=None, client=client)
        assert response.status_code == 400

    def test_SignUp_NoPassword_Invalid(self, client):
        """/sign_up should return an error if the password was not provided"""
        response = TestSignUp.post_sign_up(password=None, client=client)
        assert response.status_code == 400

    def test_SignUp_DuplicateUsername_Invalid(self, client):
        """/sign_up should return an error if the username was already taken"""
        response = TestSignUp.post_sign_up(username='testuser', password='duplicatepassword', client=client)
        assert response.status_code == 409

    def test_SignUp_EmptyUsername_Invalid(self, client):
        """/sign_up should return an error if the username was blank"""
        response = TestSignUp.post_sign_up(username='', client=client)
        assert response.status_code == 400

    def test_SignUp_EmptyPassword_Invalid(self, client):
        """/sign_up should return an error if the password was blank"""
        response = TestSignUp.post_sign_up(password='', client=client)
        assert response.status_code == 400

    def test_SignUp_GoodSignUpData_Success(self, client, fresh_db):
        """/sign_up should return success to a request to sign up a new user with a valid password"""
        response = TestSignUp.post_sign_up(client)
        assert response.status_code == 200

    def test_SignUp_GoodSignUpData_IsNotLoggedIn(self, client, fresh_db):
        """if /sign_up succeeds then the user should not be logged in"""
        response = TestSignUp.post_sign_up(client)
        assert response.status_code == 200
        assert '_user_id' not in flask.session

    def test_SignUp_GoodSignUpData_IsLogInable(self, client, fresh_db):
        """if /sign_up succeeded then we should be able to log in as the user"""
        response = TestSignUp.post_sign_up(client)
        assert response.status_code == 200
        response = TestSignUp.post_login(client)
        assert response.status_code == 200
        assert '_user_id' in flask.session
        assert flask.session['_user_id'] == TestSignUp.USERNAME


class TestUserAlbum:
    TEST_CATALOG = 'TPLP101'  # Vespertine

    def post_album(client=None, catalog=TEST_CATALOG):
        params = {}
        if catalog is not None:
            params['catalog'] = catalog
        url = flask.url_for('user.user_album', **params)
        return client.post(url)

    def get_album(client):
        url = flask.url_for('user.user_album')
        return client.get(url)

    def stop_play(client):
        url = flask.url_for('user.user_album')
        return client.delete(url)

    # POST /user/album

    def test_UserAlbum_NotLoggedIn_SetAlbum_Unauthorized(self, client):
        """if the user is not logged in then setting the current album should return unauthorized"""
        response = TestUserAlbum.post_album(client)
        assert response.status_code == 401

    def test_UserAlbum_SetNoAlbum_Invalid(self, testuser_client):
        """setting the current album should be rejected if no album was provided"""
        response = TestUserAlbum.post_album(catalog=None, client=testuser_client)
        assert response.status_code == 400

    def test_UserAlbum_SetEmptyAlbum_Invalid(self, testuser_client):
        """setting the current album to an empty album should be rejected"""
        response = TestUserAlbum.post_album(catalog='', client=testuser_client)
        assert response.status_code == 400

    def test_UserAlbum_SetInvalidAlbum_Invalid(self, testuser_client):
        """setting the current album to an unknown album should be rejected"""
        response = TestUserAlbum.post_album(catalog='imadethisup', client=testuser_client)
        assert response.status_code == 400

    def test_UserAlbum_SetAlbumNotInCollection_Invalid(self, emptyuser_client):
        """setting the current album to an album that is not in the current collection should be rejected"""
        response = TestUserAlbum.post_album(client=emptyuser_client)
        assert response.status_code == 400

    def test_UserAlbum_SetValidAlbum_Returns200Json(self, testuser_client, fresh_db):
        """setting the current album to a valid album should succeed and return properly formatted data"""
        response = TestUserAlbum.post_album(testuser_client)
        assert response.status_code == 200
        assert response.json is not None

    # GET /user/album

    def test_UserAlbum_NotLoggedIn_GetAlbum_Unauthorized(self, client):
        """if the user is not logged in then getting the current album should return unauthorized"""
        response = TestUserAlbum.get_album(client)
        assert response.status_code == 401

    def test_UserAlbum_SetValidAlbum_GetAlbum_Returns200Json(self, current_album_client):
        """once a current album is set, getting the current album should succeed and return properly formatted data"""
        response = TestUserAlbum.get_album(current_album_client)
        assert response.status_code == 200
        assert response.json is not None

    def test_UserAlbum_SetValidAlbum_GetAlbum_ReturnsSchema(self, current_album_client):
        """once a current album is set, getting the current album should return the correct kind of data"""
        response = TestUserAlbum.get_album(current_album_client).json
        assert 'album' in response
        assert 'catalog' in response['album']
        assert response['album']['catalog']
        assert 'title' in response['album']
        assert response['album']['title']
        assert 'artist' in response['album']
        assert response['album']['artist']

    def test_UserAlbum_SetValidAlbum_GetAlbum_IsCorrectAlbum(self, current_album_client):
        """once a current album is set, getting the current album should return the correct album"""
        response = TestUserAlbum.get_album(current_album_client).json
        assert response['album']['catalog'] == TestUserAlbum.TEST_CATALOG

    def test_UserAlbum_NoCurrentAlbum_GetAlbum_ReturnsEmpty(self, testuser_client, fresh_db):
        """if there isn't an album playing then getting the current album should return an empty response"""
        response = TestUserAlbum.get_album(testuser_client)
        assert response.status_code == 200
        assert response.json is not None
        assert 'album' in response.json
        assert response.json['album'] is None

    # DELETE /user/album

    def test_UserAlbum_NotLoggedIn_StopPlay_Unauthorized(self, client):
        """if the user is not logged in then stopping play should return unauthorized"""
        response = TestUserAlbum.stop_play(client)
        assert response.status_code == 401

    def test_UserAlbum_NoCurrentAlbum_StopPlay_Succeeds(self, testuser_client, fresh_db):
        """if there isn't an album playing then stopping play should succeed"""
        response = TestUserAlbum.stop_play(testuser_client)
        assert response.status_code == 204

    def test_UserAlbum_NoCurrentAlbum_StopPlay_NoAlbumShouldBePlaying(self, testuser_client, fresh_db):
        """if there isn't an album playing then stopping play should render no currently playing album"""
        response = TestUserAlbum.stop_play(testuser_client)
        assert response.status_code == 204  # smoke test
        response = TestUserAlbum.get_album(testuser_client).json
        assert response['album'] is None

    def test_UserAlbum_CurrentlyPlaying_StopPlay_Succeeds(self, current_album_client, fresh_db):
        """if there is an album playing then stopping play should succeed"""
        response = TestUserAlbum.stop_play(current_album_client)
        assert response.status_code == 204

    def test_UserAlbum_CurrentlyPlaying_StopPlay_NoAlbumShouldBePlaying(self, current_album_client, fresh_db):
        """if there is an album playing then stopping play should render no currently playing album"""
        response = TestUserAlbum.stop_play(current_album_client)
        assert response.status_code == 204  # smoke test
        response = TestUserAlbum.get_album(current_album_client).json
        assert response['album'] is None
