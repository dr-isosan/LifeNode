"""
Dijkstra Router (En Kısa Yol Baseline)

Global topoloji bilgisi kullanarak en kısa yolu bulan baseline algoritma.
Gerçek dünyada bu bilgi mevcut değildir, ancak karşılaştırma için idealdir.
"""

from typing import Dict, List, Optional, Tuple, TYPE_CHECKING
import networkx as nx

from .base import Router, TopologyEvent

if TYPE_CHECKING:
    from ..environment.world import World
    from ..environment.packet import Packet


class DijkstraRouter(Router):
    """
    Dijkstra En Kısa Yol Router

    Global topoloji bilgisine sahip olduğu varsayılır.
    Bağlantı kalitesini ağırlık olarak kullanır.

    Attributes:
        use_quality_weights: True ise kalite, False ise hop sayısı optimize edilir
        cache_enabled: Yol cache'i etkin mi?
    """

    def __init__(
        self,
        use_quality_weights: bool = True,
        cache_enabled: bool = True
    ):
        """
        Args:
            use_quality_weights: Ağırlık olarak kalite kullan
            cache_enabled: Cache kullan (topoloji değişene kadar)
        """
        self.use_quality_weights = use_quality_weights
        self.cache_enabled = cache_enabled

        # Yol cache'i
        self._path_cache: Dict[Tuple[str, str], List[str]] = {}
        self._cache_valid: bool = False

        # İstatistikler
        self._cache_hits: int = 0
        self._cache_misses: int = 0
        self._paths_computed: int = 0

    def get_name(self) -> str:
        if self.use_quality_weights:
            return "Dijkstra-Quality"
        return "Dijkstra-Hop"

    def get_next_hop(
        self,
        current_node: str,
        destination: str,
        world: 'World'
    ) -> Optional[str]:
        """
        Dijkstra algoritması ile sonraki hop'u bul

        Args:
            current_node: Mevcut düğüm
            destination: Hedef düğüm
            world: Simülasyon dünyası

        Returns:
            Sonraki hop veya None
        """
        if current_node == destination:
            return None  # Zaten hedefteyiz

        # Cache kontrolü
        cache_key = (current_node, destination)
        if self.cache_enabled and self._cache_valid:
            if cache_key in self._path_cache:
                path = self._path_cache[cache_key]
                self._cache_hits += 1
                if len(path) > 1:
                    return path[1]  # Sonraki hop
                return None

        self._cache_misses += 1

        # Graf al
        graph = world.get_topology_graph()

        # Düğümler mevcut mu?
        if current_node not in graph.nodes or destination not in graph.nodes:
            return None

        # Dijkstra ile yol bul
        try:
            if self.use_quality_weights:
                # Ağırlık = 1/kalite (düşük kalite = yüksek maliyet)
                path = nx.dijkstra_path(
                    graph,
                    current_node,
                    destination,
                    weight='weight'
                )
            else:
                # Sadece hop sayısı
                path = nx.shortest_path(graph, current_node, destination)

            self._paths_computed += 1

            # Cache'e ekle
            if self.cache_enabled:
                self._path_cache[cache_key] = path

            if len(path) > 1:
                return path[1]
            return None

        except nx.NetworkXNoPath:
            # Yol yok
            return None
        except nx.NodeNotFound:
            # Düğüm bulunamadı
            return None

    def on_topology_change(self, event: TopologyEvent):
        """Topoloji değişikliğinde cache'i geçersiz kıl"""
        self._invalidate_cache()

    def on_packet_forwarded(self, packet: 'Packet', next_hop: str):
        """Paket iletildi - cache hala geçerli"""
        pass

    def on_packet_dropped(self, packet: 'Packet'):
        """Paket düşürüldü - muhtemelen topoloji değişti"""
        # Güvenli tarafta kal, cache'i geçersiz kıl
        self._invalidate_cache()

    def _invalidate_cache(self):
        """Cache'i geçersiz kıl"""
        self._path_cache.clear()
        self._cache_valid = False

    def _validate_cache(self):
        """Cache'i geçerli işaretle"""
        self._cache_valid = True

    def reset(self):
        """Router'ı sıfırla"""
        self._invalidate_cache()
        self._cache_hits = 0
        self._cache_misses = 0
        self._paths_computed = 0

    def get_stats(self) -> dict:
        """İstatistikleri döndür"""
        stats = super().get_stats()
        stats.update({
            'cache_hits': self._cache_hits,
            'cache_misses': self._cache_misses,
            'paths_computed': self._paths_computed,
            'cache_size': len(self._path_cache),
            'use_quality_weights': self.use_quality_weights,
        })
        return stats

    # =========================================================================
    # EK METODLAR
    # =========================================================================

    def get_full_path(
        self,
        source: str,
        destination: str,
        world: 'World'
    ) -> Optional[List[str]]:
        """
        Kaynak'tan hedefe tam yolu döndür

        Args:
            source: Kaynak düğüm
            destination: Hedef düğüm
            world: Simülasyon dünyası

        Returns:
            Düğüm ID'leri listesi veya None
        """
        graph = world.get_topology_graph()

        if source not in graph.nodes or destination not in graph.nodes:
            return None

        try:
            if self.use_quality_weights:
                return nx.dijkstra_path(graph, source, destination, weight='weight')
            else:
                return nx.shortest_path(graph, source, destination)
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return None

    def get_path_cost(
        self,
        source: str,
        destination: str,
        world: 'World'
    ) -> Optional[float]:
        """
        Yol maliyetini hesapla

        Args:
            source: Kaynak düğüm
            destination: Hedef düğüm
            world: Simülasyon dünyası

        Returns:
            Maliyet veya None
        """
        graph = world.get_topology_graph()

        if source not in graph.nodes or destination not in graph.nodes:
            return None

        try:
            if self.use_quality_weights:
                return nx.dijkstra_path_length(graph, source, destination, weight='weight')
            else:
                return nx.shortest_path_length(graph, source, destination)
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return None

    def precompute_all_paths(self, world: 'World'):
        """
        Tüm çiftler için yolları önceden hesapla

        Performans optimizasyonu için kullanılabilir.

        Args:
            world: Simülasyon dünyası
        """
        if not self.cache_enabled:
            return

        graph = world.get_topology_graph()
        nodes = list(graph.nodes())

        for source in nodes:
            for dest in nodes:
                if source == dest:
                    continue

                try:
                    if self.use_quality_weights:
                        path = nx.dijkstra_path(graph, source, dest, weight='weight')
                    else:
                        path = nx.shortest_path(graph, source, dest)

                    self._path_cache[(source, dest)] = path
                    self._paths_computed += 1
                except (nx.NetworkXNoPath, nx.NodeNotFound):
                    pass

        self._validate_cache()
