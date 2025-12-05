import random
import time
from typing import List, Dict, Optional, Tuple
import networkx as nx
from .node import Node
from .topology import TopologyGenerator

class Packet:
    """Ağda dolaşan paket sınıfı"""
    
    def __init__(self, packet_id: int, source_id: int, destination_id: int, data: str = ""):
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
        return f"Packet {self.id}: {self.source}->{self.destination} (hops: {self.hop_count})"

class Network:
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
        print(f"=== AĞ OLUŞTURULUYOR ===")
        nodes_list, graph = self.topology_generator.create_random_topology(num_nodes, communication_range)
        self.nodes = {node.id: node for node in nodes_list}
        self.graph = graph
        print(f">> Ağ oluşturuldu: {len(self.nodes)} düğüm")
        
    def simulate_node_failure(self, failure_rate: float = 0.02):
        failures = []
        repairs = []
        for node_id, node in self.nodes.items():
            if random.random() < failure_rate:
                if node.is_active:
                    node.fail()
                    failures.append(node_id)
                else:
                    if random.random() < 0.5:
                        node.repair()
                        repairs.append(node_id)
        if failures:
            print(f">> Node arızaları: {failures}")
        if repairs:
            print(f">> Node tamirler: {repairs}")
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
            best_distance = float('inf')
            for neighbor_id in active_neighbors:
                neighbor_pos = self.nodes[neighbor_id].position
                distance = self.topology_generator.calculate_distance(neighbor_pos, dest_pos)
                if distance < best_distance:
                    best_distance = distance
                    best_neighbor = neighbor_id
            if best_neighbor:
                print(f"   Node {current_node_id}: En yakın komşu seçildi -> {best_neighbor}")
                return best_neighbor
        return random.choice(active_neighbors)
    
    def send_packet(self, source_id: int, destination_id: int, data: str = "test_data") -> bool:
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
                print(f"   >> PAKET TESLİM EDİLDİ! Yol: {' -> '.join(map(str, packet.path))}")
                return True
            next_hop = self.dummy_routing(packet)
            if next_hop is None:
                self.lost_packets.append(packet)
                print(f"   >> PAKET KAYBOLDU! Son konum: {current_node_id}")
                return False
            packet.add_hop(next_hop)
            current_hop += 1
            if current_hop >= max_hops:
                self.lost_packets.append(packet)
                print(f"   >> PAKET ZAMAN AŞIMI! Maksimum hop sayısına ulaşıldı")
                return False
        return False
    
    def step(self, failure_rate: float = 0.02):
        self.simulation_time += 1
        print(f"\n=== SİMÜLASYON ADIMI {self.simulation_time} ===")
        self.simulate_node_failure(failure_rate)
        active_nodes = [node_id for node_id, node in self.nodes.items() if node.is_active]
        if len(active_nodes) >= 2:
            source = random.choice(active_nodes)
            destination = random.choice([nid for nid in active_nodes if nid != source])
            self.send_packet(source, destination, f"Adım {self.simulation_time} verisi")
    
    def get_network_stats(self) -> Dict:
        active_nodes = sum(1 for node in self.nodes.values() if node.is_active)
        total_nodes = len(self.nodes)
        return {
            'simulation_time': self.simulation_time,
            'total_nodes': total_nodes,
            'active_nodes': active_nodes,
            'total_packets': self.packet_counter,
            'delivered_packets': len(self.delivered_packets),
            'lost_packets': len(self.lost_packets),
            'delivery_rate': len(self.delivered_packets) / self.packet_counter if self.packet_counter > 0 else 0,
            'graph_connected': nx.is_connected(self.graph) if self.graph.number_of_nodes() > 0 else False
        }