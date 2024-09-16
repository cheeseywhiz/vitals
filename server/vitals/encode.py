import base64
import lzma
import os
import pickle
import click
from . import album_match

PROCESSES = [
    (lambda x: pickle.dumps(x), lambda x: pickle.loads(x)),
    (lambda x: lzma.compress(x), lambda x: lzma.decompress(x)),
    (lambda x: base64.b64encode(x), lambda x: base64.b64decode(x)),
    (lambda x: x.decode(), lambda x: x.encode()),  # stringify the bytes data
]


def init_app(app):
    app.cli.add_command(codegen_descriptor_test_data)


def encode(obj):
    for (encode_step, _) in PROCESSES:
        obj = encode_step(obj)

    return obj


def decode(obj):
    for (_, decode_step) in PROCESSES[::-1]:
        obj = decode_step(obj)

    return obj


def get_test_data_descriptors(library):
    queries = []

    for fname, (_, _, _, descriptor) in library.items():
        catalog, _ = os.path.splitext(fname)
        queries.append(f"UPDATE albums SET descriptor = {encode(descriptor)!r} WHERE catalog = '{catalog}' ;")

    return '\n'.join(queries)


@click.command('codegen-descriptor-test-data', help='Generate SQL code that sets the descriptor for each album')
def codegen_descriptor_test_data():
    library = album_match.get_filesystem_library('album-covers-original', resize_width=album_match.RESIZE_WIDTH)
    print(get_test_data_descriptors(library))
