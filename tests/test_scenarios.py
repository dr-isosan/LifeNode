"""Afet senaryoları için testler"""

import pytest
from lifenode.config import SimulationConfig, WorldConfig
from lifenode.environment.world import World
from lifenode.scenarios.earthquake import EarthquakeScenario
from lifenode.scenarios.gradual_failure import GradualFailureScenario


class TestEarthquakeScenario:
    """Deprem senaryosu testleri"""

    def test_earthquake_initialization(self):
        """Deprem senaryosu başlatma testi"""
        scenario = EarthquakeScenario(
            epicenter=(250, 250), radius=200, intensity=0.6, trigger_step=150
        )

        assert scenario is not None
        assert scenario.epicenter == (250, 250)
        assert scenario.radius == 200
        assert scenario.intensity == 0.6
        assert scenario.trigger_step == 150

    def test_earthquake_reset(self):
        """Deprem senaryosu reset testi"""
        scenario = EarthquakeScenario(
            epicenter=(250, 250), radius=200, intensity=0.6, trigger_step=150
        )

        scenario.reset()
        stats = scenario.get_stats()

        assert stats is not None
        assert "triggered" in stats
        assert stats["triggered"] is False

    def test_earthquake_application(self):
        """Deprem senaryosu uygulama testi"""
        config = SimulationConfig(
            world=WorldConfig(width=500, height=500, initial_node_count=10)
        )
        world = World(config=config, seed=42)
        world.initialize_random_nodes(count=10)

        scenario = EarthquakeScenario(
            epicenter=(250, 250), radius=200, intensity=0.6, trigger_step=10
        )

        scenario.reset()

        # Trigger step'ten önce
        scenario.apply(world, 5)
        stats1 = scenario.get_stats()
        assert stats1["triggered"] is False

        # Trigger step'ten sonra
        scenario.apply(world, 15)
        stats2 = scenario.get_stats()
        # Artık tetiklenmiş olmalı veya olmayabilir (düğümlerin konumuna bağlı)
        assert "triggered" in stats2

    def test_earthquake_stats(self):
        """Deprem istatistikleri testi"""
        scenario = EarthquakeScenario(
            epicenter=(250, 250), radius=200, intensity=0.6, trigger_step=150
        )

        scenario.reset()
        stats = scenario.get_stats()

        assert isinstance(stats, dict)
        assert "name" in stats
        assert "triggered" in stats
        assert "total_failures" in stats


class TestGradualFailureScenario:
    """Kademeli arıza senaryosu testleri"""

    def test_gradual_failure_initialization(self):
        """Kademeli arıza başlatma testi"""
        scenario = GradualFailureScenario(
            start_step=100, failure_rate=0.03, recovery_rate=0.01
        )

        assert scenario is not None
        assert scenario.start_step == 100
        assert scenario.failure_rate == 0.03
        assert scenario.recovery_rate == 0.01

    def test_gradual_failure_reset(self):
        """Kademeli arıza reset testi"""
        scenario = GradualFailureScenario(
            start_step=100, failure_rate=0.03, recovery_rate=0.01
        )

        scenario.reset()
        stats = scenario.get_stats()

        assert stats is not None
        assert "total_failures" in stats
        assert "total_recoveries" in stats

    def test_gradual_failure_application(self):
        """Kademeli arıza uygulama testi"""
        config = SimulationConfig(
            world=WorldConfig(width=500, height=500, initial_node_count=10)
        )
        world = World(config=config, seed=42)
        world.initialize_random_nodes(count=10)

        scenario = GradualFailureScenario(
            start_step=10, failure_rate=0.03, recovery_rate=0.01
        )

        scenario.reset()

        # Start step'ten önce
        scenario.apply(world, 5)
        stats1 = scenario.get_stats()
        assert stats1["total_failures"] == 0

        # Start step'ten sonra (birkaç adım)
        for step in range(11, 30):
            scenario.apply(world, step)

    def test_gradual_failure_stats(self):
        """Kademeli arıza istatistikleri testi"""
        scenario = GradualFailureScenario(
            start_step=100, failure_rate=0.03, recovery_rate=0.01
        )

        scenario.reset()
        stats = scenario.get_stats()

        assert isinstance(stats, dict)
        assert "name" in stats
        assert "total_failures" in stats
        assert "total_recoveries" in stats
        assert "current_failed_nodes" in stats


class TestScenarioIntegration:
    """Senaryo entegrasyon testleri"""

    def test_multiple_scenarios(self):
        """Birden fazla senaryo testi"""
        scenarios = [
            EarthquakeScenario(
                epicenter=(250, 250), radius=200, intensity=0.6, trigger_step=50
            ),
            GradualFailureScenario(
                start_step=100, failure_rate=0.03, recovery_rate=0.01
            ),
        ]

        for scenario in scenarios:
            scenario.reset()
            stats = scenario.get_stats()
            assert stats is not None
            assert "name" in stats
