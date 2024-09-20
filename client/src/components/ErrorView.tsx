import React from 'react';
import type { VitalsHttpError } from '../types';

type ErrorViewProps = {
    [queryName: string]: unknown;
};

type RtkQueryError = {
    data?: VitalsHttpError
};

export default function ErrorView(props: ErrorViewProps) {
    const problematicQueries = Object.entries(props).filter(([_queryName, error]: [string, RtkQueryError | undefined]) => {
        return error !== undefined && 'data' in error
    }).map(([queryName, error]: [string, RtkQueryError]) => {
        return [queryName, error.data.message];
    });
    if (problematicQueries.length === 0) return <></>;

    return (
        <ul>
            {problematicQueries.map(([queryName, message]) => {
                return <li key={queryName}>Error in {queryName}: {message}</li>;
            })}
        </ul>
    );
}
