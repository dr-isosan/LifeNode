"""
Metric Collector (Metrik Toplayıcı)

Simülasyon sırasında performans metriklerini toplar.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
import time

from ..environment.packet import Packet, PacketResult, PacketStatus


@dataclass
class FailureEvent:
    """Arıza olayı"""
    timestamp: int       # Simülasyon adımı
    node_id: str         # Arızalanan düğüm
    recovery_time: Optional[int] = None  # Kurtarma süresi (adım)


@dataclass
class ExperimentMetrics:
    """
    Deney Metrikleri

    Bir simülasyon veya deneyin tüm metriklerini içerir.
    """

    # Temel sayaçlar
    total_packets_sent: int = 0
    total_packets_delivered: int = 0
    total_packets_dropped: int = 0
    total_packets_expired: int = 0

    # Gecikme (latency) ölçümleri
    latencies: List[float] = field(default_factory=list)

    # Hop sayıları
    hop_counts: List[int] = field(default_factory=list)

    # Arıza ve kurtarma
    failure_events: List[FailureEvent] = field(default_factory=list)
    recovery_times: List[int] = field(default_factory=list)

    # Zaman serisi
    pdr_over_time: List[float] = field(default_factory=list)
    latency_over_time: List[float] = field(default_factory=list)
    active_nodes_over_time: List[int] = field(default_factory=list)
    active_links_over_time: List[int] = field(default_factory=list)

    # Enerji
    total_energy_consumed: float = 0.0

    # Zaman
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None

    # =========================================================================
    # HESAPLANAN METRİKLER
    # =========================================================================

    @property
    def packet_delivery_ratio(self) -> float:
        """Paket Teslim Oranı (PDR)"""
        if self.total_packets_sent == 0:
            return 0.0
        return self.total_packets_delivered / self.total_packets_sent

    @property
    def packet_loss_ratio(self) -> float:
        """Paket Kayıp Oranı"""
        return 1.0 - self.packet_delivery_ratio

    @property
    def average_latency(self) -> float:
        """Ortalama Gecikme (ms)"""
        if not self.latencies:
            return 0.0
        return sum(self.latencies) / len(self.latencies)

    @property
    def max_latency(self) -> float:
        """Maksimum Gecikme (ms)"""
        if not self.latencies:
            return 0.0
        return max(self.latencies)

    @property
    def min_latency(self) -> float:
        """Minimum Gecikme (ms)"""
        if not self.latencies:
            return 0.0
        return min(self.latencies)

    @property
    def latency_std(self) -> float:
        """Gecikme Standart Sapması"""
        if len(self.latencies) < 2:
            return 0.0
        mean = self.average_latency
        variance = sum((x - mean) ** 2 for x in self.latencies) / len(self.latencies)
        return variance ** 0.5

    @property
    def average_hops(self) -> float:
        """Ortalama Hop Sayısı"""
        if not self.hop_counts:
            return 0.0
        return sum(self.hop_counts) / len(self.hop_counts)

    @property
    def average_recovery_time(self) -> float:
        """Ortalama Kurtarma Süresi (adım)"""
        if not self.recovery_times:
            return 0.0
        return sum(self.recovery_times) / len(self.recovery_times)

    @property
    def total_failures(self) -> int:
        """Toplam Arıza Sayısı"""
        return len(self.failure_events)

    @property
    def experiment_duration(self) -> float:
        """Deney Süresi (saniye)"""
        if self.end_time is None:
            return time.time() - self.start_time
        return self.end_time - self.start_time

    # =========================================================================
    # YARDIMCI METODLAR
    # =========================================================================

    def to_dict(self) -> dict:
        """Metrikleri sözlük olarak döndür"""
        return {
            'total_packets_sent': self.total_packets_sent,
            'total_packets_delivered': self.total_packets_delivered,
            'total_packets_dropped': self.total_packets_dropped,
            'total_packets_expired': self.total_packets_expired,
            'packet_delivery_ratio': self.packet_delivery_ratio,
            'average_latency_ms': self.average_latency,
            'max_latency_ms': self.max_latency,
            'min_latency_ms': self.min_latency,
            'latency_std': self.latency_std,
            'average_hops': self.average_hops,
            'total_failures': self.total_failures,
            'average_recovery_time': self.average_recovery_time,
            'experiment_duration_s': self.experiment_duration,
        }

    def summary(self) -> str:
        """Özet metin döndür"""
        return (
            f"PDR: {self.packet_delivery_ratio:.2%} | "
            f"Latency: {self.average_latency:.2f}ms | "
            f"Hops: {self.average_hops:.2f} | "
            f"Failures: {self.total_failures}"
        )


class MetricCollector:
    """
    Metrik Toplayıcı

    Simülasyon sırasında çeşitli metrikleri toplar.
    """

    def __init__(self):
        self.metrics = ExperimentMetrics()
        self._step_packets_sent: int = 0
        self._step_packets_delivered: int = 0

    def record_packet_sent(self):
        """Paket gönderildi"""
        self.metrics.total_packets_sent += 1
        self._step_packets_sent += 1

    def record_packet_delivered(self, packet: Packet):
        """Paket teslim edildi"""
        self.metrics.total_packets_delivered += 1
        self._step_packets_delivered += 1

        # Gecikme
        if packet.accumulated_latency > 0:
            self.metrics.latencies.append(packet.accumulated_latency)

        # Hop sayısı
        self.metrics.hop_counts.append(packet.hop_count)

    def record_packet_dropped(self, packet: Packet):
        """Paket düşürüldü"""
        self.metrics.total_packets_dropped += 1

    def record_packet_expired(self, packet: Packet):
        """Paket süresi doldu"""
        self.metrics.total_packets_expired += 1

    def record_result(self, result: PacketResult):
        """Paket sonucu kaydet"""
        if result.success:
            self.metrics.total_packets_delivered += 1
            if result.latency > 0:
                self.metrics.latencies.append(result.latency)
            self.metrics.hop_counts.append(result.hop_count)
        else:
            if result.status == PacketStatus.EXPIRED:
                self.metrics.total_packets_expired += 1
            else:
                self.metrics.total_packets_dropped += 1

    def record_failure(self, node_id: str, step: int):
        """Düğüm arızası kaydet"""
        event = FailureEvent(
            timestamp=step,
            node_id=node_id,
        )
        self.metrics.failure_events.append(event)

    def record_recovery(self, node_id: str, step: int):
        """Düğüm kurtarması kaydet"""
        # Son arızayı bul
        for event in reversed(self.metrics.failure_events):
            if event.node_id == node_id and event.recovery_time is None:
                event.recovery_time = step - event.timestamp
                self.metrics.recovery_times.append(event.recovery_time)
                break

    def record_step(self, active_nodes: int, active_links: int):
        """Adım sonunda kayıt"""
        # PDR hesapla
        if self._step_packets_sent > 0:
            step_pdr = self._step_packets_delivered / self._step_packets_sent
        else:
            step_pdr = 1.0 if self.metrics.total_packets_sent == 0 else self.metrics.packet_delivery_ratio

        self.metrics.pdr_over_time.append(step_pdr)

        # Latency
        if self.metrics.latencies:
            self.metrics.latency_over_time.append(self.metrics.latencies[-1])
        else:
            self.metrics.latency_over_time.append(0.0)

        # Topology
        self.metrics.active_nodes_over_time.append(active_nodes)
        self.metrics.active_links_over_time.append(active_links)

        # Sayaçları sıfırla
        self._step_packets_sent = 0
        self._step_packets_delivered = 0

    def finalize(self):
        """Deneyi sonlandır"""
        self.metrics.end_time = time.time()

    def get_metrics(self) -> ExperimentMetrics:
        """Metrikleri döndür"""
        return self.metrics

    def reset(self):
        """Sıfırla"""
        self.metrics = ExperimentMetrics()
        self._step_packets_sent = 0
        self._step_packets_delivered = 0
