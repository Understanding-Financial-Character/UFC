import { useAppDispatch, useAppSelector } from "../../app/hooks";
import { toastRemoved } from "../../features/session/toastSlice";

export function ToastViewport() {
  const dispatch = useAppDispatch();
  const toasts = useAppSelector((state) => state.toasts);

  if (toasts.length === 0) {
    return null;
  }

  return (
    <div className="toast-viewport" aria-live="polite" aria-label="알림">
      {toasts.map((toast) => (
        <button
          className={`toast toast--${toast.tone}`}
          key={toast.id}
          onClick={() => dispatch(toastRemoved(toast.id))}
          type="button"
        >
          {toast.message}
        </button>
      ))}
    </div>
  );
}
