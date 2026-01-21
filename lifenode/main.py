#!/usr/bin/env python3
"""
LifeNode - AI-Driven Dynamic Routing Simulation

Ana giriş noktası.
Simülasyon, eğitim ve karşılaştırma işlemleri buradan başlatılır.

Kullanım:
    # Basit simülasyon
    python -m lifenode.main

    # RL eğitimi ile karşılaştırma
    python -m lifenode.main --compare --rl-episodes 20

    # Sadece Dijkstra testi
    python -m lifenode.main --router dijkstra --steps 500
"""

import argparse
import sys
import os

# Proje kök dizinini path'e ekle
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lifenode.config import SimulationConfig, DEFAULT_CONFIG
from lifenode.environment.world import World
from lifenode.routing.dijkstra import DijkstraRouter
from lifenode.rl_agent.rl_router import RLRouter
from lifenode.experiments.runner import ExperimentRunner, ExperimentConfig
from lifenode.metrics.visualizer import Visualizer


def parse_args():
    """Komut satırı argümanlarını ayrıştır"""
    parser = argparse.ArgumentParser(
        description="LifeNode - AI-Driven Dynamic Routing Simulation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Örnekler:
  python -m lifenode.main                         # Basit simülasyon
  python -m lifenode.main --compare               # Baseline vs RL karşılaştırma
  python -m lifenode.main --nodes 50 --steps 1000 # Özelleştirilmiş
  python -m lifenode.main --train --episodes 50   # Sadece RL eğitimi
        """
    )

    # Temel parametreler
    parser.add_argument(
        '--nodes', '-n',
        type=int,
        default=30,
        help='Düğüm sayısı (varsayılan: 30)'
    )
    parser.add_argument(
        '--steps', '-s',
        type=int,
        default=500,
        help='Simülasyon adım sayısı (varsayılan: 500)'
    )
    parser.add_argument(
        '--seed',
        type=int,
        default=42,
        help='Rastgelelik tohumu (varsayılan: 42)'
    )

    # Router seçimi
    parser.add_argument(
        '--router', '-r',
        choices=['dijkstra', 'dijkstra-hop', 'rl'],
        default='dijkstra',
        help='Kullanılacak router (varsayılan: dijkstra)'
    )

    # Mod seçimi
    parser.add_argument(
        '--compare', '-c',
        action='store_true',
        help='Karşılaştırma modu (Dijkstra vs RL)'
    )
    parser.add_argument(
        '--train', '-t',
        action='store_true',
        help='Sadece RL eğitimi yap'
    )

    # RL parametreleri
    parser.add_argument(
        '--episodes', '-e',
        type=int,
        default=10,
        help='RL eğitim episode sayısı (varsayılan: 10)'
    )
    parser.add_argument(
        '--save-model',
        type=str,
        help='Eğitilen modeli kaydet (dosya yolu)'
    )
    parser.add_argument(
        '--load-model',
        type=str,
        help='Eğitilmiş model yükle (dosya yolu)'
    )

    # Afet senaryosu
    parser.add_argument(
        '--failures',
        action='store_true',
        help='Rastgele düğüm arızaları etkinleştir'
    )
    parser.add_argument(
        '--failure-rate',
        type=float,
        default=0.01,
        help='Arıza olasılığı (varsayılan: 0.01)'
    )

    # Görselleştirme
    parser.add_argument(
        '--visualize', '-v',
        action='store_true',
        help='Sonuçları görselleştir'
    )
    parser.add_argument(
        '--save-plots',
        type=str,
        help='Grafikleri kaydet (dizin yolu)'
    )

    # Sessiz mod
    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Sessiz mod (minimal çıktı)'
    )

    return parser.parse_args()


def main():
    """Ana fonksiyon"""
    args = parse_args()

    # Banner
    if not args.quiet:
        print("""
╔══════════════════════════════════════════════════════════════╗
║  ██╗     ██╗███████╗███████╗███╗   ██╗ ██████╗ ██████╗ ███████╗  ║
║  ██║     ██║██╔════╝██╔════╝████╗  ██║██╔═══██╗██╔══██╗██╔════╝  ║
║  ██║     ██║█████╗  █████╗  ██╔██╗ ██║██║   ██║██║  ██║█████╗    ║
║  ██║     ██║██╔══╝  ██╔══╝  ██║╚██╗██║██║   ██║██║  ██║██╔══╝    ║
║  ███████╗██║██║     ███████╗██║ ╚████║╚██████╔╝██████╔╝███████╗  ║
║  ╚══════╝╚═╝╚═╝     ╚══════╝╚═╝  ╚═══╝ ╚═════╝ ╚═════╝ ╚══════╝  ║
║                                                                  ║
║  AI-Driven Dynamic Routing Simulation for Ad-Hoc Networks       ║
╚══════════════════════════════════════════════════════════════════╝
        """)

    # Deney yapılandırması
    exp_config = ExperimentConfig(
        num_nodes=args.nodes,
        num_steps=args.steps,
        seed=args.seed,
        enable_failures=args.failures,
        failure_probability=args.failure_rate,
        rl_training_episodes=args.episodes,
    )

    # Experiment Runner
    runner = ExperimentRunner(
        experiment_config=exp_config
    )

    # Mod seçimi
    if args.train:
        # Sadece RL eğitimi
        rl_router = runner.train_rl_agent(
            episodes=args.episodes,
            show_progress=not args.quiet
        )

        if args.save_model:
            rl_router.save_model(args.save_model)
            print(f"Model kaydedildi: {args.save_model}")

    elif args.compare:
        # Karşılaştırma modu
        results = runner.run_full_comparison(
            include_rl=True,
            rl_episodes=args.episodes,
            show_progress=not args.quiet
        )

        if args.visualize or args.save_plots:
            runner.visualize_results(
                save_dir=args.save_plots,
                show=args.visualize
            )

    else:
        # Tek router testi
        if args.router == 'rl':
            if args.load_model:
                router = RLRouter(training_mode=False)
                router.load_model(args.load_model)
            else:
                # Önce eğit
                router = runner.train_rl_agent(
                    episodes=args.episodes,
                    show_progress=not args.quiet
                )
        elif args.router == 'dijkstra-hop':
            router = DijkstraRouter(use_quality_weights=False)
        else:
            router = DijkstraRouter(use_quality_weights=True)

        metrics = runner.run_single_experiment(
            router=router,
            show_progress=not args.quiet
        )

        if args.visualize:
            runner.visualize_results(
                save_dir=args.save_plots,
                show=True
            )

    if not args.quiet:
        print("\n✅ İşlem tamamlandı!")


if __name__ == "__main__":
    main()
