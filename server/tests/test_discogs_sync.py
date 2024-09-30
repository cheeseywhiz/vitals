import flask
import pytest
import discogs_client
import vitals


@pytest.fixture
def mock_discogs():
    return vitals.mock_discogs_client.MockDiscogsClient()


def get_collection_item_data():
    catalog = 'ABC 123'
    return catalog, dict(
        id=1,
        basic_information=dict(
            id=1,
            artists=[dict(
                id=1,
                name='John Smith',
            )],
            cover_image='https://cdn.com/image.png',
            labels=[dict(
                id=1,
                catno=catalog,
            )],
            title='My Album Title',
            formats=[dict(
                name='Vinyl',
                qty='1',
            )],
        ),
    )


def test_ValidateRelease_BasicAlbum_IsValid(mock_discogs):
    item = discogs_client.CollectionItemInstance(mock_discogs, get_collection_item_data()[1])
    validation_level, catalog = vitals.discogs_sync.validate_collection_item(item)
    assert validation_level == vitals.discogs_sync.ValidationLevel.Full
    assert catalog == item.release.labels[0].catno


def test_ValidateRelease_TwoLP_IsValid(mock_discogs):
    """A two LP will have formats[0].qty set to '2'"""
    _, item_data = get_collection_item_data()
    item_data['basic_information']['formats'][0]['qty'] = '2'
    item = discogs_client.CollectionItemInstance(mock_discogs, item_data)
    validation_level, catalog = vitals.discogs_sync.validate_collection_item(item)
    assert validation_level == vitals.discogs_sync.ValidationLevel.Full
    assert catalog == item.release.labels[0].catno


def test_ValidateRelease_ThreeLP_IsCatnoLevel(mock_discogs):
    """A three LP is not supported, but the release's catno may still be read."""
    _, item_data = get_collection_item_data()
    item_data['basic_information']['formats'][0]['qty'] = '3'
    item = discogs_client.CollectionItemInstance(mock_discogs, item_data)
    validation_level, level_data = vitals.discogs_sync.validate_collection_item(item)
    assert validation_level == vitals.discogs_sync.ValidationLevel.Catalog
    catalog, error_message = level_data
    assert catalog == item.release.labels[0].catno
    assert error_message is not None


def test_ValidateRelease_NoCatno_IsInvalid(mock_discogs):
    """A release without a catno is not supported"""
    _, item_data = get_collection_item_data()
    del item_data['basic_information']['labels'][0]['catno']
    item = discogs_client.CollectionItemInstance(mock_discogs, item_data)
    validation_level, error_message = vitals.discogs_sync.validate_collection_item(item)
    assert validation_level == vitals.discogs_sync.ValidationLevel.Fail
    assert error_message is not None
    assert isinstance(error_message, str)


def mock_collection(monkeypatch, mock_discogs=None, collection=None):
    def mocked_paginated_list(*args, **kwargs):
        return [
            discogs_client.CollectionItemInstance(mock_discogs, item)
            for item in collection
        ]
    monkeypatch.setattr(discogs_client.models, 'PaginatedList', mocked_paginated_list)
    discogs_client.models.PaginatedList()


class TestDiscogsSyncPlan:
    def get_sync_plan(client):
        url = flask.url_for('discogs.discogs_sync_plan')
        return client.get(url)

    def test_DiscogsSyncPlan_EmptyCollection_200Json(self, discogs_vitals_client, monkeypatch):
        """If the discogs collection is empty the plan should return well-formatted data"""
        mock_collection(monkeypatch, collection=[])
        response = TestDiscogsSyncPlan.get_sync_plan(discogs_vitals_client)
        assert response.status_code == 200
        assert response.json is not None

    def test_DiscogsSyncPlan_EmptyCollection_ReturnsSchema(self, discogs_vitals_client, monkeypatch):
        """if the discogs collection is empty the plan should return the expected data"""
        mock_collection(monkeypatch, collection=[])
        response = TestDiscogsSyncPlan.get_sync_plan(discogs_vitals_client)
        assert 'addCollection' in response.json
        assert 'rmCollection' in response.json
        assert 'errorMessages' in response.json

    def test_DiscogsSyncPlan_EmptyCollection_AllRemoved(self, discogs_vitals_client, monkeypatch):
        """if the discogs collection is empty the plan should be to remove all albums"""
        mock_collection(monkeypatch, collection=[])
        response = TestDiscogsSyncPlan.get_sync_plan(discogs_vitals_client)
        assert len(response.json['addCollection']) == 0
        assert len(response.json['rmCollection']) >= 1

    def test_DiscogsSyncPlan_CatalogLevelValidation_EmptyPlan(self, discogs_vitals_client, monkeypatch, mock_discogs):
        """if the discogs collection is comprised of mostly bad data except for the catalog numbers, the plan should be
        empty"""
        catalogs = [
            '06・5P-74',
            'CAD 3420',
            '19075965221',
            'TPLP101',
            'OL 5670',
            'SP-70040',
            'TestCategoryNotaReal 001',
        ]
        collection = []

        for id, catalog in enumerate(catalogs):
            collection.append(dict(
                id=id,
                basic_information=dict(
                    id=id,
                    labels=[dict(
                        id=1,
                        catno=catalog,
                    )],
                ),
            ))
        mock_collection(monkeypatch, mock_discogs, collection)
        response = TestDiscogsSyncPlan.get_sync_plan(discogs_vitals_client)
        assert len(response.json['addCollection']) == 0
        assert len(response.json['rmCollection']) == 0
        assert len(response.json['errorMessages']) != 0

    def test_DiscogsSyncPlan_CatalogLevelValidation_CannotSync(
            self, discogs_vitals_client_emptyuser, monkeypatch, mock_discogs):
        """if a collection item has no data it should not appear in the sync plan."""
        catalog = 'this catalog is not in the collection'
        collection = [
            dict(
                id=0,
                basic_information=dict(
                    id=0,
                    labels=[dict(
                        id=1,
                        catno=catalog,
                    )],
                ),
            ),
        ]
        mock_collection(monkeypatch, mock_discogs, collection)
        response = TestDiscogsSyncPlan.get_sync_plan(discogs_vitals_client_emptyuser)
        assert len(response.json['addCollection']) == 0
        assert len(response.json['rmCollection']) == 0
        assert len(response.json['errorMessages']) == 1
        assert catalog in response.json['errorMessages'][0]

    def test_DiscogsSyncPlan_ValidCollection_CanSync(
            self, discogs_vitals_client_emptyuser, monkeypatch, mock_discogs):
        """if a collection has a valid entry it should appear in the sync plan without error."""
        catalog, item_data = get_collection_item_data()
        collection = [item_data]
        mock_collection(monkeypatch, mock_discogs, collection)
        response = TestDiscogsSyncPlan.get_sync_plan(discogs_vitals_client_emptyuser)
        assert len(response.json['addCollection']) == 1
        assert len(response.json['rmCollection']) == 0
        assert len(response.json['errorMessages']) == 0

        # validate schema
        album = response.json['addCollection'][0]
        assert 'catalog' in album
        assert 'artist' in album
        assert 'title' in album
        assert album['catalog'] == catalog
        assert album['artist']
        assert album['title']
