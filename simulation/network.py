import random
import time
import sys
import os
from typing import Dict, Optional, Tuple, List
import networkx as nx
from .node import Node
from .topology import TopologyGenerator

# Logger için path ekle
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.utils.logger import get_logger  # noqa: E402
from src.config.constants import NetworkConstants  # noqa: E402

# Global logger
logger = get_logger("Network", log_to_file=False)


class Packet:
    """Ağda dolaşan paket sınıfı"""

    def __init__(
        self,
        packet_id: int,
        source_id: int,
        destination_id: int,
        data: str = "",
    ):
        self.id = packet_id
        self.source = source_id
        self.destination = destination_id
        self.data = data
        self.hop_count = 0
        self.path = [source_id]
        self.timestamp = time.time()

    def add_hop(self, node_id: int):
        """Pakete bir hop ekle"""
        self.hop_count += 1
        self.path.append(node_id)

    def __str__(self):
        return (
            f"Packet {self.id}: {self.source}->{self.destination} "
            f"(hops: {self.hop_count})"
        )


class Network:
    """
    Ağı yöneten ana sınıf
    Düğüm yönetimi, paket routing ve simülasyon kontrolü yapar
    """

    def __init__(self, width: float = 100.0, height: float = 100.0):
        """
        Network sınıfı başlatıcı

        Args:
            width: Alan genişliği
            height: Alan yüksekliği
        """
        self.width = width
        self.height = height
        self.nodes = {}
        self.graph = nx.Graph()
        self.topology_generator = TopologyGenerator(width, height)
        self.simulation_time = 0
        self.packet_counter = 0
        self.delivered_packets = []
        self.lost_packets = []
        self.communication_range = NetworkConstants.DEFAULT_COMMUNICATION_RANGE

    def create_network(self, num_nodes: int, communication_range: float):
        """
        Yeni ağ oluştur

        Args:
            num_nodes: Düğüm sayısı
            communication_range: İletişim menzili
        """
        logger.info("=== AĞ OLUŞTURULUYOR ===")

        # Communication range'i sakla
        self.communication_range = communication_range

        # Topoloji üret
        nodes_list, graph = self.topology_generator.create_random_topology(
            num_nodes, communication_range
        )

        # Node dictionary'sine ekle
        self.nodes = {node.id: node for node in nodes_list}
        self.graph = graph

        logger.info(f">> Ağ oluşturuldu: {len(self.nodes)} düğüm")

    def add_node(
        self,
        node_id: int,
        position: Tuple[float, float],
        communication_range: float,
    ):
        """
        Ağa yeni düğüm ekle

        Args:
            node_id: Düğüm ID'si
            position: (x, y) pozisyon
            communication_range: İletişim menzili
        """
        if node_id in self.nodes:
            print(f"Node {node_id} zaten mevcut!")
            return False

        # Yeni node oluştur
        new_node = Node(node_id, position)

        # Mevcut düğümlerle komşuluk kontrolü
        for existing_id, existing_node in self.nodes.items():
            distance = self.topology_generator.calculate_distance(
                position, existing_node.position
            )
            if distance <= communication_range:
                new_node.add_neighbor(existing_id)
                existing_node.add_neighbor(node_id)
                self.graph.add_edge(node_id, existing_id, weight=distance)

        # Graph'a node ekle
        self.graph.add_node(node_id, pos=position)
        self.nodes[node_id] = new_node

        neighbor_count = len(new_node.neighbors)
        print(f">> Node {node_id} ağa eklendi. Komşu sayısı: {neighbor_count}")
        return True

    def remove_node(self, node_id: int):
        """
        Düğümü ağdan çıkar

        Args:
            node_id: Çıkarılacak düğüm ID'si
        """
        if node_id not in self.nodes:
            print(f"Node {node_id} bulunamadı!")
            return False

        # Komşularından bu node'u çıkar
        for neighbor_id in self.nodes[node_id].neighbors:
            if neighbor_id in self.nodes:
                self.nodes[neighbor_id].remove_neighbor(node_id)

        # Graph'dan çıkar
        if self.graph.has_node(node_id):
            self.graph.remove_node(node_id)

        # Nodes'dan çıkar
        del self.nodes[node_id]

        print(f">> Node {node_id} ağdan çıkarıldı")
        return True

    def simulate_node_failure(self, failure_rate: float = 0.02):
        """
        Rastgele düğüm arızası simüle et

        Args:
            failure_rate: Arıza olasılığı (0.02 = %2)
        """
        failures = []
        repairs = []

        for node_id, node in self.nodes.items():
            if random.random() < failure_rate:
                if node.is_active:
                    node.fail()
                    failures.append(node_id)
                else:
                    # Bazen bozuk düğümler tamir olabilir
                    if random.random() < NetworkConstants.NODE_REPAIR_CHANCE:
                        node.repair()
                        repairs.append(node_id)

        if failures:
            logger.warning(f">> Node arızaları: {failures}")
            # Komşu listelerini güncelle
            self.update_neighbors_after_failures(failures)
        if repairs:
            logger.info(f">> Node tamirler: {repairs}")
            # Komşu listelerini güncelle
            self.update_neighbors_after_repairs(repairs)

        return failures, repairs

    def dummy_routing(self, packet: Packet) -> Optional[int]:
        """
        Basit (dummy) routing algoritması
        Rastgele komşu seçer veya flooding yapar

        Args:
            packet: Yönlendirilecek paket

        Returns:
            Seçilen komşu ID veya None
        """
        current_node_id = packet.path[-1]  # Son hop

        if current_node_id not in self.nodes:
            return None

        current_node = self.nodes[current_node_id]

        if not current_node.is_active:
            return None

        # Aktif komşuları bul
        active_neighbors = []
        for neighbor_id in current_node.neighbors:
            if neighbor_id in self.nodes:
                neighbor = self.nodes[neighbor_id]
                if neighbor.is_active and neighbor_id not in packet.path:
                    active_neighbors.append(neighbor_id)

        if not active_neighbors:
            msg = (
                f"   Node {current_node_id}: "
                f"Aktif komşu bulunamadı, paket kayboldu!"
            )
            print(msg)
            return None

        # Basit stratejiler:
        # 1. Rastgele komşu seç
        if random.random() < NetworkConstants.RANDOM_ROUTING_PROBABILITY:
            next_hop = random.choice(active_neighbors)
            msg = f"   Node {current_node_id}: " f"Rastgele komşu seçildi -> {next_hop}"
            print(msg)
            return next_hop

        # 2. En yakın komşuyu seç (hedef koordinatına)
        if packet.destination in self.nodes:
            dest_pos = self.nodes[packet.destination].position
            best_neighbor = None
            best_distance = float("inf")
            for neighbor_id in active_neighbors:
                neighbor_pos = self.nodes[neighbor_id].position
                distance = self.topology_generator.calculate_distance(
                    neighbor_pos, dest_pos
                )
                if distance < best_distance:
                    best_distance = distance
                    best_neighbor = neighbor_id

            if best_neighbor:
                msg = (
                    f"   Node {current_node_id}: "
                    f"En yakın komşu seçildi -> {best_neighbor}"
                )
                print(msg)
                return best_neighbor

        # Fallback: rastgele seç
        return random.choice(active_neighbors)

    def send_packet(
        self, source_id: int, destination_id: int, data: str = "test_data"
    ) -> bool:
        """
        Paket gönderme simülasyonu

        Args:
            source_id: Kaynak düğüm ID
            destination_id: Hedef düğüm ID
            data: Paket verisi

        Returns:
            Gönderim başarılı mı
        """
        if source_id not in self.nodes or destination_id not in self.nodes:
            msg = f"Kaynak ({source_id}) veya " f"hedef ({destination_id}) bulunamadı!"
            print(msg)
            return False

        if not self.nodes[source_id].is_active:
            print(f"Kaynak node {source_id} pasif!")
            return False

        # Paket oluştur
        packet = Packet(self.packet_counter, source_id, destination_id, data)
        self.packet_counter += 1

        print(f"\n>> PAKET GÖNDERİMİ: {packet}")

        # Paket routing simülasyonu
        max_hops = NetworkConstants.MAX_PACKET_HOPS
        current_hop = 0

        while current_hop < max_hops:
            current_node_id = packet.path[-1]

            # Hedefe ulaştı mı?
            if current_node_id == destination_id:
                self.delivered_packets.append(packet)
                path_str = " -> ".join(map(str, packet.path))
                print(f"   >> PAKET TESLİM EDİLDİ! Yol: {path_str}")
                return True

            # Sonraki hop'u bul
            next_hop = self.dummy_routing(packet)
            if next_hop is None:
                self.lost_packets.append(packet)
                msg = f"   >> PAKET KAYBOLDU! Son konum: {current_node_id}"
                print(msg)
                return False

            # Paketi ilerlet
            packet.add_hop(next_hop)
            current_hop += 1

        # Max hops aşıldı
        self.lost_packets.append(packet)
        print("   >> PAKET ZAMAN AŞIMI! Maksimum hop sayısına ulaşıldı")
        return False



    def step(self, failure_rate: float = 0.02):
        """
        Simülasyonun bir adımını çalıştır

        Args:
            failure_rate: Node arıza oranı
        """
        self.simulation_time += 1
        logger.debug(f"=== SİMÜLASYON ADIMI {self.simulation_time} ===")

        # Node arızalarını simüle et
        self.simulate_node_failure(failure_rate)

        # Rastgele paket gönderimi (test için)
        active_nodes = [
            node_id for node_id, node in self.nodes.items() if node.is_active
        ]

        if len(active_nodes) >= 2:
            source = random.choice(active_nodes)
            dest_options = [nid for nid in active_nodes if nid != source]
            destination = random.choice(dest_options)

            msg = f"Adım {self.simulation_time} verisi"
            self.send_packet(source, destination, msg)

    def get_network_stats(self) -> Dict:
        """Ağ istatistiklerini döndür"""
        active_nodes = sum(1 for node in self.nodes.values() if node.is_active)
        total_nodes = len(self.nodes)
        return {
            "simulation_time": self.simulation_time,
            "total_nodes": total_nodes,
            "active_nodes": active_nodes,
            "total_packets": self.packet_counter,
            "delivered_packets": len(self.delivered_packets),
            "lost_packets": len(self.lost_packets),
            "delivery_rate": (
                len(self.delivered_packets) / self.packet_counter
                if self.packet_counter > 0
                else 0
            ),
            "graph_connected": (
                nx.is_connected(self.graph)
                if self.graph.number_of_nodes() > 0
                else False
            ),
        }

    def update_neighbors_after_failures(self, failed_node_ids: List[int]):
        """
        Node arızalarından sonra komşu listelerini güncelle

        Args:
            failed_node_ids: Arızalanan node ID'leri
        """
        for failed_id in failed_node_ids:
            # Arızalanan node'un tüm komşularını güncelle
            if failed_id in self.nodes:
                failed_node = self.nodes[failed_id]
                for neighbor_id in list(failed_node.neighbors):
                    if neighbor_id in self.nodes:
                        neighbor = self.nodes[neighbor_id]
                        # Arızalı node'u komşu listesinden çıkar
                        if failed_id in neighbor.neighbors:
                            neighbor.neighbors.remove(failed_id)

    def update_neighbors_after_repairs(self, repaired_node_ids: List[int]):
        """
        Node tamirlerinden sonra komşu listelerini yeniden oluştur

        Args:
            repaired_node_ids: Tamir edilen node ID'leri
        """
        for repaired_id in repaired_node_ids:
            if repaired_id not in self.nodes:
                continue

            repaired_node = self.nodes[repaired_id]

            # Tamir edilen node için komşuları yeniden hesapla
            for other_id, other_node in self.nodes.items():
                if other_id == repaired_id:
                    continue

                # Mesafe kontrolü
                distance = repaired_node.distance_to(other_node)
                if distance <= self.communication_range:
                    # İki yönlü komşuluk ekle
                    if other_id not in repaired_node.neighbors:
                        repaired_node.neighbors.append(other_id)
                    if repaired_id not in other_node.neighbors and other_node.is_active:
                        other_node.neighbors.append(repaired_id)


def test_network():
    """Network sınıfının test fonksiyonu"""
    print("=== NETWORK SINIFI TEST ===")

    # Network oluştur
    network = Network(width=60.0, height=60.0)

    # Ağ oluştur
    network.create_network(num_nodes=10, communication_range=25.0)

    # Başlangıç istatistikleri
    print("\n=== BAŞLANGIÇ İSTATİSTİKLERİ ===")
    stats = network.get_network_stats()
    for key, value in stats.items():
        print(f"{key}: {value}")

    # Manuel paket gönderimi testi
    print("\n=== MANUEL PAKET GÖNDERİMİ ===")
    active_list = [nid for nid, node in network.nodes.items() if node.is_active]
    if len(active_list) >= 2:
        network.send_packet(active_list[0], active_list[-1], "Test mesajı")

    # 3 adım simülasyon
    print("\n=== SİMÜLASYON ADIMLARI ===")
    for i in range(3):
        network.step(failure_rate=0.1)  # %10 arıza oranı

    # Final istatistikler
    print("\n=== FİNAL İSTATİSTİKLERİ ===")
    stats = network.get_network_stats()
    for key, value in stats.items():
        print(f"{key}: {value}")

    return network


if __name__ == "__main__":
    network = test_network()
