"""
Centralized configuration management.

All environment-dependent values (ports, paths, log level, feature flags)
are declared ONCE here as a typed Settings object. No other module in the
codebase should call os.environ / os.getenv directly — everything reads
configuration through this module instead, so there is a single source of
truth and every value is validated at startup instead of failing later
deep inside some unrelated function.
"""

# Standard library import used to build absolute, OS-independent paths
from pathlib import Path

# functools.lru_cache lets us build the Settings object once and reuse it
# (Settings objects are cheap, but re-parsing the .env file on every
# request would be wasteful and could mask bugs if the file changes mid-run)
from functools import lru_cache

# pydantic-settings gives us a Settings base class that automatically reads
# values from environment variables (and a .env file) and validates types
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Typed application settings.

    Each attribute below corresponds to one environment variable (matched
    by name, case-insensitive). Pydantic validates types automatically —
    if PORT is not a valid integer, the app fails fast at startup with a
    clear error instead of crashing later when the server tries to bind.
    """

    # --- General application identity -----------------------------------
    app_name: str = "Wedding Photo Organizer"       # shown in logs / docs
    app_version: str = "0.1.0"                      # surfaced on /health
    app_env: str = "development"                    # development | production | test

    # --- API behavior -----------------------------------------------------
    enable_docs: bool = True                         # toggles /docs and /redoc

    # --- Server binding ----------------------------------------------------
    host: str = "127.0.0.1"                          # local-only by default (offline app)
    port: int = 8000                                 # port the desktop shell connects to

    # --- Logging -------------------------------------------------------------
    log_level: str = "INFO"                          # DEBUG/INFO/WARNING/ERROR/CRITICAL
    log_dir: str = "../data/logs"                     # where rotating log files are written

    # --- Data storage (used starting Phase 2, declared now for stability) --
    data_dir: str = "../data"                         # base dir for SQLite DB, thumbnails, etc.

    # --- CORS ------------------------------------------------------------------
    # Comma-separated string in the .env file, e.g. "http://localhost:3000,tauri://localhost"
    cors_origins: str = "http://localhost:3000,tauri://localhost"

    # --- Face detection (Phase 4) -------------------------------------------
    # Path (relative to backend/) to the bundled SCRFD .onnx weight file.
    # Bundled locally rather than downloaded at runtime, per this project's
    # offline-first requirement.
    face_detection_model_path: str = "models/scrfd/det_500m.onnx"

    # Minimum confidence score (0.0-1.0) for a detection to be kept.
    # See SCRFDFaceDetector for why 0.5 is a reasonable default.
    face_detection_confidence_threshold: float = 0.5

    # --- Face recognition (Phase 5) -----------------------------------------
    # Path (relative to backend/) to the bundled ArcFace .onnx weight file.
    # Same offline-first bundling approach as face detection above.
    face_recognition_model_path: str = "models/arcface/w600k_mbf.onnx"

    # --- Face clustering (Phase 6) -------------------------------------------
    # Maximum cosine DISTANCE (1 - cosine_similarity) between two embeddings
    # for them to be considered neighbors. See DBSCANFaceClusterer for the
    # reasoning behind this default.
    clustering_eps: float = 0.4

    # Minimum number of neighboring faces (including itself) required to
    # form a cluster. See DBSCANFaceClusterer for the reasoning.
    clustering_min_samples: int = 2

    # Tells pydantic-settings HOW to load these values: from a .env file,
    # using UTF-8 encoding, and ignoring unrelated/unknown env vars instead
    # of raising an error (so the process's full environment can stay large).
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_origins_list(self) -> list[str]:
        """
        Split the comma-separated CORS_ORIGINS string into a clean list.

        Kept as a computed property (not stored directly) so the raw env
        var stays a simple string in .env, while consumers (main.py) get
        a ready-to-use Python list.
        """
        # Split on commas, strip whitespace, drop any empty entries
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def resolved_log_dir(self) -> Path:
        """
        Return LOG_DIR as an absolute Path, resolved relative to this
        file's location rather than the current working directory.

        This matters because uvicorn can be launched from different
        working directories (project root, backend/, a packaged binary's
        install dir) — resolving relative to __file__ keeps behavior
        consistent regardless of how the process was started.
        """
        # Path(__file__).parent -> app/core/, so go up two levels to backend/
        backend_root = Path(__file__).resolve().parent.parent.parent
        return (backend_root / self.log_dir).resolve()

    @property
    def resolved_data_dir(self) -> Path:
        """Return DATA_DIR as an absolute Path, same rationale as above."""
        backend_root = Path(__file__).resolve().parent.parent.parent
        return (backend_root / self.data_dir).resolve()

    @property
    def database_url(self) -> str:
        """
        Build the SQLAlchemy connection URL for the local SQLite file.

        The database file lives inside resolved_data_dir (e.g.
        <project>/data/app.db) so it sits next to logs and thumbnails —
        one predictable place for all of the app's on-disk state, which
        matters a lot for a desktop app users might back up or relocate.
        """
        db_path = self.resolved_data_dir / "app.db"
        return f"sqlite:///{db_path}"

    @property
    def resolved_face_detection_model_path(self) -> Path:
        """
        Return the SCRFD model file path as an absolute Path, resolved
        relative to this file's location (same rationale as
        resolved_log_dir / resolved_data_dir above) rather than the
        current working directory.
        """
        backend_root = Path(__file__).resolve().parent.parent.parent
        return (backend_root / self.face_detection_model_path).resolve()

    @property
    def resolved_face_recognition_model_path(self) -> Path:
        """Return the ArcFace model file path as an absolute Path. Same rationale as above."""
        backend_root = Path(__file__).resolve().parent.parent.parent
        return (backend_root / self.face_recognition_model_path).resolve()


@lru_cache
def get_settings() -> Settings:
    """
    Return a cached, singleton Settings instance.

    FastAPI's dependency injection will call this function per-request,
    but @lru_cache ensures the .env file is only parsed once per process
    and the same Settings object is reused everywhere.
    """
    return Settings()
