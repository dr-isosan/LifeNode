"""
Node (Düğüm) Modeli

Mesh ağındaki her bir düğümü temsil eder.
Düğümler hareket edebilir, enerji tüketebilir ve arızalanabilir.
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import List, Optional, Tuple, TYPE_CHECKING
import math
import random

if TYPE_CHECKING:
    from .packet import Packet


class NodeState(Enum):
    """Düğüm durumları"""
    ACTIVE = auto()      # Çalışıyor
    LOW_ENERGY = auto()  # Düşük enerji (<%20)
    FAILED = auto()      # Arızalı
    RECOVERING = auto()  # Kurtarılıyor


@dataclass
class Node:
    """
    Mesh ağ düğümü

    Attributes:
        id: Benzersiz düğüm kimliği
        position: (x, y) koordinatları (metre)
        energy: Mevcut enerji seviyesi (0-100)
        transmission_range: İletim menzili (metre)
        max_queue_size: Maksimum kuyruk boyutu
    """

    id: str
    position: Tuple[float, float]
    energy: float = 100.0
    transmission_range: float = 75.0
    max_queue_size: int = 50

    # Dahili durum
    state: NodeState = field(default=NodeState.ACTIVE)
    queue: List['Packet'] = field(default_factory=list)

    # Hareket parametreleri
    velocity: Tuple[float, float] = field(default=(0.0, 0.0))
    max_speed: float = 2.0

    # İstatistikler
    packets_sent: int = 0
    packets_received: int = 0
    packets_dropped: int = 0
    packets_forwarded: int = 0

    # Enerji tüketim sabitleri
    energy_per_transmit: float = 0.1
    energy_per_receive: float = 0.05
    energy_per_idle: float = 0.001

    def __post_init__(self):
        """Başlangıç durumu kontrolü"""
        self._update_state()

    # =========================================================================
    # KONUM VE MENZIL
    # =========================================================================

    def distance_to(self, other: 'Node') -> float:
        """
        Başka bir düğüme olan mesafeyi hesapla

        Args:
            other: Hedef düğüm

        Returns:
            Öklid mesafesi (metre)
        """
        dx = self.position[0] - other.position[0]
        dy = self.position[1] - other.position[1]
        return math.sqrt(dx * dx + dy * dy)

    def can_reach(self, other: 'Node') -> bool:
        """
        Başka bir düğüme ulaşılabilir mi?

        Args:
            other: Hedef düğüm

        Returns:
            True eğer menzil içindeyse ve her iki düğüm de aktifse
        """
        if not self.is_active or not other.is_active:
            return False
        return self.distance_to(other) <= self.transmission_range

    def move(self, bounds: Tuple[float, float], dt: float = 1.0):
        """
        Düğümü hareket ettir (random waypoint modeli)

        Args:
            bounds: (genişlik, yükseklik) sınırları
            dt: Zaman adımı
        """
        if not self.is_active:
            return

        # Yeni pozisyon hesapla
        new_x = self.position[0] + self.velocity[0] * dt
        new_y = self.position[1] + self.velocity[1] * dt

        # Sınırları kontrol et (bounce)
        if new_x < 0 or new_x > bounds[0]:
            self.velocity = (-self.velocity[0], self.velocity[1])
            new_x = max(0, min(bounds[0], new_x))

        if new_y < 0 or new_y > bounds[1]:
            self.velocity = (self.velocity[0], -self.velocity[1])
            new_y = max(0, min(bounds[1], new_y))

        self.position = (new_x, new_y)

    def set_random_velocity(self):
        """Rastgele hız ata"""
        speed = random.uniform(0, self.max_speed)
        angle = random.uniform(0, 2 * math.pi)
        self.velocity = (speed * math.cos(angle), speed * math.sin(angle))

    # =========================================================================
    # ENERJİ YÖNETİMİ
    # =========================================================================

    def consume_energy(self, amount: float):
        """
        Enerji tüket

        Args:
            amount: Tüketilecek enerji miktarı
        """
        self.energy = max(0.0, self.energy - amount)
        self._update_state()

    def consume_transmit_energy(self):
        """Paket gönderimi için enerji tüket"""
        self.consume_energy(self.energy_per_transmit)

    def consume_receive_energy(self):
        """Paket alımı için enerji tüket"""
        self.consume_energy(self.energy_per_receive)

    def consume_idle_energy(self):
        """Boşta bekleme için enerji tüket"""
        self.consume_energy(self.energy_per_idle)

    def recharge(self, amount: float):
        """
        Enerji şarj et (kurtarma senaryosu)

        Args:
            amount: Şarj miktarı
        """
        self.energy = min(100.0, self.energy + amount)
        self._update_state()

    @property
    def energy_ratio(self) -> float:
        """Enerji oranı (0-1)"""
        return self.energy / 100.0

    # =========================================================================
    # KUYRUK YÖNETİMİ
    # =========================================================================

    def enqueue_packet(self, packet: 'Packet') -> bool:
        """
        Paketi kuyruğa ekle

        Args:
            packet: Eklenecek paket

        Returns:
            True eğer başarıyla eklendiyse, False eğer kuyruk doluysa
        """
        if len(self.queue) >= self.max_queue_size:
            self.packets_dropped += 1
            return False

        self.queue.append(packet)
        return True

    def dequeue_packet(self) -> Optional['Packet']:
        """
        Kuyruktan paket al (FIFO)

        Returns:
            İlk paket veya None
        """
        if self.queue:
            return self.queue.pop(0)
        return None

    @property
    def queue_length(self) -> int:
        """Kuyruk uzunluğu"""
        return len(self.queue)

    @property
    def queue_fullness(self) -> float:
        """Kuyruk doluluk oranı (0-1)"""
        return len(self.queue) / self.max_queue_size

    # =========================================================================
    # DURUM YÖNETİMİ
    # =========================================================================

    def _update_state(self):
        """Enerji seviyesine göre durumu güncelle"""
        if self.state == NodeState.FAILED:
            return  # Arızalı düğüm kendini düzeltemez

        if self.energy <= 0:
            self.state = NodeState.FAILED
        elif self.energy < 20:
            self.state = NodeState.LOW_ENERGY
        else:
            self.state = NodeState.ACTIVE

    @property
    def is_active(self) -> bool:
        """Düğüm aktif mi?"""
        return self.state in (NodeState.ACTIVE, NodeState.LOW_ENERGY)

    def fail(self):
        """Düğümü arızalı olarak işaretle"""
        self.state = NodeState.FAILED
        self.queue.clear()

    def recover(self, energy: float = 50.0):
        """
        Düğümü kurtar

        Args:
            energy: Kurtarma sonrası enerji seviyesi
        """
        self.state = NodeState.RECOVERING
        self.energy = energy
        self._update_state()

    # =========================================================================
    # İSTATİSTİKLER
    # =========================================================================

    def record_sent(self):
        """Gönderilen paket sayacını artır"""
        self.packets_sent += 1

    def record_received(self):
        """Alınan paket sayacını artır"""
        self.packets_received += 1

    def record_forwarded(self):
        """İletilen paket sayacını artır"""
        self.packets_forwarded += 1

    def reset_stats(self):
        """İstatistikleri sıfırla"""
        self.packets_sent = 0
        self.packets_received = 0
        self.packets_dropped = 0
        self.packets_forwarded = 0

    # =========================================================================
    # YARDIMCI METODLAR
    # =========================================================================

    def __repr__(self) -> str:
        return (
            f"Node(id={self.id}, pos=({self.position[0]:.1f}, {self.position[1]:.1f}), "
            f"energy={self.energy:.1f}, state={self.state.name}, queue={self.queue_length})"
        )

    def to_dict(self) -> dict:
        """Düğümü sözlük olarak döndür (serileştirme için)"""
        return {
            'id': self.id,
            'position': self.position,
            'energy': self.energy,
            'state': self.state.name,
            'queue_length': self.queue_length,
            'packets_sent': self.packets_sent,
            'packets_received': self.packets_received,
            'packets_dropped': self.packets_dropped,
        }
