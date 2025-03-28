"""Top-level package for Data Product Tracker."""

__author__ = """William Christopher Fong"""
__email__ = "willfong@mit.edu"
__version__ = "0.1.5"


from data_product_tracker import sql as _sql  # noqa F401
from data_product_tracker.io.trackers import tracker

try:
    import deal

    deal.disable()
except ImportError:
    pass

__all__ = [
    "tracker",
]
