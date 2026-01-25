"""Simülasyon bileşenleri için testler"""

import pytest
from lifenode.config import SimulationConfig, WorldConfig
from lifenode.environment.world import World
from lifenode.environment.node import Node
from lifenode.environment.link import Link
from lifenode.routing.dijkstra import DijkstraRouter
from lifenode.metrics.collector import MetricCollector


class TestWorld:
    """World simülasyon testleri"""

    def test_world_initialization(self):
        """World başlatma testi"""
        config = SimulationConfig(
            world=WorldConfig(width=500, height=500, initial_node_count=10)
        )
        world = World(config=config, seed=42)
        assert world is not None

    def test_node_creation(self):
        """Node oluşturma testi"""
        config = SimulationConfig(
            world=WorldConfig(width=500, height=500, initial_node_count=10)
        )
        world = World(config=config, seed=42)
        world.initialize_random_nodes(count=10)

        assert len(world.nodes) == 10

    def test_world_step(self):
        """World step fonksiyonu testi"""
        config = SimulationConfig(
            world=WorldConfig(width=500, height=500, initial_node_count=10)
        )
        world = World(config=config, seed=42)
        world.initialize_random_nodes(count=10)

        router = DijkstraRouter(use_quality_weights=True)
        world.set_router(router)

        result = world.step()

        assert result is not None
        assert hasattr(result, "packets_sent")
        assert hasattr(result, "delivered_packets")
        assert hasattr(result, "dropped_packets")
        assert hasattr(result, "active_nodes")
        assert hasattr(result, "active_links")

    def test_simulation_consistency(self):
        """Simülasyon tutarlılık testi - aynı seed aynı sonuç vermeli"""
        seed = 42

        # İki farklı simülasyon aynı seed ile
        results = []
        for _ in range(2):
            config = SimulationConfig(
                world=WorldConfig(width=500, height=500, initial_node_count=10)
            )
            world = World(config=config, seed=seed)
            world.initialize_random_nodes(count=10)

            router = DijkstraRouter(use_quality_weights=True)
            world.set_router(router)

            packets = 0
            for _ in range(5):
                result = world.step()
                packets += result.packets_sent

            results.append(packets)

        # Aynı seed aynı sonucu vermeli
        assert results[0] == results[1]


class TestMetricCollector:
    """MetricCollector testleri"""

    def test_metric_collector_initialization(self):
        """MetricCollector başlatma testi"""
        collector = MetricCollector()
        assert collector is not None

    def test_packet_recording(self):
        """Paket kaydetme testi"""
        collector = MetricCollector()

        # Paket gönder
        for _ in range(10):
            collector.record_packet_sent()

        collector.finalize()
        metrics = collector.get_metrics()

        assert metrics.total_packets_sent == 10

    def test_metrics_calculation(self):
        """Metrik hesaplama testi"""
        collector = MetricCollector()

        # Simülasyon
        for _ in range(10):
            collector.record_packet_sent()

        collector.finalize()
        metrics = collector.get_metrics()

        assert hasattr(metrics, "packet_delivery_ratio")
        assert hasattr(metrics, "average_latency")
        assert hasattr(metrics, "average_hops")
        assert hasattr(metrics, "total_packets_sent")
        assert hasattr(metrics, "total_packets_delivered")
        assert hasattr(metrics, "total_packets_dropped")

    def test_full_simulation_metrics(self):
        """Tam simülasyon metrik testi"""
        config = SimulationConfig(
            world=WorldConfig(width=500, height=500, initial_node_count=10)
        )
        world = World(config=config, seed=42)
        world.initialize_random_nodes(count=10)

        router = DijkstraRouter(use_quality_weights=True)
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

            collector.record_step(result.active_nodes, result.active_links)

        collector.finalize()
        metrics = collector.get_metrics()

        # PDR 0 ile 1 arasında olmalı
        assert 0 <= metrics.packet_delivery_ratio <= 1

        # Gönderilen paketler = teslim edilen + düşen
        assert metrics.total_packets_sent == (
            metrics.total_packets_delivered + metrics.total_packets_dropped
        )
