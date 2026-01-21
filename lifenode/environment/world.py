"""
World (Dünya) - Simülasyon Ortamı

Ana simülasyon motorunu içerir.
Düğümler, bağlantılar ve paketleri yönetir.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Set, TYPE_CHECKING
import random
import math

import networkx as nx

from .node import Node, NodeState
from .link import Link
from .packet import Packet, PacketStatus, PacketResult
from .traffic import TrafficGenerator, TrafficPattern
from ..config import SimulationConfig, DEFAULT_CONFIG

if TYPE_CHECKING:
    from ..routing.base import Router


@dataclass
class StepResult:
    """Bir simülasyon adımının sonuçları"""

    step: int
    packets_sent: int = 0
    packets_delivered: int = 0
    packets_dropped: int = 0
    active_nodes: int = 0
    active_links: int = 0

    # Detaylı sonuçlar
    delivered_packets: List[PacketResult] = field(default_factory=list)
    dropped_packets: List[PacketResult] = field(default_factory=list)


class World:
    """
    Simülasyon Dünyası

    Tüm ağ bileşenlerini ve simülasyon döngüsünü yönetir.

    Attributes:
        config: Simülasyon yapılandırması
        nodes: Düğüm sözlüğü (id -> Node)
        links: Bağlantı sözlüğü ((id_a, id_b) -> Link)
        current_step: Mevcut simülasyon adımı
    """

    def __init__(
        self,
        config: Optional[SimulationConfig] = None,
        seed: Optional[int] = None
    ):
        """
        Args:
            config: Simülasyon yapılandırması
            seed: Rastgelelik tohumu
        """
        self.config = config or DEFAULT_CONFIG

        # Rastgelelik
        self._seed = seed or self.config.world.seed
        if self._seed is not None:
            random.seed(self._seed)

        # Ana veri yapıları
        self.nodes: Dict[str, Node] = {}
        self.links: Dict[Tuple[str, str], Link] = {}

        # Aktif paketler
        self.packets_in_flight: List[Packet] = []
        self.completed_packets: List[Packet] = []

        # Zaman
        self.current_step: int = 0

        # Trafik üreteci
        self.traffic_generator = TrafficGenerator(
            pattern=TrafficPattern(
                packets_per_step=self.config.traffic.packets_per_step,
                min_size=self.config.traffic.min_packet_size,
                max_size=self.config.traffic.max_packet_size,
            ),
            seed=self._seed
        )

        # Router (dışarıdan atanır)
        self.router: Optional['Router'] = None

        # İstatistikler
        self._stats = {
            'total_packets_sent': 0,
            'total_packets_delivered': 0,
            'total_packets_dropped': 0,
        }

    # =========================================================================
    # DÜĞÜM YÖNETİMİ
    # =========================================================================

    def add_node(self, node: Node):
        """
        Düğüm ekle

        Args:
            node: Eklenecek düğüm
        """
        self.nodes[node.id] = node
        self._update_links_for_node(node)

    def remove_node(self, node_id: str):
        """
        Düğüm kaldır

        Args:
            node_id: Kaldırılacak düğüm ID'si
        """
        if node_id not in self.nodes:
            return

        # Bağlı linkleri kaldır
        links_to_remove = [
            key for key in self.links.keys()
            if node_id in key
        ]
        for key in links_to_remove:
            del self.links[key]

        del self.nodes[node_id]

    def get_node(self, node_id: str) -> Optional[Node]:
        """Düğümü ID ile getir"""
        return self.nodes.get(node_id)

    def get_active_nodes(self) -> List[Node]:
        """Aktif düğümleri döndür"""
        return [n for n in self.nodes.values() if n.is_active]

    def get_node_ids(self) -> List[str]:
        """Tüm düğüm ID'lerini döndür"""
        return list(self.nodes.keys())

    # =========================================================================
    # BAĞLANTI YÖNETİMİ
    # =========================================================================

    def _get_link_key(self, node_a: str, node_b: str) -> Tuple[str, str]:
        """Sıralı link anahtarı oluştur"""
        return (node_a, node_b) if node_a < node_b else (node_b, node_a)

    def _update_links_for_node(self, node: Node):
        """
        Bir düğüm için bağlantıları güncelle

        Args:
            node: Bağlantıları güncellenecek düğüm
        """
        for other_id, other in self.nodes.items():
            if other_id == node.id:
                continue

            distance = node.distance_to(other)
            key = self._get_link_key(node.id, other_id)

            # Menzil içinde mi?
            if distance <= node.transmission_range and distance <= other.transmission_range:
                if key not in self.links:
                    # Yeni bağlantı oluştur
                    self.links[key] = Link(
                        node_a=key[0],
                        node_b=key[1],
                        distance=distance,
                        path_loss_exponent=self.config.link.path_loss_exponent,
                        reference_loss_db=self.config.link.reference_loss_db,
                        noise_floor_dbm=self.config.link.noise_floor_dbm,
                        min_snr_db=self.config.link.min_snr_db,
                        base_latency_ms=self.config.link.base_latency_ms,
                        base_packet_loss_rate=self.config.link.base_packet_loss_rate,
                    )
                else:
                    # Mevcut bağlantıyı güncelle
                    self.links[key].update_distance(distance)
            else:
                # Menzil dışında, bağlantıyı kaldır
                if key in self.links:
                    del self.links[key]

    def update_all_links(self):
        """Tüm bağlantıları güncelle (düğüm hareketi sonrası)"""
        # Önce tüm linkleri temizle
        self.links.clear()

        # Yeniden oluştur
        node_list = list(self.nodes.values())
        for i, node_a in enumerate(node_list):
            for node_b in node_list[i + 1:]:
                if not node_a.is_active or not node_b.is_active:
                    continue

                distance = node_a.distance_to(node_b)

                if distance <= node_a.transmission_range and distance <= node_b.transmission_range:
                    key = self._get_link_key(node_a.id, node_b.id)
                    self.links[key] = Link(
                        node_a=key[0],
                        node_b=key[1],
                        distance=distance,
                        path_loss_exponent=self.config.link.path_loss_exponent,
                        reference_loss_db=self.config.link.reference_loss_db,
                        noise_floor_dbm=self.config.link.noise_floor_dbm,
                        min_snr_db=self.config.link.min_snr_db,
                        base_latency_ms=self.config.link.base_latency_ms,
                        base_packet_loss_rate=self.config.link.base_packet_loss_rate,
                    )

    def get_link(self, node_a: str, node_b: str) -> Optional[Link]:
        """İki düğüm arasındaki bağlantıyı getir"""
        key = self._get_link_key(node_a, node_b)
        return self.links.get(key)

    def get_active_links(self) -> List[Link]:
        """Aktif bağlantıları döndür"""
        return [l for l in self.links.values() if l.is_active]

    # =========================================================================
    # KOMŞULUK
    # =========================================================================

    def get_neighbors(self, node_id: str) -> List[str]:
        """
        Bir düğümün aktif komşularını döndür

        Args:
            node_id: Düğüm ID'si

        Returns:
            Komşu ID'leri listesi
        """
        neighbors = []

        for key, link in self.links.items():
            if not link.is_active:
                continue

            if key[0] == node_id:
                neighbor_id = key[1]
            elif key[1] == node_id:
                neighbor_id = key[0]
            else:
                continue

            # Komşu aktif mi?
            neighbor = self.nodes.get(neighbor_id)
            if neighbor and neighbor.is_active:
                neighbors.append(neighbor_id)

        return neighbors

    def get_neighbor_link_quality(self, node_id: str, neighbor_id: str) -> float:
        """İki düğüm arasındaki link kalitesini döndür"""
        link = self.get_link(node_id, neighbor_id)
        if link and link.is_active:
            return link.quality
        return 0.0

    # =========================================================================
    # NETWORKX ENTEGRASYONU
    # =========================================================================

    def get_topology_graph(self) -> nx.Graph:
        """
        Ağ topolojisini NetworkX graph olarak döndür

        Returns:
            NetworkX Graph nesnesi
        """
        G = nx.Graph()

        # Aktif düğümleri ekle
        for node_id, node in self.nodes.items():
            if node.is_active:
                G.add_node(
                    node_id,
                    pos=node.position,
                    energy=node.energy,
                    queue_length=node.queue_length,
                )

        # Aktif bağlantıları ekle
        for (node_a, node_b), link in self.links.items():
            if link.is_active and node_a in G.nodes and node_b in G.nodes:
                G.add_edge(
                    node_a, node_b,
                    weight=1.0 / link.quality if link.quality > 0 else float('inf'),
                    distance=link.distance,
                    quality=link.quality,
                    latency=link.latency,
                )

        return G

    # =========================================================================
    # SİMÜLASYON DÖNGÜSÜ
    # =========================================================================

    def step(self) -> StepResult:
        """
        Bir simülasyon adımı çalıştır

        Returns:
            Adım sonuçları
        """
        result = StepResult(step=self.current_step)

        # 1. Düğüm güncellemeleri
        self._update_nodes()

        # 2. Hareket (eğer etkinse)
        if self.config.node.mobility_enabled:
            self._move_nodes()
            self.update_all_links()

        # 3. Yeni trafik üret
        new_packets = self.traffic_generator.generate(
            self.current_step,
            self.get_active_nodes()
        )
        for packet in new_packets:
            packet.send(self.current_step)
            self.packets_in_flight.append(packet)
            result.packets_sent += 1
            self._stats['total_packets_sent'] += 1

        # 4. Paketleri ilet
        self._process_packets(result)

        # 5. Aktif sayıları hesapla
        result.active_nodes = len(self.get_active_nodes())
        result.active_links = len(self.get_active_links())

        # 6. Adımı artır
        self.current_step += 1

        return result

    def _update_nodes(self):
        """Düğüm durumlarını güncelle"""
        for node in self.nodes.values():
            if node.is_active:
                node.consume_idle_energy()

    def _move_nodes(self):
        """Düğümleri hareket ettir"""
        bounds = (self.config.world.width, self.config.world.height)
        for node in self.nodes.values():
            if node.is_active:
                node.move(bounds)

    def _process_packets(self, result: StepResult):
        """
        Paketleri işle ve ilet

        Args:
            result: Adım sonuç nesnesi (güncellenir)
        """
        if self.router is None:
            return

        remaining_packets = []

        for packet in self.packets_in_flight:
            # TTL kontrolü
            if packet.ttl <= 0:
                packet.drop("TTL expired")
                result.dropped_packets.append(PacketResult.from_packet(packet))
                result.packets_dropped += 1
                self._stats['total_packets_dropped'] += 1
                self.completed_packets.append(packet)
                continue

            current_node_id = packet.current_node
            current_node = self.nodes.get(current_node_id)

            # Düğüm aktif mi?
            if not current_node or not current_node.is_active:
                packet.drop("Node failed")
                result.dropped_packets.append(PacketResult.from_packet(packet))
                result.packets_dropped += 1
                self._stats['total_packets_dropped'] += 1
                self.completed_packets.append(packet)
                continue

            # Hedefe ulaştı mı?
            if current_node_id == packet.destination:
                packet.deliver(self.current_step)
                current_node.record_received()
                result.delivered_packets.append(PacketResult.from_packet(packet))
                result.packets_delivered += 1
                self._stats['total_packets_delivered'] += 1
                self.completed_packets.append(packet)

                # Router'a bildir
                self.router.on_packet_delivered(packet)
                continue

            # Sonraki hop'u belirle
            next_hop = self.router.get_next_hop(
                current_node=current_node_id,
                destination=packet.destination,
                world=self
            )

            if next_hop is None:
                # Rota bulunamadı
                packet.drop("No route")
                result.dropped_packets.append(PacketResult.from_packet(packet))
                result.packets_dropped += 1
                self._stats['total_packets_dropped'] += 1
                self.completed_packets.append(packet)

                # Router'a bildir
                self.router.on_packet_dropped(packet)
                continue

            # Bağlantı kontrolü
            link = self.get_link(current_node_id, next_hop)
            if not link or not link.is_active:
                packet.drop("Link down")
                result.dropped_packets.append(PacketResult.from_packet(packet))
                result.packets_dropped += 1
                self._stats['total_packets_dropped'] += 1
                self.completed_packets.append(packet)

                # Router'a bildir
                self.router.on_packet_dropped(packet)
                continue

            # İletim simülasyonu
            if link.attempt_transmission():
                # Başarılı iletim
                packet.forward(next_hop, link.latency)
                current_node.consume_transmit_energy()
                current_node.record_forwarded()

                next_node = self.nodes.get(next_hop)
                if next_node:
                    next_node.consume_receive_energy()

                # Router'a bildir
                self.router.on_packet_forwarded(packet, next_hop)

                remaining_packets.append(packet)
            else:
                # İletim başarısız
                packet.drop("Transmission failed")
                result.dropped_packets.append(PacketResult.from_packet(packet))
                result.packets_dropped += 1
                self._stats['total_packets_dropped'] += 1
                self.completed_packets.append(packet)

                # Router'a bildir
                self.router.on_packet_dropped(packet)

        self.packets_in_flight = remaining_packets

    # =========================================================================
    # BAŞLATMA
    # =========================================================================

    def initialize_random_nodes(
        self,
        count: Optional[int] = None,
        seed: Optional[int] = None
    ):
        """
        Rastgele düğümler oluştur

        Args:
            count: Düğüm sayısı
            seed: Rastgelelik tohumu
        """
        if seed is not None:
            random.seed(seed)

        count = count or self.config.world.initial_node_count

        for i in range(count):
            x = random.uniform(0, self.config.world.width)
            y = random.uniform(0, self.config.world.height)

            node = Node(
                id=f"N{i:03d}",
                position=(x, y),
                energy=self.config.node.initial_energy,
                transmission_range=self.config.node.transmission_range,
                max_queue_size=self.config.node.max_queue_size,
                max_speed=self.config.node.max_speed,
            )

            if self.config.node.mobility_enabled:
                node.set_random_velocity()

            self.add_node(node)

    def set_router(self, router: 'Router'):
        """
        Router ata

        Args:
            router: Kullanılacak yönlendirici
        """
        self.router = router

    def reset(self):
        """Simülasyonu sıfırla"""
        self.nodes.clear()
        self.links.clear()
        self.packets_in_flight.clear()
        self.completed_packets.clear()
        self.current_step = 0
        self.traffic_generator.reset()
        self._stats = {
            'total_packets_sent': 0,
            'total_packets_delivered': 0,
            'total_packets_dropped': 0,
        }

        if self._seed is not None:
            random.seed(self._seed)

    # =========================================================================
    # İSTATİSTİKLER
    # =========================================================================

    def get_stats(self) -> dict:
        """Simülasyon istatistiklerini döndür"""
        pdr = 0.0
        if self._stats['total_packets_sent'] > 0:
            pdr = self._stats['total_packets_delivered'] / self._stats['total_packets_sent']

        avg_latency = 0.0
        delivered_count = 0
        for packet in self.completed_packets:
            if packet.is_delivered and packet.end_to_end_latency is not None:
                avg_latency += packet.end_to_end_latency
                delivered_count += 1
        if delivered_count > 0:
            avg_latency /= delivered_count

        return {
            'current_step': self.current_step,
            'total_nodes': len(self.nodes),
            'active_nodes': len(self.get_active_nodes()),
            'total_links': len(self.links),
            'active_links': len(self.get_active_links()),
            'packets_sent': self._stats['total_packets_sent'],
            'packets_delivered': self._stats['total_packets_delivered'],
            'packets_dropped': self._stats['total_packets_dropped'],
            'packets_in_flight': len(self.packets_in_flight),
            'packet_delivery_ratio': pdr,
            'average_latency_ms': avg_latency,
        }

    def __repr__(self) -> str:
        stats = self.get_stats()
        return (
            f"World(step={stats['current_step']}, "
            f"nodes={stats['active_nodes']}/{stats['total_nodes']}, "
            f"links={stats['active_links']}, "
            f"PDR={stats['packet_delivery_ratio']:.2%})"
        )
