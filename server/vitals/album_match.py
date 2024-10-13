# https://docs.opencv.org/4.x/dc/dc3/tutorial_py_matcher.html
import os
import io
from pprint import pprint as pp
import click
import cv2 as cv
import flask
import flask_login
import numpy as np
import werkzeug
from . import db
from . import utils

album_match = flask.Blueprint('album_match', __name__)

# settings
DEBUG = False
RESIZE_WIDTH = 150


def init_app(app):
    app.register_blueprint(album_match)
    app.cli.add_command(test_matcher)


# Library functions


def get_sift():
    if 'sift' not in flask.g:
        flask.g.sift = cv.SIFT_create()
    return flask.g.sift


def imshow(img):
    cv.imshow('album_match', img)
    key = cv.waitKey(0)
    print(f'key {key} {chr(key)!r} pressed')
    cv.destroyAllWindows()


def load_im_from_stream(stream, flags=cv.IMREAD_COLOR):
    try:
        array = np.asarray(bytearray(stream.read()), dtype=np.uint8)
        return cv.imdecode(array, flags)
    except Exception:
        # wrap all errors into bad image response
        return None


def imread(file, resize_width=None):
    if isinstance(file, str):
        # file is a file path
        img = cv.imread(file)
    elif isinstance(file, werkzeug.datastructures.file_storage.FileStorage):
        img = load_im_from_stream(file)
        if img is None:
            # bad image
            return
    elif isinstance(file, bytes):
        # file is file contents
        img = load_im_from_stream(io.BytesIO(file))
        if img is None:
            # bad image
            return
    else:
        # bad type(file)
        return

    if resize_width is not None:
        (h, w) = img.shape[:2]
        aspect_ratio = h / w
        new_height = int(resize_width * aspect_ratio)
        img = cv.resize(img, (resize_width, new_height))

    gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
    keypoints, descriptor = get_sift().detectAndCompute(gray, None)

    if DEBUG:
        # see how many keypoints an album cover may have
        kp_img = cv.drawKeypoints(gray, keypoints, img, flags=cv.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS)
        imshow(kp_img)

    return img, gray, keypoints, descriptor


def get_filesystem_library(folder, resize_width=None):
    return {
        fname: imread(f'{folder}/{fname}', resize_width)
        for fname in os.listdir(folder)
    }


def query_image(library, queries, query_fname):
    q_img, q_gray, q_kp, q_descriptor = queries[query_fname]
    all_matches = {}

    for album in library.values():
        matcher = cv.BFMatcher()
        matches = matcher.knnMatch(album.descriptor, q_descriptor, k=2)
        matches = [
            [m]
            for m,  n in matches
            if m.distance < 0.75 * n.distance
        ]

        matches_stat = len(matches)
        all_matches[album.catalog] = matches_stat, album

    return sorted(all_matches.values(), key=lambda p: -p[0])


# Commands


@click.command('test-matcher', help='test the album matcher')
@click.argument('queries_dir', metavar='QUERIES', type=click.Path(exists=True, file_okay=False))
def test_matcher(queries_dir):
    library = db.db_load_library(username='testuser')
    # assume query album will take up about 2/3 of the query picture
    queries = get_filesystem_library(queries_dir, resize_width=RESIZE_WIDTH * 3 // 2)

    for query_fname in queries:
        # do query
        all_matches = query_image(library, queries, query_fname)

        # print results
        print(f'matches for {query_fname}')
        pp(all_matches)
        print()

        # check results
        if not all_matches:
            raise RuntimeError('no matches')
        q_catalog, *_ = query_fname.split('.')
        _, album_match = all_matches[0]
        if q_catalog != album_match.catalog:
            raise RuntimeError(f'Expected catalog {q_catalog} but got catalog {album_match.catalog} from query '
                               f'{query_fname}')


# Routes


@album_match.route('/user/album/query', methods=['POST'])
@flask_login.login_required
def query_album_match():
    file = flask.request.files['query']
    # assume query album will take up about 2/3 of the query picture
    img_data = imread(file, resize_width=RESIZE_WIDTH * 3 // 2)
    if img_data is None:
        return utils.jsonify_error('bad image provided', status=400)
    queries = {
        'query': img_data,
    }
    library = db.db_load_library(flask_login.current_user.username)
    all_matches = query_image(library, queries, 'query')

    albums = []

    for matches_stat, album in all_matches:
        serialized = album.serialize()
        serialized['matches_stat'] = matches_stat
        albums.append(serialized)

    return utils.jsonify()({'albums': albums})
