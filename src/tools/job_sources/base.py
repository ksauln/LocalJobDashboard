from abc import ABC, abstractmethod
from typing import List

from ...models import Job


class BaseJobSource(ABC):
    name: str

    @abstractmethod
    def search(self, query: str, limit: int = 50) -> List[Job]:
        raise NotImplementedError
