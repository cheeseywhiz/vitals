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
    selectedSide: number | null;
};

const initialState: ListeningPageState = {
    selectedAlbum: null,
    selectedSide: null,
};

const listeningPageSlice = createSlice({
    name: 'listeningPage',
    initialState,
    reducers: {
        setSelectedAlbum: (state, action: PayloadAction<Album | null>) => {
            state.selectedAlbum = action.payload;
            state.selectedSide = action.payload !== null ? 0 : null;
        },
        setSelectedSide: (state, action: PayloadAction<number | null>) => {
            state.selectedSide = action.payload;
        },
    },
    selectors: {
        selectSelectedAlbum: (state) => state.selectedAlbum,
        selectSelectedSide: (state) => state.selectedSide,
    },
});

export const { setSelectedAlbum, setSelectedSide } = listeningPageSlice.actions;
export const { selectSelectedAlbum, selectSelectedSide } = listeningPageSlice.selectors;
export default listeningPageSlice.reducer;

 export const SideToString = (side: number) => `Side ${String.fromCharCode(0x41 + side)}`;
