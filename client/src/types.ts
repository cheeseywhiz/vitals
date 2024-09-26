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
};

export type CurrentAlbumState = {
    album: Album | null;
};

export type AlbumMatchesState = {
    albums: Album[];
};
