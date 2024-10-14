import dataclasses
import datetime
import os
import pathlib
import shlex
import shutil
import sys
import click
import flask
import natsort
import numpy as np
import psycopg
from . import db
from . import encode
from . import utils


def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(db_shell)
    app.cli.add_command(db_reset)
    app.cli.add_command(db_version)
    app.cli.add_command(db_migrate)
    app.cli.add_command(db_load_test_data)


# Database Definition


def get_db():
    if 'psql_db' not in flask.g:
        flask.g.psql_db = psycopg.connect(
            get_db_url(),
            row_factory=psycopg.rows.namedtuple_row,
        )
    return flask.g.psql_db


def close_db(error=None):
    db = flask.g.pop('psql_db', None)
    if db is None:
        return
    db.commit()
    db.close()


@dataclasses.dataclass
class Album:
    catalog: str
    title: str
    artist: str
    num_discs: int | None = None
    discogs_release_id: str | None = None
    album_cover_url: str | None = None
    created: datetime.datetime | None = None
    descriptor: np.ndarray | None = dataclasses.field(default_factory=lambda: None, repr=None)

    @classmethod
    def load(cls, catalog):
        cur = db.get_db().cursor(row_factory=psycopg.rows.class_row(cls))
        return cur.execute('SELECT catalog, title, artist, num_discs, album_cover_url '
                           'FROM albums WHERE catalog = %s', (catalog, )).fetchone()

    def serialize(self):
        return dict(
            catalog=self.catalog,
            title=self.title,
            artist=self.artist,
            num_discs=self.num_discs,
            album_cover_url=self.album_cover_url,
        )


# Database Helpers


def get_db_url(*, dbname=None):
    host = os.getenv('VITALS_PSQL_HOSTNAME')
    user = os.getenv('VITALS_PSQL_USERNAME')
    password = os.getenv('VITALS_PSQL_PASSWORD')
    dbname = os.getenv('VITALS_PSQL_DATABASE') if dbname is None else dbname
    port = os.getenv('VITALS_PSQL_PORT')
    if any(not val for val in (host, user, password, dbname, port)):
        raise RuntimeError('source db.env')
    return f'postgres://{user}:{password}@{host}:{port}/{dbname}'


def get_db_metadata():
    return get_db().execute('SELECT * FROM db_metadata;').fetchone()


def get_version():
    return get_db_metadata().version if does_db_metadata_exist() else '2024-01-01-01'


def does_db_metadata_exist():
    db = get_db()
    cur = db.execute("SELECT EXISTS ( SELECT FROM information_schema.tables WHERE table_name = 'db_metadata' );")
    return any(table.exists for table in cur.fetchall())


def db_load_library(username):
    db = get_db().cursor(row_factory=psycopg.rows.dict_row)
    albums = {}
    query = '''\
SELECT A.*
FROM collections C
JOIN albums A ON A.catalog = C.catalog
WHERE C.username = %s
;''', (username, )

    for album in db.execute(*query).fetchall():
        album['descriptor'] = encode.decode(album['descriptor'])
        albums[album['catalog']] = Album(**album)

    return albums


def set_real_data_flag():
    # TODO implement set_real_data_flag
    ...


# Commands


@click.command('db-shell', help='start a db shell session')
def db_shell():
    command = shlex.join(['psql', get_db_url()])
    exit_code = os.system(command)
    if exit_code:
        sys.exit(exit_code)


@click.command('db-reset', help='Re-initialize the db')
@click.option('--migrations', metavar='<migrations>', default='migrations', type=pathlib.Path,
              help='Folder of migrations')
@click.option('--to-version', metavar='<version>', default='9999-99-99-99', help='Version to reset to')
@click.option('--empty', default=False, is_flag=True, help='do not initialize the db')
@click.option('--force', default=False, is_flag=True, help='force reset the db if it contains real data')
def db_reset(migrations, to_version, empty, force):
    dbname = os.getenv('VITALS_PSQL_DATABASE')
    if not dbname:
        raise RuntimeError('source db.env')

    # first check if there is real data
    try:
        metadata = get_db_metadata()
    except Exception:
        # ignore all exceptions. on initial run, all of role, database, and table will be missing.
        metadata = None

    if metadata is not None and metadata.has_real_data:
        if force:
            print('force resetting...', end='')
        else:
            raise RuntimeError('db has real data; use --force to reset')

    # need to close this connection before opening the postgres db connection
    close_db()

    # then clear the db
    try:
        postgres_db = psycopg.connect(get_db_url(dbname='postgres'), autocommit=True)
    except psycopg.OperationalError:
        user = os.getenv('VITALS_PSQL_USERNAME')
        password = os.getenv('VITALS_PSQL_PASSWORD')
        print('Run this command as your administrative user:')
        print(f'CREATE ROLE {user} WITH LOGIN CREATEDB PASSWORD \'{password}\';')
        print('')
        raise

    with postgres_db:
        postgres_db.execute(f'DROP DATABASE IF EXISTS {dbname} ;')
        postgres_db.execute(f'CREATE DATABASE {dbname} ;')
        postgres_db.execute(f"ALTER DATABASE {dbname} SET timezone = 'UTC'")

    print('db reset')

    # reset static files
    if utils.static_files().is_dir():
        print(f'clearing static files {utils.static_files()}')
        shutil.rmtree(utils.static_files())
    utils.static_files().mkdir()

    # then set up the db
    if not empty:
        db_migrate(['--migrations', migrations, '--to-version', to_version])
    else:
        print('not initializing the db')


@click.command('db-version', help='Print the version of the db')
def db_version():
    print(get_version())


@click.command('db-migrate', help='Update the db to the latest version')
@click.option('--migrations', metavar='<migrations>', default='migrations', type=pathlib.Path,
              help='Folder of migrations')
@click.option('--to-version', metavar='<version>', default='9999-99-99-99', help='Version to upgrade to')
def db_migrate(migrations, to_version):
    fname_versions = sort_and_filter_migration_fnames(os.listdir(migrations), get_version(), to_version)

    for fname, version in fname_versions:
        print(fname)
        _, ext = fname.split('.', maxsplit=1)

        if ext == 'sql':
            execute_sql_migration(migrations, fname, version)
        elif ext == 'sh':
            execute_sh_migration(migrations, fname, version)

    if not fname_versions:
        print('no migrations to do')


def execute_sql_migration(migrations, fname, version):
    with (migrations / fname).open() as f:
        sql = f.read()

    execute_migration(version, sql)


def execute_sh_migration(migrations, fname, version):
    exit_code = os.system(f'bash {migrations / fname}')
    if exit_code:
        raise RuntimeError(f'migration {fname} exited {exit_code}')
    execute_migration(version)


def execute_migration(version, sql=None):
    db = get_db()

    with db.transaction():
        if sql is not None:
            db.execute(sql)
        db.execute('UPDATE db_metadata SET version = %s', (version, ))


def sort_and_filter_migration_fnames(fnames, db_version, to_version):
    fname_versions = []
    db_version = natsort.natsort_key(db_version)
    to_version = natsort.natsort_key(to_version)

    for fname in sorted(fnames, key=natsort.natsort_key):
        _, ext = fname.split('.', maxsplit=1)
        if ext not in ('sql', 'sh'):
            continue

        version, version_key = fname_to_version(fname)

        if not (db_version < version_key <= to_version):
            continue

        fname_versions.append((fname, version))

    return fname_versions


@click.command('db-load-test-data', help='Load test data into the db')
@click.option('--migrations', metavar='<migrations>', default='migrations', type=pathlib.Path,
              help='Folder of migrations')
def db_load_test_data(migrations):
    if get_db_metadata().has_test_data:
        raise RuntimeError('db already has test data')

    fnames = sort_and_filter_test_data_fnames(os.listdir(migrations), get_version())

    db = get_db()

    for fname in fnames:
        print(fname)
        _, ext = fname.split('.', maxsplit=1)

        if ext == 'data.sql':
            load_sql_data(migrations, fname)
        elif ext == 'data.sh':
            load_sh_data(migrations, fname)

    if fnames:
        db.execute("UPDATE db_metadata SET has_test_data = 'yes'")
    else:
        print('no test data to load')


def load_sql_data(migrations, fname):
    with (migrations / fname).open() as f:
        sql = f.read()

    get_db().execute(sql)


def load_sh_data(migrations, fname):
    exit_code = os.system(f'bash {migrations / fname}')
    if exit_code:
        raise RuntimeError(f'test data {fname} exited {exit_code}')


def sort_and_filter_test_data_fnames(fnames, db_version):
    out_fnames = []
    db_version = natsort.natsort_key(db_version)

    for fname in sorted(fnames, key=natsort.natsort_key):
        _, ext = fname.split('.', maxsplit=1)
        if ext not in ('data.sql', 'data.sh'):
            continue

        _, version_key = fname_to_version(fname)

        if not version_key <= db_version:
            continue

        out_fnames.append(fname)

    return out_fnames


def fname_to_version(fname):
    try:
        year, month, day, seq, *_ = fname.split('-', 4)
    except ValueError:
        raise RuntimeError(f'fname not in correct format YYYY-MM-DD-SS-name.sql: {fname}')

    version = '-'.join((year, month, day, seq))
    version_key = natsort.natsort_key(version)
    return version, version_key
