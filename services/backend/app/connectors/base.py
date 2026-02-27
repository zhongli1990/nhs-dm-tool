from abc import ABC, abstractmethod
from typing import Dict, List


class SourceTargetConnector(ABC):
    @abstractmethod
    def list_tables(self) -> List[str]:
        raise NotImplementedError

    @abstractmethod
    def describe_table(self, table_name: str) -> List[Dict[str, str]]:
        raise NotImplementedError

    @abstractmethod
    def sample_rows(self, table_name: str, limit: int = 20) -> List[Dict[str, str]]:
        raise NotImplementedError
