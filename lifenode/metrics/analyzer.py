"""
Metric Analyzer (Metrik Analizcisi)

Toplanan metrikleri analiz eder ve karşılaştırma raporları oluşturur.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
import statistics

from .collector import ExperimentMetrics


@dataclass
class ComparisonResult:
    """Karşılaştırma sonucu"""
    metric_name: str
    values: Dict[str, float]       # router_name -> value
    best_router: str
    worst_router: str
    improvement_percent: float     # best vs worst


class MetricAnalyzer:
    """
    Metrik Analizcisi

    Farklı routing protokollerinin sonuçlarını karşılaştırır.
    """

    def __init__(self):
        self.experiments: Dict[str, ExperimentMetrics] = {}

    def add_experiment(self, name: str, metrics: ExperimentMetrics):
        """
        Deney sonuçları ekle

        Args:
            name: Deney/router adı
            metrics: Deney metrikleri
        """
        self.experiments[name] = metrics

    def compare_pdr(self) -> ComparisonResult:
        """Packet Delivery Ratio karşılaştırması"""
        values = {name: m.packet_delivery_ratio for name, m in self.experiments.items()}
        return self._create_comparison("PDR", values, higher_is_better=True)

    def compare_latency(self) -> ComparisonResult:
        """Ortalama gecikme karşılaştırması"""
        values = {name: m.average_latency for name, m in self.experiments.items()}
        return self._create_comparison("Average Latency", values, higher_is_better=False)

    def compare_hops(self) -> ComparisonResult:
        """Ortalama hop sayısı karşılaştırması"""
        values = {name: m.average_hops for name, m in self.experiments.items()}
        return self._create_comparison("Average Hops", values, higher_is_better=False)

    def compare_recovery_time(self) -> ComparisonResult:
        """Kurtarma süresi karşılaştırması"""
        values = {name: m.average_recovery_time for name, m in self.experiments.items()}
        return self._create_comparison("Recovery Time", values, higher_is_better=False)

    def _create_comparison(
        self,
        metric_name: str,
        values: Dict[str, float],
        higher_is_better: bool
    ) -> ComparisonResult:
        """Karşılaştırma sonucu oluştur"""
        if not values:
            return ComparisonResult(
                metric_name=metric_name,
                values={},
                best_router="N/A",
                worst_router="N/A",
                improvement_percent=0.0,
            )

        if higher_is_better:
            best_router = max(values, key=values.get)
            worst_router = min(values, key=values.get)
        else:
            best_router = min(values, key=values.get)
            worst_router = max(values, key=values.get)

        # İyileşme yüzdesi
        best_val = values[best_router]
        worst_val = values[worst_router]

        if worst_val != 0:
            if higher_is_better:
                improvement = ((best_val - worst_val) / worst_val) * 100
            else:
                improvement = ((worst_val - best_val) / worst_val) * 100
        else:
            improvement = 0.0

        return ComparisonResult(
            metric_name=metric_name,
            values=values,
            best_router=best_router,
            worst_router=worst_router,
            improvement_percent=improvement,
        )

    def full_comparison(self) -> Dict[str, ComparisonResult]:
        """Tüm metrikler için karşılaştırma"""
        return {
            'pdr': self.compare_pdr(),
            'latency': self.compare_latency(),
            'hops': self.compare_hops(),
            'recovery_time': self.compare_recovery_time(),
        }

    def generate_report(self) -> str:
        """
        Markdown formatında karşılaştırma raporu oluştur

        Returns:
            Markdown string
        """
        lines = ["# Deney Karşılaştırma Raporu\n"]

        # Özet tablo
        lines.append("## Özet Tablo\n")
        lines.append("| Router | PDR | Latency (ms) | Hops | Dropped |")
        lines.append("|--------|-----|--------------|------|---------|")

        for name, metrics in self.experiments.items():
            lines.append(
                f"| {name} | {metrics.packet_delivery_ratio:.2%} | "
                f"{metrics.average_latency:.2f} | {metrics.average_hops:.2f} | "
                f"{metrics.total_packets_dropped} |"
            )

        lines.append("\n## Detaylı Karşılaştırma\n")

        # Her metrik için karşılaştırma
        comparisons = self.full_comparison()

        for metric_name, result in comparisons.items():
            lines.append(f"### {result.metric_name}\n")

            for router, value in result.values.items():
                if metric_name == 'pdr':
                    lines.append(f"- **{router}**: {value:.2%}")
                else:
                    lines.append(f"- **{router}**: {value:.2f}")

            lines.append(f"\n🏆 En İyi: **{result.best_router}**")
            lines.append(f"📉 En Kötü: {result.worst_router}")
            lines.append(f"📊 İyileşme: {result.improvement_percent:.1f}%\n")

        return "\n".join(lines)

    def statistical_summary(self, experiment_name: str) -> Dict[str, float]:
        """
        Bir deney için istatistiksel özet

        Args:
            experiment_name: Deney adı

        Returns:
            İstatistik sözlüğü
        """
        metrics = self.experiments.get(experiment_name)
        if not metrics:
            return {}

        summary = {
            'pdr': metrics.packet_delivery_ratio,
            'pdr_percent': metrics.packet_delivery_ratio * 100,
            'latency_mean': metrics.average_latency,
            'latency_std': metrics.latency_std,
            'latency_min': metrics.min_latency,
            'latency_max': metrics.max_latency,
            'hops_mean': metrics.average_hops,
            'failures': metrics.total_failures,
            'recovery_mean': metrics.average_recovery_time,
            'duration_s': metrics.experiment_duration,
        }

        # Percentile hesapla (yeterli veri varsa)
        if len(metrics.latencies) >= 10:
            sorted_latencies = sorted(metrics.latencies)
            n = len(sorted_latencies)
            summary['latency_p50'] = sorted_latencies[int(n * 0.50)]
            summary['latency_p90'] = sorted_latencies[int(n * 0.90)]
            summary['latency_p99'] = sorted_latencies[int(n * 0.99)]

        return summary

    def reset(self):
        """Tüm deneyleri temizle"""
        self.experiments.clear()
