import matplotlib.pyplot as plt
import matplotlib.animation as animation
import networkx as nx
from typing import Dict, List, Optional
import numpy as np

class NetworkVisualizer:
    """
    Ağı görselleştiren sınıf
    Statik çizim ve animasyon desteği
    """

    def __init__(self, figsize=(12, 10)):
        """
        Görselleştirici başlatıcı

        Args:
            figsize: Figür boyutu (genişlik, yükseklik)
        """
        self.figsize = figsize
        self.fig = None
        self.ax = None

    def plot_network(self, network, title: str = "LifeNode Network",
                    show_labels: bool = True, save_path: Optional[str] = None):
        """
        Ağı statik olarak çiz

        Args:
            network: Network objesi
            title: Grafik başlığı
            show_labels: Node ID'lerini göster
            save_path: Kaydedilecek dosya yolu (None ise göster)
        """
        self.fig, self.ax = plt.subplots(figsize=self.figsize)

        # Graph'tan pozisyonları al
        pos = nx.get_node_attributes(network.graph, 'pos')

        # Node renklerini duruma göre ayarla
import networkx as nx
from typing import Dict, List, Optional
import os
from datetime import datetime
import random
import string

class NetworkVisualizer:
    """Ağı görselleştiren sınıf"""

    def __init__(self, figsize=(12, 10), output_dir="visualization/outputs"):
        self.figsize = figsize
        self.fig = None
        self.ax = None
        self.output_dir = output_dir
        self.test_counter = 0

        # Benzersiz session ID oluştur (her yeni visualizer için)
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + ''.join(random.choices(string.ascii_lowercase, k=4))

        # Output klasörünü oluştur
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            print(f">> Cikti klasoru olusturuldu: {self.output_dir}")

        print(f">> Session ID: {self.session_id}")

    def plot_network(self, network, title: str = "LifeNode Network",
                    show_labels: bool = True, save_path: Optional[str] = None):
        self.fig, self.ax = plt.subplots(figsize=self.figsize)
        pos = nx.get_node_attributes(network.graph, 'pos')

        node_colors = []
        for node_id in network.graph.nodes():
            if node_id in network.nodes:
                if network.nodes[node_id].is_active:
                    node_colors.append('#2ecc71')  # Yeşil - aktif
                else:
                    node_colors.append('#e74c3c')  # Kırmızı - pasif
            else:
                node_colors.append('#95a5a6')  # Gri - bilinmeyen

        # Node boyutlarını komşu sayısına göre ayarla
        node_sizes = []
        for node_id in network.graph.nodes():
            if node_id in network.nodes:
                neighbor_count = len(network.nodes[node_id].neighbors)
                size = 300 + (neighbor_count * 100)
                node_sizes.append(size)
            else:
                node_sizes.append(300)

        # Bağlantıları çiz (gri, ince)
        nx.draw_networkx_edges(network.graph, pos,
                              edge_color='#bdc3c7',
                              width=1.5,
                              alpha=0.6,
                              ax=self.ax)

        # Düğümleri çiz
        nx.draw_networkx_nodes(network.graph, pos,
                              node_color=node_colors,
                              node_size=node_sizes,
                              alpha=0.9,
                              edgecolors='black',
                              linewidths=2,
                              ax=self.ax)

        # Node ID'lerini göster
        if show_labels:
            nx.draw_networkx_labels(network.graph, pos,
                                   font_size=10,
                                   font_weight='bold',
                                   font_color='white',
                                   ax=self.ax)

        # Başlık ve bilgiler
        self.ax.set_title(title, fontsize=16, fontweight='bold', pad=20)

        # İstatistikleri göster
        stats = network.get_network_stats()
        info_text = (
            f"Toplam Düğüm: {stats['total_nodes']} | "
            f"Aktif: {stats['active_nodes']} | "
            f"Bağlantı: {network.graph.number_of_edges()}\n"
            f"Teslim Edilen Paket: {stats['delivered_packets']}/{stats['total_packets']} | "
            f"Başarı Oranı: {stats['delivery_rate']:.1%}"
        )
        self.ax.text(0.5, -0.05, info_text,
                    transform=self.ax.transAxes,
                    ha='center', va='top',
                    fontsize=11,
                    bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

        # Legend ekle
        from matplotlib.patches import Patch
        legend_elements = [
            Patch(facecolor='#2ecc71', edgecolor='black', label='Aktif Düğüm'),
            Patch(facecolor='#e74c3c', edgecolor='black', label='Pasif Düğüm')
        ]
        self.ax.legend(handles=legend_elements, loc='upper right', fontsize=10)
                    node_colors.append('#2ecc71')
                else:
                    node_colors.append('#e74c3c')
            else:
                node_colors.append('#95a5a6')

        nx.draw_networkx_edges(network.graph, pos, edge_color='#bdc3c7', width=1.5, alpha=0.6, ax=self.ax)
        nx.draw_networkx_nodes(network.graph, pos, node_color=node_colors, node_size=500,
                              alpha=0.9, edgecolors='black', linewidths=2, ax=self.ax)

        if show_labels:
            nx.draw_networkx_labels(network.graph, pos, font_size=10,
                                   font_weight='bold', font_color='white', ax=self.ax)

        self.ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
        stats = network.get_network_stats()
        info_text = (f"Toplam: {stats['total_nodes']} | Aktif: {stats['active_nodes']} | "
                    f"Paket Başarı: {stats['delivery_rate']:.1%}")
        self.ax.text(0.5, -0.05, info_text, transform=self.ax.transAxes, ha='center',
                    fontsize=11, bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

        self.ax.axis('off')
        self.ax.set_aspect('equal')
        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f">> Grafik kaydedildi: {save_path}")
        else:
            plt.show()

    def plot_packet_path(self, network, packet_path: List[int],
                        title: str = "Paket Yolu"):
        """
        Belirli bir paket yolunu görselleştir

        Args:
            network: Network objesi
            packet_path: Paket yolu [node_id1, node_id2, ...]
            title: Grafik başlığı
        """
        self.fig, self.ax = plt.subplots(figsize=self.figsize)

        pos = nx.get_node_attributes(network.graph, 'pos')

        # Tüm düğümleri soluk çiz
        node_colors = ['#ecf0f1' for _ in network.graph.nodes()]
        nx.draw_networkx_nodes(network.graph, pos,
                              node_color=node_colors,
                              node_size=400,
                              alpha=0.5,
                              ax=self.ax)

        # Tüm bağlantıları soluk çiz
        nx.draw_networkx_edges(network.graph, pos,
                              edge_color='#ecf0f1',
                              width=1,
                              alpha=0.3,
                              ax=self.ax)

        # Paket yolundaki düğümleri vurgula
        path_nodes = packet_path
        path_colors = ['#3498db' if i < len(path_nodes)-1 else '#e74c3c'
                      for i in range(len(path_nodes))]

        nx.draw_networkx_nodes(network.graph, pos,
                              nodelist=path_nodes,
                              node_color=path_colors,
                              node_size=600,
                              alpha=0.9,
                              edgecolors='black',
                              linewidths=3,
                              ax=self.ax)

        # Paket yolu bağlantılarını vurgula
        path_edges = [(path_nodes[i], path_nodes[i+1])
                     for i in range(len(path_nodes)-1)]
        nx.draw_networkx_edges(network.graph, pos,
                              edgelist=path_edges,
                              edge_color='#e67e22',
                              width=4,
                              alpha=0.8,
                              arrows=True,
                              arrowsize=20,
                              arrowstyle='->',
                              ax=self.ax)

        # Node ID'lerini göster
        nx.draw_networkx_labels(network.graph, pos,
                               font_size=10,
                               font_weight='bold',
                               ax=self.ax)

        # Başlık
        self.ax.set_title(f"{title}\nYol: {' -> '.join(map(str, packet_path))}",
                         fontsize=14, fontweight='bold')

        # Legend
        from matplotlib.patches import Patch
        legend_elements = [
            Patch(facecolor='#3498db', edgecolor='black', label='Ara Düğüm'),
            Patch(facecolor='#e74c3c', edgecolor='black', label='Hedef Düğüm'),
            Patch(facecolor='#e67e22', label='Paket Yolu')
        ]
        self.ax.legend(handles=legend_elements, loc='upper right')

        self.ax.axis('off')
        self.ax.set_aspect('equal')
        plt.tight_layout()
        plt.show()

    def animate_simulation(self, network, num_steps: int = 20,
                          failure_rate: float = 0.05,
                          interval: int = 1000,
                          save_path: Optional[str] = None):
        """
        Simülasyonu animasyon olarak göster

        Args:
            network: Network objesi
            num_steps: Animasyon adım sayısı
            failure_rate: Node arıza oranı
            interval: Kare arası gecikme (ms)
            save_path: GIF/MP4 kayıt yolu (None ise göster)
        """
        self.fig, self.ax = plt.subplots(figsize=self.figsize)

        pos = nx.get_node_attributes(network.graph, 'pos')

        def update(frame):
            self.ax.clear()

            # Simülasyon adımı
            if frame > 0:
                network.step(failure_rate)

            # Node renkleri
            node_colors = []
            for node_id in network.graph.nodes():
                if node_id in network.nodes:
                    if network.nodes[node_id].is_active:
                        node_colors.append('#2ecc71')
                    else:
                        node_colors.append('#e74c3c')
                else:
                    node_colors.append('#95a5a6')

            # Bağlantıları çiz
            nx.draw_networkx_edges(network.graph, pos,
                                  edge_color='#bdc3c7',
                                  width=1.5,
                                  alpha=0.6,
                                  ax=self.ax)

            # Düğümleri çiz
            nx.draw_networkx_nodes(network.graph, pos,
                                  node_color=node_colors,
                                  node_size=500,
                                  alpha=0.9,
                                  edgecolors='black',
                                  linewidths=2,
                                  ax=self.ax)

            # Labels
            nx.draw_networkx_labels(network.graph, pos,
                                   font_size=10,
                                   font_weight='bold',
                                   font_color='white',
                                   ax=self.ax)

            # Başlık ve bilgiler
            stats = network.get_network_stats()
            title = f"LifeNode Simülasyonu - Adım {frame}"
            info = (f"Aktif: {stats['active_nodes']}/{stats['total_nodes']} | "
                   f"Paket Başarı: {stats['delivery_rate']:.1%}")

            self.ax.set_title(f"{title}\n{info}", fontsize=14, fontweight='bold')
            self.ax.axis('off')
            self.ax.set_aspect('equal')

        anim = animation.FuncAnimation(self.fig, update,
                                       frames=num_steps,
                                       interval=interval,
                                       repeat=True)

        if save_path:
            if save_path.endswith('.gif'):
                anim.save(save_path, writer='pillow', fps=1)
            elif save_path.endswith('.mp4'):
                anim.save(save_path, writer='ffmpeg', fps=1)
            print(f">> Animasyon kaydedildi: {save_path}")
        else:
            plt.show()

        return anim

def test_visualization():
    """Görselleştirme test fonksiyonu"""
    print("=== GÖRSELLEŞTIRME TEST ===")

    # Network oluştur
    import sys
    sys.path.append('.')
    from simulation.network import Network

    network = Network(width=80.0, height=80.0)
    network.create_network(num_nodes=15, communication_range=30.0)

    # Birkaç paket gönder
    print("\n>> Paket gönderimi...")
    active_nodes = [nid for nid, node in network.nodes.items() if node.is_active]
    if len(active_nodes) >= 2:
        network.send_packet(active_nodes[0], active_nodes[-1])
        network.send_packet(active_nodes[1], active_nodes[-2])

    # Visualizer oluştur
    visualizer = NetworkVisualizer(figsize=(14, 12))

    # 1. Statik ağ görselleştirmesi
    print("\n>> Statik ağ çizimi...")
    visualizer.plot_network(network, title="LifeNode Ağ Topolojisi")

    # 2. Teslim edilen bir paket yolunu göster
    if network.delivered_packets:
        print("\n>> Paket yolu görselleştirmesi...")
        packet = network.delivered_packets[0]
        visualizer.plot_packet_path(network, packet.path,
                                   title=f"Paket {packet.id} Yolu")

    print("\n>> Test tamamlandı!")

    return network, visualizer

if __name__ == "__main__":
    network, visualizer = test_visualization()
        # Otomatik kaydetme
        self.test_counter += 1
        if save_path is None:
            save_path = os.path.join(self.output_dir,
                f"session_{self.session_id}__test{self.test_counter:02d}_network.png")

        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f">> Gorsel kaydedildi: {save_path}")
        plt.close()
        return save_path

    def plot_packet_path(self, network, packet_path: List[int], title: str = "Paket Yolu",
                        save_path: Optional[str] = None):
        self.fig, self.ax = plt.subplots(figsize=self.figsize)
        pos = nx.get_node_attributes(network.graph, 'pos')

        nx.draw_networkx_nodes(network.graph, pos, node_color='#ecf0f1',
                              node_size=400, alpha=0.5, ax=self.ax)
        nx.draw_networkx_edges(network.graph, pos, edge_color='#ecf0f1',
                              width=1, alpha=0.3, ax=self.ax)

        path_colors = ['#3498db' if i < len(packet_path)-1 else '#e74c3c'
                      for i in range(len(packet_path))]
        nx.draw_networkx_nodes(network.graph, pos, nodelist=packet_path,
                              node_color=path_colors, node_size=600, alpha=0.9,
                              edgecolors='black', linewidths=3, ax=self.ax)

        path_edges = [(packet_path[i], packet_path[i+1]) for i in range(len(packet_path)-1)]
        nx.draw_networkx_edges(network.graph, pos, edgelist=path_edges,
                              edge_color='#e67e22', width=4, alpha=0.8,
                              arrows=True, arrowsize=20, ax=self.ax)

        nx.draw_networkx_labels(network.graph, pos, font_size=10, font_weight='bold', ax=self.ax)
        self.ax.set_title(f"{title}\nYol: {' -> '.join(map(str, packet_path))}",
                         fontsize=14, fontweight='bold')
        self.ax.axis('off')
        plt.tight_layout()

        # Otomatik kaydetme
        self.test_counter += 1
        if save_path is None:
            packet_id = packet_path[0] if packet_path else 0
            save_path = os.path.join(self.output_dir,
                f"session_{self.session_id}__test{self.test_counter:02d}_packet{packet_id}.png")

        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f">> Gorsel kaydedildi: {save_path}")
        plt.close()
        return save_path
