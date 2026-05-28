"""Stateless A/B traffic splitter.

Routes a request to the lower (Staging) version with probability
`ab_split_percent / 100`, and to the higher (Production) version otherwise.
"""

import random

from app.config import settings


def get_ab_version(available_versions: list[str]) -> str:
    """Pick a version to serve given the loaded version list.

    Args:
        available_versions: Sorted-ascending list of version strings, e.g. ["1", "2"].

    Returns:
        The version string to use for this request.
    """
    if len(available_versions) < 2:
        return available_versions[0] if available_versions else "latest"

    v1 = available_versions[0]   # lower  version → Staging
    v2 = available_versions[-1]  # higher version → Production

    return v1 if random.random() * 100 < settings.ab_split_percent else v2
