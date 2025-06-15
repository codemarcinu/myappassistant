"use client";

import { cva, type VariantProps } from 'class-variance-authority';

const cardVariants = cva(
  "rounded-lg border bg-card text-card-foreground shadow-sm",
  {
    variants: {
      variant: {
        default: "",
        destructive: "border-destructive",
        outline: "border",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
);

interface CardProps {
  className?: string;
  variant?: "default" | "destructive" | "outline";
  children?: any;
  [key: string]: any;
}

export function Card({ className, variant, children, ...props }: CardProps) {
  return (
    <div
      className={cardVariants({ variant, className })}
      {...props}
    >
      {children}
    </div>
  );
}

Card.displayName = "Card";

interface CardHeaderProps {
  className?: string;
  children?: any;
  [key: string]: any;
}

export function CardHeader({ className, children, ...props }: CardHeaderProps) {
  return (
    <div
      className={`flex flex-col space-y-1.5 p-6 ${className || ''}`}
      {...props}
    >
      {children}
    </div>
  );
}

CardHeader.displayName = "CardHeader";

interface CardTitleProps {
  className?: string;
  children?: any;
  [key: string]: any;
}

export function CardTitle({ className, children, ...props }: CardTitleProps) {
  return (
    <h3
      className={`text-xl font-semibold leading-none tracking-tight ${className || ''}`}
      {...props}
    >
      {children}
    </h3>
  );
}

CardTitle.displayName = "CardTitle";

interface CardDescriptionProps {
  className?: string;
  children?: any;
  [key: string]: any;
}

export function CardDescription({ className, children, ...props }: CardDescriptionProps) {
  return (
    <p
      className={`text-sm text-gray-500 ${className || ''}`}
      {...props}
    >
      {children}
    </p>
  );
}

CardDescription.displayName = "CardDescription";

interface CardContentProps {
  className?: string;
  children?: any;
  [key: string]: any;
}

export function CardContent({ className, children, ...props }: CardContentProps) {
  return (
    <div className={`p-6 pt-0 ${className || ''}`} {...props}>
      {children}
    </div>
  );
}

CardContent.displayName = "CardContent";

interface CardFooterProps {
  className?: string;
  children?: any;
  [key: string]: any;
}

export function CardFooter({ className, children, ...props }: CardFooterProps) {
  return (
    <div
      className={`flex items-center p-6 pt-0 ${className || ''}`}
      {...props}
    >
      {children}
    </div>
  );
}

CardFooter.displayName = "CardFooter";
