"""Routing algoritmaları için testler"""

import pytest
from lifenode.config import SimulationConfig, WorldConfig
from lifenode.environment.world import World
from lifenode.routing.dijkstra import DijkstraRouter
from lifenode.routing.aodv import AODVRouter
from lifenode.rl_agent.rl_router import RLRouter


class TestRoutingAlgorithms:
    """Routing algoritmalarını test et"""

    def setup_method(self):
        """Her test öncesi çalışır"""
        self.sim_config = SimulationConfig(
            world=WorldConfig(width=500, height=500, initial_node_count=10)
        )

    def test_dijkstra_quality_initialization(self):
        """Dijkstra (Quality) router başlatma testi"""
        router = DijkstraRouter(use_quality_weights=True)
        assert router is not None
        assert router.use_quality_weights is True

    def test_dijkstra_hop_initialization(self):
        """Dijkstra (Hop) router başlatma testi"""
        router = DijkstraRouter(use_quality_weights=False)
        assert router is not None
        assert router.use_quality_weights is False

    def test_aodv_initialization(self):
        """AODV router başlatma testi"""
        router = AODVRouter()
        assert router is not None

    def test_rl_router_initialization(self):
        """RL router başlatma testi"""
        router = RLRouter(training_mode=False)
        assert router is not None
        assert router.training_mode is False

    def test_router_reset(self):
        """Router reset fonksiyonu testi"""
        routers = [
            DijkstraRouter(use_quality_weights=True),
            DijkstraRouter(use_quality_weights=False),
            AODVRouter(),
            RLRouter(training_mode=False),
        ]

        for router in routers:
            try:
                router.reset()
            except Exception as e:
                pytest.fail(f"Router reset failed: {e}")

    def test_dijkstra_routing(self):
        """Dijkstra routing fonksiyonu testi"""
        world = World(config=self.sim_config, seed=42)
        world.initialize_random_nodes(count=10)

        router = DijkstraRouter(use_quality_weights=True)
        world.set_router(router)

        # 5 adım simülasyon çalıştır
        for _ in range(5):
            result = world.step()
            assert result is not None
            assert hasattr(result, "packets_sent")
            assert hasattr(result, "active_nodes")

    def test_aodv_routing(self):
        """AODV routing fonksiyonu testi"""
        world = World(config=self.sim_config, seed=42)
        world.initialize_random_nodes(count=10)

        router = AODVRouter()
        world.set_router(router)

        # 5 adım simülasyon çalıştır
        for _ in range(5):
            result = world.step()
            assert result is not None

    def test_rl_routing(self):
        """RL routing fonksiyonu testi"""
        world = World(config=self.sim_config, seed=42)
        world.initialize_random_nodes(count=10)

        router = RLRouter(training_mode=False)
        world.set_router(router)

        # 5 adım simülasyon çalıştır
        for _ in range(5):
            result = world.step()
            assert result is not None


class TestRouterStats:
    """Router istatistiklerini test et"""

    def test_rl_router_stats(self):
        """RL router istatistik testi"""
        router = RLRouter(training_mode=False)
        stats = router.get_stats()

        assert isinstance(stats, dict)
        assert "q_table_size" in stats
        assert "total_decisions" in stats

    def test_router_comparison(self):
        """Farklı router'ların karşılaştırmalı testi"""
        sim_config = SimulationConfig(
            world=WorldConfig(width=500, height=500, initial_node_count=10)
        )

        routers = {
            "Dijkstra-Quality": DijkstraRouter(use_quality_weights=True),
            "Dijkstra-Hop": DijkstraRouter(use_quality_weights=False),
            "AODV": AODVRouter(),
        }

        results = {}

        for name, router in routers.items():
            world = World(config=sim_config, seed=42)
            world.initialize_random_nodes(count=10)
            world.set_router(router)

            packets_sent = 0
            for _ in range(10):
                result = world.step()
                packets_sent += result.packets_sent

            results[name] = packets_sent

        # En az bir router paket göndermeli
        assert any(count > 0 for count in results.values())
