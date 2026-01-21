"""
LifeNode Konfigürasyon Dosyası

Tüm simülasyon parametreleri ve sabitler burada tanımlanır.
"""

from dataclasses import dataclass, field
from typing import Tuple, Optional


# ============================================================================
# DÜNYA (WORLD) AYARLARI
# ============================================================================

@dataclass
class WorldConfig:
    """Simülasyon dünyası yapılandırması"""

    # Alan boyutları (metre)
    width: float = 500.0
    height: float = 500.0

    # Zaman
    max_steps: int = 1000
    step_duration_ms: float = 100.0  # Her adım 100ms

    # Başlangıç düğüm sayısı (RL öğrenimi için optimal: 20-50)
    initial_node_count: int = 30

    # Rastgelelik tohumu (reproducibility için)
    seed: Optional[int] = 42


# ============================================================================
# DÜĞÜM (NODE) AYARLARI
# ============================================================================

@dataclass
class NodeConfig:
    """Düğüm yapılandırması"""

    # Enerji
    initial_energy: float = 100.0
    energy_per_transmit: float = 0.1
    energy_per_receive: float = 0.05
    energy_per_idle: float = 0.001

    # İletim
    transmission_range: float = 75.0  # metre
    transmission_power: float = 20.0  # dBm

    # Kuyruk
    max_queue_size: int = 50

    # Hareket (opsiyonel)
    max_speed: float = 2.0  # m/s
    mobility_enabled: bool = False


# ============================================================================
# BAĞLANTI (LINK) AYARLARI
# ============================================================================

@dataclass
class LinkConfig:
    """Bağlantı yapılandırması"""

    # Sinyal modeli parametreleri (Path Loss)
    path_loss_exponent: float = 3.0  # Kentsel ortam için tipik değer
    reference_distance: float = 1.0  # metre
    reference_loss_db: float = 40.0  # 1m'de kayıp

    # Gürültü
    noise_floor_dbm: float = -90.0

    # Kalite eşikleri
    min_snr_db: float = 10.0  # Minimum SNR for connection

    # Gecikme modeli
    base_latency_ms: float = 1.0
    latency_per_meter: float = 0.01  # ms/m

    # Paket kaybı
    base_packet_loss_rate: float = 0.01  # %1


# ============================================================================
# PAKET AYARLARI
# ============================================================================

@dataclass
class PacketConfig:
    """Paket yapılandırması"""

    # Boyut
    default_size_bytes: int = 1024

    # TTL (Time To Live)
    default_ttl: int = 64

    # Timeout
    timeout_ms: float = 5000.0  # 5 saniye


# ============================================================================
# TRAFİK AYARLARI
# ============================================================================

@dataclass
class TrafficConfig:
    """Trafik üreteci yapılandırması"""

    # Trafik yoğunluğu
    packets_per_step: float = 0.5  # Ortalama

    # Paket boyutu dağılımı
    min_packet_size: int = 64
    max_packet_size: int = 1500

    # Kaynak-hedef seçimi
    random_source_dest: bool = True


# ============================================================================
# RL AJANI AYARLARI
# ============================================================================

@dataclass
class RLConfig:
    """Reinforcement Learning yapılandırması"""

    # Q-Learning parametreleri
    learning_rate: float = 0.1
    discount_factor: float = 0.95

    # Epsilon-greedy
    epsilon_start: float = 1.0
    epsilon_end: float = 0.01
    epsilon_decay: float = 0.995

    # State discretization
    energy_bins: int = 10
    queue_bins: int = 5
    quality_bins: int = 10

    # Maksimum komşu sayısı (state boyutu için)
    max_neighbors: int = 8


# ============================================================================
# ÖDÜL AYARLARI
# ============================================================================

@dataclass
class RewardConfig:
    """Ödül fonksiyonu yapılandırması"""

    # Ana ödüller
    delivery_reward: float = 10.0
    drop_penalty: float = -10.0

    # Hop başına ceza
    hop_penalty: float = -0.1

    # Bonus/ceza ağırlıkları
    latency_weight: float = 1.0
    energy_weight: float = 0.5
    queue_penalty_weight: float = 0.5


# ============================================================================
# GÖRSELLEŞTİRME AYARLARI
# ============================================================================

@dataclass
class VisualizationConfig:
    """Görselleştirme yapılandırması"""

    # Pencere boyutu
    window_width: int = 1200
    window_height: int = 800

    # FPS
    target_fps: int = 30

    # Renkler (RGB)
    background_color: Tuple[int, int, int] = (20, 20, 30)
    node_active_color: Tuple[int, int, int] = (0, 200, 100)
    node_inactive_color: Tuple[int, int, int] = (200, 50, 50)
    link_color: Tuple[int, int, int] = (100, 100, 150)
    packet_color: Tuple[int, int, int] = (255, 200, 50)

    # Boyutlar
    node_radius: int = 8
    link_width: int = 1


# ============================================================================
# ANA KONFİGÜRASYON
# ============================================================================

@dataclass
class SimulationConfig:
    """Ana simülasyon yapılandırması - tüm alt konfigürasyonları içerir"""

    world: WorldConfig = field(default_factory=WorldConfig)
    node: NodeConfig = field(default_factory=NodeConfig)
    link: LinkConfig = field(default_factory=LinkConfig)
    packet: PacketConfig = field(default_factory=PacketConfig)
    traffic: TrafficConfig = field(default_factory=TrafficConfig)
    rl: RLConfig = field(default_factory=RLConfig)
    reward: RewardConfig = field(default_factory=RewardConfig)
    visualization: VisualizationConfig = field(default_factory=VisualizationConfig)


# Varsayılan konfigürasyon
DEFAULT_CONFIG = SimulationConfig()
