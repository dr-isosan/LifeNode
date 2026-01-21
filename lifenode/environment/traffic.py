"""
Traffic Generator (Trafik Üreteci)

Ağda iletilecek paketleri üreten modül.
Çeşitli trafik desenleri desteklenir.
"""

from dataclasses import dataclass
from typing import List, Optional, Tuple
import random

from .packet import Packet
from .node import Node


@dataclass
class TrafficPattern:
    """Trafik deseni yapılandırması"""

    # Paket üretim hızı
    packets_per_step: float = 0.5  # Ortalama paket/adım

    # Paket boyutu
    min_size: int = 64
    max_size: int = 1500

    # Kaynak-hedef seçimi
    random_pairs: bool = True
    specific_sources: Optional[List[str]] = None
    specific_destinations: Optional[List[str]] = None

    # Burst trafik
    burst_enabled: bool = False
    burst_probability: float = 0.1
    burst_size: int = 10


class TrafficGenerator:
    """
    Trafik üreteci

    Simülasyon sırasında paketler oluşturur.
    """

    def __init__(
        self,
        pattern: Optional[TrafficPattern] = None,
        seed: Optional[int] = None
    ):
        """
        Args:
            pattern: Trafik deseni yapılandırması
            seed: Rastgelelik tohumu
        """
        self.pattern = pattern or TrafficPattern()

        if seed is not None:
            random.seed(seed)

        # İstatistikler
        self.total_packets_generated: int = 0

    def generate(
        self,
        current_step: int,
        active_nodes: List[Node]
    ) -> List[Packet]:
        """
        Bir simülasyon adımı için paketler üret

        Args:
            current_step: Mevcut simülasyon adımı
            active_nodes: Aktif düğüm listesi

        Returns:
            Üretilen paket listesi
        """
        if len(active_nodes) < 2:
            return []

        packets = []

        # Burst kontrol
        if self.pattern.burst_enabled and random.random() < self.pattern.burst_probability:
            num_packets = self.pattern.burst_size
        else:
            # Poisson dağılımına yakın rastgele sayı
            num_packets = self._poisson_sample(self.pattern.packets_per_step)

        for _ in range(num_packets):
            packet = self._create_packet(current_step, active_nodes)
            if packet:
                packets.append(packet)
                self.total_packets_generated += 1

        return packets

    def _create_packet(
        self,
        current_step: int,
        active_nodes: List[Node]
    ) -> Optional[Packet]:
        """
        Tek bir paket oluştur

        Args:
            current_step: Mevcut simülasyon adımı
            active_nodes: Aktif düğüm listesi

        Returns:
            Paket veya None
        """
        # Kaynak ve hedef seç
        source, destination = self._select_source_destination(active_nodes)
        if source is None or destination is None:
            return None

        # Paket boyutu
        size = random.randint(self.pattern.min_size, self.pattern.max_size)

        return Packet(
            source=source,
            destination=destination,
            size=size,
            created_at=current_step,
        )

    def _select_source_destination(
        self,
        active_nodes: List[Node]
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Kaynak ve hedef düğüm seç

        Args:
            active_nodes: Aktif düğüm listesi

        Returns:
            (kaynak_id, hedef_id) tuple'ı
        """
        if len(active_nodes) < 2:
            return None, None

        # Kaynak seçimi
        if self.pattern.specific_sources:
            valid_sources = [
                n for n in active_nodes
                if n.id in self.pattern.specific_sources
            ]
            if not valid_sources:
                valid_sources = active_nodes
        else:
            valid_sources = active_nodes

        source = random.choice(valid_sources)

        # Hedef seçimi (kaynaktan farklı)
        if self.pattern.specific_destinations:
            valid_dests = [
                n for n in active_nodes
                if n.id in self.pattern.specific_destinations and n.id != source.id
            ]
            if not valid_dests:
                valid_dests = [n for n in active_nodes if n.id != source.id]
        else:
            valid_dests = [n for n in active_nodes if n.id != source.id]

        if not valid_dests:
            return None, None

        destination = random.choice(valid_dests)

        return source.id, destination.id

    def _poisson_sample(self, lam: float) -> int:
        """
        Poisson dağılımından örnekle

        Simple inverse transform sampling

        Args:
            lam: Lambda (ortalama)

        Returns:
            Rastgele tam sayı
        """
        import math

        L = math.exp(-lam)
        k = 0
        p = 1.0

        while p > L:
            k += 1
            p *= random.random()

        return k - 1

    def reset(self):
        """İstatistikleri sıfırla"""
        self.total_packets_generated = 0

    def get_stats(self) -> dict:
        """İstatistikleri döndür"""
        return {
            'total_packets_generated': self.total_packets_generated,
        }


class ConstantBitrateGenerator(TrafficGenerator):
    """
    Sabit bit hızı trafik üreteci (CBR)

    Belirli aralıklarla düzenli paketler üretir.
    """

    def __init__(
        self,
        packets_per_step: int = 1,
        packet_size: int = 1024,
        seed: Optional[int] = None
    ):
        pattern = TrafficPattern(
            packets_per_step=packets_per_step,
            min_size=packet_size,
            max_size=packet_size,
        )
        super().__init__(pattern, seed)


class BurstyTrafficGenerator(TrafficGenerator):
    """
    Patlamalı trafik üreteci

    Zaman zaman yoğun trafik patlamaları üretir.
    """

    def __init__(
        self,
        burst_probability: float = 0.2,
        burst_size: int = 20,
        seed: Optional[int] = None
    ):
        pattern = TrafficPattern(
            packets_per_step=0.3,
            burst_enabled=True,
            burst_probability=burst_probability,
            burst_size=burst_size,
        )
        super().__init__(pattern, seed)


class HotspotTrafficGenerator(TrafficGenerator):
    """
    Hotspot trafik üreteci

    Belirli düğümlere yoğun trafik yönlendirir.
    """

    def __init__(
        self,
        hotspot_nodes: List[str],
        seed: Optional[int] = None
    ):
        pattern = TrafficPattern(
            packets_per_step=1.0,
            specific_destinations=hotspot_nodes,
        )
        super().__init__(pattern, seed)
