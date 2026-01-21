#!/usr/bin/env python3
"""
LifeNode CLI - İnteraktif Komut Satırı Arayüzü

Kullanım:
    python cli.py
"""

import sys
import os
import time
from typing import Optional, Dict, List
from dataclasses import dataclass

# Rich kütüphanesi
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.progress import (
        Progress,
        SpinnerColumn,
        BarColumn,
        TextColumn,
        TimeElapsedColumn,
    )
    from rich.prompt import Prompt, IntPrompt, FloatPrompt, Confirm
    from rich.text import Text
    from rich.layout import Layout
    from rich.live import Live
    from rich import box
    from rich.markdown import Markdown
    from rich.syntax import Syntax

    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    print("Rich kütüphanesi bulunamadı. Yükleniyor...")
    os.system("pip install rich")
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.progress import (
        Progress,
        SpinnerColumn,
        BarColumn,
        TextColumn,
        TimeElapsedColumn,
    )
    from rich.prompt import Prompt, IntPrompt, FloatPrompt, Confirm
    from rich.text import Text
    from rich.layout import Layout
    from rich.live import Live
    from rich import box
    from rich.markdown import Markdown
    from rich.syntax import Syntax

# Proje modülleri
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lifenode.config import SimulationConfig, WorldConfig
from lifenode.environment.world import World
from lifenode.routing.dijkstra import DijkstraRouter
from lifenode.routing.aodv import AODVRouter
from lifenode.rl_agent.rl_router import RLRouter
from lifenode.rl_agent.qlearning import QLearningConfig
from lifenode.scenarios.earthquake import EarthquakeScenario
from lifenode.scenarios.gradual_failure import GradualFailureScenario
from lifenode.metrics.collector import MetricCollector
from lifenode.metrics.visualizer import Visualizer

console = Console()


# =============================================================================
# KONFIGÜRASYON
# =============================================================================


@dataclass
class CLIConfig:
    """CLI konfigürasyonu"""

    num_nodes: int = 40
    num_steps: int = 500
    seed: int = 42
    rl_episodes: int = 30
    rl_steps_per_episode: int = 300
    learning_rate: float = 0.1
    discount_factor: float = 0.95
    epsilon: float = 0.3
    output_dir: str = "results"
    model_dir: str = "models"


config = CLIConfig()


# =============================================================================
# BANNER VE MENÜLER
# =============================================================================

BANNER = """
[bold cyan]
██╗     ██╗███████╗███████╗███╗   ██╗ ██████╗ ██████╗ ███████╗
██║     ██║██╔════╝██╔════╝████╗  ██║██╔═══██╗██╔══██╗██╔════╝
██║     ██║█████╗  █████╗  ██╔██╗ ██║██║   ██║██║  ██║█████╗
██║     ██║██╔══╝  ██╔══╝  ██║╚██╗██║██║   ██║██║  ██║██╔══╝
███████╗██║██║     ███████╗██║ ╚████║╚██████╔╝██████╔╝███████╗
╚══════╝╚═╝╚═╝     ╚══════╝╚═╝  ╚═══╝ ╚═════╝ ╚═════╝ ╚══════╝
[/bold cyan]
[dim]AI-Driven Dynamic Routing Simulation for Ad-Hoc Networks[/dim]
"""


def show_banner():
    """Banner göster"""
    console.clear()
    console.print(BANNER, justify="center")
    console.print()


def show_main_menu():
    """Ana menüyü göster"""
    table = Table(show_header=False, box=box.ROUNDED, border_style="cyan")
    table.add_column("No", style="bold yellow", width=4)
    table.add_column("Seçenek", style="white")
    table.add_column("Açıklama", style="dim")

    table.add_row("1", "🧠 RL Eğitimi", "Reinforcement Learning ajanını eğit")
    table.add_row("2", "🔬 Karşılaştırma", "Routing algoritmalarını karşılaştır")
    table.add_row("3", "📊 Grafikler", "Sonuçları görselleştir")
    table.add_row("4", "🌋 Afet Simülasyonu", "Deprem/arıza senaryosu çalıştır")
    table.add_row("5", "⚙️  Ayarlar", "Konfigürasyonu düzenle")
    table.add_row("6", "📁 Sonuçları Görüntüle", "Kayıtlı sonuçları listele")
    table.add_row("0", "🚪 Çıkış", "Programdan çık")

    console.print(Panel(table, title="[bold]Ana Menü[/bold]", border_style="cyan"))


# =============================================================================
# RL EĞİTİMİ
# =============================================================================


def train_rl_menu():
    """RL eğitimi menüsü"""
    show_banner()
    console.print(Panel("[bold]🧠 RL Eğitimi[/bold]", border_style="green"))

    # Parametreleri göster/değiştir
    table = Table(title="Eğitim Parametreleri", box=box.SIMPLE)
    table.add_column("Parametre", style="cyan")
    table.add_column("Değer", style="yellow")

    table.add_row("Episode Sayısı", str(config.rl_episodes))
    table.add_row("Adım/Episode", str(config.rl_steps_per_episode))
    table.add_row("Learning Rate", str(config.learning_rate))
    table.add_row("Discount Factor", str(config.discount_factor))
    table.add_row("Epsilon", str(config.epsilon))
    table.add_row("Düğüm Sayısı", str(config.num_nodes))

    console.print(table)
    console.print()

    if Confirm.ask("Parametreleri değiştirmek ister misiniz?", default=False):
        config.rl_episodes = IntPrompt.ask("Episode sayısı", default=config.rl_episodes)
        config.rl_steps_per_episode = IntPrompt.ask(
            "Adım/Episode", default=config.rl_steps_per_episode
        )
        config.learning_rate = FloatPrompt.ask(
            "Learning Rate", default=config.learning_rate
        )
        config.epsilon = FloatPrompt.ask("Epsilon (keşif)", default=config.epsilon)

    if not Confirm.ask("\n[bold green]Eğitimi başlat?[/bold green]", default=True):
        return None

    console.print()
    return run_rl_training()


def run_rl_training() -> Optional[RLRouter]:
    """RL eğitimini çalıştır"""

    # World oluştur
    sim_config = SimulationConfig(
        world=WorldConfig(width=500, height=500, initial_node_count=config.num_nodes)
    )

    # RL Router oluştur
    rl_config = QLearningConfig(
        learning_rate=config.learning_rate,
        discount_factor=config.discount_factor,
        epsilon_start=config.epsilon,
        epsilon_end=0.05,
        epsilon_decay=0.995,
    )

    rl_router = RLRouter(training_mode=True, ql_config=rl_config)

    best_pdr = 0.0
    episode_results = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(bar_width=40),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        console=console,
    ) as progress:

        task = progress.add_task(
            f"[cyan]Eğitim ({config.rl_episodes} episode)...", total=config.rl_episodes
        )

        for episode in range(config.rl_episodes):
            world = World(config=sim_config, seed=config.seed + episode)
            world.initialize_random_nodes(count=config.num_nodes)
            world.set_router(rl_router)
            collector = MetricCollector()

            for step in range(config.rl_steps_per_episode):
                result = world.step()

                for _ in range(result.packets_sent):
                    collector.record_packet_sent()
                for pr in result.delivered_packets:
                    collector.record_result(pr)
                for pr in result.dropped_packets:
                    collector.record_result(pr)

            collector.finalize()
            metrics = collector.get_metrics()
            pdr = metrics.packet_delivery_ratio

            episode_results.append(
                {
                    "episode": episode + 1,
                    "pdr": pdr,
                    "latency": metrics.average_latency,
                    "delivered": metrics.total_packets_delivered,
                }
            )

            if pdr > best_pdr:
                best_pdr = pdr

            # Progress güncelle
            progress.update(
                task,
                advance=1,
                description=f"[cyan]Episode {episode+1}/{config.rl_episodes} | PDR: {pdr*100:.1f}% | Best: {best_pdr*100:.1f}%",
            )

    # Eğitim modunu kapat
    rl_router.training_mode = False

    # Sonuçları göster
    console.print()
    show_training_results(episode_results, rl_router)

    # Model kaydet
    if Confirm.ask("\n[yellow]Modeli kaydetmek ister misiniz?[/yellow]", default=True):
        save_model(rl_router)

    return rl_router


def show_training_results(results: List[Dict], router: RLRouter):
    """Eğitim sonuçlarını göster"""

    # Özet panel
    avg_pdr = sum(r["pdr"] for r in results) / len(results)
    best_pdr = max(r["pdr"] for r in results)
    final_pdr = results[-1]["pdr"]

    stats = router.get_stats()

    summary = f"""
[bold green]✅ Eğitim Tamamlandı![/bold green]

📊 [cyan]Performans Özeti:[/cyan]
   • Ortalama PDR: [yellow]{avg_pdr*100:.2f}%[/yellow]
   • En İyi PDR: [green]{best_pdr*100:.2f}%[/green]
   • Son PDR: [yellow]{final_pdr*100:.2f}%[/yellow]

🧠 [cyan]Q-Table İstatistikleri:[/cyan]
   • Durum Sayısı: [yellow]{stats.get('q_table_size', 'N/A')}[/yellow]
   • Toplam Karar: [yellow]{stats.get('total_decisions', 'N/A')}[/yellow]
   • Epsilon: [yellow]{stats.get('current_epsilon', 'N/A')}[/yellow]
"""
    console.print(Panel(summary, title="Eğitim Sonuçları", border_style="green"))

    # Son 10 episode tablosu
    table = Table(title="Son 10 Episode", box=box.SIMPLE)
    table.add_column("Episode", style="cyan", justify="center")
    table.add_column("PDR", style="yellow", justify="center")
    table.add_column("Latency (ms)", style="white", justify="center")
    table.add_column("Teslim", style="green", justify="center")

    for r in results[-10:]:
        pdr_color = "green" if r["pdr"] > avg_pdr else "red"
        table.add_row(
            str(r["episode"]),
            f"[{pdr_color}]{r['pdr']*100:.1f}%[/{pdr_color}]",
            f"{r['latency']:.2f}",
            str(r["delivered"]),
        )

    console.print(table)


def save_model(router: RLRouter):
    """Modeli kaydet"""
    os.makedirs(config.model_dir, exist_ok=True)

    filename = Prompt.ask(
        "Dosya adı", default=f"rl_model_{time.strftime('%Y%m%d_%H%M%S')}.pkl"
    )

    filepath = os.path.join(config.model_dir, filename)
    router.save_model(filepath)

    console.print(f"[green]✅ Model kaydedildi: {filepath}[/green]")


# =============================================================================
# KARŞILAŞTIRMA
# =============================================================================


def comparison_menu():
    """Karşılaştırma menüsü"""
    show_banner()
    console.print(
        Panel("[bold]🔬 Algoritma Karşılaştırması[/bold]", border_style="blue")
    )

    # Algoritma seçimi
    console.print("\n[cyan]Test edilecek algoritmalar:[/cyan]")

    algorithms = {
        "1": ("Dijkstra (Quality)", True),
        "2": ("Dijkstra (Hop)", True),
        "3": ("AODV", True),
        "4": ("RL Agent", True),
    }

    for key, (name, _) in algorithms.items():
        console.print(f"  [{key}] {name}")

    # Senaryo seçimi
    console.print("\n[cyan]Senaryo seçin:[/cyan]")
    scenarios = {
        "1": ("Normal (Afetsiz)", None),
        "2": ("Kademeli Arıza", "gradual"),
        "3": ("Deprem (Orta)", "earthquake"),
        "4": ("Deprem (Şiddetli)", "severe_earthquake"),
        "5": ("Tüm Senaryolar", "all"),
    }

    for key, (name, _) in scenarios.items():
        console.print(f"  [{key}] {name}")

    scenario_choice = Prompt.ask(
        "\nSenaryo", choices=["1", "2", "3", "4", "5"], default="1"
    )

    # RL modeli yükle veya eğit
    rl_router = None
    if Confirm.ask("\n[yellow]RL Agent dahil edilsin mi?[/yellow]", default=True):
        model_files = list_model_files()

        if model_files and Confirm.ask("Kayıtlı model yüklensin mi?", default=True):
            rl_router = load_model_menu(model_files)

        if rl_router is None:
            console.print("[yellow]RL Agent eğitiliyor...[/yellow]")
            rl_router = run_rl_training()

    if not Confirm.ask(
        "\n[bold green]Karşılaştırmayı başlat?[/bold green]", default=True
    ):
        return

    # Karşılaştırmayı çalıştır
    run_comparison(scenarios[scenario_choice][1], rl_router)


def run_comparison(scenario_type: Optional[str], rl_router: Optional[RLRouter] = None):
    """Karşılaştırma çalıştır"""

    results = {}

    # Router'ları hazırla
    routers = {
        "Dijkstra-Quality": DijkstraRouter(use_quality_weights=True),
        "Dijkstra-Hop": DijkstraRouter(use_quality_weights=False),
        "AODV": AODVRouter(),
    }

    if rl_router:
        routers["RL-Agent"] = rl_router

    # Senaryoları hazırla
    if scenario_type == "all":
        scenarios = {
            "Normal": None,
            "Kademeli Arıza": GradualFailureScenario(
                start_step=100, failure_rate=0.03, recovery_rate=0.01
            ),
            "Deprem": EarthquakeScenario(
                epicenter=(250, 250), radius=200, intensity=0.6, trigger_step=150
            ),
        }
    elif scenario_type == "gradual":
        scenarios = {
            "Kademeli Arıza": GradualFailureScenario(
                start_step=100, failure_rate=0.03, recovery_rate=0.01
            )
        }
    elif scenario_type == "earthquake":
        scenarios = {
            "Deprem": EarthquakeScenario(
                epicenter=(250, 250), radius=200, intensity=0.6, trigger_step=150
            )
        }
    elif scenario_type == "severe_earthquake":
        scenarios = {
            "Şiddetli Deprem": EarthquakeScenario(
                epicenter=(250, 250), radius=300, intensity=0.8, trigger_step=100
            )
        }
    else:
        scenarios = {"Normal": None}

    total_tests = len(routers) * len(scenarios)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(bar_width=40),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        console=console,
    ) as progress:

        task = progress.add_task("[cyan]Karşılaştırma...", total=total_tests)

        for scenario_name, scenario in scenarios.items():
            results[scenario_name] = {}

            for router_name, router in routers.items():
                progress.update(
                    task, description=f"[cyan]{scenario_name} - {router_name}"
                )

                # Simülasyon çalıştır
                sim_config = SimulationConfig(
                    world=WorldConfig(
                        width=500,
                        height=500,
                        initial_node_count=config.num_nodes,
                        seed=config.seed,
                    )
                )

                router.reset()
                world = World(config=sim_config, seed=config.seed)
                world.initialize_random_nodes(count=config.num_nodes)
                world.set_router(router)

                if scenario:
                    scenario.reset()

                collector = MetricCollector()

                for step in range(config.num_steps):
                    if scenario:
                        scenario.apply(world, step)

                    result = world.step()

                    for _ in range(result.packets_sent):
                        collector.record_packet_sent()
                    for pr in result.delivered_packets:
                        collector.record_result(pr)
                    for pr in result.dropped_packets:
                        collector.record_result(pr)

                    collector.record_step(result.active_nodes, result.active_links)

                collector.finalize()
                metrics = collector.get_metrics()

                results[scenario_name][router_name] = {
                    "pdr": metrics.packet_delivery_ratio,
                    "latency": metrics.average_latency,
                    "hops": metrics.average_hops,
                    "delivered": metrics.total_packets_delivered,
                    "dropped": metrics.total_packets_dropped,
                    "metrics": metrics,
                }

                progress.update(task, advance=1)

    # Sonuçları göster
    show_comparison_results(results)

    # Kaydet
    if Confirm.ask(
        "\n[yellow]Sonuçları kaydetmek ister misiniz?[/yellow]", default=True
    ):
        save_comparison_results(results)

    return results


def show_comparison_results(results: Dict):
    """Karşılaştırma sonuçlarını göster"""

    console.print()

    for scenario_name, scenario_results in results.items():
        # Kazananı bul
        best_router = max(scenario_results.items(), key=lambda x: x[1]["pdr"])

        table = Table(title=f"📊 {scenario_name}", box=box.ROUNDED, border_style="cyan")

        table.add_column("Algoritma", style="bold")
        table.add_column("PDR", justify="center")
        table.add_column("Latency (ms)", justify="center")
        table.add_column("Hop", justify="center")
        table.add_column("Teslim", justify="center", style="green")
        table.add_column("Düşen", justify="center", style="red")

        for router_name, data in sorted(
            scenario_results.items(), key=lambda x: -x[1]["pdr"]
        ):
            is_best = router_name == best_router[0]
            pdr_str = (
                f"[bold green]{data['pdr']*100:.1f}%[/bold green] 🏆"
                if is_best
                else f"{data['pdr']*100:.1f}%"
            )

            table.add_row(
                f"[bold]{router_name}[/bold]" if is_best else router_name,
                pdr_str,
                f"{data['latency']:.2f}",
                f"{data['hops']:.1f}",
                str(data["delivered"]),
                str(data["dropped"]),
            )

        console.print(table)
        console.print()

    # Genel özet
    if len(results) > 1:
        show_overall_summary(results)


def show_overall_summary(results: Dict):
    """Genel özet göster"""

    # Her senaryonun kazananını bul
    winners = {}
    for scenario_name, scenario_results in results.items():
        best = max(scenario_results.items(), key=lambda x: x[1]["pdr"])
        winners[scenario_name] = best[0]

    # En çok kazanan
    from collections import Counter

    winner_counts = Counter(winners.values())
    champion = winner_counts.most_common(1)[0]

    summary = f"""
[bold cyan]🏆 GENEL SONUÇ[/bold cyan]

Senaryo Kazananları:
"""
    for scenario, winner in winners.items():
        summary += f"   • {scenario}: [yellow]{winner}[/yellow]\n"

    summary += f"""
[bold green]📢 ŞAMPIYON: {champion[0]}[/bold green] ({champion[1]}/{len(results)} senaryo)
"""

    console.print(Panel(summary, border_style="green"))


def save_comparison_results(results: Dict):
    """Karşılaştırma sonuçlarını kaydet"""
    import json

    os.makedirs(config.output_dir, exist_ok=True)

    # JSON formatına dönüştür
    json_results = {}
    for scenario, scenario_results in results.items():
        json_results[scenario] = {}
        for router, data in scenario_results.items():
            json_results[scenario][router] = {
                "pdr": data["pdr"],
                "latency": data["latency"],
                "hops": data["hops"],
                "delivered": data["delivered"],
                "dropped": data["dropped"],
            }

    filename = f"comparison_{time.strftime('%Y%m%d_%H%M%S')}.json"
    filepath = os.path.join(config.output_dir, filename)

    with open(filepath, "w") as f:
        json.dump(json_results, f, indent=2)

    console.print(f"[green]✅ Sonuçlar kaydedildi: {filepath}[/green]")


# =============================================================================
# GRAFİKLER
# =============================================================================


def visualization_menu():
    """Görselleştirme menüsü"""
    show_banner()
    console.print(Panel("[bold]📊 Görselleştirme[/bold]", border_style="magenta"))

    console.print("\n[cyan]Seçenekler:[/cyan]")
    options = {
        "1": "Kayıtlı sonuçları görselleştir",
        "2": "Yeni karşılaştırma + grafik",
        "3": "Örnek grafikler göster",
        "0": "Geri dön",
    }

    for key, name in options.items():
        console.print(f"  [{key}] {name}")

    choice = Prompt.ask("\nSeçim", choices=list(options.keys()), default="1")

    if choice == "0":
        return
    elif choice == "1":
        visualize_saved_results()
    elif choice == "2":
        results = run_comparison(None, None)
        if results:
            create_visualizations(results)
    elif choice == "3":
        show_sample_visualizations()


def visualize_saved_results():
    """Kayıtlı sonuçları görselleştir"""
    import json
    import glob

    files = glob.glob(os.path.join(config.output_dir, "*.json"))

    if not files:
        console.print("[yellow]Kayıtlı sonuç bulunamadı.[/yellow]")
        return

    console.print("\n[cyan]Kayıtlı dosyalar:[/cyan]")
    for i, f in enumerate(files, 1):
        console.print(f"  [{i}] {os.path.basename(f)}")

    choice = IntPrompt.ask("Dosya seçin", default=1)

    if 1 <= choice <= len(files):
        with open(files[choice - 1]) as f:
            data = json.load(f)

        if "results" in data:
            # run_experiments.py formatı
            create_visualizations_from_raw(data)
        else:
            # comparison formatı
            create_visualizations(data)


def create_visualizations(results: Dict):
    """Grafikler oluştur"""
    import matplotlib.pyplot as plt

    console.print("\n[cyan]Grafikler oluşturuluyor...[/cyan]")

    # 1. PDR Bar Chart
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    plt.style.use("dark_background")

    # PDR grafiği
    ax1 = axes[0]
    scenarios = list(results.keys())
    routers = list(list(results.values())[0].keys())

    x = range(len(scenarios))
    width = 0.2
    colors = ["#00D4AA", "#4ECDC4", "#FFE66D", "#FF6B6B"]

    for i, router in enumerate(routers):
        pdrs = [results[s][router]["pdr"] * 100 for s in scenarios]
        ax1.bar(
            [xi + i * width for xi in x],
            pdrs,
            width,
            label=router,
            color=colors[i % len(colors)],
        )

    ax1.set_ylabel("PDR (%)")
    ax1.set_title("Paket Teslim Oranı Karşılaştırması")
    ax1.set_xticks([xi + width for xi in x])
    ax1.set_xticklabels(scenarios, rotation=15)
    ax1.legend()
    ax1.set_ylim(0, 100)
    ax1.grid(alpha=0.3)

    # Latency grafiği
    ax2 = axes[1]

    for i, router in enumerate(routers):
        latencies = [results[s][router]["latency"] for s in scenarios]
        ax2.bar(
            [xi + i * width for xi in x],
            latencies,
            width,
            label=router,
            color=colors[i % len(colors)],
        )

    ax2.set_ylabel("Gecikme (ms)")
    ax2.set_title("Ortalama Gecikme Karşılaştırması")
    ax2.set_xticks([xi + width for xi in x])
    ax2.set_xticklabels(scenarios, rotation=15)
    ax2.legend()
    ax2.grid(alpha=0.3)

    plt.tight_layout()

    # Kaydet
    os.makedirs(config.output_dir, exist_ok=True)
    filepath = os.path.join(
        config.output_dir, f"comparison_chart_{time.strftime('%Y%m%d_%H%M%S')}.png"
    )
    plt.savefig(filepath, dpi=150, bbox_inches="tight", facecolor="#1a1a2e")

    console.print(f"[green]✅ Grafik kaydedildi: {filepath}[/green]")

    if Confirm.ask("Grafiği göstermek ister misiniz?", default=True):
        plt.show()
    else:
        plt.close()


def create_visualizations_from_raw(data: Dict):
    """Ham sonuçlardan grafik oluştur"""
    import matplotlib.pyplot as plt
    import numpy as np

    results_list = data.get("results", [])

    if not results_list:
        console.print("[yellow]Sonuç verisi bulunamadı.[/yellow]")
        return

    # Verileri organize et
    scenarios = sorted(set(r["scenario"] for r in results_list))
    routers = sorted(set(r["router"] for r in results_list))

    # Ortalama hesapla
    aggregated = {}
    for scenario in scenarios:
        aggregated[scenario] = {}
        for router in routers:
            matching = [
                r
                for r in results_list
                if r["scenario"] == scenario and r["router"] == router
            ]
            if matching:
                aggregated[scenario][router] = {
                    "pdr": np.mean([r["pdr"] for r in matching]),
                    "latency": np.mean([r["avg_latency"] for r in matching]),
                    "hops": np.mean([r["avg_hops"] for r in matching]),
                }

    create_visualizations(aggregated)


def show_sample_visualizations():
    """Örnek grafikler göster"""
    import matplotlib.pyplot as plt
    import numpy as np

    plt.style.use("dark_background")

    fig, axes = plt.subplots(2, 2, figsize=(12, 10))

    # Örnek veri
    routers = ["Dijkstra", "AODV", "RL-Agent"]
    colors = ["#00D4AA", "#FFE66D", "#FF6B6B"]

    # PDR Bar
    ax1 = axes[0, 0]
    pdrs = [35, 31, 42]
    ax1.bar(routers, pdrs, color=colors)
    ax1.set_ylabel("PDR (%)")
    ax1.set_title("Paket Teslim Oranı")
    ax1.set_ylim(0, 100)

    # Latency
    ax2 = axes[0, 1]
    latencies = [11.2, 18.0, 12.5]
    ax2.bar(routers, latencies, color=colors)
    ax2.set_ylabel("Gecikme (ms)")
    ax2.set_title("Ortalama Gecikme")

    # Time series
    ax3 = axes[1, 0]
    steps = np.arange(0, 500, 10)
    for i, router in enumerate(routers):
        pdr = 30 + np.random.randn(len(steps)).cumsum() * 0.5 + (i * 5)
        pdr = np.clip(pdr, 0, 100)
        ax3.plot(steps, pdr, label=router, color=colors[i], linewidth=2)
    ax3.set_xlabel("Adım")
    ax3.set_ylabel("PDR (%)")
    ax3.set_title("PDR Zaman Serisi")
    ax3.legend()
    ax3.grid(alpha=0.3)

    # Hops
    ax4 = axes[1, 1]
    hops = [2.8, 1.7, 3.2]
    ax4.bar(routers, hops, color=colors)
    ax4.set_ylabel("Hop Sayısı")
    ax4.set_title("Ortalama Hop")

    plt.tight_layout()
    plt.suptitle("LifeNode - Örnek Grafikler", y=1.02, fontsize=14, fontweight="bold")

    plt.show()


# =============================================================================
# AFET SİMÜLASYONU
# =============================================================================


def disaster_menu():
    """Afet simülasyonu menüsü"""
    show_banner()
    console.print(Panel("[bold]🌋 Afet Simülasyonu[/bold]", border_style="red"))

    console.print("\n[cyan]Senaryo Seçin:[/cyan]")
    scenarios = {
        "1": ("Deprem (Hafif)", 0.4, 150),
        "2": ("Deprem (Orta)", 0.6, 200),
        "3": ("Deprem (Şiddetli)", 0.8, 300),
        "4": ("Kademeli Ağ Çöküşü", None, None),
        "5": ("Özel Senaryo", None, None),
    }

    for key, (name, _, _) in scenarios.items():
        console.print(f"  [{key}] {name}")

    choice = Prompt.ask("Seçim", choices=list(scenarios.keys()), default="2")

    if choice == "5":
        # Özel senaryo
        intensity = FloatPrompt.ask("Şiddet (0-1)", default=0.6)
        radius = IntPrompt.ask("Etki yarıçapı", default=200)
        trigger_step = IntPrompt.ask("Tetikleme adımı", default=150)
        scenario = EarthquakeScenario(
            epicenter=(250, 250),
            radius=radius,
            intensity=intensity,
            trigger_step=trigger_step,
        )
        scenario_name = f"Özel Deprem (Şiddet: {intensity})"
    elif choice == "4":
        failure_rate = FloatPrompt.ask("Arıza oranı", default=0.03)
        scenario = GradualFailureScenario(
            start_step=100, failure_rate=failure_rate, recovery_rate=0.01
        )
        scenario_name = f"Kademeli Arıza (Oran: {failure_rate})"
    else:
        name, intensity, radius = scenarios[choice]
        scenario = EarthquakeScenario(
            epicenter=(250, 250), radius=radius, intensity=intensity, trigger_step=150
        )
        scenario_name = name

    console.print(f"\n[yellow]Senaryo: {scenario_name}[/yellow]")

    if not Confirm.ask("Simülasyonu başlat?", default=True):
        return

    run_disaster_simulation(scenario, scenario_name)


def run_disaster_simulation(scenario, scenario_name: str):
    """Afet simülasyonunu çalıştır"""

    routers = {
        "Dijkstra": DijkstraRouter(use_quality_weights=True),
        "AODV": AODVRouter(),
    }

    # RL varsa ekle
    model_files = list_model_files()
    if model_files and Confirm.ask("RL Agent eklensin mi?", default=True):
        rl_router = load_model_menu(model_files)
        if rl_router:
            routers["RL-Agent"] = rl_router

    results = {}

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(bar_width=40),
        TimeElapsedColumn(),
        console=console,
    ) as progress:

        for router_name, router in routers.items():
            task = progress.add_task(
                f"[red]{router_name} - {scenario_name}", total=config.num_steps
            )

            sim_config = SimulationConfig(
                world=WorldConfig(
                    width=500,
                    height=500,
                    initial_node_count=config.num_nodes,
                    seed=config.seed,
                )
            )

            router.reset()
            world = World(config=sim_config, seed=config.seed)
            world.initialize_random_nodes(count=config.num_nodes)
            world.set_router(router)
            scenario.reset()

            collector = MetricCollector()
            pdr_history = []

            for step in range(config.num_steps):
                scenario.apply(world, step)
                result = world.step()

                for _ in range(result.packets_sent):
                    collector.record_packet_sent()
                for pr in result.delivered_packets:
                    collector.record_result(pr)
                for pr in result.dropped_packets:
                    collector.record_result(pr)

                collector.record_step(result.active_nodes, result.active_links)

                # Her 50 adımda PDR kaydet
                if step % 50 == 0:
                    temp_metrics = collector.get_metrics()
                    pdr_history.append((step, temp_metrics.packet_delivery_ratio))

                progress.update(task, advance=1)

            collector.finalize()
            metrics = collector.get_metrics()

            results[router_name] = {
                "pdr": metrics.packet_delivery_ratio,
                "latency": metrics.average_latency,
                "hops": metrics.average_hops,
                "delivered": metrics.total_packets_delivered,
                "pdr_history": pdr_history,
                "metrics": metrics,
            }

    # Sonuçları göster
    show_disaster_results(results, scenario_name, scenario.get_stats())


def show_disaster_results(results: Dict, scenario_name: str, scenario_stats: Dict):
    """Afet sonuçlarını göster"""

    console.print()

    # Senaryo özeti
    stats_text = "\n".join([f"   • {k}: {v}" for k, v in scenario_stats.items()])
    console.print(
        Panel(
            f"""
[bold red]🌋 {scenario_name}[/bold red]

[cyan]Senaryo İstatistikleri:[/cyan]
{stats_text}
""",
            border_style="red",
        )
    )

    # Sonuç tablosu
    table = Table(title="Performans Karşılaştırması", box=box.ROUNDED)
    table.add_column("Algoritma", style="bold")
    table.add_column("PDR", justify="center")
    table.add_column("Latency", justify="center")
    table.add_column("Hop", justify="center")
    table.add_column("Teslim", justify="center")

    best = max(results.items(), key=lambda x: x[1]["pdr"])

    for router_name, data in sorted(results.items(), key=lambda x: -x[1]["pdr"]):
        is_best = router_name == best[0]
        pdr_str = (
            f"[bold green]{data['pdr']*100:.1f}%[/bold green] 🏆"
            if is_best
            else f"{data['pdr']*100:.1f}%"
        )

        table.add_row(
            router_name,
            pdr_str,
            f"{data['latency']:.2f} ms",
            f"{data['hops']:.1f}",
            str(data["delivered"]),
        )

    console.print(table)

    # Kazanan
    console.print(f"\n[bold green]🏆 Afet Koşullarında En İyi: {best[0]}[/bold green]")


# =============================================================================
# AYARLAR
# =============================================================================


def settings_menu():
    """Ayarlar menüsü"""
    while True:
        show_banner()
        console.print(Panel("[bold]⚙️ Ayarlar[/bold]", border_style="yellow"))

        table = Table(box=box.SIMPLE)
        table.add_column("No", style="yellow", width=4)
        table.add_column("Parametre", style="cyan")
        table.add_column("Değer", style="white")

        table.add_row("1", "Düğüm Sayısı", str(config.num_nodes))
        table.add_row("2", "Simülasyon Adımı", str(config.num_steps))
        table.add_row("3", "Seed", str(config.seed))
        table.add_row("4", "RL Episode", str(config.rl_episodes))
        table.add_row("5", "RL Adım/Episode", str(config.rl_steps_per_episode))
        table.add_row("6", "Learning Rate", str(config.learning_rate))
        table.add_row("7", "Epsilon", str(config.epsilon))
        table.add_row("8", "Çıktı Dizini", config.output_dir)
        table.add_row("0", "Geri Dön", "")

        console.print(table)

        choice = Prompt.ask(
            "\nDüzenle",
            choices=["0", "1", "2", "3", "4", "5", "6", "7", "8"],
            default="0",
        )

        if choice == "0":
            break
        elif choice == "1":
            config.num_nodes = IntPrompt.ask("Düğüm Sayısı", default=config.num_nodes)
        elif choice == "2":
            config.num_steps = IntPrompt.ask(
                "Simülasyon Adımı", default=config.num_steps
            )
        elif choice == "3":
            config.seed = IntPrompt.ask("Seed", default=config.seed)
        elif choice == "4":
            config.rl_episodes = IntPrompt.ask("RL Episode", default=config.rl_episodes)
        elif choice == "5":
            config.rl_steps_per_episode = IntPrompt.ask(
                "RL Adım/Episode", default=config.rl_steps_per_episode
            )
        elif choice == "6":
            config.learning_rate = FloatPrompt.ask(
                "Learning Rate", default=config.learning_rate
            )
        elif choice == "7":
            config.epsilon = FloatPrompt.ask("Epsilon", default=config.epsilon)
        elif choice == "8":
            config.output_dir = Prompt.ask("Çıktı Dizini", default=config.output_dir)

        console.print("[green]✅ Güncellendi![/green]")
        time.sleep(0.5)


# =============================================================================
# SONUÇLAR
# =============================================================================


def results_menu():
    """Sonuçlar menüsü"""
    import glob
    import json

    show_banner()
    console.print(Panel("[bold]📁 Kayıtlı Sonuçlar[/bold]", border_style="cyan"))

    # JSON dosyalarını listele
    json_files = glob.glob(os.path.join(config.output_dir, "*.json"))
    png_files = glob.glob(os.path.join(config.output_dir, "*.png"))
    model_files = list_model_files()

    if not json_files and not png_files and not model_files:
        console.print("[yellow]Kayıtlı dosya bulunamadı.[/yellow]")
        Prompt.ask("\nDevam etmek için Enter'a basın")
        return

    # Dosyaları göster
    if json_files:
        console.print("\n[cyan]📊 Sonuç Dosyaları:[/cyan]")
        for f in json_files:
            size = os.path.getsize(f) / 1024
            console.print(f"   • {os.path.basename(f)} ({size:.1f} KB)")

    if png_files:
        console.print("\n[cyan]📈 Grafikler:[/cyan]")
        for f in png_files:
            console.print(f"   • {os.path.basename(f)}")

    if model_files:
        console.print("\n[cyan]🧠 RL Modelleri:[/cyan]")
        for f in model_files:
            console.print(f"   • {os.path.basename(f)}")

    console.print(
        "\n[dim]Seçenekler: [v] Görselleştir, [d] Detay, [x] Sil, [Enter] Geri[/dim]"
    )
    choice = Prompt.ask("", default="")

    if choice.lower() == "v" and json_files:
        visualize_saved_results()
    elif choice.lower() == "d" and json_files:
        show_result_details(json_files)


def show_result_details(files: List[str]):
    """Sonuç detaylarını göster"""
    import json

    console.print("\n[cyan]Dosya seçin:[/cyan]")
    for i, f in enumerate(files, 1):
        console.print(f"  [{i}] {os.path.basename(f)}")

    choice = IntPrompt.ask("Dosya", default=1)

    if 1 <= choice <= len(files):
        with open(files[choice - 1]) as f:
            data = json.load(f)

        console.print(
            Panel(
                Syntax(json.dumps(data, indent=2)[:2000], "json", theme="monokai"),
                title=os.path.basename(files[choice - 1]),
            )
        )

        Prompt.ask("\nDevam etmek için Enter'a basın")


# =============================================================================
# YARDIMCI FONKSİYONLAR
# =============================================================================


def list_model_files() -> List[str]:
    """Model dosyalarını listele"""
    import glob

    return glob.glob(os.path.join(config.model_dir, "*.pkl"))


def load_model_menu(files: List[str]) -> Optional[RLRouter]:
    """Model yükleme menüsü"""
    console.print("\n[cyan]Model seçin:[/cyan]")
    for i, f in enumerate(files, 1):
        console.print(f"  [{i}] {os.path.basename(f)}")

    choice = IntPrompt.ask("Model", default=1)

    if 1 <= choice <= len(files):
        rl_router = RLRouter(training_mode=False)
        rl_router.load_model(files[choice - 1])
        console.print(f"[green]✅ Model yüklendi: {files[choice-1]}[/green]")
        return rl_router

    return None


# =============================================================================
# ANA DÖNGÜ
# =============================================================================


def main():
    """Ana fonksiyon"""

    # Dizinleri oluştur
    os.makedirs(config.output_dir, exist_ok=True)
    os.makedirs(config.model_dir, exist_ok=True)

    while True:
        show_banner()
        show_main_menu()

        choice = Prompt.ask(
            "\n[bold cyan]Seçiminiz[/bold cyan]",
            choices=["0", "1", "2", "3", "4", "5", "6"],
            default="1",
        )

        try:
            if choice == "0":
                console.print("\n[bold green]👋 Güle güle![/bold green]\n")
                break
            elif choice == "1":
                train_rl_menu()
            elif choice == "2":
                comparison_menu()
            elif choice == "3":
                visualization_menu()
            elif choice == "4":
                disaster_menu()
            elif choice == "5":
                settings_menu()
            elif choice == "6":
                results_menu()
        except KeyboardInterrupt:
            console.print("\n[yellow]İşlem iptal edildi.[/yellow]")
        except Exception as e:
            console.print(f"\n[red]Hata: {e}[/red]")
            import traceback

            traceback.print_exc()

        if choice != "5":  # Ayarlar menüsü kendi döngüsünde
            Prompt.ask("\n[dim]Devam etmek için Enter'a basın[/dim]")


if __name__ == "__main__":
    main()
