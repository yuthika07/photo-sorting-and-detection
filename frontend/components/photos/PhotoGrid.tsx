"use client";

import { AnimatePresence, motion } from "framer-motion";
import { AlertCircle, CheckCircle2, ImageIcon, Loader2 } from "lucide-react";

import { PhotoCard } from "@/components/photos/PhotoCard";
import { Button } from "@/components/ui/Button";
import { useAppStore } from "@/lib/store/useAppStore";

export function PhotoGrid() {
  const photos = useAppStore((state) => state.photos);
  const searchStatus = useAppStore((state) => state.searchStatus);
  const searchError = useAppStore((state) => state.searchError);
  const selectedPersonIds = useAppStore((state) => state.selectedPersonIds);
  const exportStatus = useAppStore((state) => state.exportStatus);
  const exportError = useAppStore((state) => state.exportError);
  const lastExportResult = useAppStore((state) => state.lastExportResult);
  const exportSelected = useAppStore((state) => state.exportSelected);
  const dismissExportResult = useAppStore((state) => state.dismissExportResult);

  async function handleExportSelection() {
    const destination = window.prompt(
      "Export the matching photos to which folder?",
      "/Users/me/Desktop/wedding_export"
    );
    if (!destination) return;
    await exportSelected(destination);
  }

  return (
    <section className="flex-1 overflow-y-auto px-6 py-5">
      <div className="mb-4 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <ImageIcon size={15} className="text-ink-500" />
          <h2 className="text-[13px] font-semibold uppercase tracking-[0.1em] text-ink-500">
            {selectedPersonIds.length === 0 ? "All results" : `${photos.length} matching photo${photos.length === 1 ? "" : "s"}`}
          </h2>
        </div>

        {selectedPersonIds.length > 0 && photos.length > 0 && (
          <Button
            variant="brass"
            size="sm"
            onClick={() => void handleExportSelection()}
            disabled={exportStatus === "loading"}
          >
            {exportStatus === "loading" ? "Exporting…" : "Export selection"}
          </Button>
        )}
      </div>

      <AnimatePresence>
        {(exportStatus === "success" || exportStatus === "error") && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="mb-4 overflow-hidden"
          >
            <div
              className={[
                "flex items-start gap-2.5 rounded-lg border p-3 text-[13px]",
                exportStatus === "success"
                  ? "border-green-700/20 bg-green-50 text-green-900"
                  : "border-red-700/20 bg-red-50 text-red-900",
              ].join(" ")}
            >
              {exportStatus === "success" ? (
                <CheckCircle2 size={16} className="mt-0.5 shrink-0" />
              ) : (
                <AlertCircle size={16} className="mt-0.5 shrink-0" />
              )}
              <div className="flex-1">
                {exportStatus === "success" && lastExportResult ? (
                  <>
                    <p className="font-medium">
                      Exported {lastExportResult.totalExported} photo
                      {lastExportResult.totalExported === 1 ? "" : "s"} to {lastExportResult.outputFolder}
                    </p>
                    {lastExportResult.totalSkipped > 0 && (
                      <p className="mt-0.5 text-green-800/80">
                        {lastExportResult.totalSkipped} file{lastExportResult.totalSkipped === 1 ? "" : "s"} skipped
                        (source no longer on disk).
                      </p>
                    )}
                  </>
                ) : (
                  <p className="font-medium">{exportError ?? "Export failed."}</p>
                )}
              </div>
              <button
                onClick={dismissExportResult}
                className="shrink-0 text-current/60 hover:text-current"
                aria-label="Dismiss"
              >
                ×
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {selectedPersonIds.length === 0 && (
        <div className="flex flex-col items-center justify-center gap-2 py-24 text-center text-ink-500">
          <ImageIcon size={28} strokeWidth={1.25} className="mb-1 text-ink-500/50" />
          <p className="text-sm">Select one or more people above to see their photos.</p>
        </div>
      )}

      {selectedPersonIds.length > 0 && searchStatus === "loading" && (
        <div className="flex items-center justify-center gap-2 py-24 text-ink-500">
          <Loader2 size={18} className="animate-spin" />
          Searching…
        </div>
      )}

      {searchStatus === "error" && (
        <div className="flex items-center justify-center gap-2 py-24 text-red-800/80">
          <AlertCircle size={18} />
          {searchError ?? "Search failed."}
        </div>
      )}

      {selectedPersonIds.length > 0 && searchStatus === "ready" && photos.length === 0 && (
        <div className="flex flex-col items-center justify-center gap-2 py-24 text-center text-ink-500">
          <ImageIcon size={28} strokeWidth={1.25} className="mb-1 text-ink-500/50" />
          <p className="text-sm">No photos contain everyone selected. Try removing a person.</p>
        </div>
      )}

      {searchStatus === "ready" && photos.length > 0 && (
        <motion.div
          layout
          className="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6"
        >
          {photos.map((photo) => (
            <PhotoCard key={photo.id} photo={photo} />
          ))}
        </motion.div>
      )}
    </section>
  );
}
