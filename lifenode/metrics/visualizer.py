"""
Visualizer (Görselleştirici)

Matplotlib ile grafik oluşturma ve real-time görselleştirme.
"""

from typing import Dict, List, Optional, Tuple
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.animation import FuncAnimation
import numpy as np

from .collector import ExperimentMetrics


class Visualizer:
    """
    Görselleştirici

    Statik grafikler ve real-time animasyonlar oluşturur.
    """

    def __init__(self, style: str = 'dark_background'):
        """
        Args:
            style: Matplotlib stili
        """
        plt.style.use(style)

        # Renk paleti
        self.colors = {
            'primary': '#00D4AA',    # Turkuaz
            'secondary': '#FF6B6B',  # Kırmızı
            'tertiary': '#4ECDC4',   # Açık mavi
            'quaternary': '#FFE66D', # Sarı
            'background': '#1a1a2e',
            'grid': '#333355',
        }

        # Router renkleri
        self.router_colors = {
            'Dijkstra-Quality': '#00D4AA',
            'Dijkstra-Hop': '#4ECDC4',
            'RL-Q': '#FF6B6B',
            'AODV': '#FFE66D',
            'OLSR': '#A78BFA',
        }

    def get_router_color(self, router_name: str) -> str:
        """Router için renk döndür"""
        return self.router_colors.get(router_name, '#FFFFFF')

    # =========================================================================
    # STATİK GRAFİKLER
    # =========================================================================

    def plot_pdr_comparison(
        self,
        experiments: Dict[str, ExperimentMetrics],
        title: str = "Paket Teslim Oranı Karşılaştırması",
        save_path: Optional[str] = None
    ):
        """
        PDR bar chart karşılaştırması

        Args:
            experiments: Router adı -> metrikler
            title: Grafik başlığı
            save_path: Kayıt yolu (opsiyonel)
        """
        fig, ax = plt.subplots(figsize=(10, 6))

        names = list(experiments.keys())
        pdrs = [m.packet_delivery_ratio * 100 for m in experiments.values()]
        colors = [self.get_router_color(n) for n in names]

        bars = ax.bar(names, pdrs, color=colors, edgecolor='white', linewidth=1.5)

        # Değerleri bar üzerine yaz
        for bar, pdr in zip(bars, pdrs):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 1,
                f'{pdr:.1f}%',
                ha='center',
                fontsize=12,
                fontweight='bold',
                color='white'
            )

        ax.set_ylabel('PDR (%)', fontsize=12)
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.set_ylim(0, 110)
        ax.grid(axis='y', alpha=0.3, color=self.colors['grid'])

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')

        return fig, ax

    def plot_latency_distribution(
        self,
        experiments: Dict[str, ExperimentMetrics],
        title: str = "Gecikme Dağılımı",
        save_path: Optional[str] = None
    ):
        """
        Latency histogram karşılaştırması

        Args:
            experiments: Router adı -> metrikler
            title: Grafik başlığı
            save_path: Kayıt yolu
        """
        fig, ax = plt.subplots(figsize=(12, 6))

        for name, metrics in experiments.items():
            if metrics.latencies:
                ax.hist(
                    metrics.latencies,
                    bins=30,
                    alpha=0.5,
                    label=name,
                    color=self.get_router_color(name),
                    edgecolor='white',
                    linewidth=0.5
                )

        ax.set_xlabel('Gecikme (ms)', fontsize=12)
        ax.set_ylabel('Frekans', fontsize=12)
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.legend()
        ax.grid(alpha=0.3, color=self.colors['grid'])

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')

        return fig, ax

    def plot_metrics_over_time(
        self,
        metrics: ExperimentMetrics,
        title: str = "Zaman Serisi Metrikleri",
        save_path: Optional[str] = None
    ):
        """
        Zaman serisi grafikleri (PDR, latency, topology)

        Args:
            metrics: Deney metrikleri
            title: Grafik başlığı
            save_path: Kayıt yolu
        """
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))

        # PDR over time
        ax1 = axes[0, 0]
        ax1.plot(
            metrics.pdr_over_time,
            color=self.colors['primary'],
            linewidth=2
        )
        ax1.set_ylabel('PDR')
        ax1.set_title('Paket Teslim Oranı')
        ax1.set_ylim(0, 1.1)
        ax1.grid(alpha=0.3)

        # Latency over time
        ax2 = axes[0, 1]
        ax2.plot(
            metrics.latency_over_time,
            color=self.colors['secondary'],
            linewidth=2
        )
        ax2.set_ylabel('Gecikme (ms)')
        ax2.set_title('Ortalama Gecikme')
        ax2.grid(alpha=0.3)

        # Active nodes
        ax3 = axes[1, 0]
        ax3.plot(
            metrics.active_nodes_over_time,
            color=self.colors['tertiary'],
            linewidth=2
        )
        ax3.set_xlabel('Adım')
        ax3.set_ylabel('Aktif Düğüm')
        ax3.set_title('Ağ Topolojisi - Düğümler')
        ax3.grid(alpha=0.3)

        # Active links
        ax4 = axes[1, 1]
        ax4.plot(
            metrics.active_links_over_time,
            color=self.colors['quaternary'],
            linewidth=2
        )
        ax4.set_xlabel('Adım')
        ax4.set_ylabel('Aktif Bağlantı')
        ax4.set_title('Ağ Topolojisi - Bağlantılar')
        ax4.grid(alpha=0.3)

        fig.suptitle(title, fontsize=16, fontweight='bold')
        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')

        return fig, axes

    def plot_comparison_summary(
        self,
        experiments: Dict[str, ExperimentMetrics],
        title: str = "Performans Özeti",
        save_path: Optional[str] = None
    ):
        """
        Tüm metrikleri gösteren özet grafik

        Args:
            experiments: Router adı -> metrikler
            title: Grafik başlığı
            save_path: Kayıt yolu
        """
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))

        names = list(experiments.keys())
        colors = [self.get_router_color(n) for n in names]

        # PDR
        ax1 = axes[0, 0]
        pdrs = [m.packet_delivery_ratio * 100 for m in experiments.values()]
        ax1.bar(names, pdrs, color=colors, edgecolor='white')
        ax1.set_ylabel('PDR (%)')
        ax1.set_title('Paket Teslim Oranı')
        ax1.set_ylim(0, 110)

        # Latency
        ax2 = axes[0, 1]
        latencies = [m.average_latency for m in experiments.values()]
        ax2.bar(names, latencies, color=colors, edgecolor='white')
        ax2.set_ylabel('Gecikme (ms)')
        ax2.set_title('Ortalama Gecikme')

        # Hops
        ax3 = axes[1, 0]
        hops = [m.average_hops for m in experiments.values()]
        ax3.bar(names, hops, color=colors, edgecolor='white')
        ax3.set_ylabel('Hop Sayısı')
        ax3.set_title('Ortalama Hop')

        # Dropped packets
        ax4 = axes[1, 1]
        dropped = [m.total_packets_dropped for m in experiments.values()]
        ax4.bar(names, dropped, color=colors, edgecolor='white')
        ax4.set_ylabel('Paket Sayısı')
        ax4.set_title('Düşürülen Paketler')

        fig.suptitle(title, fontsize=16, fontweight='bold')
        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')

        return fig, axes

    # =========================================================================
    # REAL-TIME GÖRSELLEŞTİRME
    # =========================================================================

    def create_network_figure(self) -> Tuple[plt.Figure, plt.Axes]:
        """
        Ağ görselleştirmesi için figure oluştur

        Returns:
            (Figure, Axes) tuple
        """
        fig, ax = plt.subplots(figsize=(12, 10))
        ax.set_xlim(-10, 510)
        ax.set_ylim(-10, 510)
        ax.set_aspect('equal')
        ax.set_facecolor(self.colors['background'])
        fig.set_facecolor(self.colors['background'])
        ax.grid(True, alpha=0.2, color=self.colors['grid'])

        return fig, ax

    def draw_network_state(
        self,
        ax: plt.Axes,
        nodes: Dict,
        links: Dict,
        packets_in_flight: List = None,
        clear: bool = True
    ):
        """
        Ağ durumunu çiz

        Args:
            ax: Matplotlib axes
            nodes: Düğüm sözlüğü
            links: Bağlantı sözlüğü
            packets_in_flight: Aktif paketler
            clear: Önceki çizimleri temizle
        """
        if clear:
            ax.clear()
            ax.set_xlim(-10, 510)
            ax.set_ylim(-10, 510)
            ax.set_facecolor(self.colors['background'])
            ax.grid(True, alpha=0.2, color=self.colors['grid'])

        # Bağlantıları çiz
        for link in links.values():
            if not link.is_active:
                continue

            node_a = nodes.get(link.node_a)
            node_b = nodes.get(link.node_b)

            if node_a and node_b:
                alpha = 0.3 + 0.7 * link.quality
                ax.plot(
                    [node_a.position[0], node_b.position[0]],
                    [node_a.position[1], node_b.position[1]],
                    color=self.colors['tertiary'],
                    alpha=alpha,
                    linewidth=1 + link.quality * 2,
                    zorder=1
                )

        # Düğümleri çiz
        for node in nodes.values():
            if node.is_active:
                color = self.colors['primary']
                # Enerji seviyesine göre renk
                if node.energy < 20:
                    color = self.colors['secondary']
                elif node.energy < 50:
                    color = self.colors['quaternary']

                size = 80 + node.energy * 1.5
            else:
                color = '#444444'
                size = 50

            ax.scatter(
                node.position[0],
                node.position[1],
                c=color,
                s=size,
                edgecolors='white',
                linewidths=1,
                zorder=2
            )

            # Düğüm ID'si
            ax.annotate(
                node.id,
                (node.position[0], node.position[1] + 12),
                fontsize=8,
                ha='center',
                color='white',
                alpha=0.8
            )

        # Paketleri çiz (opsiyonel)
        if packets_in_flight:
            for packet in packets_in_flight[:20]:  # Max 20 paket göster
                current_node = nodes.get(packet.current_node)
                if current_node and current_node.is_active:
                    ax.scatter(
                        current_node.position[0] + 5,
                        current_node.position[1] + 5,
                        c=self.colors['quaternary'],
                        s=30,
                        marker='s',
                        zorder=3
                    )

    def show(self):
        """Grafikleri göster"""
        plt.show()

    def close_all(self):
        """Tüm grafikleri kapat"""
        plt.close('all')
