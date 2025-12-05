import matplotlib.pyplot as plt
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