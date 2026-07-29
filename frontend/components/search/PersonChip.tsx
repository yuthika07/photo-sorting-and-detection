"use client";

import { motion } from "framer-motion";
import { X } from "lucide-react";

interface PersonChipProps {
  label: string;
  onRemove: () => void;
}

export function PersonChip({ label, onRemove }: PersonChipProps) {
  return (
    <motion.span
      layout
      initial={{ opacity: 0, scale: 0.85 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.85 }}
      transition={{ duration: 0.15 }}
      className="inline-flex items-center gap-1.5 rounded-full border border-gold-600/50 bg-gradient-to-b from-gold-400 to-gold-500 py-1 pl-3 pr-1.5 text-[12.5px] font-medium text-graphite-950 shadow-[0_1px_0_rgba(255,255,255,0.35)_inset,0_1px_2px_rgba(0,0,0,0.2)]"
    >
      {label}
      <button
        type="button"
        onClick={onRemove}
        aria-label={`Remove ${label} from search`}
        className="rounded-full p-0.5 text-graphite-950/70 transition-colors hover:bg-black/10 hover:text-graphite-950"
      >
        <X size={12} strokeWidth={2.5} />
      </button>
    </motion.span>
  );
}
