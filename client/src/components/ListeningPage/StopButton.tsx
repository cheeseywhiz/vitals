import React, { useState } from 'react';
import { useCurrentAlbumQuery, useStopPlayMutation } from '../../api';
import Dialog from '../Dialog';
import { cacheKeys } from './slice';

export default function StopButton() {
    const { data: currentAlbum, isFetching: isCurrentAlbumFetching } = useCurrentAlbumQuery();
    const [ triggerStopPlay ] = useStopPlayMutation({ fixedCacheKey: cacheKeys.stopPlay });
    const [ showStopPrompt, setShowStopPrompt ] = useState(false);
    const onShowStopPrompt = () => setShowStopPrompt(true);
    const stopPrompt = "Stop play?";
    const onStopPlay = () => {
        triggerStopPlay();
        setShowStopPrompt(false);
    };
    const onCancelStopPlay = () => setShowStopPrompt(false);
    const isNotPlaying = currentAlbum !== undefined && currentAlbum.album === null;
    return <>
        <button onClick={onShowStopPrompt} disabled={!isCurrentAlbumFetching && isNotPlaying}>Stop</button>
        {showStopPrompt ? <Dialog prompt={stopPrompt} onYes={onStopPlay} onNo={onCancelStopPlay} /> : <></>}
    </>;
}
