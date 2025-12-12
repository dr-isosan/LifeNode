# src/training_loop.py
"""
LifeNode AI Eğitim Döngüsü
Gerçek simülasyon ile entegre DQN eğitimi
"""
import numpy as np
from simulation.network import Network
from src.core.simulator import SimulationNetworkAdapter
from ai.env import LifeNodeEnv
from ai.agent import DQNAgent

# AYARLAR (İleride config.yaml'dan gelecek)
EPISODES = 100
MAX_STEPS = 50
BATCH_SIZE = 64
NUM_NODES = 20
COMMUNICATION_RANGE = 30.0
TARGET_UPDATE_FREQ = 10


def main():
    print("🚀 LifeNode: AI Training Module Başlatılıyor...")
    print("=" * 60)

    # 1. Network simülasyonunu oluştur
    print("\n[1/4] Network simülasyonu oluşturuluyor...")
    network = Network(width=100.0, height=100.0)
    network.create_network(num_nodes=NUM_NODES, communication_range=COMMUNICATION_RANGE)
    print(f"✓ {NUM_NODES} node ile ağ oluşturuldu")

    # 2. Simülasyon Adapter'ını oluştur
    print("\n[2/4] Simülasyon adapter'ı oluşturuluyor...")
    sim_adapter = SimulationNetworkAdapter(network)
    print("✓ Network simülasyonu AI environment'a bağlandı")

    # 3. RL Environment'ı oluştur
    print("\n[3/4] RL Environment oluşturuluyor...")
    env = LifeNodeEnv(sim_engine=sim_adapter, max_neighbors=5)
    print(f"✓ Environment hazır (State dim: {env.observation_space.shape})")

    # 4. DQN Agent'ı oluştur
    print("\n[4/4] DQN Agent oluşturuluyor...")
    state_dim = env.observation_space.shape[0]
    action_dim = env.action_space.n
    agent = DQNAgent(state_dim, action_dim, lr=1e-3, gamma=0.99)
    print(f"✓ Agent hazır (State: {state_dim}, Actions: {action_dim})")

    print("\n" + "=" * 60)
    print("EĞİTİM BAŞLIYOR")
    print("=" * 60)

    # --- EĞİTİM DÖNGÜSÜ ---
    success_count = 0
    total_rewards = []

    for episode in range(EPISODES):
        try:
            state, info = env.reset()
            total_reward = 0
            done = False
            truncated = False

            step_count = 0
            while not done and not truncated and step_count < MAX_STEPS:
                # A. Karar Ver (Action)
                action = agent.act(state)

                # B. Uygula (Step)
                next_state, reward, done, truncated, info = env.step(action)

                # C. Hafızaya At (Remember)
                agent.remember(state, action, reward, next_state, done)

                # D. Öğren (Learn / Replay)
                if len(agent.memory) > BATCH_SIZE:
                    agent.learn()

                state = next_state
                total_reward += reward
                step_count += 1

            # Episode başarılı mı?
            if info.get("reason") == "success":
                success_count += 1

            total_rewards.append(total_reward)

            # Her 10 episode'da bir rapor
            if (episode + 1) % 10 == 0:
                avg_reward = np.mean(total_rewards[-10:])
                success_rate = success_count / (episode + 1)
                print(
                    f"Episode {episode+1}/{EPISODES} | "
                    f"Avg Reward: {avg_reward:.2f} | "
                    f"Success Rate: {success_rate:.1%} | "
                    f"Epsilon: {agent.epsilon:.3f}"
                )

            # Target network güncelleme
            if (episode + 1) % TARGET_UPDATE_FREQ == 0:
                agent.target_net.load_state_dict(agent.policy_net.state_dict())

            # Epsilon decay
            agent.update_epsilon()

        except Exception as e:
            print(f"Episode {episode+1} HATA: {e}")
            continue

    print("\n" + "=" * 60)
    print("EĞİTİM TAMAMLANDI")
    print("=" * 60)
    print(f"Toplam Episode: {EPISODES}")
    print(f"Başarı Sayısı: {success_count}")
    print(f"Başarı Oranı: {success_count/EPISODES:.1%}")
    print(f"Ortalama Reward: {np.mean(total_rewards):.2f}")


if __name__ == "__main__":
    main()
