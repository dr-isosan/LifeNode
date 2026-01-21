"""
Router Base Class (Soyut Yönlendirici Arayüzü)

Tüm routing protokolleri bu arayüzü uygulamalıdır.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional, List, TYPE_CHECKING

if TYPE_CHECKING:
    from ..environment.world import World
    from ..environment.packet import Packet


class TopologyEventType(Enum):
    """Topoloji olay türleri"""
    NODE_ADDED = auto()
    NODE_REMOVED = auto()
    NODE_FAILED = auto()
    NODE_RECOVERED = auto()
    LINK_UP = auto()
    LINK_DOWN = auto()
    LINK_QUALITY_CHANGED = auto()


@dataclass
class TopologyEvent:
    """Topoloji değişiklik olayı"""
    event_type: TopologyEventType
    node_id: Optional[str] = None
    node_id_2: Optional[str] = None  # Link olayları için
    details: Optional[dict] = None


class Router(ABC):
    """
    Soyut Router Arayüzü

    Tüm yönlendirme protokollerinin uyması gereken arayüz.
    Her router bu metodları uygulamalıdır.
    """

    @abstractmethod
    def get_next_hop(
        self,
        current_node: str,
        destination: str,
        world: 'World'
    ) -> Optional[str]:
        """
        Sonraki hop düğümünü belirle

        Bu metod, bir paketin hangi komşuya iletileceğine karar verir.

        Args:
            current_node: Mevcut düğüm ID'si
            destination: Hedef düğüm ID'si
            world: Simülasyon dünyası (topoloji bilgisi için)

        Returns:
            Sonraki hop düğüm ID'si veya None (rota bulunamazsa)
        """
        pass

    @abstractmethod
    def get_name(self) -> str:
        """
        Protokol adını döndür

        Returns:
            Protokol adı (örn: "Dijkstra", "AODV", "RL-Q")
        """
        pass

    # =========================================================================
    # OLAY BİLDİRİMLERİ (Opsiyonel - varsayılan boş implementasyon)
    # =========================================================================

    def on_packet_forwarded(self, packet: 'Packet', next_hop: str):
        """
        Paket başarıyla iletildiğinde çağrılır

        Args:
            packet: İletilen paket
            next_hop: Paketin iletildiği düğüm
        """
        pass

    def on_packet_delivered(self, packet: 'Packet'):
        """
        Paket hedefe ulaştığında çağrılır

        Args:
            packet: Teslim edilen paket
        """
        pass

    def on_packet_dropped(self, packet: 'Packet'):
        """
        Paket düşürüldüğünde çağrılır

        Args:
            packet: Düşürülen paket
        """
        pass

    def on_topology_change(self, event: TopologyEvent):
        """
        Topoloji değiştiğinde çağrılır

        Args:
            event: Topoloji olayı
        """
        pass

    def reset(self):
        """
        Router durumunu sıfırla

        Cache, routing table vb. temizlenir.
        """
        pass

    # =========================================================================
    # EĞİTİM DESTEĞİ (RL için)
    # =========================================================================

    def is_trainable(self) -> bool:
        """
        Bu router eğitilebilir mi? (RL için)

        Returns:
            True eğer RL destekliyorsa
        """
        return False

    def train_step(self):
        """
        Bir eğitim adımı çalıştır (RL için)

        Sadece is_trainable() True dönen router'lar için geçerli.
        """
        pass

    def save_model(self, path: str):
        """
        Modeli kaydet (RL için)

        Args:
            path: Kayıt yolu
        """
        pass

    def load_model(self, path: str):
        """
        Modeli yükle (RL için)

        Args:
            path: Yükleme yolu
        """
        pass

    # =========================================================================
    # İSTATİSTİKLER
    # =========================================================================

    def get_stats(self) -> dict:
        """
        Router istatistiklerini döndür

        Returns:
            İstatistik sözlüğü
        """
        return {
            'name': self.get_name(),
            'trainable': self.is_trainable(),
        }

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.get_name()})"
