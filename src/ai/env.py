# src/ai/env.py
"""
LifeNode Gymnasium Environment
Gerçek network simülasyonu ile entegre edilmiş RL environment
"""
import numpy as np
import gymnasium as gym
from gymnasium import spaces
from .state_encoder import StateEncoder
from .reward import RewardSystem


class LifeNodeEnv(gym.Env):
    """
    LifeNode için Gymnasium tabanlı RL Environment.
    Gerçek network simülasyonunu kullanır.
    """

    def __init__(self, sim_engine, max_neighbors=5):
        """
        Args:
            sim_engine: SimulationNetworkAdapter instance
            max_neighbors: Maksimum komşu sayısı
        """
        super(LifeNodeEnv, self).__init__()

        # Simülasyon motoru (gerçek network'e bağlı)
        self.sim_engine = sim_engine
        self.max_neighbors = max_neighbors

        # State encoder ve reward sistemi
        self.encoder = StateEncoder(max_neighbors=max_neighbors)
        self.reward_system = RewardSystem()

        # Action space: Hangi komşuya paket gönderilecek?
        self.action_space = spaces.Discrete(max_neighbors)

        # Observation space: StateEncoder'dan gelen boyut
        state_dim = self.encoder.state_dim
        self.observation_space = spaces.Box(
            low=0, high=1, shape=(state_dim,), dtype=np.float32
        )

        # Episode state
        self.current_node_id = None
        self.destination_id = None
        self.steps_taken = 0
        self.max_steps = 50
        self.packet_path = []

    def reset(self, seed=None, options=None):
        """
        Episode'u başlat

        Returns:
            state: Initial state
            info: Debug bilgileri
        """
        super().reset(seed=seed)

        # Simülasyondan rastgele bir kaynak ve hedef seç
        active_nodes = [
            nid for nid, node in self.sim_engine.network.nodes.items() if node.is_active
        ]

        if len(active_nodes) < 2:
            raise ValueError("Yeterli aktif node yok!")

        # Rastgele kaynak ve hedef seç
        import random

        self.current_node_id = random.choice(active_nodes)
        dest_opts = [nid for nid in active_nodes if nid != self.current_node_id]
        self.destination_id = random.choice(dest_opts)

        self.steps_taken = 0
        self.packet_path = [self.current_node_id]

        # İlk observation'ı al
        observation = self.sim_engine.get_observation(
            self.current_node_id, self.destination_id
        )

        # State'e encode et
        state = self.encoder.encode(observation)

        info = {
            "source": self.current_node_id,
            "destination": self.destination_id,
            "path": self.packet_path.copy(),
        }

        return state, info

    def step(self, action):
        """
        Bir adım ilerlet

        Args:
            action: Seçilen komşu indeksi (0-4)

        Returns:
            next_state: Yeni state
            reward: Ödül
            done: Episode bitti mi?
            truncated: Zaman aşımı?
            info: Debug bilgileri
        """
        self.steps_taken += 1

        # Current observation'ı al
        observation = self.sim_engine.get_observation(
            self.current_node_id, self.destination_id
        )

        # Action'ı neighbor ID'ye çevir
        if not observation.neighbors:
            # Komşu yok, paket kayboldu
            reward = self.reward_system.calculate_reward(
                success=False,
                energy_level=0.5,
                hop_count=self.steps_taken,
                failed=True,
            )
            done = True
            truncated = False
            info = {
                "reason": "no_neighbors",
                "path": self.packet_path.copy(),
                "steps": self.steps_taken,
            }
            return self._get_state(), reward, done, truncated, info

        # Action indeksini neighbor ID'ye map et
        if action >= len(observation.neighbors):
            action = len(observation.neighbors) - 1

        target_link = observation.neighbors[action]
        target_node_id = target_link.target_node_id

        # Simülasyonda aksiyonu uygula
        result = self.sim_engine.execute_action(self.current_node_id, target_node_id)

        if not result["success"]:
            # Aksiyon başarısız (node inactive, vb.)
            reward = self.reward_system.calculate_reward(
                success=False,
                energy_level=0.5,
                hop_count=self.steps_taken,
                failed=True,
            )
            done = True
            truncated = False
            info = {
                "reason": result.get("reason", "action_failed"),
                "path": self.packet_path.copy(),
                "steps": self.steps_taken,
            }
            return self._get_state(), reward, done, truncated, info

        # Paketi hedefe taşı
        self.current_node_id = target_node_id
        self.packet_path.append(target_node_id)

        # Hedefe ulaştık mı?
        if self.current_node_id == self.destination_id:
            reward = self.reward_system.calculate_reward(
                success=True,
                energy_level=1.0,
                hop_count=self.steps_taken,
                failed=False,
            )
            done = True
            truncated = False
            info = {
                "reason": "success",
                "path": self.packet_path.copy(),
                "steps": self.steps_taken,
            }
            return self._get_state(), reward, done, truncated, info

        # Maksimum adım aşıldı mı?
        if self.steps_taken >= self.max_steps:
            reward = self.reward_system.calculate_reward(
                success=False,
                energy_level=0.5,
                hop_count=self.steps_taken,
                failed=True,
            )
            done = False
            truncated = True
            info = {
                "reason": "max_steps",
                "path": self.packet_path.copy(),
                "steps": self.steps_taken,
            }
            return self._get_state(), reward, done, truncated, info

        # Devam ediyoruz - intermediate step
        target_node = self.sim_engine.network.nodes[target_node_id]
        energy_level = target_node.battery_level

        # Seçilen link bilgilerini al (signal, bandwidth)
        signal_strength = target_link.signal_strength
        bandwidth = target_link.bandwidth_capacity
        queue_occupancy = target_node.queue_len / target_node.queue_capacity

        reward = self.reward_system.calculate_reward(
            success=False,
            energy_level=energy_level,
            hop_count=self.steps_taken,
            failed=False,
            signal_strength=signal_strength,  # YENİ!
            bandwidth=bandwidth,  # YENİ!
            queue_occupancy=queue_occupancy,  # YENİ!
        )

        done = False
        truncated = False
        info = {
            "path": self.packet_path.copy(),
            "steps": self.steps_taken,
        }

        return self._get_state(), reward, done, truncated, info

    def _get_state(self):
        """Current state'i döndür"""
        try:
            observation = self.sim_engine.get_observation(
                self.current_node_id, self.destination_id
            )
            return self.encoder.encode(observation)
        except (KeyError, ValueError, AttributeError) as e:
            # Spesifik hatalar için loglama
            import logging
            logger = logging.getLogger(__name__)
            logger.error(
                f"State encoding failed: {e}, "
                f"node_id={self.current_node_id}, dest={self.destination_id}"
            )
            # Hata durumunda sıfırlarla doldurulmuş state döndür
            return np.zeros(self.observation_space.shape, dtype=np.float32)
        except Exception as e:
            # Beklenmeyen hatalar
            import logging
            logger = logging.getLogger(__name__)
            logger.critical(f"Unexpected error in state encoding: {type(e).__name__}: {e}")
            return np.zeros(self.observation_space.shape, dtype=np.float32)
