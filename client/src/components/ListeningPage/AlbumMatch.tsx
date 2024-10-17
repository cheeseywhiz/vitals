import React, { Fragment } from 'react';
import { useAppSelector, useAppDispatch } from '../../hooks';
import { useAlbumMatchMutation, useSetAlbumMutation } from '../../api';
import Dialog from '../Dialog';
import { selectSelectedAlbum, setSelectedAlbum, cacheKeys } from './slice';

export default function AlbumMatch() {
    const [ _trigger, {
        data: albumMatchResult, isUninitialized: isAlbumMatchUninitialized, isLoading: isAlbumMatchLoading,
        reset: clearAlbumMatchQuery,
    } ] = useAlbumMatchMutation({ fixedCacheKey: cacheKeys.albumMatch });
    const [ triggerSetAlbum, ] = useSetAlbumMutation({ fixedCacheKey: cacheKeys.setAlbum });
    const selectedAlbum = useAppSelector(selectSelectedAlbum);
    const dispatch = useAppDispatch();

    if (isAlbumMatchUninitialized) return <></>;
    if (isAlbumMatchLoading) return <p>Loading album selection...</p>;
    if (albumMatchResult === undefined) return <p>Error in albumMatch: result is undefined</p>;

    const onSelectedAlbumChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        const album = albumMatchResult.albums.find(album => album.catalog == event.target.value);
        dispatch(setSelectedAlbum(album));
    };

    // Dialog
    const prompt = `Play ${selectedAlbum.title}?`;
    const onSelect = () => {
        triggerSetAlbum(selectedAlbum);
        clearAlbumMatchQuery();
    };
    const onCancel = () => clearAlbumMatchQuery();

    return <>
        <div onChange={onSelectedAlbumChange}>
            {albumMatchResult.albums.map(album => <Fragment key={album.catalog}>
                    <input
                        type="radio"
                        name="album-match"
                        id={album.catalog}
                        value={album.catalog}
                        checked={selectedAlbum?.catalog === album.catalog}
                        readOnly
                    />
                    <label htmlFor={album.catalog}>{album.title} by {album.artist}</label>
                    <br />
            </Fragment>)}
        </div>
        <Dialog prompt={prompt} onYes={onSelect} onNo={onCancel} />
    </>;
}
