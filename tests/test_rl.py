# tests/test_rl.py
"""
RL Pipeline Test Suite - Güncellenmiş Versiyon
Gerçek network simülasyonu ile entegre
"""
import unittest
import numpy as np
from simulation.network import Network
from src.core.simulator import SimulationNetworkAdapter
from src.ai.agent import DQNAgent
from src.ai.env import LifeNodeEnv


class TestRLPipeline(unittest.TestCase):
    def setUp(self):
        """Her testten önce ortamı kur"""
        # Network simülasyonu oluştur
        self.network = Network(width=100.0, height=100.0)
        self.network.create_network(num_nodes=15, communication_range=30.0)

        # Adapter oluştur
        self.sim_adapter = SimulationNetworkAdapter(self.network)

        # Environment oluştur
        self.env = LifeNodeEnv(sim_engine=self.sim_adapter, max_neighbors=5)

        # Agent oluştur
        state_dim = self.env.observation_space.shape[0]
        action_dim = self.env.action_space.n
        self.agent = DQNAgent(state_dim=state_dim, action_dim=action_dim)

    def test_network_initialization(self):
        """Network düzgün başlatıldı mı?"""
        print("\n✅ Test 1: Network Başlatma...")
        self.assertIsNotNone(self.network)
        self.assertGreater(len(self.network.nodes), 0)
        print(f"   Network nodes: {len(self.network.nodes)}")

    def test_agent_initialization(self):
        """Ajan ve Network boyutları uyuşuyor mu?"""
        print("\n✅ Test 2: Ajan Başlatma...")
        expected_input = self.env.observation_space.shape[0]
        actual_input = self.agent.policy_net.fc1.in_features
        self.assertEqual(actual_input, expected_input)
        print(f"   State dimension: {actual_input}")

    def test_action_selection(self):
        """Ajan geçerli bir aksiyon üretiyor mu?"""
        print("\n✅ Test 3: Aksiyon Seçimi...")
        state = np.zeros(self.env.observation_space.shape)
        action = self.agent.act(state)
        self.assertTrue(0 <= action < self.env.action_space.n)
        print(f"   Üretilen Aksiyon: {action}")

    def test_memory_integration(self):
        """Hafızaya atılan veri geri okunabiliyor mu?"""
        print("\n✅ Test 4: Hafıza Entegrasyonu...")
        state = np.zeros(self.env.observation_space.shape)
        next_state = np.zeros(self.env.observation_space.shape)

        self.agent.remember(state, 1, 10, next_state, False)
        self.assertEqual(len(self.agent.memory), 1)
        print(f"   Hafıza boyutu: {len(self.agent.memory)}")

    def test_environment_reset(self):
        """Environment reset çalışıyor mu?"""
        print("\n✅ Test 5: Environment Reset...")
        state, info = self.env.reset()
        self.assertEqual(state.shape, self.env.observation_space.shape)
        self.assertIn("source", info)
        self.assertIn("destination", info)
        print(f"   Source: {info['source']}, Dest: {info['destination']}")

    def test_environment_step(self):
        """Environment step çalışıyor mu?"""
        print("\n✅ Test 6: Environment Step...")
        state, info = self.env.reset()
        action = 0
        next_state, reward, done, truncated, info = self.env.step(action)
        self.assertEqual(next_state.shape, self.env.observation_space.shape)
        self.assertIsInstance(reward, (int, float))
        self.assertIsInstance(done, bool)
        print(f"   Reward: {reward:.2f}, Done: {done}")

    def test_full_episode(self):
        """Tam bir episode çalıştırılabiliyor mu?"""
        print("\n✅ Test 7: Full Episode...")
        state, info = self.env.reset()
        total_reward = 0
        steps = 0
        max_steps = 20

        while steps < max_steps:
            action = self.agent.act(state)
            next_state, reward, done, truncated, info = self.env.step(action)
            total_reward += reward
            state = next_state
            steps += 1

            if done or truncated:
                break

        print(
            f"   Episode: {steps} adım, "
            f"Reward: {total_reward:.2f}, "
            f"Sonuç: {info.get('reason', 'unknown')}"
        )
        self.assertGreater(steps, 0)

    def test_observation_format(self):
        """Observation doğru formatta mı?"""
        print("\n✅ Test 8: Observation Format...")
        active_nodes = [nid for nid, n in self.network.nodes.items() if n.is_active]
        if len(active_nodes) >= 2:
            node_id = active_nodes[0]
            dest_id = active_nodes[1]

            obs = self.sim_adapter.get_observation(node_id, dest_id)

            self.assertIsNotNone(obs.current_node)
            self.assertIsNotNone(obs.neighbors)
            self.assertIsNotNone(obs.destination_pos)
            print(f"   Komşu sayısı: {len(obs.neighbors)}")


if __name__ == "__main__":
    unittest.main()
