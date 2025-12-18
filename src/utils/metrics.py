"""
Performance metrics collector for routing algorithms.

This module collects detailed performance metrics during actual packet
transmission in the network simulation, including delivery rates, latency,
packet loss, and network efficiency metrics.
"""

import time
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict
import statistics


@dataclass
class PacketMetrics:
    """Metrics for a single packet transmission."""
    packet_id: int
    source: int
    destination: int
    route: List[int]
    sent_time: float
    delivered_time: Optional[float] = None
    hops: int = 0
    was_delivered: bool = False
    failure_reason: Optional[str] = None
    routing_algorithm: str = "unknown"
    
    @property
    def latency(self) -> float:
        """Calculate packet latency (end-to-end delay)."""
        if self.delivered_time is not None and self.sent_time is not None:
            return self.delivered_time - self.sent_time
        return float('inf')
    
    @property
    def is_successful(self) -> bool:
        """Check if packet was successfully delivered."""
        return self.was_delivered and self.delivered_time is not None


class NetworkMetricsCollector:
    """
    Collects and analyzes network performance metrics during simulation.
    
    This class tracks packet-level metrics and provides aggregated statistics
    for analyzing routing algorithm performance in real network conditions.
    """
    
    def __init__(self, algorithm_name: str = "unknown"):
        """
        Initialize metrics collector.
        
        Args:
            algorithm_name: Name of the routing algorithm being tested
        """
        self.algorithm_name = algorithm_name
        self.packet_metrics: List[PacketMetrics] = []
        self.start_time = time.time()
        self.end_time: Optional[float] = None
        
        # Real-time counters
        self.total_packets_sent = 0
        self.total_packets_delivered = 0
        self.total_packets_lost = 0
        
        # Per-node statistics
        self.node_stats: Dict[int, Dict[str, int]] = defaultdict(
            lambda: {'packets_sent': 0, 'packets_received': 0, 'packets_forwarded': 0}
        )
        
        # Link statistics
        self.link_usage: Dict[Tuple[int, int], int] = defaultdict(int)
        
        # Failure reasons
        self.failure_reasons: Dict[str, int] = defaultdict(int)
    
    def record_packet_sent(self, packet_id: int, source: int, destination: int,
                          route: List[int], sent_time: float) -> PacketMetrics:
        """
        Record a packet being sent.
        
        Args:
            packet_id: Unique packet identifier
            source: Source node ID
            destination: Destination node ID
            route: Planned route for the packet
            sent_time: Timestamp when packet was sent
        
        Returns:
            PacketMetrics object for tracking this packet
        """
        metrics = PacketMetrics(
            packet_id=packet_id,
            source=source,
            destination=destination,
            route=route,
            sent_time=sent_time,
            hops=len(route) - 1 if route else 0,
            routing_algorithm=self.algorithm_name
        )
        
        self.packet_metrics.append(metrics)
        self.total_packets_sent += 1
        self.node_stats[source]['packets_sent'] += 1
        
        # Record link usage
        if route and len(route) > 1:
            for i in range(len(route) - 1):
                link = (route[i], route[i + 1])
                self.link_usage[link] += 1
        
        return metrics
    
    def record_packet_delivered(self, packet_id: int, delivered_time: float):
        """
        Record successful packet delivery.
        
        Args:
            packet_id: Packet identifier
            delivered_time: Timestamp when packet was delivered
        """
        # Find the packet metrics
        for metrics in self.packet_metrics:
            if metrics.packet_id == packet_id:
                metrics.was_delivered = True
                metrics.delivered_time = delivered_time
                self.total_packets_delivered += 1
                self.node_stats[metrics.destination]['packets_received'] += 1
                break
    
    def record_packet_lost(self, packet_id: int, reason: str = "unknown"):
        """
        Record packet loss.
        
        Args:
            packet_id: Packet identifier
            reason: Reason for packet loss (e.g., "node_failure", "no_route", "timeout")
        """
        for metrics in self.packet_metrics:
            if metrics.packet_id == packet_id:
                metrics.was_delivered = False
                metrics.failure_reason = reason
                self.total_packets_lost += 1
                self.failure_reasons[reason] += 1
                break
    
    def record_packet_forwarded(self, node_id: int):
        """
        Record a packet being forwarded by a node.
        
        Args:
            node_id: Node that forwarded the packet
        """
        self.node_stats[node_id]['packets_forwarded'] += 1
    
    def finalize(self):
        """Mark the end of data collection."""
        self.end_time = time.time()
    
    def get_summary_stats(self) -> Dict[str, Any]:
        """
        Get summary statistics for all collected metrics.
        
        Returns:
            Dictionary containing aggregated performance metrics
        """
        if not self.packet_metrics:
            return {
                'algorithm': self.algorithm_name,
                'no_data': True
            }
        
        # Calculate basic statistics
        delivered_packets = [m for m in self.packet_metrics if m.is_successful]
        lost_packets = [m for m in self.packet_metrics if not m.is_successful]
        
        latencies = [m.latency for m in delivered_packets if m.latency != float('inf')]
        hop_counts = [m.hops for m in delivered_packets]
        
        stats = {
            'algorithm': self.algorithm_name,
            'total_packets': len(self.packet_metrics),
            'packets_delivered': len(delivered_packets),
            'packets_lost': len(lost_packets),
            'delivery_rate': len(delivered_packets) / len(self.packet_metrics) if self.packet_metrics else 0,
            'loss_rate': len(lost_packets) / len(self.packet_metrics) if self.packet_metrics else 0,
        }
        
        # Latency statistics
        if latencies:
            stats['latency'] = {
                'mean': statistics.mean(latencies),
                'median': statistics.median(latencies),
                'min': min(latencies),
                'max': max(latencies),
                'stdev': statistics.stdev(latencies) if len(latencies) > 1 else 0
            }
        else:
            stats['latency'] = {
                'mean': 0, 'median': 0, 'min': 0, 'max': 0, 'stdev': 0
            }
        
        # Hop count statistics
        if hop_counts:
            stats['hops'] = {
                'mean': statistics.mean(hop_counts),
                'median': statistics.median(hop_counts),
                'min': min(hop_counts),
                'max': max(hop_counts)
            }
        else:
            stats['hops'] = {
                'mean': 0, 'median': 0, 'min': 0, 'max': 0
            }
        
        # Network efficiency
        if delivered_packets and hop_counts:
            # Efficiency: ratio of successful deliveries to total hops used
            total_hops = sum(hop_counts)
            stats['network_efficiency'] = len(delivered_packets) / total_hops if total_hops > 0 else 0
        else:
            stats['network_efficiency'] = 0
        
        # Throughput (packets per second)
        if self.end_time and self.start_time:
            duration = self.end_time - self.start_time
            stats['throughput'] = len(delivered_packets) / duration if duration > 0 else 0
            stats['total_duration'] = duration
        else:
            stats['throughput'] = 0
            stats['total_duration'] = 0
        
        # Failure analysis
        stats['failure_reasons'] = dict(self.failure_reasons)
        
        # Link utilization statistics
        if self.link_usage:
            usage_values = list(self.link_usage.values())
            stats['link_utilization'] = {
                'total_links_used': len(self.link_usage),
                'mean_usage': statistics.mean(usage_values),
                'max_usage': max(usage_values),
                'min_usage': min(usage_values)
            }
        else:
            stats['link_utilization'] = {
                'total_links_used': 0,
                'mean_usage': 0,
                'max_usage': 0,
                'min_usage': 0
            }
        
        return stats
    
    def get_per_node_stats(self) -> Dict[int, Dict[str, Any]]:
        """
        Get per-node statistics.
        
        Returns:
            Dictionary mapping node IDs to their statistics
        """
        return dict(self.node_stats)
    
    def get_link_usage_stats(self) -> Dict[Tuple[int, int], int]:
        """
        Get link usage statistics.
        
        Returns:
            Dictionary mapping links to usage counts
        """
        return dict(self.link_usage)
    
    def compare_with(self, other: 'NetworkMetricsCollector') -> Dict[str, Any]:
        """
        Compare this collector's metrics with another.
        
        Args:
            other: Another NetworkMetricsCollector to compare with
        
        Returns:
            Comparison results
        """
        self_stats = self.get_summary_stats()
        other_stats = other.get_summary_stats()
        
        comparison = {
            'algorithms': [self.algorithm_name, other.algorithm_name],
            'delivery_rate_diff': self_stats['delivery_rate'] - other_stats['delivery_rate'],
            'latency_diff': self_stats['latency']['mean'] - other_stats['latency']['mean'],
            'hops_diff': self_stats['hops']['mean'] - other_stats['hops']['mean'],
            'efficiency_diff': self_stats['network_efficiency'] - other_stats['network_efficiency'],
            'throughput_diff': self_stats['throughput'] - other_stats['throughput'],
            'winner': {}
        }
        
        # Determine winners for each metric (positive diff means self is better)
        comparison['winner']['delivery_rate'] = self.algorithm_name if comparison['delivery_rate_diff'] > 0 else other.algorithm_name
        comparison['winner']['latency'] = self.algorithm_name if comparison['latency_diff'] < 0 else other.algorithm_name  # Lower is better
        comparison['winner']['hops'] = self.algorithm_name if comparison['hops_diff'] < 0 else other.algorithm_name  # Lower is better
        comparison['winner']['efficiency'] = self.algorithm_name if comparison['efficiency_diff'] > 0 else other.algorithm_name
        comparison['winner']['throughput'] = self.algorithm_name if comparison['throughput_diff'] > 0 else other.algorithm_name
        
        return comparison
    
    def print_summary(self):
        """Print a human-readable summary of the metrics."""
        stats = self.get_summary_stats()
        
        print(f"\n{'='*60}")
        print(f"Performance Summary: {self.algorithm_name}")
        print(f"{'='*60}")
        
        if stats.get('no_data'):
            print("No data collected.")
            return
        
        print(f"Total Packets:      {stats['total_packets']}")
        print(f"Delivered:          {stats['packets_delivered']} ({stats['delivery_rate']*100:.2f}%)")
        print(f"Lost:               {stats['packets_lost']} ({stats['loss_rate']*100:.2f}%)")
        print(f"\nLatency:")
        print(f"  Mean:             {stats['latency']['mean']:.4f}s")
        print(f"  Median:           {stats['latency']['median']:.4f}s")
        print(f"  Min/Max:          {stats['latency']['min']:.4f}s / {stats['latency']['max']:.4f}s")
        print(f"\nHop Count:")
        print(f"  Mean:             {stats['hops']['mean']:.2f}")
        print(f"  Median:           {stats['hops']['median']:.0f}")
        print(f"  Min/Max:          {stats['hops']['min']} / {stats['hops']['max']}")
        print(f"\nNetwork Efficiency: {stats['network_efficiency']:.4f}")
        print(f"Throughput:         {stats['throughput']:.2f} packets/sec")
        
        if stats['failure_reasons']:
            print(f"\nFailure Reasons:")
            for reason, count in stats['failure_reasons'].items():
                print(f"  {reason}: {count}")
        
        print(f"{'='*60}\n")
    
    def reset(self):
        """Reset all collected metrics."""
        self.packet_metrics.clear()
        self.total_packets_sent = 0
        self.total_packets_delivered = 0
        self.total_packets_lost = 0
        self.node_stats.clear()
        self.link_usage.clear()
        self.failure_reasons.clear()
        self.start_time = time.time()
        self.end_time = None
