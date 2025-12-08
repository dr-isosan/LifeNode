4"""
Environment Wrapper - Kişi A'nın simülasyonu ile Kişi B'nin AI ortamını birleştirir
"""

import sys
import os

# Simulation modülünü import edebilmek için path'e ekle
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from simulation.network import Network, Packet
from simulation.node import Node
import numpy as np
import gymnasium as gym
from gymnasium import spaces
from .state_encoder import StateEncoder
from .reward import RewardSystem


class LifeNodeSimEnv(gym.Env):
    """
    Gerçek Network simülasyonu ile entegre edilmiş RL environment
    """

    def __init__(
        self,
        num_nodes=20,
        communication_range=25.0,
        area_width=100.0,
        area_height=100.0,
    ):
        super().__init__()

        # Simülasyon parametreleri
        self.num_nodes = num_nodes
        self.communication_range = communication_range
        self.area_width = area_width
        self.area_height = area_height

        # AI bileşenleri
        self.encoder = StateEncoder(max_neighbors=5)
        self.reward_system = RewardSystem()

        # Gymnasium spaces
        self.action_space = spaces.Discrete(self.encoder.max_neighbors)
        self.observation_space = spaces.Box(
            low=0, high=1, shape=(self.encoder.state_dim,), dtype=np.float32
        )

        # Network ve paket durumu
        self.network = None
        self.current_packet = None
        self.current_node_id = None
        self.destination_node_id = None
        self.max_hops = 50

    def reset(self, seed=None, options=None):
        """Yeni episode başlat"""
        super().reset(seed=seed)

        # Yeni network oluştur
        self.network = Network(width=self.area_width, height=self.area_height)
        self.network.create_network(
            num_nodes=self.num_nodes, communication_range=self.communication_range
        )

        # Aktif düğümleri bul
        active_nodes = [
            nid for nid, node in self.network.nodes.items() if node.is_active
        ]

        if len(active_nodes) < 2:
            raise ValueError("En az 2 aktif düğüm gerekli!")

        # Rastgele kaynak ve hedef seç
        np.random.shuffle(active_nodes)
        self.current_node_id = active_nodes[0]
        self.destination_node_id = active_nodes[1]

        # Paket oluştur
        self.current_packet = Packet(
            packet_id=0,
            source_id=self.current_node_id,
            destination_id=self.destination_node_id,
            data="RL Training Packet",
        )

        # İlk state'i encode et
        state = self._get_state()

        return state, {}

    def _get_state(self):
        """Mevcut durumu encode et"""
        current_node = self.network.nodes[self.current_node_id]
        destination_node = self.network.nodes[self.destination_node_id]

        # Komşu düğümleri al (sadece aktif olanlar)
        neighbor_nodes = []
        for neighbor_id in current_node.neighbors:
            if neighbor_id in self.network.nodes:
                neighbor = self.network.nodes[neighbor_id]
                if neighbor.is_active and neighbor_id not in self.current_packet.path:
                    neighbor_nodes.append(neighbor)

        # State'i encode et
        state = self.encoder.encode(current_node, neighbor_nodes, destination_node)

        return state

    def _get_valid_neighbors(self):
        """Geçerli komşuları döndür (aktif ve döngü olmayan)"""
        current_node = self.network.nodes[self.current_node_id]
        valid_neighbors = []

        for neighbor_id in current_node.neighbors:
            if neighbor_id in self.network.nodes:
                neighbor = self.network.nodes[neighbor_id]
                # Aktif ve daha önce gidilmemiş
                if neighbor.is_active and neighbor_id not in self.current_packet.path:
                    valid_neighbors.append(neighbor_id)

        return valid_neighbors

    def step(self, action):
        """Agent'ın seçtiği aksiyonu uygula"""

        # Geçerli komşuları al
        valid_neighbors = self._get_valid_neighbors()

        # Eğer geçerli komşu yoksa, paket kayboldu
        if not valid_neighbors:
            reward = self.reward_system.calculate(
                success=False,
                energy_level=0.5,
                hop_count=self.current_packet.hop_count,
                failed=True,
            )
            return (
                self._get_state(),
                reward,
                True,
                False,
                {"reason": "no_valid_neighbors"},
            )

        # Action'ı neighbor index'e dönüştür (action >= len ise son komşuyu seç)
        neighbor_index = min(action, len(valid_neighbors) - 1)
        selected_neighbor_id = valid_neighbors[neighbor_index]

        # Paketi yönlendir
        self.current_packet.add_hop(selected_neighbor_id)
        self.current_node_id = selected_neighbor_id

        # Seçilen komşunun enerji seviyesi
        selected_node = self.network.nodes[selected_neighbor_id]
        energy_level = selected_node.battery_level

        # Hedefe ulaştı mı kontrol et
        if self.current_node_id == self.destination_node_id:
            reward = self.reward_system.calculate(
                success=True,
                energy_level=energy_level,
                hop_count=self.current_packet.hop_count,
                failed=False,
            )
            return self._get_state(), reward, True, False, {"reason": "success"}

        # Maksimum hop aşıldı mı?
        if self.current_packet.hop_count >= self.max_hops:
            reward = self.reward_system.calculate(
                success=False,
                energy_level=energy_level,
                hop_count=self.current_packet.hop_count,
                failed=True,
            )
            return self._get_state(), reward, True, False, {"reason": "max_hops"}

        # Devam ediyor
        reward = self.reward_system.calculate(
            success=False,
            energy_level=energy_level,
            hop_count=self.current_packet.hop_count,
            failed=False,
        )

        # Rastgele node failure simüle et
        self.network.simulate_node_failure(failure_rate=0.02)

        return self._get_state(), reward, False, False, {}

    def render(self, mode="human"):
        """Durumu görselleştir"""
        if mode == "human":
            print(f"Current Node: {self.current_node_id}")
            print(f"Destination: {self.destination_node_id}")
            print(f"Path: {self.current_packet.path}")
            print(f"Hop Count: {self.current_packet.hop_count}")
