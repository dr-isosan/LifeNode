"""
Link (Bağlantı) Modeli

İki düğüm arasındaki kablosuz bağlantıyı temsil eder.
Sinyal kalitesi, gecikme ve paket kaybı modelleme.
"""

from dataclasses import dataclass, field
from typing import Tuple, Optional
import math
import random


@dataclass
class Link:
    """
    İki düğüm arasındaki kablosuz bağlantı

    Attributes:
        node_a: İlk düğüm ID'si
        node_b: İkinci düğüm ID'si
        distance: Düğümler arası mesafe (metre)
        quality: Bağlantı kalitesi (0-1, 1 = mükemmel)
        latency: Gecikme (ms)
        is_active: Bağlantı aktif mi?
    """

    node_a: str
    node_b: str
    distance: float

    # Bağlantı özellikleri
    quality: float = 1.0
    latency: float = 1.0
    bandwidth: float = 100.0  # Mbps
    is_active: bool = True

    # Sinyal modeli parametreleri
    path_loss_exponent: float = 3.0
    reference_distance: float = 1.0
    reference_loss_db: float = 40.0
    noise_floor_dbm: float = -90.0
    transmission_power_dbm: float = 20.0
    min_snr_db: float = 10.0

    # Gecikme modeli
    base_latency_ms: float = 1.0
    latency_per_meter: float = 0.01

    # Paket kaybı
    base_packet_loss_rate: float = 0.01

    # İstatistikler
    packets_transmitted: int = 0
    packets_lost: int = 0

    def __post_init__(self):
        """Başlangıç hesaplamaları"""
        self.update_quality()
        self.update_latency()

    # =========================================================================
    # SİNYAL KALİTESİ MODELİ
    # =========================================================================

    def calculate_path_loss(self, distance: float) -> float:
        """
        Yol kaybını hesapla (Log-distance path loss model)

        PL(d) = PL(d0) + 10 * n * log10(d/d0)

        Args:
            distance: Mesafe (metre)

        Returns:
            Yol kaybı (dB)
        """
        if distance <= 0:
            distance = 0.1  # Minimum mesafe

        if distance < self.reference_distance:
            return self.reference_loss_db

        path_loss = (
            self.reference_loss_db +
            10 * self.path_loss_exponent * math.log10(distance / self.reference_distance)
        )
        return path_loss

    def calculate_snr(self, distance: float) -> float:
        """
        Sinyal-gürültü oranını hesapla

        SNR = Tx_power - Path_loss - Noise_floor

        Args:
            distance: Mesafe (metre)

        Returns:
            SNR (dB)
        """
        path_loss = self.calculate_path_loss(distance)
        received_power = self.transmission_power_dbm - path_loss
        snr = received_power - self.noise_floor_dbm
        return snr

    def calculate_quality_from_snr(self, snr: float) -> float:
        """
        SNR'den kalite değeri üret (0-1)

        Sigmoid fonksiyonu kullanarak yumuşak geçiş

        Args:
            snr: Sinyal-gürültü oranı (dB)

        Returns:
            Kalite (0-1)
        """
        if snr < self.min_snr_db:
            return 0.0

        # Sigmoid: kalite min_snr'da 0, min_snr+20'de ~1
        normalized = (snr - self.min_snr_db) / 20.0
        quality = 1.0 / (1.0 + math.exp(-5 * (normalized - 0.5)))
        return min(1.0, max(0.0, quality))

    def update_quality(self):
        """Mesafeye göre kaliteyi güncelle"""
        snr = self.calculate_snr(self.distance)
        self.quality = self.calculate_quality_from_snr(snr)
        self.is_active = self.quality > 0

    # =========================================================================
    # GECİKME MODELİ
    # =========================================================================

    def update_latency(self):
        """Mesafe ve kaliteye göre gecikmeyi güncelle"""
        # Temel gecikme + mesafeye bağlı gecikme
        base = self.base_latency_ms + self.distance * self.latency_per_meter

        # Düşük kalitede gecikme artar
        if self.quality > 0:
            quality_factor = 1.0 / self.quality
            self.latency = base * min(quality_factor, 10.0)
        else:
            self.latency = float('inf')

    def get_transmission_time(self, packet_size_bytes: int) -> float:
        """
        Paket iletim süresini hesapla

        Args:
            packet_size_bytes: Paket boyutu (byte)

        Returns:
            İletim süresi (ms)
        """
        if self.bandwidth <= 0:
            return float('inf')

        # Bandwidth Mbps, boyut byte
        # 1 Mbps = 125000 byte/s = 125 byte/ms
        bytes_per_ms = self.bandwidth * 125
        transmission_time = packet_size_bytes / bytes_per_ms

        return self.latency + transmission_time

    # =========================================================================
    # PAKET KAYBI MODELİ
    # =========================================================================

    def calculate_packet_loss_rate(self) -> float:
        """
        Paket kayıp oranını hesapla

        Kalite düştükçe kayıp artar

        Returns:
            Kayıp olasılığı (0-1)
        """
        if not self.is_active:
            return 1.0

        # Temel kayıp + kaliteye bağlı kayıp
        quality_loss = (1 - self.quality) * 0.5
        total_loss = self.base_packet_loss_rate + quality_loss

        return min(1.0, max(0.0, total_loss))

    def attempt_transmission(self) -> bool:
        """
        Paket iletimini simüle et

        Returns:
            True eğer başarılı, False eğer kayıp
        """
        self.packets_transmitted += 1

        loss_rate = self.calculate_packet_loss_rate()
        if random.random() < loss_rate:
            self.packets_lost += 1
            return False

        return True

    # =========================================================================
    # DEGRADASYON
    # =========================================================================

    def degrade(self, factor: float):
        """
        Bağlantı kalitesini düşür (afet etkisi)

        Args:
            factor: Degradasyon faktörü (0-1, 0 = tam degrade)
        """
        self.quality *= factor
        self.update_latency()

        if self.quality < 0.01:
            self.is_active = False

    def recover(self, factor: float = 1.1):
        """
        Bağlantı kalitesini artır (kurtarma)

        Args:
            factor: İyileşme faktörü (>1)
        """
        if not self.is_active and self.quality > 0:
            self.is_active = True

        # Orijinal kaliteye doğru iyileştir
        original_quality = self.calculate_quality_from_snr(
            self.calculate_snr(self.distance)
        )
        self.quality = min(original_quality, self.quality * factor)
        self.update_latency()

    def update_distance(self, new_distance: float):
        """
        Mesafeyi güncelle (düğüm hareketi sonrası)

        Args:
            new_distance: Yeni mesafe (metre)
        """
        self.distance = new_distance
        self.update_quality()
        self.update_latency()

    # =========================================================================
    # YARDIMCI METODLAR
    # =========================================================================

    @property
    def packet_loss_rate(self) -> float:
        """Gözlemlenen paket kayıp oranı"""
        if self.packets_transmitted == 0:
            return 0.0
        return self.packets_lost / self.packets_transmitted

    def get_key(self) -> Tuple[str, str]:
        """Sıralı anahtar döndür (node_a < node_b)"""
        if self.node_a < self.node_b:
            return (self.node_a, self.node_b)
        return (self.node_b, self.node_a)

    def connects(self, node_id: str) -> bool:
        """Bu bağlantı belirtilen düğüme bağlı mı?"""
        return node_id in (self.node_a, self.node_b)

    def other_node(self, node_id: str) -> Optional[str]:
        """Belirtilen düğümün karşısındaki düğümü döndür"""
        if node_id == self.node_a:
            return self.node_b
        elif node_id == self.node_b:
            return self.node_a
        return None

    def __repr__(self) -> str:
        return (
            f"Link({self.node_a}<->{self.node_b}, "
            f"dist={self.distance:.1f}m, quality={self.quality:.2f}, "
            f"latency={self.latency:.1f}ms, active={self.is_active})"
        )

    def to_dict(self) -> dict:
        """Bağlantıyı sözlük olarak döndür"""
        return {
            'node_a': self.node_a,
            'node_b': self.node_b,
            'distance': self.distance,
            'quality': self.quality,
            'latency': self.latency,
            'is_active': self.is_active,
            'packets_transmitted': self.packets_transmitted,
            'packets_lost': self.packets_lost,
        }
