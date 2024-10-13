export type VitalsHttpError = ArbitraryHttpErrorProperties & {
    status: number;  // HTTP status code
    message?: string;
};

type ArbitraryHttpErrorProperties = {
    [rest: string]: string;
};

export type UserIdentity = {
    username: string | null;
};

export type LoginArgs = {
    username: string;
    password: string;
};

export type Album = {
    catalog: string;
    title: string;
    artist: string;
    album_cover_url: string;
};

export type CurrentAlbumState = {
    album: Album | null;
};

export type AlbumMatchesState = {
    albums: Album[];
};

export type DiscogsIdentityResponse = {
    loginUrl: string;
    discogsIdentity: DiscogsIdentity;
};

export type DiscogsIdentity = null | {
    username: string;
};

export type DiscogsSyncPlan = {
    addCollection: Album[];
    rmCollection: Album[];
    errorMessages: string[];
};
