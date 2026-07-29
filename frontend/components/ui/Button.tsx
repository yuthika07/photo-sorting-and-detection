"use client";

import { forwardRef } from "react";
import type { ButtonHTMLAttributes, ReactNode } from "react";

type ButtonVariant = "brass" | "chrome" | "subtle" | "danger-subtle";
type ButtonSize = "sm" | "md";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  icon?: ReactNode;
  children?: ReactNode;
}

/**
 * The app's one button primitive. Every variant is built from real
 * layered shadows (a light top edge + a darker drop shadow) rather
 * than a flat fill, so each one reads as a small physical key rather
 * than a website button — the brief's "tactile, not flat" requirement
 * applied at the smallest possible unit.
 */
export const Button = forwardRef<HTMLButtonElement, ButtonProps>(function Button(
  { variant = "chrome", size = "md", icon, children, className = "", disabled, ...rest },
  ref
) {
  const sizeClasses = size === "sm" ? "h-8 px-3 text-[13px] gap-1.5" : "h-9 px-4 text-sm gap-2";

  const variantClasses: Record<ButtonVariant, string> = {
    brass:
      "bg-gradient-to-b from-gold-400 to-gold-600 text-graphite-950 border border-gold-600/60 " +
      "shadow-[0_1px_0_rgba(255,255,255,0.35)_inset,0_1px_2px_rgba(0,0,0,0.15),0_3px_6px_-2px_rgba(169,132,28,0.5)] " +
      "hover:brightness-105 active:brightness-95 active:translate-y-px",
    chrome:
      "bg-gradient-to-b from-graphite-700 to-graphite-800 text-steel-300 border border-black/40 " +
      "shadow-[0_1px_0_rgba(255,255,255,0.08)_inset,0_1px_2px_rgba(0,0,0,0.4)] " +
      "hover:brightness-110 active:brightness-95 active:translate-y-px",
    subtle:
      "bg-paper-50 text-ink-700 border border-paper-300 shadow-card " +
      "hover:bg-white hover:text-ink-900 active:translate-y-px",
    "danger-subtle":
      "bg-paper-50 text-red-800/80 border border-paper-300 shadow-card " +
      "hover:bg-red-50 hover:text-red-900 active:translate-y-px",
  };

  return (
    <button
      ref={ref}
      disabled={disabled}
      className={[
        "inline-flex items-center justify-center rounded-md font-medium transition-all duration-150",
        "disabled:opacity-40 disabled:pointer-events-none disabled:translate-y-0",
        sizeClasses,
        variantClasses[variant],
        className,
      ].join(" ")}
      {...rest}
    >
      {icon}
      {children}
    </button>
  );
});
