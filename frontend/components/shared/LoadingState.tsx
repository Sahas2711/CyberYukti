interface LoadingStateProps {
  message?: string;
  className?: string;
}

export function LoadingState({
  message = "Loading...",
  className = "",
}: LoadingStateProps) {
  return (
    <div
      className={`flex items-center gap-3 py-10 ${className}`}
      role="status"
      aria-live="polite"
    >
      <span className="h-4 w-4 shrink-0 animate-spin rounded-full border-[1.5px] border-line-strong border-t-accent" />
      <p className="text-xs font-medium uppercase tracking-wide text-tx-secondary">
        {message}
      </p>
    </div>
  );
}