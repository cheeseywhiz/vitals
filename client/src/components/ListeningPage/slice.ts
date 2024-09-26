import { createSlice } from '@reduxjs/toolkit';
import type { PayloadAction } from '@reduxjs/toolkit';
import type { Album } from '../../types';

export const cacheKeys = {
    albumMatch: 'albumMatch',
    setAlbum: 'setAlbum',
    stopPlay: 'stopPlay',
};

type ListeningPageState = {
    // the selected album during the album match process
    selectedAlbum: Album | null;
};

const initialState: ListeningPageState = {
    selectedAlbum: null,
};

const listeningPageSlice = createSlice({
    name: 'listeningPage',
    initialState,
    reducers: {
        setSelectedAlbum: (state, action: PayloadAction<Album | null>) => {
            state.selectedAlbum = action.payload;
        },
    },
    extraReducers: (builder) => {
        builder
            .addMatcher(({ type, payload }) => {
                return type.endsWith('removeMutationResult')
                    && 'fixedCacheKey' in payload && payload.fixedCacheKey === cacheKeys.albumMatch;
            }, (state) => {
                state.selectedAlbum = null;
            });
    },
    selectors: {
        selectSelectedAlbum: (state) => state.selectedAlbum,
    },
});

export const { setSelectedAlbum } = listeningPageSlice.actions;
export const { selectSelectedAlbum } = listeningPageSlice.selectors;
export default listeningPageSlice.reducer;
