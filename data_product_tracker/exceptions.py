class DataProductTrackerException(Exception):
    pass


class ModelDoesNotExist(Exception):
    def __init__(self, Model):
        msg = f"Query for {Model.__name__} returned nothing"
        return super().__init__(msg)
