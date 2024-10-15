import React, { Fragment } from 'react';
import { useAppSelector, useAppDispatch } from '../../hooks';
import type { Album } from '../../types';
import { useSetAlbumMutation, useCurrentAlbumQuery } from '../../api';
import {
    setSelectedAlbum, selectSelectedAlbum, selectSelectedSide, setSelectedSide, cacheKeys, SideToString,
} from './slice';
import Dialog from '../Dialog';

export default function SideSelector() {
    const { data: currentAlbum, isFetching: isCurrentAlbumFetching } = useCurrentAlbumQuery();
    const [ triggerSetAlbum, ] = useSetAlbumMutation({ fixedCacheKey: cacheKeys.setAlbum });
    const selectedAlbum = useAppSelector(selectSelectedAlbum);
    const selectedSide = useAppSelector(selectSelectedSide);
    const dispatch = useAppDispatch();

    const isNotPlaying = currentAlbum !== undefined && currentAlbum.album === null;

    let album: Album = null;

    if (selectedAlbum !== null) {
        // selecting
        album = selectedAlbum;
    } else if (isCurrentAlbumFetching) {
        return <></>;
    } else if (isNotPlaying) {
        return <></>;
    } else {
        // currently playing
        album = currentAlbum.album;
    }

    // Dialog
    let dialog = <></>;

    if (selectedSide !== null) {
        dialog = <>
            <Dialog
                prompt={`Play ${SideToString(selectedSide)}?`}
                onYes={() => {
                    triggerSetAlbum({ album, side: selectedSide });
                    dispatch(setSelectedSide(null));
                }}
                onNo={() => {
                    dispatch(setSelectedAlbum(null));
                    dispatch(setSelectedSide(null));
                }}
            />
        </>;
    }

    return <>
        <ol>
            {Array(2 * album.num_discs).fill(0).map((_, sideNum) => <Fragment key={sideNum}>
                <li>
                    <div onClick={() => dispatch(setSelectedSide(sideNum))}>
                        {SideToString(sideNum)}
                    </div>
                    <ul>
                        {sideNum !== selectedSide ? <></> : <>
                            <li>Selected</li>
                        </>}
                        {!(currentAlbum !== undefined && sideNum === currentAlbum.side) ? <></> : <>
                            <li>Currently Playing</li>
                        </>}
                    </ul>
                </li>
            </Fragment>)}
        </ol>
        {dialog}
    </>;
}
