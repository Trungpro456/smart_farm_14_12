import type { AuthState, LoginReq } from "@/types/Auth.type";
import { createSlice, type PayloadAction } from "@reduxjs/toolkit";

const initState: AuthState = {
    isLogin: false,
    userId: "",
    token: "",
    refreshToken: "",
    role: "",
}
const authStore = createSlice({
    name: "auth",
    initialState: initState,
    reducers: {
        setLogin: (state, action: PayloadAction<LoginReq>) => {
            const { email, password } = action.payload;
            console.log(email, password);
            state.isLogin = true;
            
        },
        setLogout: (state) => {
            state.isLogin = false
            state.userId = ""
            state.token = ""
            state.refreshToken = ""
            state.role = ""
        }
    }
})

export const {setLogin, setLogout } = authStore.actions
export default authStore.reducer