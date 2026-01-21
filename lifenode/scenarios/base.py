"""
Scenario Base (Senaryo Temel Arayüzü)

Tüm afet senaryolarının uyması gereken arayüz.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum, auto
from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..environment.world import World


class ScenarioEventType(Enum):
    """Senaryo olay türleri"""
    NODE_FAILED = auto()
    NODE_RECOVERED = auto()
    LINK_DEGRADED = auto()
    LINK_RECOVERED = auto()
    AREA_AFFECTED = auto()


@dataclass
class ScenarioEvent:
    """Senaryo olayı"""
    event_type: ScenarioEventType
    step: int
    affected_nodes: List[str]
    details: Optional[dict] = None


class Scenario(ABC):
    """
    Soyut Senaryo Arayüzü

    Her senaryo bu arayüzü uygulamalıdır.
    """

    @abstractmethod
    def get_name(self) -> str:
        """Senaryo adını döndür"""
        pass

    @abstractmethod
    def apply(self, world: 'World', current_step: int) -> List[ScenarioEvent]:
        """
        Senaryoyu dünyaya uygula

        Args:
            world: Simülasyon dünyası
            current_step: Mevcut adım

        Returns:
            Bu adımda gerçekleşen olaylar
        """
        pass

    @abstractmethod
    def is_active(self, current_step: int) -> bool:
        """Senaryo bu adımda aktif mi?"""
        pass

    def reset(self):
        """Senaryoyu sıfırla"""
        pass

    def get_stats(self) -> dict:
        """Senaryo istatistiklerini döndür"""
        return {'name': self.get_name()}
