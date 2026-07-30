const REFRESH_TOKEN_KEY = "ufc.refresh_token";

const getStorage = (): Storage | null => {
  if (typeof window === "undefined") {
    return null;
  }
  return window.localStorage;
};

export const refreshTokenStorage = {
  get(): string | null {
    return getStorage()?.getItem(REFRESH_TOKEN_KEY) ?? null;
  },
  set(refreshToken: string): void {
    getStorage()?.setItem(REFRESH_TOKEN_KEY, refreshToken);
  },
  clear(): void {
    getStorage()?.removeItem(REFRESH_TOKEN_KEY);
  },
};
