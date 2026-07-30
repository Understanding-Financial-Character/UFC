import {
  createApi,
  fetchBaseQuery,
  type BaseQueryFn,
  type FetchArgs,
  type FetchBaseQueryError,
} from "@reduxjs/toolkit/query/react";

import type { RootState } from "../app/store";
import { sessionCleared, tokenReceived, userReceived } from "../features/auth/authSlice";
import { refreshTokenStorage } from "../features/auth/tokenStorage";
import type {
  LoginRequest,
  LogoutRequest,
  LogoutResponse,
  MeResponse,
  RefreshRequest,
  SignupRequest,
  TokenResponse,
} from "../features/auth/types";

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";
const apiPrefix = "/api/v1";

const rawBaseQuery = fetchBaseQuery({
  baseUrl: `${apiBaseUrl}${apiPrefix}`,
  prepareHeaders: (headers, { getState }) => {
    const token = (getState() as RootState).auth.accessToken;
    if (token) {
      headers.set("authorization", `Bearer ${token}`);
    }
    return headers;
  },
});

let refreshPromise: Promise<TokenResponse | null> | null = null;

const refreshAccessToken = async (
  api: Parameters<BaseQueryFn<string | FetchArgs, unknown, FetchBaseQueryError>>[1],
  extraOptions: Parameters<BaseQueryFn<string | FetchArgs, unknown, FetchBaseQueryError>>[2],
): Promise<TokenResponse | null> => {
  if (!refreshPromise) {
    const refreshToken = refreshTokenStorage.get();
    if (!refreshToken) {
      return null;
    }
    refreshPromise = (async () => {
      const result = await rawBaseQuery(
        {
          url: "/auth/refresh",
          method: "POST",
          body: { refresh_token: refreshToken } satisfies RefreshRequest,
        },
        api,
        extraOptions,
      );
      if (result.error || !result.data) {
        return null;
      }
      return result.data as TokenResponse;
    })();
  }

  try {
    return await refreshPromise;
  } finally {
    refreshPromise = null;
  }
};

const baseQueryWithRefresh: BaseQueryFn<string | FetchArgs, unknown, FetchBaseQueryError> = async (
  args,
  api,
  extraOptions,
) => {
  let result = await rawBaseQuery(args, api, extraOptions);

  if (result.error?.status === 401) {
    const refreshed = await refreshAccessToken(api, extraOptions);
    if (refreshed) {
      refreshTokenStorage.set(refreshed.refresh_token);
      api.dispatch(tokenReceived(refreshed));
      result = await rawBaseQuery(args, api, extraOptions);
    } else {
      refreshTokenStorage.clear();
      api.dispatch(sessionCleared());
    }
  }

  return result;
};

export const baseApi = createApi({
  reducerPath: "baseApi",
  baseQuery: baseQueryWithRefresh,
  tagTypes: ["Session"],
  endpoints: (builder) => ({
    signup: builder.mutation<TokenResponse, SignupRequest>({
      query: (body) => ({ url: "/auth/signup", method: "POST", body }),
      async onQueryStarted(_arg, { dispatch, queryFulfilled }) {
        const { data } = await queryFulfilled;
        refreshTokenStorage.set(data.refresh_token);
        dispatch(tokenReceived(data));
      },
      invalidatesTags: ["Session"],
    }),
    login: builder.mutation<TokenResponse, LoginRequest>({
      query: (body) => ({ url: "/auth/login", method: "POST", body }),
      async onQueryStarted(_arg, { dispatch, queryFulfilled }) {
        const { data } = await queryFulfilled;
        refreshTokenStorage.set(data.refresh_token);
        dispatch(tokenReceived(data));
      },
      invalidatesTags: ["Session"],
    }),
    logout: builder.mutation<LogoutResponse, void>({
      query: () => {
        const refreshToken = refreshTokenStorage.get() ?? "";
        return {
          url: "/auth/logout",
          method: "POST",
          body: { refresh_token: refreshToken } satisfies LogoutRequest,
        };
      },
      async onQueryStarted(_arg, { dispatch, queryFulfilled }) {
        try {
          await queryFulfilled;
        } finally {
          refreshTokenStorage.clear();
          dispatch(sessionCleared());
          dispatch(baseApi.util.resetApiState());
        }
      },
    }),
    getMe: builder.query<MeResponse, void>({
      query: () => "/me",
      async onQueryStarted(_arg, { dispatch, queryFulfilled }) {
        const { data } = await queryFulfilled;
        dispatch(userReceived(data));
      },
      providesTags: ["Session"],
    }),
  }),
});

export const {
  useGetMeQuery,
  useLazyGetMeQuery,
  useLoginMutation,
  useLogoutMutation,
  useSignupMutation,
} = baseApi;
