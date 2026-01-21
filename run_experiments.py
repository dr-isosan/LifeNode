#!/usr/bin/env python3
"""
Kapsamlı Deney Çalıştırıcı

Tüm routing protokollerini farklı senaryolarda test eder.
Detaylı istatistikler ve karşılaştırma raporları üretir.

Kullanım:
    python run_experiments.py
"""

import sys
import os
import time
import random
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# Proje path'ini ekle
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lifenode.config import SimulationConfig, WorldConfig, NodeConfig, TrafficConfig
from lifenode.environment.world import World
from lifenode.routing.dijkstra import DijkstraRouter
from lifenode.routing.aodv import AODVRouter
from lifenode.rl_agent.rl_router import RLRouter
from lifenode.rl_agent.qlearning import QLearningConfig
from lifenode.scenarios.earthquake import EarthquakeScenario
from lifenode.scenarios.gradual_failure import GradualFailureScenario
from lifenode.metrics.collector import MetricCollector, ExperimentMetrics
from lifenode.metrics.visualizer import Visualizer


# =============================================================================
# DENEY YAPILANDIRMASI
# =============================================================================

EXPERIMENT_CONFIG = {
    'num_nodes': 40,
    'num_steps': 500,
    'seed': 42,
    'rl_training_episodes': 30,
    'rl_steps_per_episode': 300,
    'num_runs': 3,  # Her senaryo için tekrar sayısı (güvenilirlik için)
}

SCENARIOS = {
    'normal': None,  # Afet yok
    'gradual_failure': {
        'type': 'gradual',
        'start_step': 100,
        'failure_rate': 0.03,
        'recovery_rate': 0.01,
    },
    'earthquake': {
        'type': 'earthquake',
        'epicenter': (250, 250),  # Ortada
        'radius': 200,
        'intensity': 0.6,
        'trigger_step': 150,
        'recovery_rate': 0.03,
    },
    'severe_earthquake': {
        'type': 'earthquake',
        'epicenter': (250, 250),
        'radius': 300,
        'intensity': 0.8,
        'trigger_step': 100,
        'recovery_rate': 0.02,
    },
}


def create_scenario(scenario_config: Optional[dict]):
    """Senaryo objesi oluştur"""
    if scenario_config is None:
        return None

    if scenario_config['type'] == 'gradual':
        return GradualFailureScenario(
            start_step=scenario_config['start_step'],
            failure_rate=scenario_config['failure_rate'],
            recovery_rate=scenario_config['recovery_rate'],
        )
    elif scenario_config['type'] == 'earthquake':
        return EarthquakeScenario(
            epicenter=scenario_config['epicenter'],
            radius=scenario_config['radius'],
            intensity=scenario_config['intensity'],
            trigger_step=scenario_config['trigger_step'],
            recovery_rate=scenario_config['recovery_rate'],
        )
    return None


def create_routers(trained_rl_router: Optional[RLRouter] = None) -> Dict:
    """Tüm router'ları oluştur"""
    routers = {
        'Dijkstra': DijkstraRouter(use_quality_weights=True),
        'AODV': AODVRouter(route_lifetime=15.0),
    }

    if trained_rl_router:
        routers['RL-Q'] = trained_rl_router

    return routers


def train_rl_agent(
    num_episodes: int,
    steps_per_episode: int,
    seed: int
) -> RLRouter:
    """RL ajanını eğit"""
    print("\n" + "=" * 60)
    print("🧠 RL AGENT EĞİTİMİ")
    print(f"   Episode: {num_episodes}, Adım/Episode: {steps_per_episode}")
    print("=" * 60)

    config = SimulationConfig()
    config.world.initial_node_count = EXPERIMENT_CONFIG['num_nodes']

    rl_router = RLRouter(
        ql_config=QLearningConfig(
            learning_rate=0.15,
            discount_factor=0.95,
            epsilon_start=1.0,
            epsilon_end=0.05,
            epsilon_decay=0.98,
        ),
        training_mode=True
    )

    training_history = {
        'episodes': [],
        'rewards': [],
        'pdrs': [],
        'epsilons': [],
    }

    for episode in range(num_episodes):
        random.seed(seed + episode)

        world = World(config=config, seed=seed + episode)
        world.initialize_random_nodes()
        world.set_router(rl_router)

        episode_reward = 0.0

        for step in range(steps_per_episode):
            result = world.step()
            episode_reward += result.packets_delivered * 10 - result.packets_dropped * 10

        rl_router.end_episode()

        stats = world.get_stats()
        training_history['episodes'].append(episode)
        training_history['rewards'].append(episode_reward)
        training_history['pdrs'].append(stats['packet_delivery_ratio'])
        training_history['epsilons'].append(rl_router.agent.epsilon)

        if (episode + 1) % 5 == 0:
            avg_reward = sum(training_history['rewards'][-5:]) / 5
            avg_pdr = sum(training_history['pdrs'][-5:]) / 5
            print(f"   Episode {episode+1:3d}/{num_episodes} | "
                  f"ε: {rl_router.agent.epsilon:.3f} | "
                  f"Reward: {avg_reward:8.1f} | "
                  f"PDR: {avg_pdr:.2%}")

        rl_router.reset()

    rl_router.set_training_mode(False)

    print(f"\n✅ Eğitim tamamlandı!")
    print(f"   Q-Table boyutu: {rl_router.agent.get_stats()['q_table_size']}")

    return rl_router


def run_single_experiment(
    router_name: str,
    router,
    scenario_name: str,
    scenario_config: Optional[dict],
    run_id: int,
    seed: int
) -> Dict:
    """Tek bir deney çalıştır"""
    random.seed(seed + run_id)

    config = SimulationConfig()
    config.world.initial_node_count = EXPERIMENT_CONFIG['num_nodes']

    world = World(config=config, seed=seed + run_id)
    world.initialize_random_nodes()
    world.set_router(router)

    scenario = create_scenario(scenario_config)
    if scenario:
        scenario.reset()

    collector = MetricCollector()
    start_time = time.time()

    for step in range(EXPERIMENT_CONFIG['num_steps']):
        # Senaryo uygula
        if scenario:
            scenario.apply(world, step)

        # Simülasyon adımı
        result = world.step()

        # Metrikleri kaydet
        for _ in range(result.packets_sent):
            collector.record_packet_sent()

        for pr in result.delivered_packets:
            collector.record_result(pr)

        for pr in result.dropped_packets:
            collector.record_result(pr)

        collector.record_step(result.active_nodes, result.active_links)

    collector.finalize()
    elapsed = time.time() - start_time

    metrics = collector.get_metrics()
    router_stats = router.get_stats()
    scenario_stats = scenario.get_stats() if scenario else {}

    return {
        'router': router_name,
        'scenario': scenario_name,
        'run_id': run_id,
        'elapsed_time': elapsed,
        'pdr': metrics.packet_delivery_ratio,
        'avg_latency': metrics.average_latency,
        'avg_hops': metrics.average_hops,
        'total_sent': metrics.total_packets_sent,
        'total_delivered': metrics.total_packets_delivered,
        'total_dropped': metrics.total_packets_dropped,
        'latency_std': metrics.latency_std,
        'min_latency': metrics.min_latency,
        'max_latency': metrics.max_latency,
        'router_stats': router_stats,
        'scenario_stats': scenario_stats,
    }


def run_all_experiments(rl_router: Optional[RLRouter] = None) -> List[Dict]:
    """Tüm deneyleri çalıştır"""
    print("\n" + "=" * 60)
    print("🔬 KAPSAMLI DENEYLER BAŞLIYOR")
    print("=" * 60)

    routers = create_routers(rl_router)
    all_results = []

    for scenario_name, scenario_config in SCENARIOS.items():
        print(f"\n📋 Senaryo: {scenario_name}")
        print("-" * 40)

        for router_name, router in routers.items():
            router.reset()

            for run_id in range(EXPERIMENT_CONFIG['num_runs']):
                result = run_single_experiment(
                    router_name=router_name,
                    router=router,
                    scenario_name=scenario_name,
                    scenario_config=scenario_config,
                    run_id=run_id,
                    seed=EXPERIMENT_CONFIG['seed'],
                )
                all_results.append(result)

                print(f"   {router_name:15s} Run {run_id+1} | "
                      f"PDR: {result['pdr']:.2%} | "
                      f"Latency: {result['avg_latency']:6.2f}ms | "
                      f"Hops: {result['avg_hops']:.2f}")

    return all_results


def analyze_results(results: List[Dict]) -> Dict:
    """Sonuçları analiz et"""
    print("\n" + "=" * 60)
    print("📊 SONUÇ ANALİZİ")
    print("=" * 60)

    analysis = {}

    # Senaryolara göre grupla
    for scenario in SCENARIOS.keys():
        scenario_results = [r for r in results if r['scenario'] == scenario]
        analysis[scenario] = {}

        # Router'lara göre grupla
        routers = set(r['router'] for r in scenario_results)
        for router in routers:
            router_results = [r for r in scenario_results if r['router'] == router]

            # Ortalamaları hesapla
            avg_pdr = sum(r['pdr'] for r in router_results) / len(router_results)
            avg_latency = sum(r['avg_latency'] for r in router_results) / len(router_results)
            avg_hops = sum(r['avg_hops'] for r in router_results) / len(router_results)

            # Standart sapma (PDR)
            pdr_values = [r['pdr'] for r in router_results]
            pdr_mean = avg_pdr
            pdr_std = (sum((x - pdr_mean) ** 2 for x in pdr_values) / len(pdr_values)) ** 0.5

            analysis[scenario][router] = {
                'pdr_mean': avg_pdr,
                'pdr_std': pdr_std,
                'latency_mean': avg_latency,
                'hops_mean': avg_hops,
                'num_runs': len(router_results),
            }

    return analysis


def print_analysis_report(analysis: Dict):
    """Analiz raporunu yazdır"""
    print("\n" + "=" * 80)
    print("📈 KARŞILAŞTIRMA RAPORU")
    print("=" * 80)

    for scenario, routers in analysis.items():
        print(f"\n🌍 Senaryo: {scenario.upper()}")
        print("-" * 60)
        print(f"{'Router':<15} | {'PDR':>10} | {'Latency':>12} | {'Hops':>8}")
        print("-" * 60)

        # PDR'a göre sırala
        sorted_routers = sorted(routers.items(), key=lambda x: x[1]['pdr_mean'], reverse=True)

        for router, stats in sorted_routers:
            pdr_str = f"{stats['pdr_mean']:.2%} ±{stats['pdr_std']:.2%}"
            latency_str = f"{stats['latency_mean']:.2f} ms"
            hops_str = f"{stats['hops_mean']:.2f}"

            # En iyi router'ı işaretle
            marker = "🏆" if router == sorted_routers[0][0] else "  "
            print(f"{marker} {router:<13} | {pdr_str:>10} | {latency_str:>12} | {hops_str:>8}")


def print_conclusion(analysis: Dict):
    """Sonuç ve değerlendirme"""
    print("\n" + "=" * 80)
    print("🎯 SONUÇ VE DEĞERLENDİRME")
    print("=" * 80)

    # Her senaryoda kazananı bul
    winners = {}
    for scenario, routers in analysis.items():
        best_router = max(routers.items(), key=lambda x: x[1]['pdr_mean'])[0]
        winners[scenario] = best_router

    print("\n📌 Senaryo Bazında En İyi Performans:")
    for scenario, winner in winners.items():
        pdr = analysis[scenario][winner]['pdr_mean']
        print(f"   • {scenario:20s} → {winner} (PDR: {pdr:.2%})")

    # RL performans analizi
    print("\n📌 RL Performans Değerlendirmesi:")

    rl_better_count = 0
    dijkstra_better_count = 0

    for scenario, routers in analysis.items():
        if 'RL-Q' in routers and 'Dijkstra' in routers:
            rl_pdr = routers['RL-Q']['pdr_mean']
            dij_pdr = routers['Dijkstra']['pdr_mean']

            if rl_pdr > dij_pdr:
                rl_better_count += 1
                diff = ((rl_pdr - dij_pdr) / dij_pdr * 100) if dij_pdr > 0 else 0
                print(f"   ✅ {scenario}: RL %{diff:.1f} daha iyi")
            else:
                dijkstra_better_count += 1
                diff = ((dij_pdr - rl_pdr) / rl_pdr * 100) if rl_pdr > 0 else 0
                print(f"   ❌ {scenario}: Dijkstra %{diff:.1f} daha iyi")

    print("\n" + "=" * 80)
    print("🔬 ARAŞTIRMA SORUSU CEVABI")
    print("=" * 80)

    total_scenarios = rl_better_count + dijkstra_better_count

    if rl_better_count > dijkstra_better_count:
        print(f"""
✅ EVET - RL routing klasik algoritmalardan DAHA İYİ performans gösterdi.

   • RL {rl_better_count}/{total_scenarios} senaryoda kazandı
   • Özellikle dinamik/afet senaryolarında adaptasyon yeteneği öne çıktı
   • Daha fazla eğitim ile performans artırılabilir
""")
    elif rl_better_count == dijkstra_better_count:
        print(f"""
⚖️ KARARSIZ - RL ve klasik algoritmalar eşit performans gösterdi.

   • Her biri {rl_better_count}/{total_scenarios} senaryoda kazandı
   • Farklı senaryolarda farklı güçlü yönler
   • Hibrit yaklaşım değerlendirilebilir
""")
    else:
        print(f"""
❌ HAYIR - Bu konfigürasyonda klasik algoritmalar daha iyi.

   • Dijkstra {dijkstra_better_count}/{total_scenarios} senaryoda kazandı
   • RL daha fazla eğitime ihtiyaç duyabilir
   • State/reward tasarımı optimize edilebilir
   • Daha karmaşık senaryolarda RL avantajlı olabilir

   ÖNERİLER:
   1. RL eğitim episode sayısını artır (100+)
   2. State space'i zenginleştir
   3. Daha agresif afet senaryoları dene
   4. Multi-agent RL değerlendir
""")


def save_results(results: List[Dict], analysis: Dict, output_dir: str = "results"):
    """Sonuçları dosyaya kaydet"""
    os.makedirs(output_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # JSON olarak kaydet
    with open(f"{output_dir}/experiment_results_{timestamp}.json", 'w') as f:
        json.dump({
            'config': EXPERIMENT_CONFIG,
            'scenarios': SCENARIOS,
            'results': results,
            'analysis': analysis,
        }, f, indent=2, default=str)

    print(f"\n💾 Sonuçlar kaydedildi: {output_dir}/experiment_results_{timestamp}.json")


def main():
    """Ana fonksiyon"""
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║     ██╗     ██╗███████╗███████╗███╗   ██╗ ██████╗ ██████╗ ███████╗           ║
║     ██║     ██║██╔════╝██╔════╝████╗  ██║██╔═══██╗██╔══██╗██╔════╝           ║
║     ██║     ██║█████╗  █████╗  ██╔██╗ ██║██║   ██║██║  ██║█████╗             ║
║     ██║     ██║██╔══╝  ██╔══╝  ██║╚██╗██║██║   ██║██║  ██║██╔══╝             ║
║     ███████╗██║██║     ███████╗██║ ╚████║╚██████╔╝██████╔╝███████╗           ║
║     ╚══════╝╚═╝╚═╝     ╚══════╝╚═╝  ╚═══╝ ╚═════╝ ╚═════╝ ╚══════╝           ║
║                                                                              ║
║                    KAPSAMLI DENEY VE ANALİZ                                  ║
║           AI-Driven Routing vs Classical Algorithms                          ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """)

    print(f"\n📋 Deney Konfigürasyonu:")
    print(f"   • Düğüm Sayısı: {EXPERIMENT_CONFIG['num_nodes']}")
    print(f"   • Simülasyon Adımı: {EXPERIMENT_CONFIG['num_steps']}")
    print(f"   • Tekrar Sayısı: {EXPERIMENT_CONFIG['num_runs']}")
    print(f"   • RL Eğitim Episode: {EXPERIMENT_CONFIG['rl_training_episodes']}")
    print(f"   • Senaryolar: {list(SCENARIOS.keys())}")

    # 1. RL Ajanını Eğit
    rl_router = train_rl_agent(
        num_episodes=EXPERIMENT_CONFIG['rl_training_episodes'],
        steps_per_episode=EXPERIMENT_CONFIG['rl_steps_per_episode'],
        seed=EXPERIMENT_CONFIG['seed']
    )

    # 2. Tüm Deneyleri Çalıştır
    results = run_all_experiments(rl_router)

    # 3. Sonuçları Analiz Et
    analysis = analyze_results(results)

    # 4. Raporu Yazdır
    print_analysis_report(analysis)

    # 5. Sonuç ve Değerlendirme
    print_conclusion(analysis)

    # 6. Sonuçları Kaydet
    save_results(results, analysis)

    print("\n✅ Tüm deneyler tamamlandı!")


if __name__ == "__main__":
    main()
