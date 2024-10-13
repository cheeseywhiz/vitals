import React from 'react';
import { useDiscogsSyncPlanMutation, useExecuteDiscogsSyncMutation } from '../../api';
import Dialog from '../Dialog';
import type { Album } from '../../types';

export default function SyncPlan() {
    const [ querySyncPlan, {
        data: discogsSyncPlan, reset: resetSyncPlan, isUninitialized: isSyncPlanUninitialized,
        isLoading: isSyncPlanLoading,
    } ] = useDiscogsSyncPlanMutation();
    const [ executeDiscogsSync, {
        data: syncResult, reset: resetExecuteSync, isLoading: isExecuteSyncLoading,
    } ] = useExecuteDiscogsSyncMutation();
    // TODO: add HTTP error and error_message support

    const onPlanSync = () => {
        resetSyncPlan();
        resetExecuteSync();
        querySyncPlan();
    };
    const syncButton = <button onClick={onPlanSync}>Sync with Discogs</button>;
    if (isExecuteSyncLoading) return <p>Syncing...</p>;
    if (syncResult !== undefined) {
        return <>
            {syncButton}
            <p>Sync succeeded</p>
        </>;
    }
    if (isSyncPlanUninitialized) return syncButton;
    if (isSyncPlanLoading) return <p>Loading sync plan</p>;
    if (discogsSyncPlan === undefined) return <p>Error in discogs sync plan</p>;

    // Dialog
    const prompt = "Sync with Discogs?";
    const onSync = () => {
        executeDiscogsSync();
        resetSyncPlan();
    };
    const onCancel = () => resetSyncPlan();

    return <>
        {syncButton}
        <AlbumList title="Remove Albums" albums={discogsSyncPlan.rmCollection} />
        <AlbumList title="Add Albums" albums={discogsSyncPlan.addCollection} />
        <Dialog prompt={prompt} onYes={onSync} onNo={onCancel} />
    </>;
}

type AlbumListProps = {
    title: string,
    albums: Album[];
};

function AlbumList({ title, albums }: AlbumListProps) {
    return <>
        <p>{title}</p>
        <ul>
            {albums.map(album => (
                <li key={album.catalog}>
                    {album.title !== null && album.artist !== null
                        ? <>{album.title} by {album.artist}</>
                        : <>catalog {album.catalog}</>}
                </li>
            ))}
        </ul>
    </>;
}
