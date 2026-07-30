let refreshTokenMemory: string | null = null;

export const refreshTokenStorage = {
  get(): string | null {
    return refreshTokenMemory;
  },
  set(refreshToken: string): void {
    refreshTokenMemory = refreshToken;
  },
  clear(): void {
    refreshTokenMemory = null;
  },
};
