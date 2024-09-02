# https://docs.opencv.org/4.x/dc/dc3/tutorial_py_matcher.html
import os
from pprint import pprint as pp
import click
import cv2 as cv
import flask
import numpy as np
import werkzeug
from . import encode
from . import utils

album_match = flask.Blueprint('album_match', __name__)

# settings
DEBUG = False
RESIZE_WIDTH = 150


def init_app(app):
    app.register_blueprint(album_match)
    app.cli.add_command(test_matcher)


def get_sift():
    if 'sift' not in flask.g:
        flask.g.sift = cv.SIFT_create()
    return flask.g.sift


def get_library2():
    if 'library' not in flask.g:
        flask.g.library = get_library('album-covers-original', resize_width=RESIZE_WIDTH)
    return flask.g.library


def imshow(img):
    cv.imshow('album_match', img)
    key = cv.waitKey(0)
    print(f'key {key} {chr(key)!r} pressed')
    cv.destroyAllWindows()


def load_im_from_stream(stream, flags=cv.IMREAD_COLOR):
    array = np.asarray(bytearray(stream.read()), dtype=np.uint8)
    return cv.imdecode(array, flags)


def imread(file, resize_width=None):
    if isinstance(file, str):
        img = cv.imread(file)
    elif isinstance(file, werkzeug.datastructures.file_storage.FileStorage):
        img = load_im_from_stream(file)
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


def get_library(folder, resize_width=None):
    return {
        fname: imread(f'{folder}/{fname}', resize_width)
        for fname in os.listdir(folder)
    }


@click.command('test-matcher', help="test the album matcher")
def test_matcher():
    library = get_library('album-covers-original', resize_width=RESIZE_WIDTH)
    # assume query album will take up about 2/3 of the query picture
    queries = get_library('queries', resize_width=RESIZE_WIDTH * 3 // 2)

    for query_fname in queries:
        query_image(queries, query_fname)

    pp(queries)

    encode.test_encoding(library)


def query_image(queries, query_fname):
    q_img, q_gray, q_kp, query_descriptor = queries[query_fname]
    all_matches = {}

    for library_fname, (l_img, _, l_kp, library_descriptor) in get_library2().items():
        matcher = cv.BFMatcher()
        matches = matcher.knnMatch(library_descriptor, query_descriptor, k=2)
        matches = [
            [m]
            for m, n in matches
            if m.distance < 0.75 * n.distance
        ]

        if DEBUG:
            matches_img = cv.drawMatchesKnn(l_img, l_kp, q_img, q_kp, matches, None,
                                            flags=cv.DrawMatchesFlags_NOT_DRAW_SINGLE_POINTS)
            imshow(matches_img)

        matches_stat = len(matches)
        all_matches[library_fname] = matches_stat

    winner = sorted(all_matches.items(), key=lambda p: p[1])[-1] if all_matches else None
    queries[query_fname] = winner, all_matches


@album_match.route("/query_album_match", methods=["POST"])
def query_album_match():
    file = flask.request.files['query']
    # assume query album will take up about 2/3 of the query picture
    img_data = imread(file, resize_width=RESIZE_WIDTH * 3 // 2)
    if img_data is None:
        return utils.jsonify_error('bad image provided', status=400)
    queries = {
        'query': img_data,
    }
    query_image(queries, 'query')
    return utils.jsonify()(queries)
