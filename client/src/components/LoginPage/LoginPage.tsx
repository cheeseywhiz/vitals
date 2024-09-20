import React, { useState } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useUserIdentityQuery } from '../../api';
import { LoginForm, SignUpForm } from './Forms';

export default function LoginPage() {
    const [ isLoginForm, setIsLoginForm ] = useState(true);
    const location = useLocation();
    const { data: identity } = useUserIdentityQuery();

    // if logged in, redirect to the referrer provided in the url
    if (identity !== undefined && identity.username !== null) {
        const params = new URLSearchParams(location.search);
        const referrer = params.get('referrer');
        return <Navigate to={referrer || "/"} replace={true} />;
    }

    const onSwitchForm = () => setIsLoginForm(!isLoginForm);
    return isLoginForm ? <LoginForm onSwitchForm={onSwitchForm} /> : <SignUpForm onSwitchForm={onSwitchForm} />;
}
