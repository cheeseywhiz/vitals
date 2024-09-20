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
