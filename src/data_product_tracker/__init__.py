"""Top-level package for Data Product Tracker."""

__author__ = """William Christopher Fong"""
__email__ = "willfong@mit.edu"

try:
    from ._version import version as __version__
except ImportError:
    # package is not installed
    __version__ = "0.0.0dev"


from data_product_tracker import sql as _sql  # noqa F401
from data_product_tracker.io.trackers import tracker

__all__ = [
    "tracker",
]
