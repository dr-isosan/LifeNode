"""
Earthquake Scenario (Deprem Senaryosu)

Deprem simülasyonu:
- Merkez üssü ve yarıçap
- Yoğunluğa göre düğüm hasarı
- Link kalite degradasyonu
- Kademeli iyileşme
"""

from dataclasses import dataclass, field
from typing import List, Tuple, Set, TYPE_CHECKING
import random
import math

from .base import Scenario, ScenarioEvent, ScenarioEventType

if TYPE_CHECKING:
    from ..environment.world import World


@dataclass
class EarthquakeScenario(Scenario):
    """
    Deprem Senaryosu

    Belirli bir merkez üssünden yayılan deprem etkisini simüle eder.

    Attributes:
        epicenter: Merkez üssü koordinatları (x, y)
        radius: Etki yarıçapı (metre)
        intensity: Yoğunluk (0-1, 1 = maksimum yıkım)
        trigger_step: Deprem tetiklenme adımı
        recovery_rate: Kurtarma hızı (0-1)
        aftershock_probability: Artçı sarsıntı olasılığı
    """

    epicenter: Tuple[float, float]
    radius: float
    intensity: float
    trigger_step: int
    recovery_rate: float = 0.02
    aftershock_probability: float = 0.1
    aftershock_intensity: float = 0.3

    # Dahili durum
    _triggered: bool = field(default=False, repr=False)
    _failed_nodes: Set[str] = field(default_factory=set, repr=False)
    _degraded_links: Set[Tuple[str, str]] = field(default_factory=set, repr=False)
    _total_failures: int = field(default=0, repr=False)
    _total_recoveries: int = field(default=0, repr=False)

    def get_name(self) -> str:
        return f"Earthquake(intensity={self.intensity:.1f})"

    def is_active(self, current_step: int) -> bool:
        return current_step >= self.trigger_step

    def apply(self, world: 'World', current_step: int) -> List[ScenarioEvent]:
        """Deprem etkilerini uygula"""
        events = []

        if current_step < self.trigger_step:
            return events

        # Ana deprem
        if current_step == self.trigger_step:
            events.extend(self._trigger_earthquake(world, current_step))

        # Artçı sarsıntılar
        elif current_step > self.trigger_step:
            if random.random() < self.aftershock_probability:
                events.extend(self._trigger_aftershock(world, current_step))

            # Kurtarma
            events.extend(self._apply_recovery(world, current_step))

        return events

    def _trigger_earthquake(
        self,
        world: 'World',
        step: int
    ) -> List[ScenarioEvent]:
        """Ana depremi tetikle"""
        self._triggered = True
        events = []
        failed_nodes = []

        for node in list(world.nodes.values()):
            distance = self._distance_to_epicenter(node.position)

            if distance < self.radius:
                # Mesafeye göre hasar olasılığı
                damage_factor = 1 - (distance / self.radius)
                damage_probability = self.intensity * damage_factor

                if random.random() < damage_probability:
                    node.fail()
                    self._failed_nodes.add(node.id)
                    failed_nodes.append(node.id)
                    self._total_failures += 1
                else:
                    # Enerji kaybı
                    energy_loss = self.intensity * damage_factor * 30
                    node.consume_energy(energy_loss)

        # Link degradasyonu
        for link in list(world.links.values()):
            node_a = world.nodes.get(link.node_a)
            node_b = world.nodes.get(link.node_b)

            if node_a and node_b:
                avg_dist = (
                    self._distance_to_epicenter(node_a.position) +
                    self._distance_to_epicenter(node_b.position)
                ) / 2

                if avg_dist < self.radius:
                    damage_factor = 1 - (avg_dist / self.radius)
                    degrade_amount = 1 - (self.intensity * damage_factor * 0.5)
                    link.degrade(degrade_amount)
                    self._degraded_links.add(link.get_key())

        # Linkleri güncelle
        world.update_all_links()

        if failed_nodes:
            events.append(ScenarioEvent(
                event_type=ScenarioEventType.AREA_AFFECTED,
                step=step,
                affected_nodes=failed_nodes,
                details={'type': 'earthquake', 'intensity': self.intensity}
            ))

        return events

    def _trigger_aftershock(
        self,
        world: 'World',
        step: int
    ) -> List[ScenarioEvent]:
        """Artçı sarsıntı"""
        events = []
        failed_nodes = []

        # Rastgele merkez (ana merkeze yakın)
        offset_x = random.uniform(-self.radius * 0.5, self.radius * 0.5)
        offset_y = random.uniform(-self.radius * 0.5, self.radius * 0.5)
        aftershock_center = (
            self.epicenter[0] + offset_x,
            self.epicenter[1] + offset_y
        )
        aftershock_radius = self.radius * 0.5

        for node in list(world.nodes.values()):
            if not node.is_active:
                continue

            dx = node.position[0] - aftershock_center[0]
            dy = node.position[1] - aftershock_center[1]
            distance = math.sqrt(dx * dx + dy * dy)

            if distance < aftershock_radius:
                damage_factor = 1 - (distance / aftershock_radius)
                damage_prob = self.aftershock_intensity * damage_factor

                if random.random() < damage_prob:
                    node.fail()
                    self._failed_nodes.add(node.id)
                    failed_nodes.append(node.id)
                    self._total_failures += 1

        world.update_all_links()

        if failed_nodes:
            events.append(ScenarioEvent(
                event_type=ScenarioEventType.AREA_AFFECTED,
                step=step,
                affected_nodes=failed_nodes,
                details={'type': 'aftershock'}
            ))

        return events

    def _apply_recovery(
        self,
        world: 'World',
        step: int
    ) -> List[ScenarioEvent]:
        """Kademeli kurtarma"""
        events = []
        recovered_nodes = []

        for node_id in list(self._failed_nodes):
            if random.random() < self.recovery_rate:
                node = world.nodes.get(node_id)
                if node:
                    node.recover(energy=50.0)
                    self._failed_nodes.discard(node_id)
                    recovered_nodes.append(node_id)
                    self._total_recoveries += 1

        # Link kurtarma
        for link_key in list(self._degraded_links):
            if random.random() < self.recovery_rate:
                link = world.links.get(link_key)
                if link:
                    link.recover(factor=1.2)
                    if link.quality > 0.8:
                        self._degraded_links.discard(link_key)

        world.update_all_links()

        if recovered_nodes:
            events.append(ScenarioEvent(
                event_type=ScenarioEventType.NODE_RECOVERED,
                step=step,
                affected_nodes=recovered_nodes,
            ))

        return events

    def _distance_to_epicenter(self, position: Tuple[float, float]) -> float:
        """Merkez üssüne mesafe"""
        dx = position[0] - self.epicenter[0]
        dy = position[1] - self.epicenter[1]
        return math.sqrt(dx * dx + dy * dy)

    def reset(self):
        """Senaryoyu sıfırla"""
        self._triggered = False
        self._failed_nodes.clear()
        self._degraded_links.clear()
        self._total_failures = 0
        self._total_recoveries = 0

    def get_stats(self) -> dict:
        """İstatistikleri döndür"""
        return {
            'name': self.get_name(),
            'triggered': self._triggered,
            'total_failures': self._total_failures,
            'total_recoveries': self._total_recoveries,
            'current_failed_nodes': len(self._failed_nodes),
            'current_degraded_links': len(self._degraded_links),
        }
