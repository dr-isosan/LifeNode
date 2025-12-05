"""
LifeNode - Afet Durumu İletişim Ağı Simülasyonu
Kişi A: Network & Simulation Architect
"""

from simulation.network import Network
from visualization.plot_utils import NetworkVisualizer
import sys

def main():
    print("=" * 60)
    print("  LifeNode: Afet Durumu İletişim Ağı Simülasyonu")
    print("=" * 60)
    
    NUM_NODES = 20
    COMMUNICATION_RANGE = 25.0
    AREA_WIDTH = 100.0
    AREA_HEIGHT = 100.0
    NODE_FAILURE_RATE = 0.05
    
    network = Network(width=AREA_WIDTH, height=AREA_HEIGHT)
    network.create_network(num_nodes=NUM_NODES, communication_range=COMMUNICATION_RANGE)
    
    print(f"\n{'='*60}")
    print(">> TEST PAKET GÖNDERİMLERİ")
    active_nodes = [nid for nid, node in network.nodes.items() if node.is_active]
    
    if len(active_nodes) >= 2:
        for i in range(3):
            if i < len(active_nodes) - 1:
                source = active_nodes[i]
                dest = active_nodes[-(i+1)]
                network.send_packet(source, dest, f"Test mesajı {i+1}")
    
    print(f"\n{'='*60}")
    print(">> SİMÜLASYON ADIMLARI")
    for i in range(5):
        network.step(failure_rate=NODE_FAILURE_RATE)
    
    print(f"\n{'='*60}")
    print(">> FİNAL İSTATİSTİKLERİ")
    stats = network.get_network_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    print(f"\n{'='*60}")
    print("  Simülasyon Tamamlandı!")
    return network

def run_quick_test():
    print("=== HIZLI TEST MODU ===\n")
    network = Network(width=50.0, height=50.0)
    network.create_network(num_nodes=10, communication_range=20.0)
    print("\n>> Test paket gönderimi...")
    active = [nid for nid, n in network.nodes.items() if n.is_active]
    if len(active) >= 2:
        network.send_packet(active[0], active[-1])
    print("\n>> İstatistikler:")
    stats = network.get_network_stats()
    for k, v in stats.items():
        print(f"   {k}: {v}")
    return network

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--quick":
        network = run_quick_test()
    else:
        network = main()