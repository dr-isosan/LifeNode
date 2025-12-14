# src/config/constants.py
"""
LifeNode Proje Sabitleri
Tüm magic number'lar bu dosyada toplanmıştır.
"""


class NetworkConstants:
    """Network simülasyonu için sabitler"""

    # Routing parametreleri
    RANDOM_ROUTING_PROBABILITY = 0.7  # %70 ihtimalle rastgele komşu seç
    GREEDY_ROUTING_PROBABILITY = 0.3  # %30 ihtimalle en yakın komşu seç
    MAX_PACKET_HOPS = 10  # Maksimum paket sıçrama sayısı

    # Node arıza parametreleri
    NODE_REPAIR_CHANCE = 0.5  # %50 şans ile bozuk node tamir olur
    DEFAULT_NODE_FAILURE_RATE = 0.02  # Default %2 arıza oranı

    # Default network parametreleri
    DEFAULT_COMMUNICATION_RANGE = 25.0  # Meter
    DEFAULT_AREA_WIDTH = 100.0
    DEFAULT_AREA_HEIGHT = 100.0
    DEFAULT_NUM_NODES = 20


class SignalThresholds:
    """Sinyal gücü eşik değerleri (802.11g standardı)"""

    EXCELLENT = 0.8  # Mükemmel sinyal: 64-QAM modulation
    GOOD = 0.6       # İyi sinyal: 16-QAM modulation
    FAIR = 0.4       # Orta sinyal: QPSK modulation
    WEAK = 0.2       # Zayıf sinyal: BPSK modulation
    # < 0.2: Çok zayıf sinyal


class BandwidthRatios:
    """Sinyal gücüne göre bandwidth oranları"""

    EXCELLENT_RATIO = 1.0   # %100 bandwidth (64-QAM)
    GOOD_RATIO = 0.75       # %75 bandwidth (16-QAM)
    FAIR_RATIO = 0.5        # %50 bandwidth (QPSK)
    WEAK_RATIO = 0.25       # %25 bandwidth (BPSK)
    MINIMUM_RATIO = 0.1     # %10 minimum bandwidth


class PhysicsConstants:
    """Fiziksel katman sabitleri"""

    # Bandwidth
    MAX_BANDWIDTH_MBPS = 54.0  # 802.11g standardı
    MIN_BANDWIDTH_MBPS = 1.0   # Minimum garanti

    # Latency
    BASE_LATENCY_MS = 1.0      # Base latency: 1ms
    LATENCY_PER_METER_MS = 0.1 # Her metre için 0.1ms ek

    # Energy
    BASE_ENERGY_COST = 0.5     # Base energy cost
    ENERGY_COST_PER_METER = 0.01  # Her metre için ek enerji
    DISTANCE_PENALTY_FACTOR = 0.3  # Bandwidth hesabında mesafe cezası

    # Signal
    SIGNAL_QUADRATIC_FALLOFF = 2  # Sinyal düşüş üssü (quadratic)


class AITrainingConfig:
    """AI eğitim parametreleri"""

    # Training loop
    DEFAULT_EPISODES = 100
    MAX_STEPS_PER_EPISODE = 50
    BATCH_SIZE = 64
    TARGET_UPDATE_FREQUENCY = 10  # Her 10 episode'da target net güncelle

    # DQN Agent
    LEARNING_RATE = 1e-3
    GAMMA = 0.99  # Discount factor
    EPSILON_START = 1.0
    EPSILON_MIN = 0.01
    EPSILON_DECAY = 0.995

    # Network architecture
    HIDDEN_LAYER_SIZE = 64
    REPLAY_BUFFER_SIZE = 10000

    # Environment
    MAX_NEIGHBORS = 5


class RewardWeights:
    """Reward function ağırlıkları"""

    # Temel ödüller
    SUCCESS_REWARD = 100.0
    FAILURE_PENALTY = -1.0
    STEP_PENALTY = -5.0

    # Enerji cezası
    ENERGY_PENALTY_WEIGHT = -50.0

    # Yeni: Ek faktörler
    SIGNAL_BONUS_WEIGHT = 3.0
    BANDWIDTH_BONUS_WEIGHT = 2.0
    QUEUE_PENALTY_WEIGHT = -10.0
    HOP_BONUS_PER_STEP = 2.0  # Kısa yol bonusu


class StateEncoderConfig:
    """State encoder sabitleri"""

    MAX_DISTANCE_METERS = 1000.0  # Normalizasyon için maksimum mesafe
    FEATURES_PER_NEIGHBOR = 3  # Sinyal, enerji, kuyruk


class LoggerConfig:
    """Logger ayarları"""

    DEFAULT_LOG_LEVEL = "INFO"
    LOG_TO_FILE = False
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
