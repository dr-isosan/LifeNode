"""
State Representation (Durum Temsili) - DÜZELTILMIŞ

RL ajanının gözlemlediği durumu tanımlar.
State, routing kararları için gerekli tüm bilgileri içerir.

ÖNEMLİ DÜZELTME: Hedefe olan mesafe bilgisi eklendi.
Komşular hedefe uzaklıklarına göre sıralanıyor.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Tuple, TYPE_CHECKING
import numpy as np
import math

if TYPE_CHECKING:
    from ..environment.world import World
    from ..environment.node import Node


@dataclass
class NeighborState:
    """
    Bir komşu düğümün durumu

    RL ajanı her komşu için bu bilgileri görür.
    """

    neighbor_id: str
    link_quality: float          # 0-1 arası bağlantı kalitesi
    neighbor_energy: float       # 0-100 arası enerji
    neighbor_queue_length: int   # Kuyruk uzunluğu
    distance_to_current: float   # Mevcut düğüme mesafe
    distance_to_dest: float      # HEDEFE MESAFE (normalize edilmiş)
    is_closer_to_dest: bool      # Hedefe daha mı yakın?
    recent_success_rate: float   # Bu komşu üzerinden son başarı oranı


@dataclass
class RoutingState:
    """
    RL ajanının gördüğü tam durum

    Bir paket için routing kararı verirken kullanılır.
    """

    # Mevcut düğüm bilgileri
    current_node_id: str
    current_node_energy: float
    current_queue_length: int
    current_distance_to_dest: float  # Mevcut düğümün hedefe mesafesi

    # Hedef bilgisi
    destination_id: str

    # Komşu bilgileri (hedefe uzaklığa göre SIRALANMIŞ)
    neighbor_states: List[NeighborState] = field(default_factory=list)

    # En iyi komşu (hedefe en yakın)
    best_neighbor_id: Optional[str] = None
    num_closer_neighbors: int = 0  # Hedefe daha yakın komşu sayısı

    # Geçmiş performans
    recent_success_rate: float = 0.5

    @property
    def num_neighbors(self) -> int:
        """Komşu sayısı"""
        return len(self.neighbor_states)

    @property
    def has_neighbors(self) -> bool:
        """Komşu var mı?"""
        return len(self.neighbor_states) > 0


class StateEncoder:
    """
    State Vector Encoder (Düzeltilmiş)

    Hedefe mesafe bilgisi dahil edildi.
    """

    def __init__(
        self,
        max_neighbors: int = 8,
        energy_bins: int = 5,
        queue_bins: int = 3,
        quality_bins: int = 5,
        distance_bins: int = 5
    ):
        self.max_neighbors = max_neighbors
        self.energy_bins = energy_bins
        self.queue_bins = queue_bins
        self.quality_bins = quality_bins
        self.distance_bins = distance_bins

    def discretize(self, state: RoutingState) -> Tuple:
        """
        State'i discrete tuple'a çevir

        ÖNEMLİ: Hedefe mesafe bilgisi eklendi!
        """
        # Mevcut düğüm
        energy_bin = self._bin_value(state.current_node_energy / 100.0, self.energy_bins)
        queue_bin = self._bin_value(state.current_queue_length / 20.0, self.queue_bins)

        # Komşu özellikleri
        if state.neighbor_states:
            # En iyi komşunun kalitesi
            best_neighbor = state.neighbor_states[0]  # Zaten hedefe en yakına göre sıralı
            best_quality = self._bin_value(best_neighbor.link_quality, self.quality_bins)
            best_energy = self._bin_value(best_neighbor.neighbor_energy / 100.0, self.energy_bins)

            # Hedefe daha yakın komşu var mı?
            has_closer = 1 if state.num_closer_neighbors > 0 else 0

            # Ortalama komşu kalitesi
            avg_quality = sum(n.link_quality for n in state.neighbor_states) / len(state.neighbor_states)
            avg_quality_bin = self._bin_value(avg_quality, self.quality_bins)
        else:
            best_quality = 0
            best_energy = 0
            has_closer = 0
            avg_quality_bin = 0

        num_neighbors = min(len(state.neighbor_states), 5)

        return (
            energy_bin,
            queue_bin,
            best_quality,
            best_energy,
            has_closer,       # KRİTİK: hedefe yakınlık bilgisi
            avg_quality_bin,
            num_neighbors,
        )

    def _bin_value(self, value: float, num_bins: int) -> int:
        """Değeri bin'e çevir"""
        value = max(0.0, min(1.0, value))
        bin_idx = int(value * num_bins)
        return min(bin_idx, num_bins - 1)


class StateBuilder:
    """
    State Builder (Düzeltilmiş)

    Hedefe mesafe hesaplaması eklendi.
    Komşular hedefe uzaklıklarına göre sıralanıyor.
    """

    def __init__(self, world: 'World'):
        self.world = world
        self._neighbor_success: dict = {}  # (node_id, neighbor_id) -> [success, total]

    def build_state(
        self,
        current_node_id: str,
        destination_id: str
    ) -> Optional[RoutingState]:
        """
        State oluştur

        Komşular hedefe olan uzaklıklarına göre SIRALANIR.
        """
        current_node = self.world.get_node(current_node_id)
        destination_node = self.world.get_node(destination_id)

        if current_node is None or not current_node.is_active:
            return None
        if destination_node is None:
            return None

        # Mevcut düğümün hedefe mesafesi
        current_to_dest = self._calculate_distance(
            current_node.position,
            destination_node.position
        )

        # Komşuları al ve hedefe mesafelerini hesapla
        neighbor_ids = self.world.get_neighbors(current_node_id)
        neighbor_states = []

        for neighbor_id in neighbor_ids:
            neighbor = self.world.get_node(neighbor_id)
            if neighbor is None or not neighbor.is_active:
                continue

            link = self.world.get_link(current_node_id, neighbor_id)
            if link is None or not link.is_active:
                continue

            # Komşunun hedefe mesafesi
            neighbor_to_dest = self._calculate_distance(
                neighbor.position,
                destination_node.position
            )

            # Komşu hedefe daha mı yakın?
            is_closer = neighbor_to_dest < current_to_dest

            # Başarı oranı
            key = (current_node_id, neighbor_id)
            if key in self._neighbor_success:
                success, total = self._neighbor_success[key]
                success_rate = success / total if total > 0 else 0.5
            else:
                success_rate = 0.5

            ns = NeighborState(
                neighbor_id=neighbor_id,
                link_quality=link.quality,
                neighbor_energy=neighbor.energy,
                neighbor_queue_length=neighbor.queue_length,
                distance_to_current=link.distance,
                distance_to_dest=neighbor_to_dest,
                is_closer_to_dest=is_closer,
                recent_success_rate=success_rate,
            )
            neighbor_states.append(ns)

        # KRİTİK: Komşuları hedefe uzaklığa göre SIRALA (en yakın önce)
        neighbor_states.sort(key=lambda n: n.distance_to_dest)

        # En iyi komşu ve hedefe yakın komşu sayısı
        best_neighbor_id = neighbor_states[0].neighbor_id if neighbor_states else None
        num_closer = sum(1 for n in neighbor_states if n.is_closer_to_dest)

        # Genel başarı oranı
        total_success = sum(
            self._neighbor_success.get((current_node_id, n), (0, 0))[0]
            for n in neighbor_ids
        )
        total_attempts = sum(
            self._neighbor_success.get((current_node_id, n), (0, 0))[1]
            for n in neighbor_ids
        )
        overall_success = total_success / total_attempts if total_attempts > 0 else 0.5

        return RoutingState(
            current_node_id=current_node_id,
            current_node_energy=current_node.energy,
            current_queue_length=current_node.queue_length,
            current_distance_to_dest=current_to_dest,
            destination_id=destination_id,
            neighbor_states=neighbor_states,
            best_neighbor_id=best_neighbor_id,
            num_closer_neighbors=num_closer,
            recent_success_rate=overall_success,
        )

    def _calculate_distance(self, pos1: Tuple[float, float], pos2: Tuple[float, float]) -> float:
        """İki nokta arası mesafe"""
        dx = pos1[0] - pos2[0]
        dy = pos1[1] - pos2[1]
        return math.sqrt(dx * dx + dy * dy)

    def record_success(self, node_id: str, neighbor_id: str, success: bool):
        """Sonuç kaydet"""
        key = (node_id, neighbor_id)
        if key not in self._neighbor_success:
            self._neighbor_success[key] = [0, 0]

        if success:
            self._neighbor_success[key][0] += 1
        self._neighbor_success[key][1] += 1

        # Sliding window
        if self._neighbor_success[key][1] > 100:
            self._neighbor_success[key][0] = int(self._neighbor_success[key][0] * 0.9)
            self._neighbor_success[key][1] = int(self._neighbor_success[key][1] * 0.9)

    def reset(self):
        """Sıfırla"""
        self._neighbor_success.clear()
