import { HTMLAttributes, forwardRef } from "react";

type CardVariant = "default" | "panel" | "elevated";

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  variant?: CardVariant;
}

const variantStyles: Record<CardVariant, string> = {
  default: "bg-graphite border border-line",
  panel: "bg-graphite-panel border border-line",
  elevated: "bg-graphite-raised border border-line-strong shadow-lg",
};

export const Card = forwardRef<HTMLDivElement, CardProps>(
  ({ variant = "default", className = "", children, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={`rounded-sm ${variantStyles[variant]} ${className}`}
        {...props}
      >
        {children}
      </div>
    );
  }
);

Card.displayName = "Card";