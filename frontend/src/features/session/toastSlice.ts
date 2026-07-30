import { createSlice, nanoid, type PayloadAction } from "@reduxjs/toolkit";

export type ToastTone = "success" | "error" | "info";

export interface ToastMessage {
  id: string;
  tone: ToastTone;
  message: string;
}

const initialState: ToastMessage[] = [];

export const toastSlice = createSlice({
  name: "toasts",
  initialState,
  reducers: {
    toastAdded: {
      reducer(state, action: PayloadAction<ToastMessage>) {
        state.push(action.payload);
      },
      prepare(message: string, tone: ToastTone = "info") {
        return { payload: { id: nanoid(), message, tone } };
      },
    },
    toastRemoved(state, action: PayloadAction<string>) {
      return state.filter((toast) => toast.id !== action.payload);
    },
  },
});

export const { toastAdded, toastRemoved } = toastSlice.actions;
export const toastReducer = toastSlice.reducer;
