"""
LifeNode - Afet Durumu İletişim Ağı Simülasyonu
Kişi A: Network & Simulation Architect
İlk Hafta: Temel Ağ Simülasyonu ve Görselleştirme
"""

from simulation.network import Network
from visualization.plot_utils import NetworkVisualizer
import sys


def main():
    """Ana simülasyon fonksiyonu"""

    print("=" * 60)
    print("  LifeNode: Afet Durumu İletişim Ağı Simülasyonu")
    print("  Hafta 1: Temel Ağ Simülasyonu")
    print("=" * 60)

    # Simülasyon parametreleri
    print("=" * 60)
    print("  LifeNode: Afet Durumu İletişim Ağı Simülasyonu")
    print("=" * 60)

    NUM_NODES = 20
    COMMUNICATION_RANGE = 25.0
    AREA_WIDTH = 100.0
    AREA_HEIGHT = 100.0
    NODE_FAILURE_RATE = 0.05  # %5

    print(f"\n>> Simülasyon Parametreleri:")
    print(f"   - Düğüm Sayısı: {NUM_NODES}")
    print(f"   - İletişim Menzili: {COMMUNICATION_RANGE}")
    print(f"   - Alan Boyutu: {AREA_WIDTH}x{AREA_HEIGHT}")
    print(f"   - Node Arıza Oranı: {NODE_FAILURE_RATE*100}%")

    # Network oluştur
    print(f"\n{'='*60}")
    network = Network(width=AREA_WIDTH, height=AREA_HEIGHT)
    network.create_network(num_nodes=NUM_NODES, communication_range=COMMUNICATION_RANGE)

    # Başlangıç durumunu göster
    print(f"\n{'='*60}")
    print(">> BAŞLANGIÇ DURUMU")
    stats = network.get_network_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")

    # Test paket gönderimler
    NODE_FAILURE_RATE = 0.05

    network = Network(width=AREA_WIDTH, height=AREA_HEIGHT)
    network.create_network(num_nodes=NUM_NODES, communication_range=COMMUNICATION_RANGE)

    print(f"\n{'='*60}")
    print(">> TEST PAKET GÖNDERİMLERİ")
    active_nodes = [nid for nid, node in network.nodes.items() if node.is_active]

    if len(active_nodes) >= 2:
        # 3 farklı paket gönder
        for i in range(3):
            if i < len(active_nodes) - 1:
                source = active_nodes[i]
                dest = active_nodes[-(i + 1)]
                network.send_packet(source, dest, f"Test mesajı {i+1}")

    # Simülasyon adımları
    print(f"\n{'='*60}")
    print(">> SİMÜLASYON ADIMLARI (5 adım)")
    for i in range(5):
        network.step(failure_rate=NODE_FAILURE_RATE)

    # Final istatistikleri
    print(f"\n{'='*60}")
    print(">> SİMÜLASYON ADIMLARI")
    for i in range(5):
        network.step(failure_rate=NODE_FAILURE_RATE)

    print(f"\n{'='*60}")
    print(">> FİNAL İSTATİSTİKLERİ")
    stats = network.get_network_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")

    # Görselleştirme
    print(f"\n{'='*60}")
    print(">> GÖRSELLEŞTİRME")
    visualizer = NetworkVisualizer(figsize=(14, 12))

    try:
        # Ağ görselleştirmesi
        print("   1. Ağ topolojisi çiziliyor...")
        visualizer.plot_network(
            network, title="LifeNode Ağ Topolojisi - İlk Hafta", show_labels=True
        )

        # Başarılı paket yollarını göster
        if network.delivered_packets:
            print(
                f"   2. Teslim edilen paket yolları çiziliyor ({len(network.delivered_packets)} adet)..."
            )
            for i, packet in enumerate(network.delivered_packets[:3]):  # İlk 3 paket
                visualizer.plot_packet_path(
                    network,
                    packet.path,
                    title=f"Paket {packet.id}: {packet.source} → {packet.destination}",
                )

        print("   >> Görselleştirme tamamlandı!")

    except Exception as e:
        print(f"   !! Görselleştirme hatası: {e}")
        print("   (Not: GUI olmayan ortamlarda görselleştirme çalışmayabilir)")

    print(f"\n{'='*60}")
    print("  Simülasyon Tamamlandı!")
    print("=" * 60)

    return network, visualizer


def run_quick_test():
    """Hızlı test fonksiyonu (görselleştirme olmadan)"""
    print("=== HIZLI TEST MODU ===\n")

    network = Network(width=50.0, height=50.0)
    network.create_network(num_nodes=10, communication_range=20.0)

    print(f"\n{'='*60}")
    print(">> GÖRSELLEŞTİRME")
    try:
        visualizer = NetworkVisualizer(figsize=(14, 12))

        # 1. Ağ görselleştirmesi (otomatik kaydedilir)
        print("   Ağ topolojisi çiziliyor ve kaydediliyor...")
        visualizer.plot_network(network, title="LifeNode Ağ Topolojisi")

        # 2. Paket yollarını göster
        if network.delivered_packets:
            print(
                f"   Teslim edilen paket yolları çiziliyor ({len(network.delivered_packets)} adet)..."
            )
            for packet in network.delivered_packets[:3]:
                visualizer.plot_packet_path(
                    network,
                    packet.path,
                    title=f"Paket {packet.id}: {packet.source} -> {packet.destination}",
                )

        print("   >> Tüm görseller visualization/outputs/ klasörüne kaydedildi!")
    except Exception as e:
        print(f"   Hata: {e}")

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

    print("\n>> Hızlı test tamamlandı!")
    return network




if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--quick":
        run_quick_test()
    else:
        main()
