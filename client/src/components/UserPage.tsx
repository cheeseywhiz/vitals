import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useUserIdentityQuery, useLogoutMutation } from '../api';

export default function UserPage() {
    const { data: identity, isFetching: isIdentityFetching } = useUserIdentityQuery();
    if (isIdentityFetching) return <p>Loading user profile...</p>;
    return <>
        <p>{identity.username} is logged in</p>
        <LogoutButton />
    </>;
}

function LogoutButton() {
    const [ triggerLogout ] = useLogoutMutation();
    const navigate = useNavigate();
    const onClick = () => {
        triggerLogout();
        navigate('/');
    };
    return <button onClick={onClick}>Log Out</button>;
}
