
import sys
import os
import random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lifenode.config import SimulationConfig, WorldConfig
from lifenode.environment.world import World
from lifenode.rl_agent.rl_router import RLRouter
from lifenode.rl_agent.qlearning import QLearningConfig
from lifenode.rl_agent.state import StateBuilder

def debug_run():
    print("🚀 Starting Debug Trace...")

    # 1. Setup minimal world
    config = SimulationConfig()
    config.world.initial_node_count = 10
    config.world.width = 300
    config.world.height = 300

    rl_config = QLearningConfig(
        learning_rate=0.5,
        epsilon_start=0.5,
        epsilon_end=0.0,
        discount_factor=0.9
    )

    router = RLRouter(ql_config=rl_config, training_mode=True)

    # Enable debug print in router? No, we inspect externally.

    training_episodes = 50
    print(f"\n--- Training Loop Trace ({training_episodes} episodes) ---")

    for ep in range(training_episodes):
        # IMPORTANT: Use same seed to keep topology constant?
        # Or random to test generalization?
        # User problem is generalization. Let's use Random seeds.
        seed = 42 + ep

        world = World(config=config, seed=seed)
        world.initialize_random_nodes()
        world.set_router(router)

        delivered = 0
        dropped = 0

        # Run standard steps
        for step in range(200):
            res = world.step()
            delivered += res.packets_delivered
            dropped += res.packets_dropped

        router.end_episode()

        if ep % 10 == 0:
            print(f"Ep {ep}: Del={delivered} Drop={dropped} | Q-Table Size: {len(router.agent.q_table)} | Epsilon: {router.agent.epsilon:.2f}")

    print("\n--- Final Q-Table (Top 10 States) ---")
    # Sort states by max Q-value
    sorted_items = sorted(
        router.agent.q_table.items(),
        key=lambda item: max(item[1].values()) if item[1] else -999,
        reverse=True
    )

    for k, v in sorted_items[:10]:
        print(f"State: {k}")
        print(f"   Actions: {dict(v)}")

        # Decode state roughly
        # (energy_bin, queue_bin, best_quality, best_energy, has_closer, avg_quality_bin, num_neighbors)
        print(f"   Interpretation: HasCloser={k[4]}, Quality={k[2]}, NumNeighbors={k[6]}")

if __name__ == "__main__":
    debug_run()
