import { configureStore } from "@reduxjs/toolkit";

import { baseApi } from "../api/baseApi";
import { authReducer } from "../features/auth/authSlice";
import { toastReducer } from "../features/session/toastSlice";

export const store = configureStore({
  reducer: {
    auth: authReducer,
    toasts: toastReducer,
    [baseApi.reducerPath]: baseApi.reducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware().concat(baseApi.middleware),
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
