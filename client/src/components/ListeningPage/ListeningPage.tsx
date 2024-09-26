import React from 'react';
import { useCurrentAlbumQuery, useAlbumMatchMutation, useStopPlayMutation, useSetAlbumMutation } from '../../api';
import type { Album } from '../../types';
import { useAppSelector } from '../../hooks';
import ErrorView from '../ErrorView';
import AlbumMatch from './AlbumMatch';
import StopButton from './StopButton';
import { selectSelectedAlbum, cacheKeys } from './slice';

type AlbumCoverProps = {
    status: AlbumCoverStatus;
    album: Album | null;
};

type AlbumCoverStatus = "Album" | "NotPlaying" | "Loading";

function AlbumCover({ status, album }: AlbumCoverProps) {
    switch (status) {
        case "Album": return <p>{album.title} by {album.artist}</p>;
        case "NotPlaying": return <p>Not playing</p>;
        case "Loading": return <p>Loading currently playing album...</p>;
    }
}

function ListeningPageErrorView() {
    // the page owns the error view so components don't have to worry about it
    const [ _triggerSetAlbum, { error: setAlbumError } ] = useSetAlbumMutation({ fixedCacheKey: cacheKeys.setAlbum });
    const { error: currentAlbumError } = useCurrentAlbumQuery();
    const [ _triggerStopPlay, { error: stopPlayError } ] = useStopPlayMutation({ fixedCacheKey: cacheKeys.stopPlay });
    const [ _triggerAlbumMatch, { error: albumMatchError } ] = useAlbumMatchMutation({ fixedCacheKey: cacheKeys.albumMatch });

    return <ErrorView
        setAlbum={setAlbumError}
        currentAlbum={currentAlbumError}
        stopPlay={stopPlayError}
        albumMatch={albumMatchError}
    />;
}

export default function ListeningPage() {
    const { data: currentAlbum, isFetching: isCurrentAlbumFetching } = useCurrentAlbumQuery();
    const [ queryAlbumMatch, {
        reset: clearAlbumMatchQuery,
    } ] = useAlbumMatchMutation({ fixedCacheKey: cacheKeys.albumMatch });
    const selectedAlbum = useAppSelector(selectSelectedAlbum);

    const isNotPlaying = currentAlbum !== undefined && currentAlbum.album === null;

    let albumCoverStatus: AlbumCoverStatus = null;
    let albumCover: Album = null;

    if (selectedAlbum !== null) {
        albumCoverStatus = "Album";
        albumCover = selectedAlbum;
    } else if (isCurrentAlbumFetching) {
        albumCoverStatus = "Loading";
    } else if (isNotPlaying) {
        albumCoverStatus = "NotPlaying";
    } else {
        albumCoverStatus = "Album";
        albumCover = currentAlbum.album;
    }

    const onQueryAlbumFileChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
        if (event.target.files.length === 0) {
            clearAlbumMatchQuery();
        } else {
            await queryAlbumMatch(event.target.files[0]);
        }
    };

    return <>
        <AlbumCover status={albumCoverStatus} album={albumCover} />
        <label htmlFor="upload-album-match-query">
            <div style={{ border: "1px solid red", width: "fit-content" }}>
                Record icon
            </div>
            <input
                type="file"
                id="upload-album-match-query"
                style={{ display: "none" }}
                accept="image/png, image/jpeg"
                onChange={onQueryAlbumFileChange}
                capture="environment"
                multiple={false}
            />
        </label>
        <StopButton />
        <ListeningPageErrorView />
        <AlbumMatch />
    </>;
}
