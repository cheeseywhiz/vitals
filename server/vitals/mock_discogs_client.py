class MockDiscogsClient:
    def __init__(self, username=None):
        self._base_url = ''
        # self._fetcher = MockFetcher()
        self._identity = MockIdentity(username)

    def identity(self):
        return self._identity

    def _get(self, *args, **kwargs):
        raise NotImplementedError('you need to provide mock data for this request')


class MockFetcher:
    def fetch(self, *args, **kwargs):
        pass
        breakpoint()


class MockIdentity:
    def __init__(self, username=None):
        self.username = username
