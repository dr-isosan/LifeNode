"""
Experiment Runner (Deney Çalıştırıcı)

Simülasyon deneylerini yapılandırır ve çalıştırır.
Farklı routing protokollerini karşılaştırır.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable, Type
import time
import random

from ..config import SimulationConfig, DEFAULT_CONFIG
from ..environment.world import World
from ..environment.node import Node
from ..routing.base import Router
from ..routing.dijkstra import DijkstraRouter
from ..rl_agent.rl_router import RLRouter
from ..rl_agent.qlearning import QLearningConfig
from ..metrics.collector import MetricCollector, ExperimentMetrics
from ..metrics.analyzer import MetricAnalyzer
from ..metrics.visualizer import Visualizer


@dataclass
class ExperimentConfig:
    """Deney yapılandırması"""

    name: str = "default"
    num_nodes: int = 64
    num_steps: int = 500
    seed: Optional[int] = 42

    # Trafik
    packets_per_step: float = 0.5

    # Afet senaryoları
    enable_failures: bool = False
    failure_probability: float = 0.01
    failure_start_step: int = 100

    # RL eğitim
    rl_training_episodes: int = 1500


class ExperimentRunner:
    """
    Deney Çalıştırıcı

    Simülasyon deneylerini yönetir.
    """

    def __init__(
        self,
        config: Optional[SimulationConfig] = None,
        experiment_config: Optional[ExperimentConfig] = None,
    ):
        """
        Args:
            config: Simülasyon yapılandırması
            experiment_config: Deney yapılandırması
        """
        self.sim_config = config or DEFAULT_CONFIG
        self.exp_config = experiment_config or ExperimentConfig()

        # Sonuçlar
        self.results: Dict[str, ExperimentMetrics] = {}

        # Analyzer ve Visualizer
        self.analyzer = MetricAnalyzer()
        self.visualizer = Visualizer()

    def run_single_experiment(
        self,
        router: Router,
        name: Optional[str] = None,
        num_steps: Optional[int] = None,
        show_progress: bool = True,
        callback: Optional[Callable] = None,
    ) -> ExperimentMetrics:
        """
        Tek bir deney çalıştır

        Args:
            router: Kullanılacak router
            name: Deney adı
            num_steps: Adım sayısı
            show_progress: İlerleme göster
            callback: Her adımda çağrılacak fonksiyon

        Returns:
            Deney metrikleri
        """
        name = name or router.get_name()
        num_steps = num_steps or self.exp_config.num_steps

        if show_progress:
            print(f"\n{'='*60}")
            print(f"Deney: {name}")
            print(f"Router: {router.get_name()}")
            print(f"Düğüm: {self.exp_config.num_nodes}, Adım: {num_steps}")
            print(f"{'='*60}")

        # World oluştur
        world = World(config=self.sim_config, seed=self.exp_config.seed)
        world.initialize_random_nodes(count=self.exp_config.num_nodes)
        world.set_router(router)

        # Metric collector
        collector = MetricCollector()

        start_time = time.time()

        # Simülasyon döngüsü
        for step in range(num_steps):
            # Afet simülasyonu
            if (
                self.exp_config.enable_failures
                and step >= self.exp_config.failure_start_step
            ):
                self._apply_random_failures(world, step, collector)

            # Adım çalıştır
            result = world.step()

            # Metrikleri kaydet
            for _ in range(result.packets_sent):
                collector.record_packet_sent()

            for packet_result in result.delivered_packets:
                collector.record_result(packet_result)

            for packet_result in result.dropped_packets:
                collector.record_result(packet_result)

            collector.record_step(result.active_nodes, result.active_links)

            # Callback
            if callback:
                callback(step, world, result)

            # İlerleme
            if show_progress and (step + 1) % 100 == 0:
                stats = world.get_stats()
                print(
                    f"  Adım {step+1}/{num_steps} | "
                    f"PDR: {stats['packet_delivery_ratio']:.2%} | "
                    f"Aktif: {stats['active_nodes']}/{stats['total_nodes']}"
                )

        collector.finalize()

        elapsed = time.time() - start_time

        if show_progress:
            metrics = collector.get_metrics()
            print(f"\n✅ Tamamlandı ({elapsed:.2f}s)")
            print(f"   {metrics.summary()}")

        # Sonucu kaydet
        self.results[name] = collector.get_metrics()
        self.analyzer.add_experiment(name, collector.get_metrics())

        return collector.get_metrics()

    def _apply_random_failures(
        self, world: World, step: int, collector: MetricCollector
    ):
        """Rastgele düğüm arızaları uygula"""
        for node in list(world.nodes.values()):
            if node.is_active and random.random() < self.exp_config.failure_probability:
                node.fail()
                collector.record_failure(node.id, step)
                world.update_all_links()

    def run_comparison(
        self, routers: Optional[List[Router]] = None, show_progress: bool = True
    ) -> Dict[str, ExperimentMetrics]:
        """
        Birden fazla router karşılaştır

        Args:
            routers: Karşılaştırılacak router'lar
            show_progress: İlerleme göster

        Returns:
            Router adı -> metrikler
        """
        if routers is None:
            routers = [
                DijkstraRouter(use_quality_weights=True),
                DijkstraRouter(use_quality_weights=False),
            ]

        self.results.clear()
        self.analyzer.reset()

        for router in routers:
            # Her router için aynı seed kullan
            random.seed(self.exp_config.seed)

            self.run_single_experiment(router=router, show_progress=show_progress)

        if show_progress:
            print("\n" + "=" * 60)
            print("KARŞILAŞTIRMA SONUÇLARI")
            print("=" * 60)
            print(self.analyzer.generate_report())

        return self.results

    def train_rl_agent(
        self,
        episodes: Optional[int] = None,
        steps_per_episode: int = 200,
        show_progress: bool = True,
    ) -> RLRouter:
        """
        RL ajanını eğit

        Args:
            episodes: Episode sayısı
            steps_per_episode: Episode başına adım
            show_progress: İlerleme göster

        Returns:
            Eğitilmiş RL router
        """
        episodes = episodes or self.exp_config.rl_training_episodes

        if show_progress:
            print(f"\n{'='*60}")
            print("RL AGENT EĞİTİMİ")
            print(f"Episode: {episodes}, Adım/Episode: {steps_per_episode}")
            print(f"{'='*60}")

        # RL Router oluştur
        rl_router = RLRouter(
            ql_config=QLearningConfig(
                learning_rate=0.1,
                discount_factor=0.97,
                epsilon_start=1.0,
                epsilon_end=0.05,
                epsilon_decay=0.995,
            ),
            training_mode=True,
        )

        training_rewards = []
        training_pdrs = []

        for episode in range(episodes):
            # Her episode için yeni world
            random.seed(self.exp_config.seed + episode)

            world = World(config=self.sim_config, seed=self.exp_config.seed + episode)
            world.initialize_random_nodes(count=self.exp_config.num_nodes)
            world.set_router(rl_router)

            episode_reward = 0.0

            for step in range(steps_per_episode):
                result = world.step()

                # Reward topla
                episode_reward += (
                    result.packets_delivered * 10 - result.packets_dropped * 10
                )

            # Episode sonu
            rl_router.end_episode()

            stats = world.get_stats()
            training_rewards.append(episode_reward)
            training_pdrs.append(stats["packet_delivery_ratio"])

            if show_progress and (episode + 1) % 5 == 0:
                avg_reward = sum(training_rewards[-5:]) / 5
                avg_pdr = sum(training_pdrs[-5:]) / 5
                print(
                    f"  Episode {episode+1}/{episodes} | "
                    f"ε: {rl_router.agent.epsilon:.3f} | "
                    f"Reward: {avg_reward:.1f} | "
                    f"PDR: {avg_pdr:.2%}"
                )

            # Router state'ini sıfırla (ama Q-table'ı koru)
            rl_router.reset()

        # Eğitim modunu kapat
        rl_router.set_training_mode(False)

        if show_progress:
            print(f"\n✅ Eğitim tamamlandı!")
            agent_stats = rl_router.agent.get_stats()
            print(f"   Q-Table boyutu: {agent_stats['q_table_size']}")
            print(f"   Final ε: {agent_stats['epsilon']:.4f}")

        return rl_router

    def run_full_comparison(
        self, include_rl: bool = True, rl_episodes: int = 10, show_progress: bool = True
    ) -> Dict[str, ExperimentMetrics]:
        """
        Tam karşılaştırma çalıştır (baseline + RL)

        Args:
            include_rl: RL agent dahil et
            rl_episodes: RL eğitim episode sayısı
            show_progress: İlerleme göster

        Returns:
            Sonuçlar
        """
        routers = [
            DijkstraRouter(use_quality_weights=True),
        ]

        if include_rl:
            # RL ajanını eğit
            rl_router = self.train_rl_agent(
                episodes=rl_episodes, show_progress=show_progress
            )
            routers.append(rl_router)

        return self.run_comparison(routers, show_progress)

    def visualize_results(self, save_dir: Optional[str] = None, show: bool = True):
        """
        Sonuçları görselleştir

        Args:
            save_dir: Kayıt dizini
            show: Grafikleri göster
        """
        if not self.results:
            print("Henüz sonuç yok!")
            return

        # PDR karşılaştırması
        self.visualizer.plot_pdr_comparison(
            self.results,
            save_path=f"{save_dir}/pdr_comparison.png" if save_dir else None,
        )

        # Latency dağılımı
        self.visualizer.plot_latency_distribution(
            self.results,
            save_path=f"{save_dir}/latency_distribution.png" if save_dir else None,
        )

        # Özet grafik
        self.visualizer.plot_comparison_summary(
            self.results, save_path=f"{save_dir}/summary.png" if save_dir else None
        )

        if show:
            self.visualizer.show()

    def generate_report(self) -> str:
        """Markdown raporu oluştur"""
        return self.analyzer.generate_report()
