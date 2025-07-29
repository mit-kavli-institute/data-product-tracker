"""Custom exceptions for Data Product Tracker."""


class DataProductTrackerException(Exception):
    """Base exception for all Data Product Tracker errors."""

    pass


class ModelDoesNotExist(Exception):
    """Raised when a database query returns no results."""

    def __init__(self, Model):
        """Initialize ModelDoesNotExist exception.

        Parameters
        ----------
        Model : type
            The SQLAlchemy model class that was not found.
        """
        msg = f"Query for {Model.__name__} returned nothing"
        super().__init__(msg)
