"use client";

import { motion } from "framer-motion";
import { ImageOff } from "lucide-react";

import type { Photo } from "@/lib/types";

interface PhotoCardProps {
  photo: Photo;
}

function formatDate(iso: string | null): string | null {
  if (!iso) return null;
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return null;
  return date.toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" });
}

function fileName(path: string): string {
  const segments = path.split(/[/\\]/);
  return segments[segments.length - 1] || path;
}

/**
 * Styled as a small printed photograph mounted on a paper card —
 * consistent with PersonCard's "physical print" language. The backend
 * doesn't serve photo thumbnails yet (see backend/README.md), so this
 * renders a textured placeholder rather than pretending an image
 * exists; swapping in `photo.thumbnailUrl` once that endpoint exists
 * is a one-line change here.
 */
export function PhotoCard({ photo }: PhotoCardProps) {
  const dateLabel = formatDate(photo.takenAt);

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ y: -2 }}
      transition={{ duration: 0.16, ease: [0.22, 1, 0.36, 1] }}
      className="paper-surface rounded-lg border border-paper-300 p-1.5 pb-2 shadow-card hover:shadow-card-elevated"
    >
      <div className="flex aspect-[4/3] w-full items-center justify-center overflow-hidden rounded-md border border-black/5 bg-gradient-to-br from-graphite-800 to-graphite-900 text-steel-500">
        {photo.thumbnailUrl ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={photo.thumbnailUrl} alt={fileName(photo.filePath)} className="h-full w-full object-cover" />
        ) : (
          <ImageOff size={22} strokeWidth={1.5} />
        )}
      </div>
      <div className="mt-1.5 px-0.5">
        <p className="truncate text-[12px] font-medium text-ink-900">{fileName(photo.filePath)}</p>
        {dateLabel && <p className="text-[11px] text-ink-500">{dateLabel}</p>}
      </div>
    </motion.div>
  );
}
