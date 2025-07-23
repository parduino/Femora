from __future__ import annotations

"""Singleton class providing a Qt-based progress bar that mirrors the
:pyclass:`femora.utils.progress.Progress` console helper.

Usage example
-------------
>>> from femora.gui.progress_gui import get_progress_callback_gui
>>> cb = get_progress_callback_gui("Exporting")
>>> cb(10, "initialising")
>>> cb(100, "done")

The first time the callback is invoked the progress bar widget is lazily
created and inserted *below the interactive console* in the right-hand panel
of the main application window.
"""

from typing import Callable, Optional

from qtpy.QtCore import Qt
from qtpy.QtWidgets import QProgressBar, QWidget, QVBoxLayout, QLabel

__all__ = ["ProgressGUI", "get_progress_callback_gui"]


class _ProgressWidget(QWidget):
    """Lightweight container bundling a label and a :class:`QProgressBar`."""

    def __init__(self, desc: str):
        super().__init__()
        self._bar = QProgressBar(self)
        self._bar.setRange(0, 100)
        self._bar.setAlignment(Qt.AlignCenter)
        self._bar.setFormat(f"{desc} - %p%")

        self._label = QLabel("", self)
        self._label.setAlignment(Qt.AlignCenter)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.addWidget(self._label)
        layout.addWidget(self._bar)

    # Expose convenient passthroughs ---------------------------------
    def set_value(self, value: int):  # noqa: D401
        self._bar.setValue(value)

    def set_message(self, message: str):  # noqa: D401
        self._label.setText(message)

    def close(self):  # noqa: D401  (keep interface parity)
        super().close()


class ProgressGUI:
    """Singleton that manages a GUI progress bar and provides a callback."""

    _widget: Optional[_ProgressWidget] = None
    _last_value: int = 0

    # --------------------------------------------------------------
    @classmethod
    def _ensure_widget(cls, desc: str) -> None:
        """Lazy-initialise the underlying widget and attach it to the UI."""
        if cls._widget is not None:
            return

        # Import here to avoid circular dependencies
        from femora.gui.main_window import MainWindow

        try:
            main_window = MainWindow.get_instance()
        except RuntimeError:
            # GUI has not been launched; silently ignore
            return

        cls._widget = _ProgressWidget(desc)

        # Insert as the last widget in the right-hand splitter (index 2)
        right_panel = getattr(main_window, "right_panel", None)
        if right_panel is not None:
            right_panel.addWidget(cls._widget)
        else:
            # Fallback: add to the status bar if available
            main_window.statusBar().addPermanentWidget(cls._widget)

    # --------------------------------------------------------------
    @classmethod
    def callback(cls, value: float, message: str = "", *, desc: str = "Processing") -> None:
        """Qt-aware progress callback mirroring :meth:`Progress.callback`."""
        value_int = int(value)

        # All GUI manipulations must happen in the main thread.  We wrap the
        # logic inside a closure dispatched via *invokeMethod* to guarantee
        # thread-safety even when the callback is triggered from worker threads.
        def _update():
            cls._ensure_widget(desc)
            if cls._widget is None:
                return  # GUI not available

            cls._widget.set_message(message)
            cls._widget.set_value(value_int)
            # Keep the description in sync if different tasks supply different *desc*.
            cls._widget._bar.setFormat(f"{desc} - %p%")
            cls._last_value = value_int

            if value_int >= 100:
                # After showing 100 % for a moment, reset to idle but keep widget.
                from qtpy.QtCore import QTimer

                def _reset_idle():
                    if cls._widget is not None:
                        cls._widget.set_message("Idle")
                        cls._widget.set_value(0)

                QTimer.singleShot(1500, _reset_idle)

        # Execute immediately if already in the GUI thread; otherwise queue.
        from qtpy.QtCore import QThread, QTimer
        from qtpy.QtWidgets import QApplication

        if cls._widget is not None and cls._widget.thread() == QThread.currentThread():
            _update()
            # Process events so the bar repaints during long loops running in
            # the same thread.
            QApplication.processEvents()
        else:
            QTimer.singleShot(0, _update)

    # --------------------------------------------------------------
    @classmethod
    def close(cls):
        """Remove the widget and reset the singleton state."""
        if cls._widget is not None:
            cls._widget.close()
            cls._widget.setParent(None)
            cls._widget = None
            cls._last_value = 0

    # --------------------------------------------------------------
    @classmethod
    def show(cls, desc: str = "Progress") -> None:  # noqa: D401
        """Ensure the progress widget exists and display an *Idle* state."""
        cls._ensure_widget(desc)
        if cls._widget is not None:
            cls._widget.set_message("Idle")
            cls._widget.set_value(0)


# Convenience helper --------------------------------------------------


def get_progress_callback_gui(desc: str = "Processing") -> Callable[[float, str], None]:
    """Return a partially-applied :pyattr:`ProgressGUI.callback` with *desc* preset."""

    def _cb(value: float, message: str = "") -> None:  # noqa: D401
        ProgressGUI.callback(value, message, desc=desc)

    return _cb 