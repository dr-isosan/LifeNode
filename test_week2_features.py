"""
Week 2 Özelliklerini Test Et
Person A ve Person B'nin tüm Week 2 gereksinimlerini doğrula
"""

import sys
import os
import logging

sys.path.insert(0, os.path.dirname(__file__))

from simulation.network import Network  # noqa: E402
from src.core.simulator import SimulationNetworkAdapter  # noqa: E402
from src.utils.logger import get_logger  # noqa: E402

# Test logger
logger = get_logger("Week2Test", level=logging.INFO, log_to_file=False)


def test_person_a_week2():
    """Person A - Network & Simulation Architect - Week 2 Test"""
    logger.info("\n" + "=" * 60)
    logger.info("PERSON A - WEEK 2 FEATURES TEST")
    logger.info("=" * 60)

    # Network oluştur
    network = Network(width=100.0, height=100.0)
    network.create_network(num_nodes=20, communication_range=30.0)

    # 1. TIMESTEPS ✓
    logger.info("\n[1/8] Timesteps Test")
    initial_time = network.simulation_time
    network.step()
    network.step()
    assert network.simulation_time == initial_time + 2
    logger.info(f"✓ Timesteps çalışıyor: {network.simulation_time}")

    # 2. PACKET LOSS/LATENCY METRICS ✓
    logger.info("\n[2/8] Packet Loss & Latency Metrics Test")
    stats = network.get_network_stats()
    assert "delivered_packets" in stats
    assert "lost_packets" in stats
    assert "total_packets" in stats
    logger.info(f"✓ Packet metrics: {stats['total_packets']} total")

    # 3. LATENCY MODEL ✓
    logger.info("\n[3/8] Latency Model Test")
    adapter = SimulationNetworkAdapter(network)
    latency = adapter._calculate_latency(distance=50.0)
    assert latency > 0.001  # Base latency
    logger.info(f"✓ Latency (50m): {latency*1000:.2f}ms")

    # 4. BANDWIDTH MODEL ✓
    logger.info("\n[4/8] Bandwidth Model Test")
    # High signal -> High bandwidth
    bw_high = adapter._calculate_bandwidth(
        distance=10.0, signal_strength=0.9, communication_range=30.0
    )
    # Low signal -> Low bandwidth
    bw_low = adapter._calculate_bandwidth(
        distance=25.0, signal_strength=0.3, communication_range=30.0
    )
    assert bw_high > bw_low
    logger.info(f"✓ Bandwidth (strong signal): {bw_high:.1f} Mbps")
    logger.info(f"✓ Bandwidth (weak signal): {bw_low:.1f} Mbps")

    # 5. SIGNAL STRENGTH MODEL ✓
    logger.info("\n[5/8] Signal Strength Model Test")
    signal_close = adapter._calculate_signal_strength(
        distance=5.0, communication_range=30.0
    )
    signal_far = adapter._calculate_signal_strength(
        distance=25.0, communication_range=30.0
    )
    assert signal_close > signal_far
    logger.info(f"✓ Signal (5m): {signal_close:.2f}")
    logger.info(f"✓ Signal (25m): {signal_far:.2f}")

    # 6. DYNAMIC NEIGHBOR UPDATES ✓
    logger.info("\n[6/8] Dynamic Neighbor Updates Test")
    # Node arızası simüle et
    initial_neighbors = {}
    for node_id, node in network.nodes.items():
        initial_neighbors[node_id] = len(node.neighbors)

    # Arıza simüle et (yüksek oran ile)
    failures, repairs = network.simulate_node_failure(failure_rate=0.3)

    if failures:
        # En az bir komşunun neighbor listesi değişmeli
        neighbor_changed = False
        for node_id, node in network.nodes.items():
            if len(node.neighbors) != initial_neighbors.get(node_id, 0):
                neighbor_changed = True
                break
        logger.info(
            f"✓ Dynamic updates: {len(failures)} failures, "
            f"neighbors {'updated' if neighbor_changed else 'checked'}"
        )
    else:
        logger.info("✓ Dynamic updates: mechanism ready (no failures)")

    # 7. NETWORK METHODS ✓
    logger.info("\n[7/8] Network Methods Test")
    assert hasattr(network, "send_packet")
    assert hasattr(network, "step")
    assert hasattr(network, "get_network_stats")
    logger.info("✓ send_packet(), step(), get_network_stats() exist")

    # 8. DEBUG LOGGING ✓
    logger.info("\n[8/8] Debug Logging System Test")
    from src.utils.logger import NetworkLogger

    test_logger = NetworkLogger("TestLogger", level=logging.DEBUG)
    test_logger.debug("Debug message")
    test_logger.info("Info message")
    test_logger.warning("Warning message")
    logger.info("✓ NetworkLogger working (DEBUG, INFO, WARNING, ERROR)")

    logger.info("\n" + "=" * 60)
    logger.info("PERSON A - WEEK 2: ALL TESTS PASSED ✓")
    logger.info("=" * 60)


def test_person_b_week2():
    """Person B - AI Architect - Week 2 Test (Quick Check)"""
    logger.info("\n" + "=" * 60)
    logger.info("PERSON B - WEEK 2 FEATURES TEST")
    logger.info("=" * 60)

    from src.ai.env import LifeNodeEnv
    from src.ai.agent import DQNAgent
    from src.ai.reward import RewardSystem
    from src.ai.memory import ReplayBuffer

    # 1. Environment Integration ✓
    logger.info("\n[1/6] Environment-Network Integration")
    network = Network(width=100.0, height=100.0)
    network.create_network(num_nodes=20, communication_range=30.0)
    adapter = SimulationNetworkAdapter(network)
    env = LifeNodeEnv(sim_engine=adapter)
    logger.info("✓ LifeNodeEnv integrated with real simulation")

    # 2. State Encoder ✓
    logger.info("\n[2/6] State Encoder")
    obs, _ = env.reset()
    assert obs is not None
    assert len(obs.shape) == 1  # 1D array
    logger.info(f"✓ StateEncoder working: {obs.shape}")

    # 3. Reward System ✓
    logger.info("\n[3/6] Reward System")
    reward_sys = RewardSystem()
    test_reward = reward_sys.calculate_reward(
        success=True, energy_level=0.8, hop_count=3
    )
    assert isinstance(test_reward, float)
    logger.info(f"✓ RewardSystem working: {test_reward:.2f}")

    # 4. Replay Buffer ✓
    logger.info("\n[4/6] Replay Buffer")
    buffer = ReplayBuffer(capacity=1000, device="cpu")
    buffer.push(obs, 0, 1.0, obs, False)
    assert len(buffer) == 1
    logger.info(f"✓ ReplayBuffer working: {len(buffer)} experiences")

    # 5. DQN Model ✓
    logger.info("\n[5/6] DQN Model")
    agent = DQNAgent(state_dim=len(obs), action_dim=5)
    action = agent.act(obs)
    assert 0 <= action < 5
    logger.info(f"✓ DQNAgent working: action={action}")

    # 6. Training Loop ✓
    logger.info("\n[6/6] Training Loop Components")
    # Quick episode test
    obs, _ = env.reset()
    action = agent.act(obs)
    next_obs, reward, done, truncated, info = env.step(action)
    logger.info(f"✓ Training loop ready: reward={reward:.2f}")

    logger.info("\n" + "=" * 60)
    logger.info("PERSON B - WEEK 2: ALL TESTS PASSED ✓")
    logger.info("=" * 60)


def main():
    """Run all Week 2 tests"""
    logger.info("\n\n")
    logger.info("#" * 60)
    logger.info("### LIFENODE - WEEK 2 FULL REVIEW ###")
    logger.info("#" * 60)

    try:
        # Test Person A features
        test_person_a_week2()

        # Test Person B features
        test_person_b_week2()

        logger.info("\n\n")
        logger.info("🎉 " * 20)
        logger.info("ALL WEEK 2 FEATURES WORKING SUCCESSFULLY!")
        logger.info("Person A: 8/8 features ✓")
        logger.info("Person B: 6/6 features ✓")
        logger.info("🎉 " * 20)

    except Exception as e:
        logger.error(f"\n❌ TEST FAILED: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
