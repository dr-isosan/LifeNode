"""
Gradual Failure Scenario (Kademeli Arıza Senaryosu)

Zaman içinde kademeli düğüm arızaları.
RL'nin adaptasyon yeteneğini test etmek için idealdir.
"""

from dataclasses import dataclass, field
from typing import List, Set, TYPE_CHECKING
import random

from .base import Scenario, ScenarioEvent, ScenarioEventType

if TYPE_CHECKING:
    from ..environment.world import World


@dataclass
class GradualFailureScenario(Scenario):
    """
    Kademeli Arıza Senaryosu

    Her adımda belirli olasılıkla düğümler arızalanır.
    Sabit oranda kurtarma yapılır.

    Attributes:
        start_step: Başlangıç adımı
        failure_rate: Adım başına arıza olasılığı
        recovery_rate: Adım başına kurtarma olasılığı
        max_failures: Aynı anda maksimum arızalı düğüm oranı
    """

    start_step: int = 100
    failure_rate: float = 0.02
    recovery_rate: float = 0.01
    max_failures: float = 0.3  # Max %30 arızalı

    # Dahili durum
    _failed_nodes: Set[str] = field(default_factory=set, repr=False)
    _total_failures: int = field(default=0, repr=False)
    _total_recoveries: int = field(default=0, repr=False)

    def get_name(self) -> str:
        return f"GradualFailure(rate={self.failure_rate})"

    def is_active(self, current_step: int) -> bool:
        return current_step >= self.start_step

    def apply(self, world: 'World', current_step: int) -> List[ScenarioEvent]:
        """Kademeli arızaları uygula"""
        if current_step < self.start_step:
            return []

        events = []

        # Mevcut arıza oranı
        total_nodes = len(world.nodes)
        current_failure_ratio = len(self._failed_nodes) / total_nodes if total_nodes > 0 else 0

        # Arıza uygula
        if current_failure_ratio < self.max_failures:
            failed = self._apply_failures(world, current_step)
            if failed:
                events.append(ScenarioEvent(
                    event_type=ScenarioEventType.NODE_FAILED,
                    step=current_step,
                    affected_nodes=failed,
                ))

        # Kurtarma uygula
        recovered = self._apply_recovery(world, current_step)
        if recovered:
            events.append(ScenarioEvent(
                event_type=ScenarioEventType.NODE_RECOVERED,
                step=current_step,
                affected_nodes=recovered,
            ))

        return events

    def _apply_failures(self, world: 'World', step: int) -> List[str]:
        """Rastgele arızalar uygula"""
        failed = []

        for node in list(world.nodes.values()):
            if node.is_active and random.random() < self.failure_rate:
                node.fail()
                self._failed_nodes.add(node.id)
                failed.append(node.id)
                self._total_failures += 1

        if failed:
            world.update_all_links()

        return failed

    def _apply_recovery(self, world: 'World', step: int) -> List[str]:
        """Rastgele kurtarma uygula"""
        recovered = []

        for node_id in list(self._failed_nodes):
            if random.random() < self.recovery_rate:
                node = world.nodes.get(node_id)
                if node:
                    node.recover(energy=60.0)
                    self._failed_nodes.discard(node_id)
                    recovered.append(node_id)
                    self._total_recoveries += 1

        if recovered:
            world.update_all_links()

        return recovered

    def reset(self):
        """Senaryoyu sıfırla"""
        self._failed_nodes.clear()
        self._total_failures = 0
        self._total_recoveries = 0

    def get_stats(self) -> dict:
        """İstatistikleri döndür"""
        return {
            'name': self.get_name(),
            'total_failures': self._total_failures,
            'total_recoveries': self._total_recoveries,
            'current_failed_nodes': len(self._failed_nodes),
        }
