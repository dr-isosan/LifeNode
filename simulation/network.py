import random
import time
from typing import List, Dict, Optional, Tuple
import networkx as nx
from .node import Node
from .topology import TopologyGenerator


class Packet:
    """Ağda dolaşan paket sınıfı"""

    def __init__(
        self, packet_id: int, source_id: int, destination_id: int, data: str = ""
    ):
        self.id = packet_id
        self.source = source_id
        self.destination = destination_id
        self.data = data
        self.hop_count = 0
        self.path = [source_id]  # Paketin gittiği yollar
        self.path = [source_id]
        self.timestamp = time.time()

    def add_hop(self, node_id: int):
        """Pakete bir hop ekle"""
        self.hop_count += 1
        self.path.append(node_id)

    def __str__(self):
        return f"Packet {self.id}: {self.source}->{self.destination} (hops: {self.hop_count})"


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
        self.nodes = {}  # {node_id: Node} dictionary

    """Ağı yöneten ana sınıf"""

    def __init__(self, width: float = 100.0, height: float = 100.0):
        self.width = width
        self.height = height
        self.nodes = {}
        self.graph = nx.Graph()
        self.topology_generator = TopologyGenerator(width, height)
        self.simulation_time = 0
        self.packet_counter = 0
        self.delivered_packets = []
        self.lost_packets = []

    def create_network(self, num_nodes: int, communication_range: float):
        """
        Yeni ağ oluştur

        Args:
            num_nodes: Düğüm sayısı
            communication_range: İletişim menzili
        """
        print(f"=== AĞ OLUŞTURULUYOR ===")

        # Topoloji üret
        nodes_list, graph = self.topology_generator.create_random_topology(
            num_nodes, communication_range
        )

        # Node dictionary'sine ekle
        self.nodes = {node.id: node for node in nodes_list}
        self.graph = graph

        print(f">> Ağ oluşturuldu: {len(self.nodes)} düğüm")

    def add_node(
        self, node_id: int, position: Tuple[float, float], communication_range: float
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

        print(f">> Node {node_id} ağa eklendi. Komşu sayısı: {len(new_node.neighbors)}")
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
                    if random.random() < 0.5:  # %50 şans
                        node.repair()
                        repairs.append(node_id)

        if failures:
            print(f">> Node arızaları: {failures}")
        if repairs:
            print(f">> Node tamirler: {repairs}")

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
            if neighbor_id in self.nodes and self.nodes[neighbor_id].is_active:
                # Döngüyü önlemek için zaten gidilen yerleri atla
                if neighbor_id not in packet.path:
                    active_neighbors.append(neighbor_id)

        if not active_neighbors:
            print(f"   Node {current_node_id}: Aktif komşu bulunamadı, paket kayboldu!")
            return None

        # Basit stratejiler:
        # 1. Rastgele komşu seç
        if random.random() < 0.7:  # %70 ihtimalle rastgele
            next_hop = random.choice(active_neighbors)
            print(f"   Node {current_node_id}: Rastgele komşu seçildi -> {next_hop}")
            return next_hop

        # 2. En yakın komşuyu seç (hedef koordinatına)
        if packet.destination in self.nodes:
            dest_pos = self.nodes[packet.destination].position
            current_pos = current_node.position

            best_neighbor = None
            best_distance = float("inf")

        return failures, repairs

    def dummy_routing(self, packet: Packet) -> Optional[int]:
        current_node_id = packet.path[-1]
        if current_node_id not in self.nodes:
            return None
        current_node = self.nodes[current_node_id]
        if not current_node.is_active:
            return None
        active_neighbors = []
        for neighbor_id in current_node.neighbors:
            if neighbor_id in self.nodes and self.nodes[neighbor_id].is_active:
                if neighbor_id not in packet.path:
                    active_neighbors.append(neighbor_id)
        if not active_neighbors:
            print(f"   Node {current_node_id}: Aktif komşu bulunamadı, paket kayboldu!")
            return None
        if random.random() < 0.7:
            next_hop = random.choice(active_neighbors)
            print(f"   Node {current_node_id}: Rastgele komşu seçildi -> {next_hop}")
            return next_hop
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
                print(
                    f"   Node {current_node_id}: En yakın komşu seçildi -> {best_neighbor}"
                )
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
            print(f"Kaynak ({source_id}) veya hedef ({destination_id}) bulunamadı!")
            return False

        if not self.nodes[source_id].is_active:
            print(f"Kaynak node {source_id} pasif!")
            return False

        # Paket oluştur
        packet = Packet(self.packet_counter, source_id, destination_id, data)
        self.packet_counter += 1

        print(f"\n>> PAKET GÖNDERİMİ: {packet}")

        # Paket routing simülasyonu (maksimum 10 hop)
        max_hops = 10
        current_hop = 0

        while current_hop < max_hops:
            current_node_id = packet.path[-1]

            # Hedefe ulaştı mı?
            if best_neighbor:
                print(
                    f"   Node {current_node_id}: En yakın komşu seçildi -> {best_neighbor}"
                )
                return best_neighbor
        return random.choice(active_neighbors)

    def send_packet(
        self, source_id: int, destination_id: int, data: str = "test_data"
    ) -> bool:
        if source_id not in self.nodes or destination_id not in self.nodes:
            print(f"Kaynak ({source_id}) veya hedef ({destination_id}) bulunamadı!")
            return False
        if not self.nodes[source_id].is_active:
            print(f"Kaynak node {source_id} pasif!")
            return False
        packet = Packet(self.packet_counter, source_id, destination_id, data)
        self.packet_counter += 1
        print(f"\n>> PAKET GÖNDERİMİ: {packet}")
        max_hops = 10
        current_hop = 0
        while current_hop < max_hops:
            current_node_id = packet.path[-1]
            if current_node_id == destination_id:
                self.delivered_packets.append(packet)
                print(
                    f"   >> PAKET TESLİM EDİLDİ! Yol: {' -> '.join(map(str, packet.path))}"
                )
                return True

            # Sonraki hop'u bul
            next_hop = self.dummy_routing(packet)

            next_hop = self.dummy_routing(packet)
            if next_hop is None:
                self.lost_packets.append(packet)
                print(f"   >> PAKET KAYBOLDU! Son konum: {current_node_id}")
                return False

            # Paketi ilerlet
            packet.add_hop(next_hop)
            current_hop += 1

            if current_hop >= max_hops:
                self.lost_packets.append(packet)
                print(f"   >> PAKET ZAMANAŞıMı! Maksimum hop sayısına ulaşıldı")
                return False

        return False

    def step(self, failure_rate: float = 0.02):
        """
        Simülasyonun bir adımını çalıştır

        Args:
            failure_rate: Node arıza oranı
        """
        self.simulation_time += 1
        print(f"\n=== SİMÜLASYON ADIMI {self.simulation_time} ===")

        # Node arızalarını simüle et
        self.simulate_node_failure(failure_rate)

        # Rastgele paket gönderimi (test için)
        active_nodes = [
            node_id for node_id, node in self.nodes.items() if node.is_active
        ]

        if len(active_nodes) >= 2:
            source = random.choice(active_nodes)
            destination = random.choice([nid for nid in active_nodes if nid != source])

            self.send_packet(source, destination, f"Adım {self.simulation_time} verisi")

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


def test_network():
    """Network sınıfının test fonksiyonu"""
    print("=== NETWORK SINIFI TEST ===")

    # Network oluştur
    network = Network(width=60.0, height=60.0)

    # Ağ oluştur
    network.create_network(num_nodes=10, communication_range=25.0)

    # Başlangıç istatistikleri
    print(f"\n=== BAŞLANGIÇ İSTATİSTİKLERİ ===")
    stats = network.get_network_stats()
    for key, value in stats.items():
        print(f"{key}: {value}")

    # Manuel paket gönderimi testi
    print(f"\n=== MANUEL PAKET GÖNDERİMİ ===")
    active_nodes = [nid for nid, node in network.nodes.items() if node.is_active]
    if len(active_nodes) >= 2:
        network.send_packet(active_nodes[0], active_nodes[-1], "Test mesajı")

    # 3 adım simülasyon
    print(f"\n=== SİMÜLASYON ADIMI ===")
    for i in range(3):
        network.step(failure_rate=0.1)  # %10 arıza oranı

    # Final istatistikler
    print(f"\n=== FİNAL İSTATİSTİKLERİ ===")
    stats = network.get_network_stats()
    for key, value in stats.items():
        print(f"{key}: {value}")

    return network


if __name__ == "__main__":
    network = test_network()
