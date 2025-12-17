export interface AuthState {
    isLogin: boolean,
    userId: string,
    token: string,
    refreshToken: string,
    role: string,
    
}
export interface LoginReq {
    email: string;
    password: string;
}
export interface LoginRes {
    userId: string;
    token: string;
    refreshToken: string;
    role: string;
}