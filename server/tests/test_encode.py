import os
import numpy as np
import pytest
import vitals


@pytest.fixture  # (scope='session')
def fs_library(app):
    return vitals.album_match.get_filesystem_library(
        'album-covers-original', resize_width=vitals.album_match.RESIZE_WIDTH)


@pytest.mark.parametrize('object_equal', [
    ('abc', None),
    (np.asarray([[1, 0], [0, 1]]), np.array_equal),
    (np.asarray([]), np.array_equal),
])
def test_encode_decode_correctly(object_equal):
    """x == decode(encode(x))"""
    obj, equal = object_equal
    if equal is None:
        def equal(x, y):
            return x == y
    object2 = vitals.encode.decode(vitals.encode.encode(obj))
    assert equal(obj, object2)


def test_encoding(fs_library):
    """make sure each descriptor in the fs_library are encodable"""
    for fname, (_, _, _, descriptor) in fs_library.items():
        save_descriptor = descriptor
        descriptor = vitals.encode.encode(descriptor)
        descriptor = vitals.encode.decode(descriptor)
        assert np.array_equal(descriptor, save_descriptor)


def test_codegen(fresh_db, fs_library):
    """wipe the descriptors from the database, reset them with the codegen output, then check the descriptors."""
    # wipe the descriptors from the database
    vitals.db.get_db().execute('UPDATE albums SET descriptor = NULL')

    # reset the descriptors with the codegen output
    query = vitals.encode.get_test_data_descriptors(fs_library)
    vitals.db.get_db().execute(query)

    # check the descriptors from the database
    for fname, (_, _, _, descriptor) in fs_library.items():
        catalog, _ = os.path.splitext(fname)
        db_descriptor = vitals.db.get_db() \
            .execute('SELECT descriptor FROM albums WHERE catalog = %s', (catalog, )).fetchone().descriptor
        db_descriptor = vitals.encode.decode(db_descriptor)
        assert np.array_equal(descriptor, db_descriptor)
