"""
Reward Function (Ödül Fonksiyonu)

RL ajanının davranışlarını şekillendiren ödül sistemi.
İyi routing kararları ödüllendirilir, kötü kararlar cezalandırılır.
"""

from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..environment.packet import Packet
    from ..environment.node import Node
    from ..environment.link import Link


class RoutingEvent(Enum):
    """Routing olayları"""

    FORWARDED = auto()  # Paket başarıyla iletildi
    DELIVERED = auto()  # Paket hedefe ulaştı
    DROPPED = auto()  # Paket düşürüldü
    NO_ROUTE = auto()  # Rota bulunamadı
    QUEUE_FULL = auto()  # Kuyruk dolu


@dataclass
class RewardConfig:
    """Ödül fonksiyonu yapılandırması"""

    # Ana ödüller/cezalar
    delivery_reward: float = 10.0  # Başarılı teslimat
    drop_penalty: float = -10.0  # Paket kaybı
    no_route_penalty: float = -5.0  # Rota bulunamadı

    # Hop başına ceza (uzun rotaları önle)
    hop_penalty: float = -0.1

    # Gecikme bonusu/cezası
    latency_weight: float = 1.0
    target_latency_ms: float = 50.0  # Hedef gecikme

    # Enerji bonusu (yüksek enerjili düğümleri tercih et)
    energy_weight: float = 0.5

    # Kuyruk cezası (dolu kuyrukları önle)
    queue_penalty_weight: float = 0.5

    # Link kalitesi bonusu
    quality_weight: float = 0.3

    # Hedefe yaklaşma ödülü (ileri yönlendirmede)
    # Pozitif: hedefe yaklaşıldı, Negatif: uzaklaşıldı
    progress_weight: float = 1.0

    # Döngü cezası (aynı düğümü tekrar ziyaret etme)
    loop_penalty: float = -2.0


class RewardCalculator:
    """
    Ödül Hesaplayıcı

    Her routing kararı için ödül hesaplar.
    """

    def __init__(self, config: Optional[RewardConfig] = None):
        """
        Args:
            config: Ödül yapılandırması
        """
        self.config = config or RewardConfig()

        # İstatistikler
        self._total_reward: float = 0.0
        self._reward_count: int = 0

    def calculate(
        self,
        event: RoutingEvent,
        packet: Optional["Packet"] = None,
        chosen_neighbor: Optional["Node"] = None,
        link: Optional["Link"] = None,
        is_loop: bool = False,
        progress_ratio: Optional[float] = None,
    ) -> float:
        """
        Ödül hesapla

        Args:
            event: Routing olayı
            packet: İlgili paket (opsiyonel)
            chosen_neighbor: Seçilen komşu düğüm (opsiyonel)
            link: Kullanılan bağlantı (opsiyonel)
            is_loop: Döngü mü?

        Returns:
            Ödül değeri
        """
        reward = 0.0

        # Ana ödül/ceza
        if event == RoutingEvent.DELIVERED:
            reward += self.config.delivery_reward
            reward += self._latency_bonus(packet)

        elif event == RoutingEvent.DROPPED:
            reward += self.config.drop_penalty

        elif event == RoutingEvent.NO_ROUTE:
            reward += self.config.no_route_penalty

        elif event == RoutingEvent.FORWARDED:
            # Her hop için küçük ceza
            reward += self.config.hop_penalty

            # Komşu kalitesi bonusları
            if chosen_neighbor:
                reward += self._energy_bonus(chosen_neighbor)
                reward += self._queue_penalty(chosen_neighbor)

            if link:
                reward += self._quality_bonus(link)

            # Hedefe yaklaşma ödülü/cezası
            if progress_ratio is not None:
                progress_ratio = max(-1.0, min(1.0, progress_ratio))
                reward += self.config.progress_weight * progress_ratio

        # Döngü cezası
        if is_loop:
            reward += self.config.loop_penalty

        # İstatistikleri güncelle
        self._total_reward += reward
        self._reward_count += 1

        return reward

    def _latency_bonus(self, packet: Optional["Packet"]) -> float:
        """
        Gecikme bonusu hesapla

        Düşük gecikme = yüksek bonus
        """
        if packet is None or packet.accumulated_latency is None:
            return 0.0

        latency = packet.accumulated_latency
        target = self.config.target_latency_ms

        if latency <= target:
            # Hedef altında: tam bonus
            return self.config.latency_weight * (1.0 - latency / target)
        else:
            # Hedef üstünde: ceza
            excess = (latency - target) / target
            return -self.config.latency_weight * min(excess, 2.0)

    def _energy_bonus(self, neighbor: "Node") -> float:
        """
        Enerji bonusu hesapla

        Yüksek enerjili düğümleri tercih et
        """
        energy_ratio = neighbor.energy / 100.0
        return self.config.energy_weight * (energy_ratio - 0.5)  # -0.25 ile +0.25 arası

    def _queue_penalty(self, neighbor: "Node") -> float:
        """
        Kuyruk cezası hesapla

        Dolu kuyrukları önle
        """
        queue_fullness = neighbor.queue_fullness
        return -self.config.queue_penalty_weight * queue_fullness

    def _quality_bonus(self, link: "Link") -> float:
        """
        Link kalitesi bonusu

        Yüksek kaliteli bağlantıları tercih et
        """
        return self.config.quality_weight * (link.quality - 0.5)

    # =========================================================================
    # İSTATİSTİKLER
    # =========================================================================

    @property
    def average_reward(self) -> float:
        """Ortalama ödül"""
        if self._reward_count == 0:
            return 0.0
        return self._total_reward / self._reward_count

    def reset(self):
        """İstatistikleri sıfırla"""
        self._total_reward = 0.0
        self._reward_count = 0

    def get_stats(self) -> dict:
        """İstatistikleri döndür"""
        return {
            "total_reward": self._total_reward,
            "reward_count": self._reward_count,
            "average_reward": self.average_reward,
        }
