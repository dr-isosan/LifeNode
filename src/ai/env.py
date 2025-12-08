# src/ai/env.py
import numpy as np
import gymnasium as gym
from gymnasium import spaces

# Kendi yazdığımız modülleri çağırıyoruz
from .state_encoder import StateEncoder
from .reward import RewardSystem


class LifeNodeEnv(gym.Env):
    def __init__(self):
        super(LifeNodeEnv, self).__init__()

        # 1. YARDIMCI SINIFLARI BAŞLAT
        self.encoder = StateEncoder(max_neighbors=5)
        self.reward_system = RewardSystem()

        # 2. ACTION SPACE
        self.action_space = spaces.Discrete(self.encoder.max_neighbors)

        # 3. OBSERVATION SPACE (Encoder'dan gelen boyuta göre dinamik)
        self.observation_space = spaces.Box(
            low=0, high=1, shape=(self.encoder.state_dim,), dtype=np.float32
        )

        # Simülasyon durumu (Mocking)
        self.steps_taken = 0

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self.steps_taken = 0

        # TODO: Kişi A'nın simülasyonundan gerçek node verilerini çek.
        # Şimdilik "sahte" verilerle encoder'ı test ediyoruz:
        mock_current_node = type("Node", (), {"distance_to": lambda x: 500})
        mock_neighbors = []  # Boş komşu listesi (encoder padding yapacak mı görelim)
        mock_dest = None

        # Encoder'ı kullanarak state üret
        state = self.encoder.encode(mock_current_node, mock_neighbors, mock_dest)

        return state, {}

    def step(self, action):
        self.steps_taken += 1

        # 1. SİMÜLASYON ADIMI (Mock)
        # Gerçekte: packet.move_to(neighbor[action])
        packet_arrived = np.random.rand() < 0.1  # %10 şansla vardı
        packet_dropped = self.steps_taken > 20  # 20 adımda varamazsa düşer

        # Seçilen komşunun enerjisi (Mock)
        selected_node_energy = 0.8

        # 2. ÖDÜL HESAPLA (Reward System kullanıyoruz)
        reward = self.reward_system.calculate(
            success=packet_arrived,
            energy_level=selected_node_energy,
            hop_count=self.steps_taken,
            failed=packet_dropped,
        )

        # 3. YENİ STATE (Mock)
        next_state = self.encoder.encode(
            type("Node", (), {"distance_to": lambda x: 400}), [], None
        )

        done = packet_arrived or packet_dropped

        return next_state, reward, done, False, {}
