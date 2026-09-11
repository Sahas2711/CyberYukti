interface TooltipProps {
  content: string;
  children: React.ReactNode;
  className?: string;
}

export function Tooltip({ content, children, className = "" }: TooltipProps) {
  return (
    <span className={`relative inline-block cursor-help ${className}`} title={content}>
      {children}
    </span>
  );
}