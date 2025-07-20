from __future__ import annotations

"""Reusable progress-reporting helpers used across the Femora package.

To show progress in long-running operations we often need a simple callback
with the signature ``callback(value: float, message: str)`` where *value* is a
percentage in the 0–100 range.

This module centralises that logic so every component can obtain the same
consistent progress reporter (currently powered by *tqdm*).  It avoids
duplicating the progress-bar code in many classes (e.g. MeshMaker).
"""

from typing import Callable, Optional
import tqdm

__all__ = ["Progress", "get_progress_callback"]


class Progress:
    """Singleton that owns a *tqdm* bar and offers a plain callback method."""

    _bar: Optional[tqdm.tqdm] = None
    _last_value: int = 0

    @classmethod
    def _ensure_bar(cls, desc: str) -> None:
        if cls._bar is None:
            # Lazily create the bar when the first update happens
            cls._bar = tqdm.tqdm(
                total=100,
                desc=desc,
                bar_format="{desc}: {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt} [" "{elapsed}<{remaining}] {postfix}",
            )
            cls._last_value = 0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    @classmethod
    def callback(cls, value: float, message: str = "", *, desc: str = "Processing") -> None:
        """A generic progress-callback suitable for any component.

        Parameters
        ----------
        value : float
            Progress between 0 and 100 (will be cast to ``int``).
        message : str
            Short status to show next to the bar.
        desc : str, optional
            Description for the bar (only used when it is first created).
        """
        value_int = int(value)
        cls._ensure_bar(desc)
        if cls._bar is None:  # for type checkers
            return

        cls._bar.set_postfix_str(message)
        cls._bar.n = value_int
        cls._bar.refresh()
        cls._last_value = value_int

        if value_int >= 100:
            cls.close()

    # ------------------------------------------------------------------
    @classmethod
    def close(cls):
        """Close and reset the internal tqdm bar (if any)."""
        if cls._bar is not None:
            cls._bar.close()
            cls._bar = None
            cls._last_value = 0


# Convenience helpers --------------------------------------------------

def get_progress_callback(desc: str = "Processing") -> Callable[[float, str], None]:
    """Return a partially-applied ``Progress.callback`` with preset *desc*.

    Usage
    -----
    >>> progress = get_progress_callback("Exporting")
    >>> progress(10, "initialising")
    >>> progress(100, "done")
    """

    def _cb(value: float, message: str = "") -> None:  # noqa: D401
        Progress.callback(value, message, desc=desc)

    return _cb 