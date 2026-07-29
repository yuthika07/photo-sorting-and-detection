"""
Services package -- business logic.

Contents so far:
    photo_search_service.py   -> PhotoSearchService (Phase 7): finds
                                  photos containing one or more people,
                                  validating requested person ids before
                                  running the underlying search query.
    export/                     -> PhotoExportService (Phase 8): copies
                                    photos matching a person search into
                                    a person-named output folder,
                                    built directly on top of
                                    photo_search_service.py.

Routers call into this layer instead of talking to repositories or the
AI modules directly, which keeps routers thin and this logic
independently testable without a running HTTP server.
"""
