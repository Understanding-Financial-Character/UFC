import type { FetchBaseQueryError } from "@reduxjs/toolkit/query";
import type { SerializedError } from "@reduxjs/toolkit";

import type { ApiErrorPayload } from "./types";

export const getAuthErrorMessage = (
  error: FetchBaseQueryError | SerializedError | undefined,
): string => {
  if (!error) {
    return "요청을 다시 시도해 주세요.";
  }

  if ("status" in error) {
    const data = error.data as ApiErrorPayload | undefined;
    return data?.error?.message ?? "인증 요청을 처리하지 못했습니다.";
  }

  return error.message ?? "인증 요청을 처리하지 못했습니다.";
};
