import matplotlib.pyplot as plt
import matplotlib.animation as animation
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

        # Otomatik kaydetme
        self.test_counter += 1
        if save_path is None:
            save_path = os.path.join(self.output_dir,
                f"session_{self.session_id}__test{self.test_counter:02d}_network.png")

        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f">> Grafik kaydedildi: {save_path}")
        plt.close()
        return save_path

    def plot_packet_path(self, network, packet_path: List[int],
                        title: str = "Paket Yolu", save_path: Optional[str] = None):
        """
        Belirli bir paket yolunu görselleştir ve kaydet
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

        # Başlık - ID'leri 5'erli gruplar halinde for loop yerine string join ile ekle, uzun yolları kes
        path_str = ' -> '.join(map(str, packet_path))
        if len(path_str) > 50:
            path_str = path_str[:47] + "..."

        self.ax.set_title(f"{title}\nYol: {path_str}",
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

        # Otomatik kaydetme
        self.test_counter += 1
        if save_path is None:
            packet_id = packet_path[0] if packet_path else 0
            # Dosya adını güvenli hale getir
            safe_title = "".join([c if c.isalnum() else "_" for c in title])[:30]
            save_path = os.path.join(self.output_dir,
                f"session_{self.session_id}__test{self.test_counter:02d}_{safe_title}.png")

        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f">> Grafik kaydedildi: {save_path}")
        plt.close()
        return save_path

    def animate_simulation(self, network, num_steps: int = 20,
                          failure_rate: float = 0.05,
                          interval: int = 1000,
                          save_path: Optional[str] = None):
        """
        Simülasyonu animasyon olarak göster
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

    # Network oluştur (Module import path fix)
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
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

class RoutingComparisonVisualizer:
    """
    Visualizer for comparing routing algorithm performance.
    
    Creates various plots and charts to compare different routing
    algorithms based on their performance metrics.
    """
    
    def __init__(self, output_dir: str = "visualization/outputs"):
        """
        Initialize comparison visualizer.
        
        Args:
            output_dir: Directory to save output plots
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        # Set style
        plt.style.use('seaborn-v0_8-darkgrid')
    
    def plot_metrics_comparison(self, metrics_dict: Dict[str, Dict], 
                               title: str = "Routing Algorithm Comparison",
                               save_path: Optional[str] = None):
        """
        Create bar charts comparing multiple metrics across algorithms.
        
        Args:
            metrics_dict: Dict mapping algorithm names to their summary stats
            title: Plot title
            save_path: Path to save the plot
        """
        fig, axes = plt.subplots(2, 3, figsize=(18, 10))
        fig.suptitle(title, fontsize=16, fontweight='bold', y=1.02)
        
        algorithms = list(metrics_dict.keys())
        colors = plt.cm.Set3(range(len(algorithms)))
        
        # 1. Delivery Rate
        ax = axes[0, 0]
        delivery_rates = [metrics_dict[algo]['delivery_rate'] * 100 
                         for algo in algorithms]
        bars = ax.bar(algorithms, delivery_rates, color=colors, edgecolor='black', linewidth=1.5)
        ax.set_ylabel('Delivery Rate (%)', fontweight='bold')
        ax.set_title('Delivery Rate', fontweight='bold')
        ax.set_ylim([0, 105])
        ax.grid(axis='y', alpha=0.3)
        
        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{height:.1f}%', ha='center', va='bottom', fontweight='bold')
        
        # 2. Average Latency
        ax = axes[0, 1]
        latencies = [metrics_dict[algo]['latency']['mean'] * 1000 
                    for algo in algorithms]
        bars = ax.bar(algorithms, latencies, color=colors, edgecolor='black', linewidth=1.5)
        ax.set_ylabel('Latency (ms)', fontweight='bold')
        ax.set_title('Average Latency', fontweight='bold')
        ax.grid(axis='y', alpha=0.3)
        
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{height:.2f}', ha='center', va='bottom', fontweight='bold')
        
        # 3. Average Hops
        ax = axes[0, 2]
        hops = [metrics_dict[algo]['hops']['mean'] for algo in algorithms]
        bars = ax.bar(algorithms, hops, color=colors, edgecolor='black', linewidth=1.5)
        ax.set_ylabel('Hops', fontweight='bold')
        ax.set_title('Average Hop Count', fontweight='bold')
        ax.grid(axis='y', alpha=0.3)
        
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{height:.2f}', ha='center', va='bottom', fontweight='bold')
        
        # 4. Network Efficiency
        ax = axes[1, 0]
        efficiency = [metrics_dict[algo]['network_efficiency'] 
                     for algo in algorithms]
        bars = ax.bar(algorithms, efficiency, color=colors, edgecolor='black', linewidth=1.5)
        ax.set_ylabel('Efficiency', fontweight='bold')
        ax.set_title('Network Efficiency', fontweight='bold')
        ax.grid(axis='y', alpha=0.3)
        
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{height:.4f}', ha='center', va='bottom', fontweight='bold')
        
        # 5. Throughput
        ax = axes[1, 1]
        throughput = [metrics_dict[algo]['throughput'] for algo in algorithms]
        bars = ax.bar(algorithms, throughput, color=colors, edgecolor='black', linewidth=1.5)
        ax.set_ylabel('Throughput (pkt/s)', fontweight='bold')
        ax.set_title('Throughput', fontweight='bold')
        ax.grid(axis='y', alpha=0.3)
        
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{height:.2f}', ha='center', va='bottom', fontweight='bold')
        
        # 6. Packet Loss Rate
        ax = axes[1, 2]
        loss_rates = [metrics_dict[algo]['loss_rate'] * 100 
                     for algo in algorithms]
        bars = ax.bar(algorithms, loss_rates, color=colors, edgecolor='black', linewidth=1.5)
        ax.set_ylabel('Loss Rate (%)', fontweight='bold')
        ax.set_title('Packet Loss Rate', fontweight='bold')
        ax.grid(axis='y', alpha=0.3)
        
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{height:.1f}%', ha='center', va='bottom', fontweight='bold')
        
        plt.tight_layout()
        
        if save_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            save_path = os.path.join(self.output_dir, f"metrics_comparison_{timestamp}.png")
        
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f">> Comparison plot saved: {save_path}")
        plt.close()
        
        return save_path
    
    def plot_latency_distribution(self, collectors: List, 
                                  title: str = "Latency Distribution",
                                  save_path: Optional[str] = None):
        """
        Plot latency distribution for multiple algorithms.
        
        Args:
            collectors: List of NetworkMetricsCollector objects
            title: Plot title
            save_path: Path to save the plot
        """
        fig, ax = plt.subplots(figsize=(12, 6))
        
        for collector in collectors:
            latencies = [m.latency * 1000 for m in collector.packet_metrics 
                        if m.is_successful and m.latency != float('inf')]
            
            if latencies:
                ax.hist(latencies, bins=20, alpha=0.6, label=collector.algorithm_name,
                       edgecolor='black', linewidth=1.2)
        
        ax.set_xlabel('Latency (ms)', fontsize=12, fontweight='bold')
        ax.set_ylabel('Frequency', fontsize=12, fontweight='bold')
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.legend(fontsize=11)
        ax.grid(alpha=0.3)
        
        plt.tight_layout()
        
        if save_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            save_path = os.path.join(self.output_dir, f"latency_dist_{timestamp}.png")
        
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f">> Latency distribution saved: {save_path}")
        plt.close()
        
        return save_path
    
    def plot_link_utilization_heatmap(self, collector, graph: nx.Graph,
                                     title: str = "Link Utilization Heatmap",
                                     save_path: Optional[str] = None):
        """
        Plot heatmap of link utilization.
        
        Args:
            collector: NetworkMetricsCollector object
            graph: NetworkX graph
            title: Plot title
            save_path: Path to save the plot
        """
        fig, ax = plt.subplots(figsize=(12, 10))
        
        pos = nx.spring_layout(graph, seed=42)
        
        # Get link usage
        link_usage = collector.get_link_usage_stats()
        max_usage = max(link_usage.values()) if link_usage else 1
        
        # Draw nodes
        nx.draw_networkx_nodes(graph, pos, node_size=300, 
                              node_color='lightblue', 
                              edgecolors='black', linewidths=2, ax=ax)
        
        # Draw edges with colors based on usage
        for edge in graph.edges():
            usage = link_usage.get(edge, link_usage.get((edge[1], edge[0]), 0))
            color_intensity = usage / max_usage if max_usage > 0 else 0
            
            nx.draw_networkx_edges(graph, pos, edgelist=[edge],
                                  edge_color=[plt.cm.YlOrRd(color_intensity)],
                                  width=2 + (usage / max_usage * 4) if max_usage > 0 else 2,
                                  alpha=0.8, ax=ax)
        
        # Draw labels
        nx.draw_networkx_labels(graph, pos, font_size=10, 
                               font_weight='bold', ax=ax)
        
        ax.set_title(f"{title}\n({collector.algorithm_name})", 
                    fontsize=14, fontweight='bold')
        ax.axis('off')
        
        # Add colorbar
        sm = plt.cm.ScalarMappable(cmap=plt.cm.YlOrRd, 
                                   norm=plt.Normalize(vmin=0, vmax=max_usage))
        sm.set_array([])
        cbar = plt.colorbar(sm, ax=ax, fraction=0.046, pad=0.04)
        cbar.set_label('Usage Count', fontweight='bold')
        
        plt.tight_layout()
        
        if save_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            save_path = os.path.join(self.output_dir, 
                                    f"link_heatmap_{collector.algorithm_name}_{timestamp}.png")
        
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f">> Link utilization heatmap saved: {save_path}")
        plt.close()
        
        return save_path
    
    def plot_performance_radar(self, metrics_dict: Dict[str, Dict],
                              title: str = "Performance Radar Chart",
                              save_path: Optional[str] = None):
        """
        Create radar chart comparing algorithms across multiple metrics.
        
        Args:
            metrics_dict: Dict mapping algorithm names to their summary stats
            title: Plot title
            save_path: Path to save the plot
        """
        from math import pi
        
        # Metrics to compare (normalize to 0-1 scale)
        metrics = ['Delivery\nRate', 'Network\nEfficiency', 'Throughput', 
                  'Low\nLatency', 'Low\nHops']
        
        fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(projection='polar'))
        
        algorithms = list(metrics_dict.keys())
        angles = [n / float(len(metrics)) * 2 * pi for n in range(len(metrics))]
        angles += angles[:1]
        
        ax.set_theta_offset(pi / 2)
        ax.set_theta_direction(-1)
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(metrics, fontsize=11, fontweight='bold')
        
        colors = plt.cm.Set2(range(len(algorithms)))
        
        for idx, algo in enumerate(algorithms):
            stats = metrics_dict[algo]
            
            # Normalize metrics to 0-1 scale (higher is better)
            max_latency = max(metrics_dict[a]['latency']['mean'] 
                            for a in algorithms if metrics_dict[a]['latency']['mean'] > 0)
            max_hops = max(metrics_dict[a]['hops']['mean'] 
                          for a in algorithms if metrics_dict[a]['hops']['mean'] > 0)
            max_throughput = max(metrics_dict[a]['throughput'] 
                               for a in algorithms if metrics_dict[a]['throughput'] > 0)
            
            values = [
                stats['delivery_rate'],
                stats['network_efficiency'],
                stats['throughput'] / max_throughput if max_throughput > 0 else 0,
                1 - (stats['latency']['mean'] / max_latency) if max_latency > 0 else 0,
                1 - (stats['hops']['mean'] / max_hops) if max_hops > 0 else 0
            ]
            values += values[:1]
            
            ax.plot(angles, values, 'o-', linewidth=2, label=algo, color=colors[idx])
            ax.fill(angles, values, alpha=0.15, color=colors[idx])
        
        ax.set_ylim(0, 1)
        ax.set_yticks([0.2, 0.4, 0.6, 0.8, 1.0])
        ax.set_yticklabels(['0.2', '0.4', '0.6', '0.8', '1.0'], fontsize=9)
        ax.grid(True, alpha=0.3)
        
        plt.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1), fontsize=11)
        plt.title(title, fontsize=14, fontweight='bold', pad=20)
        
        plt.tight_layout()
        
        if save_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            save_path = os.path.join(self.output_dir, f"performance_radar_{timestamp}.png")
        
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f">> Radar chart saved: {save_path}")
        plt.close()
        
        return save_path
    
    def create_comparison_dashboard(self, metrics_dict: Dict[str, Dict],
                                   collectors: List,
                                   graph: nx.Graph,
                                   title: str = "Routing Comparison Dashboard",
                                   save_path: Optional[str] = None):
        """
        Create comprehensive dashboard with multiple visualizations.
        
        Args:
            metrics_dict: Dict mapping algorithm names to their summary stats
            collectors: List of NetworkMetricsCollector objects
            graph: NetworkX graph
            title: Dashboard title
            save_path: Path to save the dashboard
        """
        fig = plt.figure(figsize=(20, 12))
        gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)
        
        fig.suptitle(title, fontsize=18, fontweight='bold', y=0.98)
        
        algorithms = list(metrics_dict.keys())
        colors = plt.cm.Set3(range(len(algorithms)))
        
        # 1. Delivery Rate Comparison
        ax1 = fig.add_subplot(gs[0, 0])
        delivery_rates = [metrics_dict[algo]['delivery_rate'] * 100 for algo in algorithms]
        bars = ax1.bar(algorithms, delivery_rates, color=colors, edgecolor='black', linewidth=1.5)
        ax1.set_ylabel('Delivery Rate (%)', fontweight='bold')
        ax1.set_title('Delivery Rate', fontweight='bold', fontsize=12)
        ax1.grid(axis='y', alpha=0.3)
        for bar in bars:
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.1f}%', ha='center', va='bottom', fontsize=9, fontweight='bold')
        
        # 2. Latency Comparison
        ax2 = fig.add_subplot(gs[0, 1])
        latencies = [metrics_dict[algo]['latency']['mean'] * 1000 for algo in algorithms]
        bars = ax2.bar(algorithms, latencies, color=colors, edgecolor='black', linewidth=1.5)
        ax2.set_ylabel('Latency (ms)', fontweight='bold')
        ax2.set_title('Average Latency', fontweight='bold', fontsize=12)
        ax2.grid(axis='y', alpha=0.3)
        for bar in bars:
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.2f}', ha='center', va='bottom', fontsize=9, fontweight='bold')
        
        # 3. Hop Count Comparison
        ax3 = fig.add_subplot(gs[0, 2])
        hops = [metrics_dict[algo]['hops']['mean'] for algo in algorithms]
        bars = ax3.bar(algorithms, hops, color=colors, edgecolor='black', linewidth=1.5)
        ax3.set_ylabel('Hops', fontweight='bold')
        ax3.set_title('Average Hop Count', fontweight='bold', fontsize=12)
        ax3.grid(axis='y', alpha=0.3)
        for bar in bars:
            height = bar.get_height()
            ax3.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.2f}', ha='center', va='bottom', fontsize=9, fontweight='bold')
        
        # 4. Latency Distribution
        ax4 = fig.add_subplot(gs[1, :2])
        for collector in collectors:
            latencies = [m.latency * 1000 for m in collector.packet_metrics 
                        if m.is_successful and m.latency != float('inf')]
            if latencies:
                ax4.hist(latencies, bins=15, alpha=0.6, label=collector.algorithm_name,
                        edgecolor='black', linewidth=1.2)
        ax4.set_xlabel('Latency (ms)', fontweight='bold')
        ax4.set_ylabel('Frequency', fontweight='bold')
        ax4.set_title('Latency Distribution', fontweight='bold', fontsize=12)
        ax4.legend()
        ax4.grid(alpha=0.3)
        
        # 5. Network Stats Summary
        ax5 = fig.add_subplot(gs[1, 2])
        ax5.axis('off')
        summary_text = "Network Summary\n" + "="*25 + "\n\n"
        summary_text += f"Nodes: {graph.number_of_nodes()}\n"
        summary_text += f"Edges: {graph.number_of_edges()}\n\n"
        
        for algo in algorithms:
            stats = metrics_dict[algo]
            summary_text += f"{algo}:\n"
            summary_text += f"  Packets: {stats['total_packets']}\n"
            summary_text += f"  Success: {stats['delivery_rate']*100:.1f}%\n"
            summary_text += f"  Efficiency: {stats['network_efficiency']:.4f}\n\n"
        
        ax5.text(0.1, 0.9, summary_text, transform=ax5.transAxes,
                fontsize=10, verticalalignment='top', fontfamily='monospace',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        # 6. Efficiency & Throughput
        ax6 = fig.add_subplot(gs[2, :])
        x = range(len(algorithms))
        width = 0.35
        
        efficiency = [metrics_dict[algo]['network_efficiency'] for algo in algorithms]
        throughput = [metrics_dict[algo]['throughput'] / 100 for algo in algorithms]  # Scale down
        
        bars1 = ax6.bar([i - width/2 for i in x], efficiency, width, 
                       label='Network Efficiency', color='skyblue', edgecolor='black', linewidth=1.5)
        bars2 = ax6.bar([i + width/2 for i in x], throughput, width,
                       label='Throughput (×100 pkt/s)', color='lightcoral', edgecolor='black', linewidth=1.5)
        
        ax6.set_ylabel('Value', fontweight='bold')
        ax6.set_title('Network Efficiency & Throughput', fontweight='bold', fontsize=12)
        ax6.set_xticks(x)
        ax6.set_xticklabels(algorithms)
        ax6.legend()
        ax6.grid(axis='y', alpha=0.3)
        
        for bars in [bars1, bars2]:
            for bar in bars:
                height = bar.get_height()
                ax6.text(bar.get_x() + bar.get_width()/2., height,
                        f'{height:.3f}', ha='center', va='bottom', fontsize=8)
        
        if save_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            save_path = os.path.join(self.output_dir, f"dashboard_{timestamp}.png")
        
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f">> Dashboard saved: {save_path}")
        plt.close()
        
        return save_path

class RoutingComparisonVisualizer:
    """Routing algoritmaları karşılaştırmasını görselleştiren sınıf"""
    
    def __init__(self, output_dir: str = "results/routing_comparison"):
        self.output_dir = output_dir
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
    
    def plot_metrics_comparison(self, collectors_dict: Dict, save_path: Optional[str] = None):
        """
        Farklı routing algoritmaları için metrikleri bar chart ile karşılaştırır.
        
        Args:
            collectors_dict: {algorithm_name: NetworkMetricsCollector}
            save_path: Kaydedilecek dosya yolu
        """
        # Metrikleri topla
        metrics_data = {}
        for algo_name, collector in collectors_dict.items():
            stats = collector.get_summary_stats()
            metrics_data[algo_name] = {
                'delivery_rate': stats['delivery_rate'] * 100,
                'loss_rate': stats['loss_rate'] * 100,
                'avg_latency': stats['latency']['mean'] * 1000,  # ms
                'avg_hops': stats['hops']['mean'],
                'efficiency': stats['network_efficiency'],
                'throughput': stats['throughput']
            }
        
        # 6 subplot oluştur
        fig, axes = plt.subplots(2, 3, figsize=(16, 10))
        fig.suptitle('Routing Algorithms Performance Comparison', fontsize=18, fontweight='bold')
        axes = axes.flatten()
        
        algorithms = list(metrics_data.keys())
        colors = ['#3498db', '#e74c3c', '#2ecc71', '#f39c12'][:len(algorithms)]
        
        # 1. Delivery Rate
        delivery_rates = [metrics_data[algo]['delivery_rate'] for algo in algorithms]
        axes[0].bar(algorithms, delivery_rates, color=colors, alpha=0.7, edgecolor='black')
        axes[0].set_ylabel('Delivery Rate (%)', fontweight='bold')
        axes[0].set_title('Delivery Rate', fontweight='bold')
        axes[0].set_ylim([0, 105])
        for i, v in enumerate(delivery_rates):
            axes[0].text(i, v + 2, f'{v:.1f}%', ha='center', fontweight='bold')
        
        # 2. Loss Rate
        loss_rates = [metrics_data[algo]['loss_rate'] for algo in algorithms]
        axes[1].bar(algorithms, loss_rates, color=colors, alpha=0.7, edgecolor='black')
        axes[1].set_ylabel('Loss Rate (%)', fontweight='bold')
        axes[1].set_title('Packet Loss Rate', fontweight='bold')
        axes[1].set_ylim([0, 105])
        for i, v in enumerate(loss_rates):
            axes[1].text(i, v + 2, f'{v:.1f}%', ha='center', fontweight='bold')
        
        # 3. Average Latency
        latencies = [metrics_data[algo]['avg_latency'] for algo in algorithms]
        axes[2].bar(algorithms, latencies, color=colors, alpha=0.7, edgecolor='black')
        axes[2].set_ylabel('Latency (ms)', fontweight='bold')
        axes[2].set_title('Average Latency', fontweight='bold')
        for i, v in enumerate(latencies):
            axes[2].text(i, v + 0.5, f'{v:.2f}ms', ha='center', fontweight='bold')
        
        # 4. Average Hops
        hops = [metrics_data[algo]['avg_hops'] for algo in algorithms]
        axes[3].bar(algorithms, hops, color=colors, alpha=0.7, edgecolor='black')
        axes[3].set_ylabel('Average Hops', fontweight='bold')
        axes[3].set_title('Average Hop Count', fontweight='bold')
        for i, v in enumerate(hops):
            axes[3].text(i, v + 0.1, f'{v:.2f}', ha='center', fontweight='bold')
        
        # 5. Network Efficiency
        efficiency = [metrics_data[algo]['efficiency'] for algo in algorithms]
        axes[4].bar(algorithms, efficiency, color=colors, alpha=0.7, edgecolor='black')
        axes[4].set_ylabel('Efficiency', fontweight='bold')
        axes[4].set_title('Network Efficiency', fontweight='bold')
        for i, v in enumerate(efficiency):
            axes[4].text(i, v + 0.01, f'{v:.4f}', ha='center', fontweight='bold')
        
        # 6. Throughput
        throughput = [metrics_data[algo]['throughput'] for algo in algorithms]
        axes[5].bar(algorithms, throughput, color=colors, alpha=0.7, edgecolor='black')
        axes[5].set_ylabel('Throughput (pkt/sec)', fontweight='bold')
        axes[5].set_title('Network Throughput', fontweight='bold')
        for i, v in enumerate(throughput):
            axes[5].text(i, v + 1, f'{v:.1f}', ha='center', fontweight='bold')
        
        plt.tight_layout()
        
        if save_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            save_path = os.path.join(self.output_dir, f"metrics_comparison_{timestamp}.png")
        
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f">> Metrics comparison saved: {save_path}")
        plt.close()
        
        return save_path
    
    def plot_latency_distribution(self, collectors_dict: Dict, save_path: Optional[str] = None):
        """
        Latency dağılımını histogram ile gösterir.
        
        Args:
            collectors_dict: {algorithm_name: NetworkMetricsCollector}
            save_path: Kaydedilecek dosya yolu
        """
        fig, ax = plt.subplots(figsize=(12, 6))
        
        algorithms = list(collectors_dict.keys())
        colors = ['#3498db', '#e74c3c', '#2ecc71', '#f39c12'][:len(algorithms)]
        
        for algo_name, collector, color in zip(algorithms, collectors_dict.values(), colors):
            packets = collector.packet_metrics
            latencies = [p.latency * 1000 for p in packets if p.is_successful and p.latency != float('inf')]
            
            if latencies:
                ax.hist(latencies, bins=20, alpha=0.6, label=algo_name, color=color, edgecolor='black')
        
        ax.set_xlabel('Latency (ms)', fontweight='bold', fontsize=12)
        ax.set_ylabel('Frequency', fontweight='bold', fontsize=12)
        ax.set_title('Latency Distribution Comparison', fontweight='bold', fontsize=14)
        ax.legend(fontsize=11)
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            save_path = os.path.join(self.output_dir, f"latency_distribution_{timestamp}.png")
        
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f">> Latency distribution saved: {save_path}")
        plt.close()
        
        return save_path
    
    def plot_link_utilization_heatmap(self, collectors_dict: Dict, graph: Optional[object] = None,
                                      save_path: Optional[str] = None):
        """
        Link kullanımını ısı haritası ile gösterir.
        
        Args:
            collectors_dict: {algorithm_name: NetworkMetricsCollector}
            graph: NetworkX graph (optional)
            save_path: Kaydedilecek dosya yolu
        """
        algorithms = list(collectors_dict.keys())
        fig, axes = plt.subplots(1, len(algorithms), figsize=(6*len(algorithms), 5))
        
        if len(algorithms) == 1:
            axes = [axes]
        
        for ax, algo_name, collector in zip(axes, algorithms, collectors_dict.values()):
            link_usage = collector.get_link_usage_stats()
            
            if not link_usage:
                ax.text(0.5, 0.5, 'No link usage data', ha='center', va='center',
                       transform=ax.transAxes, fontsize=12)
                ax.set_title(algo_name, fontweight='bold')
                continue
            
            # Link'leri sırala
            sorted_links = sorted(link_usage.items(), key=lambda x: x[1], reverse=True)[:15]
            link_names = [f"{u}-{v}" for (u, v), _ in sorted_links]
            link_values = [v for _, v in sorted_links]
            
            # Bar chart
            bars = ax.barh(link_names, link_values, color='#3498db', edgecolor='black')
            
            # Renk gradient
            max_val = max(link_values) if link_values else 1
            for i, bar in enumerate(bars):
                bar.set_color(plt.cm.RdYlGn_r(link_values[i] / max_val))
            
            ax.set_xlabel('Usage Count', fontweight='bold')
            ax.set_title(f'Top Links - {algo_name}', fontweight='bold')
            ax.grid(True, alpha=0.3, axis='x')
        
        plt.tight_layout()
        
        if save_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            save_path = os.path.join(self.output_dir, f"link_utilization_{timestamp}.png")
        
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f">> Link utilization heatmap saved: {save_path}")
        plt.close()
        
        return save_path
    
    def plot_performance_radar(self, collectors_dict: Dict, save_path: Optional[str] = None):
        """
        Radar chart ile çok boyutlu performans karşılaştırması.
        
        Args:
            collectors_dict: {algorithm_name: NetworkMetricsCollector}
            save_path: Kaydedilecek dosya yolu
        """
        from math import pi
        
        categories = ['Delivery Rate', 'Efficiency', 'Throughput', 'Low Latency', 'Few Hops']
        num_vars = len(categories)
        
        angles = [n / float(num_vars) * 2 * pi for n in range(num_vars)]
        angles += angles[:1]
        
        fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(projection='polar'))
        colors = ['#3498db', '#e74c3c', '#2ecc71', '#f39c12']
        
        for idx, (algo_name, collector) in enumerate(collectors_dict.items()):
            stats = collector.get_summary_stats()
            
            # Normalize metrikleri 0-1 aralığına
            values = [
                stats['delivery_rate'],  # 0-1
                stats['network_efficiency'],  # 0-1
                min(stats['throughput'] / 500, 1),  # Normalize to 0-1
                max(0, 1 - (stats['latency']['mean'] / 0.1)),  # Lower is better
                max(0, 1 - (stats['hops']['mean'] / 10))  # Lower is better
            ]
            
            values += values[:1]
            
            ax.plot(angles, values, 'o-', linewidth=2, label=algo_name, color=colors[idx % len(colors)])
            ax.fill(angles, values, alpha=0.15, color=colors[idx % len(colors)])
        
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(categories, size=11, fontweight='bold')
        ax.set_ylim(0, 1)
        ax.set_title('Performance Radar Chart', fontweight='bold', fontsize=14, pad=20)
        ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1), fontsize=11)
        ax.grid(True)
        
        plt.tight_layout()
        
        if save_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            save_path = os.path.join(self.output_dir, f"radar_chart_{timestamp}.png")
        
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f">> Radar chart saved: {save_path}")
        plt.close()
        
        return save_path
    
    def create_comparison_dashboard(self, collectors_dict: Dict, graph: Optional[object] = None,
                                   save_path: Optional[str] = None):
        """
        Tüm görselleştirmeleri tek bir comprehensive dashboard'da birleştirir.
        
        Args:
            collectors_dict: {algorithm_name: NetworkMetricsCollector}
            graph: NetworkX graph (optional)
            save_path: Kaydedilecek dosya yolu
        """
        # 4 ana grafik için figure
        fig = plt.figure(figsize=(20, 14))
        gs = fig.add_gridspec(3, 2, hspace=0.3, wspace=0.3)
        
        algorithms = list(collectors_dict.keys())
        colors = ['#3498db', '#e74c3c', '#2ecc71', '#f39c12'][:len(algorithms)]
        
        # 1. Metrics Comparison (top-left, large)
        ax1 = fig.add_subplot(gs[0:2, 0])
        metrics_data = {}
        for algo_name, collector in collectors_dict.items():
            stats = collector.get_summary_stats()
            metrics_data[algo_name] = stats['delivery_rate'] * 100
        
        bars = ax1.barh(algorithms, list(metrics_data.values()), color=colors, alpha=0.7, edgecolor='black')
        ax1.set_xlabel('Delivery Rate (%)', fontweight='bold')
        ax1.set_title('Delivery Rate Comparison', fontweight='bold', fontsize=12)
        ax1.set_xlim([0, 105])
        for i, v in enumerate(metrics_data.values()):
            ax1.text(v + 1, i, f'{v:.1f}%', va='center', fontweight='bold')
        
        # 2. Latency Comparison (top-right)
        ax2 = fig.add_subplot(gs[0, 1])
        latencies = {}
        for algo_name, collector in collectors_dict.items():
            stats = collector.get_summary_stats()
            latencies[algo_name] = stats['latency']['mean'] * 1000
        
        bars = ax2.bar(algorithms, list(latencies.values()), color=colors, alpha=0.7, edgecolor='black')
        ax2.set_ylabel('Latency (ms)', fontweight='bold')
        ax2.set_title('Average Latency', fontweight='bold', fontsize=11)
        for i, v in enumerate(latencies.values()):
            ax2.text(i, v + 0.1, f'{v:.2f}ms', ha='center', fontweight='bold', fontsize=9)
        
        # 3. Hops Comparison (middle-right)
        ax3 = fig.add_subplot(gs[1, 1])
        hops = {}
        for algo_name, collector in collectors_dict.items():
            stats = collector.get_summary_stats()
            hops[algo_name] = stats['hops']['mean']
        
        bars = ax3.bar(algorithms, list(hops.values()), color=colors, alpha=0.7, edgecolor='black')
        ax3.set_ylabel('Average Hops', fontweight='bold')
        ax3.set_title('Average Hop Count', fontweight='bold', fontsize=11)
        for i, v in enumerate(hops.values()):
            ax3.text(i, v + 0.05, f'{v:.2f}', ha='center', fontweight='bold', fontsize=9)
        
        # 4. Link Utilization (bottom-left)
        ax4 = fig.add_subplot(gs[2, 0])
        for idx, (algo_name, collector) in enumerate(collectors_dict.items()):
            link_usage = collector.get_link_usage_stats()
            usage_values = list(link_usage.values()) if link_usage else []
            if usage_values:
                avg_usage = sum(usage_values) / len(usage_values)
                ax4.bar(idx, avg_usage, color=colors[idx], alpha=0.7, edgecolor='black', width=0.6)
                ax4.text(idx, avg_usage + 0.1, f'{avg_usage:.1f}', ha='center', fontweight='bold')
        
        ax4.set_ylabel('Avg Link Usage', fontweight='bold')
        ax4.set_title('Average Link Utilization', fontweight='bold', fontsize=11)
        ax4.set_xticks(range(len(algorithms)))
        ax4.set_xticklabels(algorithms)
        
        # 5. Network Efficiency (bottom-right)
        ax5 = fig.add_subplot(gs[2, 1])
        efficiency = {}
        for algo_name, collector in collectors_dict.items():
            stats = collector.get_summary_stats()
            efficiency[algo_name] = stats['network_efficiency']
        
        bars = ax5.bar(algorithms, list(efficiency.values()), color=colors, alpha=0.7, edgecolor='black')
        ax5.set_ylabel('Efficiency', fontweight='bold')
        ax5.set_title('Network Efficiency', fontweight='bold', fontsize=11)
        for i, v in enumerate(efficiency.values()):
            ax5.text(i, v + 0.01, f'{v:.4f}', ha='center', fontweight='bold', fontsize=9)
        
        fig.suptitle('Routing Algorithms Comprehensive Dashboard', fontsize=16, fontweight='bold')
        
        if save_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            save_path = os.path.join(self.output_dir, f"dashboard_{timestamp}.png")
        
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f">> Dashboard saved: {save_path}")
        plt.close()
        
        return save_path

if __name__ == "__main__":
    network, visualizer = test_visualization()
