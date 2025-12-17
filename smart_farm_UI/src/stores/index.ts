import { configureStore } from '@reduxjs/toolkit'
import counterReducer from './counter.store'
import authStore from './store/auth.store'

export const store = configureStore({
    reducer: {
        counter: counterReducer,
        auth: authStore,
    },
})

export type RootState = ReturnType<typeof store.getState>

export type AppDispatch = typeof store.dispatch
