from importlib import metadata


def yield_distributions_used():
    mask = set()
    for dist in metadata.distributions():
        if dist.metadata["Name"] in mask:
            continue
        yield dist
        mask.add(str(dist.metadata["Name"]))
