"use client";

import { Aperture } from "lucide-react";

/**
 * Purely decorative window chrome (the three traffic-light dots) —
 * this is one of the strongest, cheapest signals that a webpage
 * "isn't a website," borrowed directly from the brief's macOS
 * professional-app reference point.
 */
export function TitleBar() {
  return (
    <div className="flex items-center gap-3 px-4 pt-3 pb-2">
      <div className="flex gap-1.5 pl-1">
        <span className="h-3 w-3 rounded-full bg-gradient-to-b from-red-400 to-red-600 shadow-[0_1px_0_rgba(255,255,255,0.25)_inset]" />
        <span className="h-3 w-3 rounded-full bg-gradient-to-b from-yellow-300 to-yellow-500 shadow-[0_1px_0_rgba(255,255,255,0.25)_inset]" />
        <span className="h-3 w-3 rounded-full bg-gradient-to-b from-green-400 to-green-600 shadow-[0_1px_0_rgba(255,255,255,0.25)_inset]" />
      </div>

      <div className="mx-auto flex items-center gap-2 text-steel-300">
        <Aperture size={15} strokeWidth={2} className="text-gold-400" />
        <span className="text-[13px] font-semibold tracking-tight">Wedding Photo Organizer</span>
      </div>

      {/* Balances the traffic lights on the left so the title stays visually centered */}
      <div className="w-14" />
    </div>
  );
}
