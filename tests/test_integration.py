"""Entegrasyon testleri - tüm bileşenleri birlikte test et"""

import pytest
import os
import json
import tempfile
from lifenode.config import SimulationConfig, WorldConfig
from lifenode.environment.world import World
from lifenode.routing.dijkstra import DijkstraRouter
from lifenode.routing.aodv import AODVRouter
from lifenode.rl_agent.rl_router import RLRouter
from lifenode.scenarios.earthquake import EarthquakeScenario
from lifenode.scenarios.gradual_failure import GradualFailureScenario
from lifenode.metrics.collector import MetricCollector


class TestFullSimulation:
    """Tam simülasyon testleri"""

    def test_simple_simulation(self):
        """Basit simülasyon testi"""
        config = SimulationConfig(
            world=WorldConfig(width=500, height=500, initial_node_count=15)
        )
        world = World(config=config, seed=42)
        world.initialize_random_nodes(count=15)

        router = DijkstraRouter(use_quality_weights=True)
        world.set_router(router)

        collector = MetricCollector()

        # 50 adım simülasyon
        for _ in range(50):
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

        assert metrics.total_packets_sent > 0
        assert 0 <= metrics.packet_delivery_ratio <= 1

    def test_disaster_simulation(self):
        """Afetli simülasyon testi"""
        config = SimulationConfig(
            world=WorldConfig(width=500, height=500, initial_node_count=15)
        )
        world = World(config=config, seed=42)
        world.initialize_random_nodes(count=15)

        router = DijkstraRouter(use_quality_weights=True)
        world.set_router(router)

        scenario = EarthquakeScenario(
            epicenter=(250, 250), radius=200, intensity=0.6, trigger_step=25
        )
        scenario.reset()

        collector = MetricCollector()

        # 50 adım simülasyon
        for step in range(50):
            scenario.apply(world, step)
            result = world.step()

            for _ in range(result.packets_sent):
                collector.record_packet_sent()

            for pr in result.delivered_packets:
                collector.record_result(pr)

            for pr in result.dropped_packets:
                collector.record_result(pr)

        collector.finalize()
        metrics = collector.get_metrics()

        assert 0 <= metrics.packet_delivery_ratio <= 1


class TestRouterComparison:
    """Router karşılaştırma testleri"""

    def test_all_routers_comparison(self):
        """Tüm router'ları karşılaştır"""
        config = SimulationConfig(
            world=WorldConfig(width=500, height=500, initial_node_count=10)
        )

        routers = {
            "Dijkstra-Quality": DijkstraRouter(use_quality_weights=True),
            "Dijkstra-Hop": DijkstraRouter(use_quality_weights=False),
            "AODV": AODVRouter(),
            "RL": RLRouter(training_mode=False),
        }

        results = {}

        for name, router in routers.items():
            world = World(config=config, seed=42)
            world.initialize_random_nodes(count=10)
            world.set_router(router)

            collector = MetricCollector()

            for _ in range(30):
                result = world.step()

                for _ in range(result.packets_sent):
                    collector.record_packet_sent()

                for pr in result.delivered_packets:
                    collector.record_result(pr)

                for pr in result.dropped_packets:
                    collector.record_result(pr)

            collector.finalize()
            metrics = collector.get_metrics()

            results[name] = {
                "pdr": metrics.packet_delivery_ratio,
                "latency": metrics.average_latency,
                "packets_sent": metrics.total_packets_sent,
            }

        # Tüm router'lar çalışmalı
        assert len(results) == 4

        # PDR değerleri geçerli olmalı
        for name, data in results.items():
            assert 0 <= data["pdr"] <= 1, f"{name} PDR değeri hatalı"


class TestJSONOperations:
    """JSON işlemleri testleri"""

    def test_save_results_to_json(self):
        """Sonuçları JSON'a kaydetme testi"""
        test_results = {
            "Normal": {
                "Dijkstra-Quality": {
                    "pdr": 0.85,
                    "latency": 12.5,
                    "hops": 2.3,
                    "delivered": 85,
                    "dropped": 15,
                },
                "AODV": {
                    "pdr": 0.78,
                    "latency": 15.2,
                    "hops": 2.8,
                    "delivered": 78,
                    "dropped": 22,
                },
            }
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            with open(tmp_path, "w") as f:
                json.dump(test_results, f, indent=2)

            assert os.path.exists(tmp_path)

            # Dosyayı oku
            with open(tmp_path, "r") as f:
                loaded = json.load(f)

            assert loaded == test_results
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)


class TestEndToEnd:
    """Uçtan uca testler"""

    def test_complete_workflow(self):
        """Tüm iş akışı testi: Eğitim -> Karşılaştırma -> Kaydetme"""
        # 1. RL Eğitimi
        rl_router = RLRouter(training_mode=True)

        config = SimulationConfig(
            world=WorldConfig(width=500, height=500, initial_node_count=10)
        )

        # Kısa eğitim
        for episode in range(3):
            world = World(config=config, seed=42 + episode)
            world.initialize_random_nodes(count=10)
            world.set_router(rl_router)

            for _ in range(20):
                world.step()

        rl_router.training_mode = False

        # 2. Karşılaştırma
        routers = {
            "Dijkstra": DijkstraRouter(use_quality_weights=True),
            "RL": rl_router,
        }

        results = {}

        for name, router in routers.items():
            world = World(config=config, seed=42)
            world.initialize_random_nodes(count=10)
            world.set_router(router)

            collector = MetricCollector()

            for _ in range(20):
                result = world.step()

                for _ in range(result.packets_sent):
                    collector.record_packet_sent()

                for pr in result.delivered_packets:
                    collector.record_result(pr)

                for pr in result.dropped_packets:
                    collector.record_result(pr)

            collector.finalize()
            metrics = collector.get_metrics()

            results[name] = {
                "pdr": metrics.packet_delivery_ratio,
                "packets": metrics.total_packets_sent,
            }

        # 3. Kaydetme
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            with open(tmp_path, "w") as f:
                json.dump(results, f, indent=2)

            assert os.path.exists(tmp_path)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

        # Test başarılı
        assert len(results) == 2
