import React from 'react';
import { Link } from 'react-router-dom';

export default function NavBar() {
    return (
        <ul>
            <li><Link to="/">Listening Page</Link></li>
            <li><Link to="/sync">Sync</Link></li>
            <li><Link to="/me">User Profile</Link></li>
        </ul>
    );
}
