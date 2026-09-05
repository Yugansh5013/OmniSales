import * as React from "react";
import { cn } from "@/lib/utils";

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?:
    | "default"
    | "destructive"
    | "outline"
    | "secondary"
    | "ghost"
    | "link"
    | "success";
  size?: "default" | "sm" | "lg" | "icon";
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "default", size = "default", ...props }, ref) => {
    const variantStyles = {
      default:
        "bg-primary text-primary-foreground hover:bg-primary/90 bg-blue-600 hover:bg-blue-500 text-white shadow-sm",
      destructive:
        "bg-[#d03b3b]/85 text-white hover:bg-[#d03b3b] border border-[rgba(208,59,59,0.5)] shadow-sm",
      outline:
        "border border-zinc-800 bg-transparent hover:bg-zinc-800/60 text-zinc-100",
      secondary:
        "bg-zinc-800 text-zinc-100 hover:bg-zinc-700 border border-zinc-700/50 shadow-sm",
      ghost: "hover:bg-zinc-800 text-zinc-300 hover:text-white",
      link: "text-blue-400 underline-offset-4 hover:underline p-0 h-auto",
      success:
        "bg-[#0ca30c]/85 hover:bg-[#0ca30c] text-white shadow-sm border border-[rgba(12,163,12,0.5)]",
    };

    const sizeStyles = {
      default: "h-9 px-4 py-2 text-sm",
      sm: "h-8 rounded-md px-3 text-xs",
      lg: "h-11 rounded-md px-8 text-base",
      icon: "h-9 w-9 p-0 flex items-center justify-center",
    };

    return (
      <button
        className={cn(
          "inline-flex items-center justify-center rounded-md font-medium transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-zinc-400 disabled:pointer-events-none disabled:opacity-50",
          variantStyles[variant],
          sizeStyles[size],
          className
        )}
        ref={ref}
        {...props}
      />
    );
  }
);
Button.displayName = "Button";

export { Button };
