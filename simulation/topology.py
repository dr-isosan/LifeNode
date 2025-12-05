import random
import math
import networkx as nx
from typing import List, Tuple, Dict
from .node import Node

class TopologyGenerator:
    """
    Random Geometric Graph (RGG) oluşturan sınıf.
    Düğümleri rastgele yerleştirir ve belirli mesafedeki düğümleri birbirine bağlar.
    """
    
    def __init__(self, width: float = 100.0, height: float = 100.0):
        """
        Topoloji üretici başlatıcı
        
        Args:
            width: Alan genişliği
            height: Alan yüksekliği
        """
        self.width = width
        self.height = height
    
    def calculate_distance(self, pos1: Tuple[float, float], pos2: Tuple[float, float]) -> float:
        """
        İki nokta arası Euclidean mesafe hesabı
        
        Args:
            pos1: İlk nokta (x1, y1)
            pos2: İkinci nokta (x2, y2)
            
        Returns:
            İki nokta arası mesafe
        """
        x1, y1 = pos1
        x2, y2 = pos2
        return math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
    
    def generate_random_positions(self, num_nodes: int) -> List[Tuple[float, float]]:
        """
        N adet düğüm için rastgele pozisyonlar üret
        
        Args:
            num_nodes: Düğüm sayısı
            
        Returns:
            (x, y) pozisyon listesi
        """
        positions = []
        for i in range(num_nodes):
            x = random.uniform(0, self.width)
            y = random.uniform(0, self.height)
            positions.append((x, y))
        
        return positions
    
    def find_neighbors_within_range(self, positions: List[Tuple[float, float]], 
                                  communication_range: float) -> Dict[int, List[int]]:
        """
        Her düğüm için iletişim menzilindeki komşuları bul
        
        Args:
            positions: Tüm düğümlerin pozisyon listesi
            communication_range: İletişim menzili
            
        Returns:
            {node_id: [neighbor_ids]} şeklinde komşuluk listesi
        """
        neighbors = {i: [] for i in range(len(positions))}
        
        for i in range(len(positions)):
            for j in range(i + 1, len(positions)):
                distance = self.calculate_distance(positions[i], positions[j])
                
                # Eğer mesafe iletişim menzili içindeyse komşu olarak ekle
                if distance <= communication_range:
                    neighbors[i].append(j)
                    neighbors[j].append(i)
        
        return neighbors
    
    def create_networkx_graph(self, positions: List[Tuple[float, float]], 
                            neighbors: Dict[int, List[int]]) -> nx.Graph:
        """
        NetworkX graf objesi oluştur
        
        Args:
            positions: Düğüm pozisyonları
            neighbors: Komşuluk listesi
            
        Returns:
            NetworkX Graf objesi
        """
        G = nx.Graph()
        
        # Düğümleri ekle
        for i, pos in enumerate(positions):
            G.add_node(i, pos=pos)
        
        # Kenarları ekle
        for node_id, neighbor_list in neighbors.items():
            for neighbor_id in neighbor_list:
                if not G.has_edge(node_id, neighbor_id):
                    distance = self.calculate_distance(positions[node_id], positions[neighbor_id])
                    G.add_edge(node_id, neighbor_id, weight=distance)
        
        return G
    
    def create_random_topology(self, num_nodes: int, communication_range: float) -> Tuple[List[Node], nx.Graph]:
        """
        Rastgele topoloji oluşturan ana fonksiyon
        
        Args:
            num_nodes: Düğüm sayısı
            communication_range: İletişim menzili
            
        Returns:
            (nodes_list, networkx_graph) tuple'ı
        """
        print(f"=== TOPOLOJI OLUŞTURULUYOR ===")
        print(f"Düğüm sayısı: {num_nodes}")
        print(f"İletişim menzili: {communication_range}")
        print(f"Alan boyutu: {self.width}x{self.height}")
        
        # 1. Rastgele pozisyonlar üret
        positions = self.generate_random_positions(num_nodes)
        print(f">> {num_nodes} düğüm rastgele yerleştirildi")
        
        # 2. Komşulukları bul
        neighbors = self.find_neighbors_within_range(positions, communication_range)
        
        # 3. Node objelerini oluştur
        nodes = []
        for i, pos in enumerate(positions):
            node = Node(i, pos)
            # Komşuları ekle
            for neighbor_id in neighbors[i]:
                node.add_neighbor(neighbor_id)
            nodes.append(node)
        
        # 4. NetworkX grafını oluştur
        graph = self.create_networkx_graph(positions, neighbors)
        
        # İstatistikler
        total_edges = graph.number_of_edges()
        avg_degree = sum(len(neighbors[i]) for i in range(num_nodes)) / num_nodes if num_nodes > 0 else 0
        
        print(f">> Topoloji oluşturuldu:")
        print(f"   - Toplam bağlantı: {total_edges}")
        print(f"   - Ortalama komşu sayısı: {avg_degree:.2f}")
        
        # Bağlantısız düğümleri kontrol et
        isolated_nodes = [i for i in range(num_nodes) if len(neighbors[i]) == 0]
        if isolated_nodes:
            print(f"!! İzole düğümler: {isolated_nodes}")
        
        return nodes, graph
    
    def get_topology_stats(self, graph: nx.Graph) -> Dict:
        """
        Topoloji istatistiklerini döndür
        
        Args:
            graph: NetworkX graf objesi
            
        Returns:
            İstatistik bilgileri
        """
        return {
            'num_nodes': graph.number_of_nodes(),
            'num_edges': graph.number_of_edges(),
            'is_connected': nx.is_connected(graph),
            'density': nx.density(graph),
            'avg_clustering': nx.average_clustering(graph) if graph.number_of_nodes() > 0 else 0,
            'diameter': nx.diameter(graph) if nx.is_connected(graph) else 'N/A'
        }

def test_topology():
    """Topoloji üreticinin test fonksiyonu"""
    print("=== TOPOLOJI ÜRETICI TEST ===")
    
    # Topoloji üretici oluştur
    topo_gen = TopologyGenerator(width=50.0, height=50.0)
    
    # Küçük bir ağ oluştur
    nodes, graph = topo_gen.create_random_topology(num_nodes=8, communication_range=20.0)
    
    print(f"\n=== DÜĞÜM BİLGİLERİ ===")
    for node in nodes:
        print(f"{node}")
    
    print(f"\n=== GRAF İSTATİSTİKLERİ ===")
    stats = topo_gen.get_topology_stats(graph)
    for key, value in stats.items():
        print(f"{key}: {value}")
    
    # Mesafe hesabı testi
    print(f"\n=== MESAFE HESABI TEST ===")
    if len(nodes) >= 2:
        pos1 = nodes[0].position
        pos2 = nodes[1].position
        distance = topo_gen.calculate_distance(pos1, pos2)
        print(f"Node {nodes[0].id} ({pos1}) ile Node {nodes[1].id} ({pos2}) arası mesafe: {distance:.2f}")
    
    return nodes, graph

if __name__ == "__main__":
    test_topology()