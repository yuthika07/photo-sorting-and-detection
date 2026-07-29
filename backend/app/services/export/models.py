"""
Data models for the export service.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class ExportedFile:
    """One photo that was successfully copied."""

    source_path: Path
    destination_path: Path


@dataclass(frozen=True)
class SkippedFile:
    """
    One photo that could NOT be copied, and why.

    Returned explicitly — never silently dropped — same philosophy as
    the scanning module's ScanReport: a user exporting their wedding
    photos needs to know "312 copied, 2 skipped because the file was
    moved," not just receive a folder with fewer photos than expected
    and no explanation.
    """

    source_path: Path
    reason: str


@dataclass
class ExportResult:
    """The full outcome of one export operation."""

    output_folder: Path
    exported_files: list[ExportedFile] = field(default_factory=list)
    skipped_files: list[SkippedFile] = field(default_factory=list)

    @property
    def total_exported(self) -> int:
        return len(self.exported_files)

    @property
    def total_skipped(self) -> int:
        return len(self.skipped_files)
