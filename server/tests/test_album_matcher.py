import pathlib
import flask
import pytest
import vitals
from conftest import resources

queries_dir = resources / 'queries'


def test_test_matcher(runner):
    result = runner.invoke(vitals.album_match.test_matcher, [str(queries_dir)], catch_exceptions=False)
    assert result.exit_code == 0


def post_query(client=None, filename: str | pathlib.Path = None):
    if filename is None:
        filename = queries_dir / 'SP-70040.what-is-beat.png'
    url = flask.url_for('album_match.query_album_match')
    with open(str(filename), 'rb') as file:
        return client.post(url, data={
            'query': file,
        })


def test_QueryAlbumMatch_LoggedOut_Unauthorized(client):
    """if the user is logged out then /query_album_match should return unauthorized"""
    response = post_query(client).json
    assert 'status' in response
    assert response['status'] == 401


def test_QueryAlbumMatch_NoFile_ReturnsError(testuser_client):
    """/query_album_match should return an error if the query image was not provided"""
    url = flask.url_for('album_match.query_album_match')
    response = testuser_client.post(url)
    assert response.status_code == 400


def test_QueryAlbumMatch_EmptyFile_ReturnsError(testuser_client):
    """/query_album_match should return an error if the query image was empty"""
    response = post_query(filename='/dev/null', client=testuser_client)
    assert response.status_code == 400
    assert response.json is not None
    assert 'status' in response.json
    assert response.json['status'] == 400
    assert 'message' in response.json
    assert response.json['message']


def test_QueryAlbumMatch_BasicQuery_Returns200Json(testuser_client):
    """/query_album_match should return properly formatted json with one key 'albums'"""
    response = post_query(testuser_client)
    assert response.status_code == 200
    assert response.json is not None


def test_QueryAlbumMatch_BasicQuery_ReturnsSchema(testuser_client, helpers):
    """/query_album_match should return the catalog, album title, and artist for each matching album"""
    response = post_query(testuser_client).json
    assert 'albums' in response
    assert len(response['albums']) >= 1

    for album in response['albums']:
        assert 'catalog' in album
        assert album['catalog']  # assert non-empty etc
        assert 'title' in album
        assert album['title']
        assert 'artist' in album
        assert album['artist']
        assert 'album_cover_url' in album
        assert album['album_cover_url']
        helpers.validate_static_file_exists(album['album_cover_url'])


def test_QueryAlbumMatch_EmptyUser_EmptyAlbums(emptyuser_client):
    """if the user does not have a collection then /query_album_match should return an empty albums list"""
    response = post_query(emptyuser_client).json
    assert 'albums' in response
    assert len(response['albums']) == 0


@pytest.mark.parametrize('query_fname', queries_dir.iterdir())
def test_QueryAlbumMatch_BasicQueries_MatchesCorrectly(testuser_client, query_fname):
    """/query_album_match should return the matching album as the first album in the matches list"""
    # get the catalog from the query_fname
    q_catalog, *_ = query_fname.name.split('.')
    response = post_query(filename=query_fname, client=testuser_client).json

    album_match = response['albums'][0]
    assert q_catalog == album_match['catalog']
