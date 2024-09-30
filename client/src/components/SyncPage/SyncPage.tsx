import React from 'react';
import { useLocation } from 'react-router-dom';
import { useDiscogsIdentityQuery } from '../../api';

function SyncPageContent() {
    const { data: discogsIdentityResponse } = useDiscogsIdentityQuery();
    if (discogsIdentityResponse === undefined) return <p>Loading discogs</p>;
    const { discogsIdentity } = discogsIdentityResponse;

    return <p>Logged in to discogs as {discogsIdentity.username}</p>
}

function RequireDiscogsAuth({ children }: React.PropsWithChildren<unknown>) {
    const { data: discogsIdentityResponse } = useDiscogsIdentityQuery();
    const location = useLocation();

    if (discogsIdentityResponse !== undefined && discogsIdentityResponse.discogsIdentity === null) {
        const currentUrl = `${location.pathname}${location.search}${location.hash}`;
        const params = new URLSearchParams();
        params.set('vitals_callback', currentUrl);
        const loginUrl = `${discogsIdentityResponse.loginUrl}?${params}`;
        return <a href={loginUrl}>Log in with discogs</a>;
    }

    return children;
}

export default function SyncPage() {
    return <RequireDiscogsAuth>
        <SyncPageContent />
    </RequireDiscogsAuth>;
}
