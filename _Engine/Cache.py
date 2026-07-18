import os
import json
import time
from typing import Any, Optional


class Cache:
    """
    A simple cache manager that stores data in files with expiration support.

    Cache files are stored in the './Cache/' directory. Supports JSON and TXT formats.
    """

    CACHE_DIR = "./_cache"

    def __init__(self) -> None:
        """
        Initialize the Cache instance and ensure the cache directory exists.
        """
        os.makedirs(self.CACHE_DIR, exist_ok=True)

    def _get_full_path(self, path: str, format: str) -> str:
        """
        Get the full file path for the given relative path and format.

        Args:
            path: Relative path (e.g., "google/search/python")
            format: File format ("json" or "txt")

        Returns:
            Full path to the cache file
        """
        # Ensure proper extension
        if not path.endswith(f".{format}"):
            path = f"{path}.{format}"

        # Join with cache directory, handling subdirectories
        full_path = os.path.join(self.CACHE_DIR, path)

        # Ensure parent directories exist
        os.makedirs(os.path.dirname(full_path), exist_ok=True)

        return full_path

    def _is_expired(self, created: int, expire: int) -> bool:
        """
        Check if the cache entry has expired.

        Args:
            created: Unix timestamp when created
            expire: Expiration in hours

        Returns:
            True if expired, False otherwise
        """
        current_time = int(time.time())
        expiration_time = created + (expire * 3600)
        return current_time > expiration_time

    def _parse_txt(self, content: str) -> dict:
        """
        Parse TXT cache file content.

        Args:
            content: Raw text content of the file

        Returns:
            Dictionary with created, expire, and content
        """
        lines = content.strip().split("\n")
        metadata = {}
        content_start = 0

        for i, line in enumerate(lines):
            if line.strip() == "--------------------":
                content_start = i + 1
                break
            if "=" in line:
                key, value = line.split("=", 1)
                metadata[key.strip()] = value.strip()

        content_data = "\n".join(lines[content_start:]) if content_start > 0 else ""

        return {
            "created": int(metadata.get("created", 0)),
            "expire": int(metadata.get("expire", 0)),
            "content": content_data
        }

    def save(
            self,
            path: str,
            content: Any,
            format: str = "json",
            expire: int = 24
    ) -> None:
        """
        Save content to cache with specified format and expiration.

        Args:
            path: Relative path for the cache file (e.g., "google/search/python")
            content: Data to cache (any serializable type for JSON, str for TXT)
            format: Storage format ("json" or "txt")
            expire: Expiration time in hours

        Raises:
            ValueError: If format is not supported
        """
        if format not in ["json", "txt"]:
            raise ValueError(f"Unsupported format: {format}. Supported: json, txt")

        full_path = self._get_full_path(path, format)

        created = int(time.time())

        if format == "json":
            data = {
                "created": created,
                "expire": expire,
                "content": content
            }
            with open(full_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        else:  # txt
            header = f"created={created}\nexpire={expire}\n\n--------------------\n"
            txt_content = str(content)
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(header + txt_content)

    def load(self, path: str) -> Optional[Any]:
        """
        Load content from cache if it exists and is not expired.

        Args:
            path: Relative path to the cache file

        Returns:
            Cached content if valid, None if not found or expired
        """
        # Try JSON first
        json_path = self._get_full_path(path, "json")
        if os.path.exists(json_path):
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                if self._is_expired(data["created"], data["expire"]):
                    os.remove(json_path)
                    return None

                return data["content"]
            except (json.JSONDecodeError, KeyError, TypeError):
                # Invalid JSON, remove it
                os.remove(json_path)
                return None

        # Try TXT
        txt_path = self._get_full_path(path, "txt")
        if os.path.exists(txt_path):
            try:
                with open(txt_path, "r", encoding="utf-8") as f:
                    raw_content = f.read()

                parsed = self._parse_txt(raw_content)

                if self._is_expired(parsed["created"], parsed["expire"]):
                    os.remove(txt_path)
                    return None

                return parsed["content"]
            except (ValueError, KeyError, IndexError):
                # Invalid format, remove it
                os.remove(txt_path)
                return None

        return None

    def exists(self, path: str) -> bool:
        """
        Check if a valid (non-expired) cache entry exists.

        Args:
            path: Relative path to check

        Returns:
            True if valid cache exists, False otherwise
        """
        # Check JSON
        json_path = self._get_full_path(path, "json")
        if os.path.exists(json_path):
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                if self._is_expired(data.get("created", 0), data.get("expire", 0)):
                    os.remove(json_path)
                    return False
                return True
            except Exception:
                os.remove(json_path)
                return False

        # Check TXT
        txt_path = self._get_full_path(path, "txt")
        if os.path.exists(txt_path):
            try:
                with open(txt_path, "r", encoding="utf-8") as f:
                    raw_content = f.read()

                parsed = self._parse_txt(raw_content)

                if self._is_expired(parsed["created"], parsed["expire"]):
                    os.remove(txt_path)
                    return False
                return True
            except Exception:
                os.remove(txt_path)
                return False

        return False

    def delete(self, path: str) -> bool:
        """
        Delete a cache file if it exists.

        Args:
            path: Relative path of the cache to delete

        Returns:
            True if file was deleted, False if not found
        """
        deleted = False

        # Try JSON
        json_path = self._get_full_path(path, "json")
        if os.path.exists(json_path):
            try:
                os.remove(json_path)
                deleted = True
            except OSError:
                pass

        # Try TXT
        txt_path = self._get_full_path(path, "txt")
        if os.path.exists(txt_path):
            try:
                os.remove(txt_path)
                deleted = True
            except OSError:
                pass

        return deleted

    def clear(self) -> None:
        """
        Clear all cache files and subdirectories.
        """
        if os.path.exists(self.CACHE_DIR):
            for root, dirs, files in os.walk(self.CACHE_DIR, topdown=False):
                for file in files:
                    try:
                        os.remove(os.path.join(root, file))
                    except OSError:
                        pass
                for dir_name in dirs:
                    try:
                        os.rmdir(os.path.join(root, dir_name))
                    except OSError:
                        pass
            try:
                os.rmdir(self.CACHE_DIR)
            except OSError:
                pass
        # Recreate empty directory
        os.makedirs(self.CACHE_DIR, exist_ok=True)