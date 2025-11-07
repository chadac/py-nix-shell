"""Caching functionality for Nix builds and shells."""

import json
import time
from pathlib import Path
from typing import TypedDict

from nix_shell.build import NixBuild
from nix_shell.constants import CACHE_ROOT, LOCAL_CACHE_ROOT


class CacheHistoryEntry(TypedDict):
    """Entry in the cache history file."""

    build_id: str
    timestamp: float
    json_path: str
    profile_path: str


class CacheHistoryData(TypedDict):
    """Structure of the cache history JSON file."""

    entries: list[CacheHistoryEntry]
    aliases: dict[str, str]  # cache_key -> build_id mapping


class CacheHistory:
    """Manages cache history with automatic cleanup."""

    def __init__(self, history_file: Path, max_history: int):
        """Initialize cache history manager."""
        self.history_file = history_file
        self.max_history = max_history
        self._entries: list[CacheHistoryEntry] = []
        self._aliases: dict[str, str] = {}
        self._load()

    def _load(self) -> None:
        """Load existing history from file."""
        if self.history_file.exists():
            try:
                with self.history_file.open("r") as f:
                    data = json.load(f)

                # Handle both old and new formats
                if isinstance(data, list):
                    # Old format: list of entries
                    self._entries = data
                    self._aliases = {}
                else:
                    # New format: dict with entries and aliases
                    self._entries = data.get("entries", [])
                    self._aliases = data.get("aliases", {})
            except (json.JSONDecodeError, KeyError):
                self._entries = []
                self._aliases = {}

    def _save(self) -> None:
        """Save history to file."""
        data: CacheHistoryData = {
            "entries": self._entries,
            "aliases": self._aliases,
        }
        with self.history_file.open("w") as f:
            json.dump(data, f, indent=2)

    def push(self, build: "NixBuild", cache_key: str | None = None) -> None:
        """Add a new entry to the queue and clean up oldest entries."""
        build_id = build.build_id

        # Generate cache paths using the cache_key if provided, otherwise build_id
        file_key = cache_key if cache_key is not None else build_id
        json_path = self.history_file.parent / f"{file_key}.json"
        profile_path = self.history_file.parent / f"{file_key}-profile"

        # Create entry from build (always uses build_id)
        entry: CacheHistoryEntry = {
            "build_id": build_id,
            "timestamp": time.time(),
            "json_path": str(json_path),
            "profile_path": str(profile_path),
        }

        # Update aliases if cache_key provided
        if cache_key is not None:
            self._aliases[cache_key] = build_id

        # Remove existing entry for this build_id if present
        self._entries = [e for e in self._entries if e["build_id"] != build_id]

        # Add new entry
        self._entries.append(entry)

        # Sort by timestamp (newest first) and limit to max_history
        self._entries.sort(key=lambda x: x["timestamp"], reverse=True)

        # Remove old entries beyond max_history
        old_entries = self._entries[self.max_history :]
        self._entries = self._entries[: self.max_history]

        # Clean up old files and remove orphaned aliases
        for old_entry in old_entries:
            self._cleanup_entry(old_entry)
            # Remove aliases pointing to this build_id
            self._aliases = {
                k: v for k, v in self._aliases.items() if v != old_entry["build_id"]
            }

        # Save updated history
        self._save()

    def get(self, cache_key: str) -> CacheHistoryEntry | None:
        """Get an entry by cache key, resolving aliases if necessary."""
        # First check if cache_key is an alias
        build_id = self._aliases.get(cache_key, cache_key)

        # Find entry by build_id
        for entry in self._entries:
            if entry["build_id"] == build_id:
                return entry
        return None

    def peek(self) -> CacheHistoryEntry | None:
        """Get the latest (most recent) entry in the queue."""
        if self._entries:
            return self._entries[0]  # First entry is newest due to sorting
        return None

    def _cleanup_entry(self, entry: CacheHistoryEntry) -> None:
        """Remove files associated with a cache entry."""
        try:
            json_path = Path(entry["json_path"])
            if json_path.exists():
                json_path.unlink()
        except (OSError, KeyError):
            pass

        try:
            profile_path = Path(entry["profile_path"])
            if profile_path.exists():
                profile_path.unlink()
        except (OSError, KeyError):
            pass


def load(
    build: NixBuild,
    *,
    use_global_cache: bool = False,
    history: int | None = None,
) -> NixBuild:
    """
    Load a cached Nix build or save it if not cached.

    Args:
        build: The NixBuild object to load or cache
        use_global_cache: Save in CACHE_ROOT instead of LOCAL_CACHE_ROOT
        history: Number of recent builds to keep in history (enables cleanup)

    Returns:
        The loaded NixBuild object with cached data populated
    """
    return _load(
        build,
        cache_key=build.build_id,
        use_global_cache=use_global_cache,
        history=history,
    )


def _load(
    build: NixBuild,
    *,
    cache_key: str,
    use_global_cache: bool = False,
    history: int | None = None,
) -> NixBuild:
    """
    Internal load method with customizable cache key.

    Args:
        build: The NixBuild object to load or cache
        cache_key: Custom key to use for cache file naming
        use_global_cache: Save in CACHE_ROOT instead of LOCAL_CACHE_ROOT
        history: Number of recent builds to keep in history (enables cleanup)

    Returns:
        The loaded NixBuild object with cached data populated
    """
    cache_root = CACHE_ROOT if use_global_cache else LOCAL_CACHE_ROOT
    cache_root.mkdir(parents=True, exist_ok=True)

    json_path = cache_root / f"{cache_key}.json"
    profile_path = cache_root / f"{cache_key}-profile"

    # Check if cached version exists and load it
    if json_path.exists():
        try:
            with json_path.open("r") as f:
                data = json.load(f)

            # Validate that the cached build_id matches the actual build
            if data.get("build_id") == build.build_id:
                build.load(json_path)

                # Update history if enabled
                if history is not None:
                    history_file = cache_root / "history.json"
                    cache_history = CacheHistory(history_file, history)
                    # Only add alias if cache_key differs from build_id
                    alias_key = cache_key if cache_key != build.build_id else None
                    cache_history.push(build, alias_key)

                return build
        except (json.JSONDecodeError, KeyError):
            # Invalid cache file, will rebuild
            pass

    # Cache doesn't exist or is invalid, build and save
    build.save_json(json_path)
    build.save_link(profile_path)

    # Update history if enabled
    if history is not None:
        history_file = cache_root / "history.json"
        cache_history = CacheHistory(history_file, history)
        # Only add alias if cache_key differs from build_id
        alias_key = cache_key if cache_key != build.build_id else None
        cache_history.push(build, alias_key)

    return build
