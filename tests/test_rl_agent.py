"""RL Agent için testler"""

import pytest
import os
import tempfile
from lifenode.rl_agent.rl_router import RLRouter
from lifenode.rl_agent.qlearning import QLearningConfig
from lifenode.config import SimulationConfig, WorldConfig
from lifenode.environment.world import World


class TestRLAgent:
    """RL Agent testleri"""

    def test_rl_agent_initialization(self):
        """RL agent başlatma testi"""
        router = RLRouter(training_mode=True)
        assert router is not None
        assert router.training_mode is True

    def test_rl_agent_with_config(self):
        """RL agent konfigürasyon testi"""
        ql_config = QLearningConfig(
            learning_rate=0.1,
            discount_factor=0.95,
            epsilon_start=0.3,
            epsilon_end=0.05,
            epsilon_decay=0.995,
        )

        router = RLRouter(training_mode=True, ql_config=ql_config)
        assert router is not None

    def test_rl_agent_training_mode_toggle(self):
        """RL agent eğitim modu değiştirme testi"""
        router = RLRouter(training_mode=True)
        assert router.training_mode is True

        router.training_mode = False
        assert router.training_mode is False

    def test_rl_agent_stats(self):
        """RL agent istatistik testi"""
        router = RLRouter(training_mode=False)
        stats = router.get_stats()

        assert isinstance(stats, dict)
        assert "q_table_size" in stats
        assert "total_decisions" in stats

    def test_rl_agent_reset(self):
        """RL agent reset testi"""
        router = RLRouter(training_mode=True)

        try:
            router.reset()
        except Exception as e:
            pytest.fail(f"RL agent reset failed: {e}")

    def test_rl_agent_simulation(self):
        """RL agent simülasyon testi"""
        config = SimulationConfig(
            world=WorldConfig(width=500, height=500, initial_node_count=10)
        )
        world = World(config=config, seed=42)
        world.initialize_random_nodes(count=10)

        router = RLRouter(training_mode=True)
        world.set_router(router)

        # 10 adım simülasyon
        for _ in range(10):
            result = world.step()
            assert result is not None

    def test_rl_agent_learning(self):
        """RL agent öğrenme testi"""
        config = SimulationConfig(
            world=WorldConfig(width=500, height=500, initial_node_count=10)
        )

        router = RLRouter(training_mode=True)

        # Başlangıç durumu
        initial_stats = router.get_stats()
        initial_decisions = initial_stats["total_decisions"]

        # Eğitim
        world = World(config=config, seed=42)
        world.initialize_random_nodes(count=10)
        world.set_router(router)

        for _ in range(20):
            world.step()

        # Eğitim sonrası
        final_stats = router.get_stats()
        final_decisions = final_stats["total_decisions"]

        # Karar sayısı artmış olmalı (veya en azından değişmemiş olabilir)
        assert final_decisions >= initial_decisions


class TestRLModelSaveLoad:
    """RL model kaydetme/yükleme testleri"""

    def test_model_save(self):
        """Model kaydetme testi"""
        router = RLRouter(training_mode=True)

        # Geçici dosya
        with tempfile.NamedTemporaryFile(suffix=".pkl", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            router.save_model(tmp_path)
            assert os.path.exists(tmp_path)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def test_model_load(self):
        """Model yükleme testi"""
        # Model kaydet
        router1 = RLRouter(training_mode=True)

        with tempfile.NamedTemporaryFile(suffix=".pkl", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            router1.save_model(tmp_path)

            # Model yükle
            router2 = RLRouter(training_mode=False)
            router2.load_model(tmp_path)

            # İstatistikler benzer olmalı (Q-table boyutu)
            stats1 = router1.get_stats()
            stats2 = router2.get_stats()

            assert stats1["q_table_size"] == stats2["q_table_size"]
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def test_existing_models(self):
        """Mevcut model yükleme testi"""
        model_dir = "models"

        if not os.path.exists(model_dir):
            pytest.skip("Model dizini bulunamadı")

        model_files = [f for f in os.listdir(model_dir) if f.endswith(".pkl")]

        if not model_files:
            pytest.skip("Model dosyası bulunamadı")

        # İlk modeli yükle
        router = RLRouter(training_mode=False)
        model_path = os.path.join(model_dir, model_files[0])

        try:
            router.load_model(model_path)
            stats = router.get_stats()

            assert stats["q_table_size"] > 0
        except Exception as e:
            pytest.fail(f"Model yükleme başarısız: {e}")
