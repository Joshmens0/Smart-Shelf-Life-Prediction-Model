"""
DEPRECATED — json_file.py
--------------------------
``JsonFile`` has been merged into ``DataLoader``.
This module exists only for backward compatibility and will be removed
in a future version.

Migration
---------
Replace::

    from json_file import JsonFile
    loader = JsonFile()

With::

    from data_loader import DataLoader
    loader = DataLoader()
"""
import warnings

from data_loader import DataLoader

warnings.warn(
    "json_file.JsonFile is deprecated and will be removed in a future version. "
    "Use data_loader.DataLoader instead.",
    DeprecationWarning,
    stacklevel=2,
)

# Alias for backward compatibility
JsonFile = DataLoader

__all__ = ['JsonFile']