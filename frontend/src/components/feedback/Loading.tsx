interface LoadingProps {
  label?: string;
}

export function Loading({ label = "불러오는 중입니다" }: LoadingProps) {
  return (
    <div className="state-panel" role="status" aria-live="polite">
      <span className="spinner" aria-hidden="true" />
      <p>{label}</p>
    </div>
  );
}
