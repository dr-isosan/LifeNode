"""
Packet (Paket) Modeli

Ağda iletilen veri paketlerini temsil eder.
Her paket kaynak, hedef, TTL ve zaman damgası içerir.
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import List, Optional
import time
import uuid


class PacketStatus(Enum):
    """Paket durumları"""
    CREATED = auto()     # Oluşturuldu
    IN_QUEUE = auto()    # Kuyrukta bekliyor
    IN_TRANSIT = auto()  # İletimde
    DELIVERED = auto()   # Teslim edildi
    DROPPED = auto()     # Düşürüldü (kayıp)
    EXPIRED = auto()     # TTL doldu


@dataclass
class Packet:
    """
    Ağ paketi

    Attributes:
        id: Benzersiz paket kimliği
        source: Kaynak düğüm ID'si
        destination: Hedef düğüm ID'si
        size: Paket boyutu (byte)
        ttl: Time To Live (maksimum hop sayısı)
        created_at: Oluşturulma zamanı (simülasyon adımı)
        priority: Öncelik (0-10, yüksek = daha öncelikli)
    """

    source: str
    destination: str
    size: int = 1024
    ttl: int = 64
    created_at: int = 0
    priority: int = 5

    # Otomatik oluşturulan alanlar
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    status: PacketStatus = field(default=PacketStatus.CREATED)

    # Yolculuk geçmişi
    path: List[str] = field(default_factory=list)
    hop_count: int = 0

    # Zaman takibi
    sent_at: Optional[int] = None
    delivered_at: Optional[int] = None

    # Gecikme birikimi
    accumulated_latency: float = 0.0

    def __post_init__(self):
        """Başlangıç ayarları"""
        if not self.path:
            self.path = [self.source]

    # =========================================================================
    # PAKET YAŞAM DÖNGÜSÜ
    # =========================================================================

    def send(self, current_step: int):
        """
        Paketi gönder

        Args:
            current_step: Mevcut simülasyon adımı
        """
        self.sent_at = current_step
        self.status = PacketStatus.IN_TRANSIT

    def forward(self, next_hop: str, latency: float):
        """
        Paketi bir sonraki düğüme ilet

        Args:
            next_hop: Sonraki düğüm ID'si
            latency: Bu hop'un gecikmesi (ms)
        """
        self.path.append(next_hop)
        self.hop_count += 1
        self.ttl -= 1
        self.accumulated_latency += latency

        if self.ttl <= 0:
            self.status = PacketStatus.EXPIRED

    def deliver(self, current_step: int):
        """
        Paketi teslim et

        Args:
            current_step: Mevcut simülasyon adımı
        """
        self.delivered_at = current_step
        self.status = PacketStatus.DELIVERED

    def drop(self, reason: str = "unknown"):
        """
        Paketi düşür

        Args:
            reason: Düşürme nedeni
        """
        self.status = PacketStatus.DROPPED
        self._drop_reason = reason

    def queue(self):
        """Paketi kuyruğa ekle"""
        self.status = PacketStatus.IN_QUEUE

    # =========================================================================
    # DURUM KONTROL
    # =========================================================================

    @property
    def is_alive(self) -> bool:
        """Paket hala aktif mi? (iletimde veya kuyrukta)"""
        return self.status in (PacketStatus.IN_QUEUE, PacketStatus.IN_TRANSIT)

    @property
    def is_delivered(self) -> bool:
        """Paket teslim edildi mi?"""
        return self.status == PacketStatus.DELIVERED

    @property
    def is_failed(self) -> bool:
        """Paket başarısız mı? (düşürüldü veya süresi doldu)"""
        return self.status in (PacketStatus.DROPPED, PacketStatus.EXPIRED)

    @property
    def current_node(self) -> str:
        """Paketin şu an bulunduğu düğüm"""
        return self.path[-1] if self.path else self.source

    # =========================================================================
    # METRİKLER
    # =========================================================================

    @property
    def end_to_end_latency(self) -> Optional[float]:
        """
        Uçtan uca gecikme (ms)

        Returns:
            Toplam gecikme veya None (henüz teslim edilmediyse)
        """
        if self.status != PacketStatus.DELIVERED:
            return None
        return self.accumulated_latency

    @property
    def delivery_time_steps(self) -> Optional[int]:
        """
        Teslim süresi (simülasyon adımı)

        Returns:
            Adım sayısı veya None
        """
        if self.sent_at is None or self.delivered_at is None:
            return None
        return self.delivered_at - self.sent_at

    @property
    def route_length(self) -> int:
        """Kat edilen yol uzunluğu (hop sayısı)"""
        return len(self.path) - 1  # Kaynak hariç

    # =========================================================================
    # YARDIMCI METODLAR
    # =========================================================================

    def visited(self, node_id: str) -> bool:
        """Paket bu düğümü ziyaret etti mi?"""
        return node_id in self.path

    def clone(self) -> 'Packet':
        """Paketin bir kopyasını oluştur"""
        return Packet(
            source=self.source,
            destination=self.destination,
            size=self.size,
            ttl=self.ttl,
            created_at=self.created_at,
            priority=self.priority,
        )

    def __repr__(self) -> str:
        return (
            f"Packet(id={self.id}, {self.source}->{self.destination}, "
            f"status={self.status.name}, hops={self.hop_count}, ttl={self.ttl})"
        )

    def to_dict(self) -> dict:
        """Paketi sözlük olarak döndür"""
        return {
            'id': self.id,
            'source': self.source,
            'destination': self.destination,
            'size': self.size,
            'status': self.status.name,
            'hop_count': self.hop_count,
            'ttl': self.ttl,
            'path': self.path.copy(),
            'latency': self.accumulated_latency,
            'created_at': self.created_at,
            'delivered_at': self.delivered_at,
        }


@dataclass
class PacketResult:
    """
    Paket iletim sonucu

    Analiz ve metriklerde kullanılır.
    """

    packet_id: str
    source: str
    destination: str
    success: bool
    hop_count: int
    latency: float
    path: List[str]
    status: PacketStatus

    @classmethod
    def from_packet(cls, packet: Packet) -> 'PacketResult':
        """Paketten sonuç nesnesi oluştur"""
        return cls(
            packet_id=packet.id,
            source=packet.source,
            destination=packet.destination,
            success=packet.is_delivered,
            hop_count=packet.hop_count,
            latency=packet.accumulated_latency,
            path=packet.path.copy(),
            status=packet.status,
        )
