import enum
import os
import pprint
import textwrap
import urllib
import click
import flask_login
import discogs_client
from . import db as vitals_db
from . import discogs_auth
from .discogs_auth import discogs_routes
from . import utils


def init_app(app):
    app.cli.add_command(print_collection)
    app.cli.add_command(print_sync_plan)


# Commands


def pp(object):
    pprint.pprint(object, width=120)


@click.command('print-collection')
def print_collection():
    discogs = discogs_auth.get_discogs(key='csv')
    collection, error_messages = get_discogs_collection(discogs=discogs)
    collection = {
        catalog: item.data if item is not None else None
        for catalog, item in collection.items()
    }
    pp(collection)
    if error_messages:
        pp(error_messages)


@click.command('print-sync-plan')
def print_sync_plan():
    discogs = discogs_auth.get_discogs(key='csv')
    collection, error_messages = get_discogs_collection(discogs=discogs)
    add_collection, rm_collection, add_db = get_sync_with_discogs_actions(collection, username='testuser')
    plans = get_sync_with_discogs_plan(collection, 'testuser', add_collection, rm_collection, add_db)

    for prep_plan, transaction in plans:
        if prep_plan is not None:
            pp(prep_plan)
        else:
            print('>' * 8)

        for sql, args in transaction:
            sql = textwrap.dedent(sql).strip()
            sql = textwrap.indent(sql, ' ' * 8)
            args = tuple(map(repr, args))

            try:
                print(sql % args)
            except TypeError:
                raise
                breakpoint()

    if error_messages:
        pp(error_messages)


# Validation


def validate_schema(object, schema, path):
    """returns is_valid, error_message"""
    if isinstance(schema, dict):
        if not isinstance(object, dict):
            return False, f'{path} is not a dict: {object!r}'
        for field, field_schema in schema.items():
            if field not in object:
                return False, f'{field} not in {path} which has {set(object)}'
            is_valid, error_message = validate_schema(object[field], field_schema, f'{path}.{field}')
            if not is_valid:
                return is_valid, error_message
    elif isinstance(schema, list):
        if not isinstance(object, list):
            return False, f'{path} is not a list: {object!r}'
        if not object:
            return False, f'{path} is empty'
        list_schema = schema[0]
        for i, i_object in enumerate(object):
            is_valid, error_message = validate_schema(i_object, list_schema, f'{path}[{i}]')
            if not is_valid:
                return is_valid, error_message
    elif schema is str:
        if not isinstance(object, str):
            return False, f'{path} is not a str: {object!r}'
        if not object:
            return False, f'{path} is empty string'
    elif schema is int:
        if not isinstance(object, int):
            return False, f'{path} is not an int: {object!r}'
    else:
        raise RuntimeError(f'unknown schema: {schema!r}')

    # fallthrough
    return True, None


class ValidationLevel(enum.StrEnum):
    # Ok to use all data
    Full = enum.auto()  # catalog

    # Some data may be broken, but that is OK if we already have this catalog in the db
    Catalog = enum.auto()  # (catalog, error_message)

    # We need to figure out how to support this release
    Fail = enum.auto()  # error_message


def validate_collection_item(item: discogs_client.CollectionItemInstance):
    """returns ValidationLevel, level_data"""
    catalog, catalog_error_message = get_collection_item_catalog(item)
    if catalog is None:
        return ValidationLevel.Fail, catalog_error_message
    is_valid, schema_error_message = validate_collection_item_schema(item)
    if is_valid:
        return ValidationLevel.Full, catalog
    return ValidationLevel.Catalog, (catalog, schema_error_message)


def get_collection_item_catalog(item: discogs_client.CollectionItemInstance):
    """returns (catalog, None) or (None, error_message)"""
    catalog_schema = {
        'basic_information': {
            'labels': [{
                'id': int,
                'catno': str,
            }],
        },
    }
    is_valid, error_message = validate_schema(item.data, catalog_schema, path='collection_item')
    return (item.release.labels[0].catno, None) if is_valid else (None, error_message)


def validate_collection_item_schema(item: discogs_client.CollectionItemInstance):
    """returns is_valid, error_message"""
    item_schema = {
        'id': int,
        'basic_information': {
            'id': int,
            'artists': [{
                'id': int,
                'name': str,
            }],
            'cover_image': str,
            'labels': [{
                'id': int,
                'catno': str,
            }],
            'title': str,
            'formats': [{
                'name': str,
                'qty': str,
            }],
        },
    }
    is_valid, error_message = validate_schema(item.data, item_schema, path='collection_item')
    if not is_valid:
        return is_valid, error_message

    # ids must match
    id1 = item.id
    id2 = item.release.id
    if id1 != id2:
        return False, f"ids don't match: {id1!r} and {id2!r}"

    # qty must be 1 or 2
    qty = item.release.formats[0]['qty']
    if qty not in ('1', '2'):
        return False, 'Only One LPs and Two LPs are supported'

    # format must be vinyl
    format_name = item.release.formats[0]['name']
    if format_name != 'Vinyl':
        return False, f'format is not Vinyl: {format_name!r}'

    # cover_image must be a valid image url
    # cover_image is not in the public API, so look out for missing cover_images. The alternative in the public API is
    # thumb which is really low quality (150px). The right way to go is to go to the individual release.
    cover_image = item.release.data['cover_image']
    url = urllib.parse.urlparse(cover_image)
    _, ext = os.path.splitext(url.path)
    if url.scheme != 'https':
        return False, f'bad cover_image url scheme: {url.scheme!r} {cover_image}'
    if ext not in ('.jpeg', '.jpg', '.png'):
        return False, f'bad cover_image url extension: {ext!r} {cover_image}'

    return True, None


# Collection Sync Plan


def map_actions_to_data(collection, add_collection, rm_collection, add_db):
    add_data = {}

    for catalog in add_collection:
        add_data[catalog] = vitals_db.Album.load(catalog)

    rm_data = {}

    for catalog in rm_collection:
        rm_data[catalog] = vitals_db.Album.load(catalog)

    for catalog in add_db:
        item = collection[catalog]

        if item is None:
            album = vitals_db.Album(
                catalog=catalog,
                title=None,
                artist=None,
            )
        else:
            album = vitals_db.Album(
                catalog=item.release.labels[0].catno,
                title=item.release.title,
                artist=item.release.artists[0].name,
            )

        add_data[catalog] = album

    return list(add_data.values()), list(rm_data.values())


def get_sync_with_discogs_actions(collection, username):
    albums_with_no_data = {
        catalog
        for catalog, item in collection.items()
        if item is None
    }
    all_synced_albums = get_all_synced_albums()
    user_synced_albums = get_user_synced_albums(username)
    new_albums_to_add_to_db_and_collection = set(collection) - all_synced_albums - albums_with_no_data
    old_albums_to_add_to_collection = set(collection).intersection(all_synced_albums) \
        - user_synced_albums \
        - new_albums_to_add_to_db_and_collection
    albums_to_remove_from_collection = user_synced_albums - set(collection)
    return old_albums_to_add_to_collection, albums_to_remove_from_collection, new_albums_to_add_to_db_and_collection


def get_sync_with_discogs_plan(collection, username, old_albums_to_add_to_collection, albums_to_remove_from_collection,
                               new_albums_to_add_to_db_and_collection):
    plans = []

    for catalog in old_albums_to_add_to_collection:
        plans.append((None, [plan_to_add_album_to_collection(username, catalog)]))

    for catalog in albums_to_remove_from_collection:
        plans.append((None, [plan_to_remove_album_from_collection(username, catalog)]))

    for catalog in new_albums_to_add_to_db_and_collection:
        if collection[catalog] is None:
            continue
        album_cover_sql_plan, album_cover_download_plan = plan_to_download_album_cover(collection, catalog)
        transaction = [
            plan_to_add_album_to_db(collection, catalog),
            album_cover_sql_plan,
            plan_to_add_album_to_collection(username, catalog)
        ]
        plans.append((album_cover_download_plan, transaction))

    return plans


def plan_to_add_album_to_db(collection, catalog):
    item = collection[catalog]
    title = item.release.title
    artist = item.release.artists[0].name
    discogs_release_id = item.release.id
    return '''\
        INSERT INTO albums(catalog, title, artist, discogs_release_id)
        VALUES (%s, %s, %s, %s);
    ''', (catalog, title, artist, discogs_release_id)


def plan_to_add_album_to_collection(username, catalog):
    return 'INSERT INTO collections(username, catalog) VALUES (%s, %s);', (username, catalog)


def plan_to_remove_album_from_collection(username, catalog):
    return 'DELETE FROM collections WHERE username = %s AND catalog = %s;', (username, catalog)


def plan_to_download_album_cover(collection, catalog):
    item = collection[catalog]
    cover_image_url = item.release.data['cover_image']
    url = urllib.parse.urlparse(cover_image_url)
    _, ext = os.path.splitext(url.path)
    static_path = f'album_covers/{catalog}{ext}'
    album_cover_file_location = utils.static_files() / static_path
    album_cover_url = f'/static/{static_path}'
    # TODO: do not call the lambda with None
    return (lambda descriptor: plan_to_set_album_cover(catalog, album_cover_url, descriptor))(None), dict(
        cover_image_url=cover_image_url,
        album_cover_file_location=album_cover_file_location,
    )


def plan_to_set_album_cover(catalog, album_cover_url, descriptor):
    return 'UPDATE albums SET album_cover_url = %s, descriptor = %s WHERE catalog = %s;', \
            (album_cover_url, descriptor, catalog)


def get_discogs_collection(collection_id=0, *, discogs=None):
    """returns (collection, error_messages)"""
    # default collection is the all collection
    # default discogs is the session discogs
    if discogs is None:
        discogs = discogs_auth.get_discogs()
    user = discogs.identity()
    collection_items = discogs_client.models.PaginatedList(
        client=discogs,
        url=f'{discogs._base_url}/users/{user.username}/collection/folders/{collection_id}/releases',
        key='releases',
        class_=discogs_client.CollectionItemInstance,
    )
    collection = {
        # catalog: None | CollectionItemInstance
    }
    error_messages = [
        # str
    ]

    for item in collection_items:
        validation_level, level_data = validate_collection_item(item)
        catalog = None
        error_message = None

        if validation_level == ValidationLevel.Full:
            catalog = level_data
        elif validation_level == ValidationLevel.Catalog:
            catalog, error_message = level_data
        elif validation_level == ValidationLevel.Fail:
            error_message = level_data

        if error_message is not None:
            if catalog is not None:
                error_messages.append(f'Problem with release {catalog!r}: {error_message}')
            else:
                error_messages.append(f'Problem with a release: {error_message}')

        if catalog is None:
            continue

        if catalog in collection:
            error_messages.append(f'Duplicate catalog from release#{item.id}: {catalog!r}')

        collection[catalog] = item if validation_level == ValidationLevel.Full else None

    return collection, error_messages


def get_user_synced_albums(username):
    return {
        row.catalog
        for row in vitals_db.get_db().execute('SELECT catalog FROM collections WHERE username = %s;', (username, ))
    }


def get_all_synced_albums():
    return {
        row.catalog
        for row in vitals_db.get_db().execute('SELECT catalog FROM albums;')
    }


# Routes


@discogs_routes.route('/discogs/sync_plan')
@flask_login.login_required
@discogs_auth.discogs_login_required
def discogs_sync_plan():
    collection, error_messages = get_discogs_collection()
    add_collection, rm_collection, add_db = get_sync_with_discogs_actions(collection, flask_login.current_user.username)
    add_collection = [*add_collection, *add_db]
    rm_collection = list(rm_collection)
    add_data, rm_data = map_actions_to_data(collection, add_collection, rm_collection, add_db)
    return utils.jsonify()(
        addCollection=add_data, rmCollection=rm_data, errorMessages=error_messages,
    )
