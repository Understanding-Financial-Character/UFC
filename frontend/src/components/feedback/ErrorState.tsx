interface ErrorStateProps {
  title?: string;
  message: string;
}

export function ErrorState({ title = "요청을 처리하지 못했습니다", message }: ErrorStateProps) {
  return (
    <div className="state-panel state-panel--error" role="alert">
      <h2>{title}</h2>
      <p>{message}</p>
    </div>
  );
}
