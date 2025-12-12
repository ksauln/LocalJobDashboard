from typing import List

from ...config import JOB_SOURCES
from .dummy import DummySource
from .greenhouse import GreenhouseSource
from .lever import LeverSource
from .remotive import RemotiveSource

SOURCE_MAP = {
    "dummy": DummySource,
    "greenhouse": GreenhouseSource,
    "lever": LeverSource,
    "remotive": RemotiveSource,
}


def get_sources_from_env() -> List:
    sources = []
    for name in JOB_SOURCES:
        cls = SOURCE_MAP.get(name)
        if cls:
            sources.append(cls())
    return sources
