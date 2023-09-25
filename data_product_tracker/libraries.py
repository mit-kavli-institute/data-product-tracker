from functools import lru_cache
from importlib import metadata


@lru_cache
def get_distribution_used(name: str):
    try:
        return metadata.distribution(name)
    except metadata.PackageNotFoundError:
        return None


def yield_distributions_used():
    mask = set()
    for dist in metadata.distributions():
        if dist.metadata["Name"] in mask:
            continue
        used = get_distribution_used(dist.metadata["Name"])
        yield used
        mask.add(dist.metadata["Name"])
