import React from 'react';
import { Navigate, Routes, Route, useLocation } from 'react-router-dom';
import { useUserIdentityQuery } from '../api';
import NavBar from './NavBar';
import ListeningPage from './ListeningPage/ListeningPage';
import LoginPage from './LoginPage/LoginPage';
import UserPage from './UserPage';
import SyncPage from './SyncPage/SyncPage';
import Color from './Color';

function RequireAuth({ children }: React.PropsWithChildren<unknown>) {
    // optimistically render children unless the identity comes back as not logged in
    const { data: identity, error: identityError, isFetching: isIdentityFetching, isError: isIdentityError } = useUserIdentityQuery();
    const location = useLocation();

    if (isIdentityError) {
        const error: string | undefined = 'error' in identityError ? identityError.error as string : undefined;
        const data: string | undefined = 'data' in identityError ? identityError.data as string : undefined;
        return <>
            <p>Error: could not connect to vitals API: {error}</p>
            <pre style={{ whiteSpace: "pre-wrap" }}>{JSON.stringify(identityError, null, 2)}</pre>
            <pre style={{ whiteSpace: "pre-wrap" }}>{data}</pre>
        </>;
    }

    if (!isIdentityFetching && identity === undefined) {
        return <p>identity is undefined despite being loaded with no errors</p>;
    }

    if (identity !== undefined && identity.username === null) {
        // craft the current url and redirect to the login page
        const url = `${location.pathname}${location.search}${location.hash}`;
        let loginRedirectUrl = '/login';

        if (url !== '/') {
            const params = new URLSearchParams();
            params.set('referrer', url);
            loginRedirectUrl += `?${params}`;
        }

        return <Navigate to={loginRedirectUrl} replace={true} />;
    }

    // we are logged in: show authenticated content
    return children;
}

export default function App() {
    return <>
        <Routes>
            <Route path="/" element={<RequireAuth><ListeningPage /></RequireAuth>} />
            <Route path="login" element={<LoginPage />} />
            <Route path="me" element={<RequireAuth><UserPage /></RequireAuth>} />
            <Route path="sync" element={<RequireAuth><SyncPage /></RequireAuth>} />
            <Route path="color" element={<Color />} />
        </Routes>
        <NavBar />
    </>;
};
