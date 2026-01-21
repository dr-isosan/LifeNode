"""
AODV Router (Ad-hoc On-Demand Distance Vector)

Reaktif (on-demand) routing protokolü.
Sadece ihtiyaç duyulduğunda rota keşfi yapar.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, TYPE_CHECKING
from collections import defaultdict
import time

from .base import Router, TopologyEvent, TopologyEventType

if TYPE_CHECKING:
    from ..environment.world import World
    from ..environment.packet import Packet


@dataclass
class RouteEntry:
    """AODV routing table entry"""
    destination: str
    next_hop: str
    hop_count: int
    sequence_number: int
    lifetime: float  # saniye
    is_valid: bool = True
    created_at: float = field(default_factory=time.time)

    def is_expired(self) -> bool:
        """Rota süresi dolmuş mu?"""
        return (time.time() - self.created_at) > self.lifetime


class AODVRouter(Router):
    """
    AODV (Ad-hoc On-Demand Distance Vector) Router

    Basitleştirilmiş AODV implementasyonu:
    - Route Request (RREQ) flood ile rota keşfi
    - Route Reply (RREP) ile rota onayı
    - Sequence number ile rota güncelliği
    - Route timeout ile eski rotaları temizleme
    """

    def __init__(
        self,
        route_lifetime: float = 10.0,  # saniye
        rreq_retries: int = 3
    ):
        """
        Args:
            route_lifetime: Rota geçerlilik süresi (saniye)
            rreq_retries: RREQ tekrar deneme sayısı
        """
        self.route_lifetime = route_lifetime
        self.rreq_retries = rreq_retries

        # Routing table: destination -> RouteEntry
        self.routing_table: Dict[str, RouteEntry] = {}

        # Sequence numbers
        self.sequence_number: int = 0
        self.dest_sequence_numbers: Dict[str, int] = defaultdict(int)

        # RREQ tracking
        self._rreq_id: int = 0
        self._seen_rreqs: Set[tuple] = set()  # (source, rreq_id)

        # İstatistikler
        self._route_discoveries: int = 0
        self._route_failures: int = 0
        self._cache_hits: int = 0

    def get_name(self) -> str:
        return "AODV"

    def get_next_hop(
        self,
        current_node: str,
        destination: str,
        world: 'World'
    ) -> Optional[str]:
        """
        AODV ile sonraki hop'u bul

        Önce routing table kontrol edilir.
        Rota yoksa veya geçersizse, rota keşfi başlatılır.
        """
        if current_node == destination:
            return None

        # Routing table kontrol
        route = self.routing_table.get(destination)

        if route and route.is_valid and not route.is_expired():
            # Geçerli rota var
            self._cache_hits += 1

            # Next hop hala erişilebilir mi?
            neighbors = world.get_neighbors(current_node)
            if route.next_hop in neighbors:
                return route.next_hop
            else:
                # Rota kırıldı
                route.is_valid = False

        # Rota keşfi gerekli
        new_route = self._discover_route(current_node, destination, world)

        if new_route:
            self._route_discoveries += 1
            self.routing_table[destination] = new_route
            return new_route.next_hop
        else:
            self._route_failures += 1
            return None

    def _discover_route(
        self,
        source: str,
        destination: str,
        world: 'World'
    ) -> Optional[RouteEntry]:
        """
        BFS ile rota keşfi (RREQ/RREP simülasyonu)

        Gerçek AODV'de mesaj flood yapılır.
        Burada simülasyon için BFS kullanıyoruz.
        """
        # BFS ile en kısa yol bul
        visited = {source}
        queue = [(source, [source])]
        parent = {source: None}

        while queue:
            current, path = queue.pop(0)

            if current == destination:
                # Rota bulundu
                if len(path) < 2:
                    return None

                self.sequence_number += 1
                return RouteEntry(
                    destination=destination,
                    next_hop=path[1],
                    hop_count=len(path) - 1,
                    sequence_number=self.sequence_number,
                    lifetime=self.route_lifetime,
                )

            # Komşuları keşfet
            neighbors = world.get_neighbors(current)
            for neighbor in neighbors:
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))

        return None

    def on_packet_forwarded(self, packet: 'Packet', next_hop: str):
        """Paket iletildi - rota kullanılıyor"""
        # Rota lifetime'ını yenile
        dest = packet.destination
        if dest in self.routing_table:
            self.routing_table[dest].created_at = time.time()

    def on_packet_dropped(self, packet: 'Packet'):
        """Paket düşürüldü - rota geçersiz olabilir"""
        dest = packet.destination
        if dest in self.routing_table:
            self.routing_table[dest].is_valid = False

    def on_topology_change(self, event: TopologyEvent):
        """Topoloji değişikliği - etkilenen rotaları geçersiz kıl"""
        if event.event_type in (
            TopologyEventType.NODE_FAILED,
            TopologyEventType.LINK_DOWN
        ):
            affected_node = event.node_id

            # Bu düğümü next_hop olarak kullanan rotaları geçersiz kıl
            for route in self.routing_table.values():
                if route.next_hop == affected_node:
                    route.is_valid = False

    def reset(self):
        """Router'ı sıfırla"""
        self.routing_table.clear()
        self._seen_rreqs.clear()
        self.sequence_number = 0
        self.dest_sequence_numbers.clear()
        self._route_discoveries = 0
        self._route_failures = 0
        self._cache_hits = 0

    def get_stats(self) -> dict:
        """İstatistikleri döndür"""
        total_lookups = self._route_discoveries + self._route_failures + self._cache_hits

        return {
            'name': self.get_name(),
            'trainable': False,
            'routing_table_size': len(self.routing_table),
            'route_discoveries': self._route_discoveries,
            'route_failures': self._route_failures,
            'cache_hits': self._cache_hits,
            'cache_hit_rate': self._cache_hits / total_lookups if total_lookups > 0 else 0.0,
            'valid_routes': sum(1 for r in self.routing_table.values() if r.is_valid),
        }
