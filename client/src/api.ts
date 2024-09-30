import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';
import type { Album, UserIdentity, LoginArgs, CurrentAlbumState, AlbumMatchesState, DiscogsIdentityResponse } from './types';
import { setSelectedAlbum } from './components/ListeningPage/slice';

const RtkBaseQuery = fetchBaseQuery({
    baseUrl: 'api/v1',
    credentials: 'include',
});

const VitalsBaseQuery: ReturnType<typeof fetchBaseQuery> = async (args, queryApi, extraOptions) => {
    const result = await RtkBaseQuery(args, queryApi, extraOptions);

    if (result.error && result.error.status === 401) {
        const identity: UserIdentity = { username: null };
        queryApi.dispatch(api.util.upsertQueryData('userIdentity', undefined, identity));
    }

    return result;
}

export const api = createApi({
    reducerPath: 'vitalsApi',
    baseQuery: VitalsBaseQuery,
    tagTypes: ['UserIdentity', 'CurrentAlbum', 'DiscogsIdentity'],
    endpoints: (builder) => ({
        /* user */
        userIdentity: builder.query<UserIdentity, void>({
            providesTags: ['UserIdentity'],
            queryFn: async (_arg, _queryApi, _extraOptions, baseQuery) => {
                /* Merge the error result into the data result */
                const result = await baseQuery('user/me');

                if (result.error && result.error.status === 401) {
                    const identity: UserIdentity = { username: null };
                    return { data: identity };
                }

                if (result.data) {
                    return { data: result.data as UserIdentity };
                }

                return { error: result.error };
            },
        }),
        login: builder.mutation<UserIdentity, LoginArgs>({
            invalidatesTags: ['CurrentAlbum', 'DiscogsIdentity'],
            query: ({ username, password }) => ({
                url: 'user/login',
                method: 'POST',
                body: { username, password },
            }),
            onQueryStarted: async (_args, { dispatch, queryFulfilled }) => {
                /* set UserIdentity to the username that was logged in */
                try {
                    const result = await queryFulfilled;
                    const identity = result.data as { username: string };
                    dispatch(
                        api.util.updateQueryData('userIdentity', undefined, (draft) => {
                            Object.assign(draft, identity);
                        })
                    );
                } catch {
                    // defer error handling; do not update the identity cache yet
                }
            },
        }),
        logout: builder.mutation<void, void>({
            query: () => ({
                url: 'user/logout',
                method: 'POST',
            }),
            onQueryStarted: async (_args, { dispatch, queryFulfilled }) => {
                /* clear the userIdentity after the log out has been confirmed */
                const patch: UserIdentity = { username: null };

                try {
                    await queryFulfilled;
                    dispatch(
                        api.util.updateQueryData('userIdentity', undefined, (draft) => {
                            Object.assign(draft, patch);
                        })
                    );
                } catch {
                    // defer error handling; do not update the identity cache yet
                }
            },
        }),
        signUp: builder.mutation<void, LoginArgs>({
            query: ({ username, password }) => ({
                url: 'user/sign_up',
                method: 'POST',
                body: { username, password },
            }),
        }),
        currentAlbum: builder.query<CurrentAlbumState, void>({
            providesTags: ['CurrentAlbum'],
            query: () => 'user/album',
        }),
        albumMatch: builder.mutation<AlbumMatchesState, File>({
            query: (queryImage) => {
                const formData = new FormData();
                formData.append('query', queryImage);
                return {
                    url: 'user/album/query',
                    method: 'POST',
                    body: formData,
                };
            },
            onQueryStarted: async (_args, { dispatch, queryFulfilled }) => {
                // select the first album
                let selectedAlbum;

                try {
                    const { data } = await queryFulfilled;
                    selectedAlbum = data.albums[0];
                } catch {
                    selectedAlbum = null;
                }

                dispatch(setSelectedAlbum(selectedAlbum));
            },
        }),
        stopPlay: builder.mutation<void, void>({
            query: () => ({
                url: 'user/album',
                method: 'DELETE',
            }),
            onQueryStarted: async (_args, { dispatch, queryFulfilled }) => {
                // clear the currently playing album optimistically
                const patch: CurrentAlbumState = { album: null };

                const patchResult = dispatch(api.util.updateQueryData('currentAlbum', undefined, (draft) => {
                    Object.assign(draft, patch);
                }));

                try {
                    await queryFulfilled;
                } catch {
                    patchResult.undo();
                }
            },
        }),
        setAlbum: builder.mutation<void, Album>({
            query: (album) => ({
                url: `user/album?catalog=${album.catalog}`,
                method: 'POST',
            }),
            onQueryStarted: async (album, { dispatch, queryFulfilled }) => {
                // set CurrentAlbum optimistically
                const patch: CurrentAlbumState = { album };

                const patchResult = dispatch(api.util.updateQueryData('currentAlbum', undefined, (draft) => {
                    Object.assign(draft, patch);
                }));

                try {
                    await queryFulfilled;
                } catch {
                    patchResult.undo();
                }
            },
        }),
        /* discogs */
        discogsIdentity: builder.query<DiscogsIdentityResponse, void>({
            providesTags: ['DiscogsIdentity'],
            query: () => 'discogs/identity',
        }),
    }),
});

export const {
    /* user */
    useUserIdentityQuery,
    useLoginMutation,
    useLogoutMutation,
    useSignUpMutation,
    useCurrentAlbumQuery,
    useStopPlayMutation,
    useAlbumMatchMutation,
    useSetAlbumMutation,
    /* discogs */
    useDiscogsIdentityQuery,
} = api;
