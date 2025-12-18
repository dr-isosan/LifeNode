"""
Example script to test performance metrics collection.

This script demonstrates how to use NetworkMetricsCollector to track
detailed performance metrics during packet transmission simulation.
"""

import sys
from pathlib import Path
import time
import random

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import networkx as nx
from src.utils import NetworkMetricsCollector
from src.routing import DijkstraRouting, AODVRouting


def simulate_packet_transmission(graph: nx.Graph, route: list, 
                                 failure_probability: float = 0.1) -> tuple:
    """
    Simulate packet transmission through a route.
    
    Args:
        graph: Network graph
        route: Route to follow
        failure_probability: Probability of node failure
    
    Returns:
        Tuple of (success, actual_time, failure_reason)
    """
    if not route or len(route) < 2:
        return False, 0, "invalid_route"
    
    # Simulate transmission time (latency per hop)
    base_latency = 0.01  # 10ms base latency per hop
    actual_time = 0
    
    for i in range(len(route) - 1):
        current_node = route[i]
        next_node = route[i + 1]
        
        # Check if link exists
        if not graph.has_edge(current_node, next_node):
            return False, actual_time, "link_failure"
        
        # Simulate node failure
        if random.random() < failure_probability:
            return False, actual_time, "node_failure"
        
        # Add transmission latency
        hop_latency = base_latency + random.uniform(0, 0.005)
        actual_time += hop_latency
        time.sleep(0.001)  # Simulate processing time
    
    return True, actual_time, None


def run_performance_test(algorithm_name: str, routing_algo, 
                        graph: nx.Graph, test_routes: list,
                        failure_prob: float = 0.05) -> NetworkMetricsCollector:
    """
    Run performance test for a routing algorithm.
    
    Args:
        algorithm_name: Name of the algorithm
        routing_algo: Routing algorithm instance
        graph: Network graph
        test_routes: List of (source, destination) pairs
        failure_prob: Node failure probability
    
    Returns:
        NetworkMetricsCollector with results
    """
    collector = NetworkMetricsCollector(algorithm_name)
    
    print(f"\nTesting {algorithm_name}...")
    print(f"  Test routes: {len(test_routes)}")
    print(f"  Failure probability: {failure_prob*100:.1f}%")
    
    packet_id = 0
    
    for source, destination in test_routes:
        # Find route using the algorithm
        route = routing_algo.find_route(graph, source, destination)
        
        if route is None:
            # No route found
            sent_time = time.time()
            collector.record_packet_sent(packet_id, source, destination, [], sent_time)
            collector.record_packet_lost(packet_id, "no_route")
            packet_id += 1
            continue
        
        # Record packet being sent
        sent_time = time.time()
        collector.record_packet_sent(packet_id, source, destination, route, sent_time)
        
        # Simulate actual packet transmission
        success, transmission_time, failure_reason = simulate_packet_transmission(
            graph, route, failure_prob
        )
        
        delivered_time = sent_time + transmission_time
        
        if success:
            collector.record_packet_delivered(packet_id, delivered_time)
        else:
            collector.record_packet_lost(packet_id, failure_reason)
        
        packet_id += 1
    
    collector.finalize()
    return collector


def main():
    """Main function to test performance metrics."""
    
    print("\n" + "="*70)
    print("PERFORMANCE METRICS COLLECTION TEST")
    print("="*70)
    
    # Set random seed for reproducibility
    random.seed(42)
    
    # Create test network
    print("\nCreating test network...")
    graph = nx.random_geometric_graph(30, 0.25, seed=42)
    print(f"  Nodes: {graph.number_of_nodes()}")
    print(f"  Edges: {graph.number_of_edges()}")
    
    # Generate test routes
    print("\nGenerating test routes...")
    nodes = list(graph.nodes())
    test_routes = []
    for _ in range(50):
        source = random.choice(nodes)
        destination = random.choice(nodes)
        if source != destination:
            test_routes.append((source, destination))
    print(f"  Generated {len(test_routes)} routes")
    
    # Test Dijkstra
    dijkstra = DijkstraRouting()
    dijkstra_collector = run_performance_test(
        "Dijkstra", dijkstra, graph, test_routes, failure_prob=0.05
    )
    dijkstra_collector.print_summary()
    
    # Test AODV
    aodv = AODVRouting()
    aodv_collector = run_performance_test(
        "AODV", aodv, graph, test_routes, failure_prob=0.05
    )
    aodv_collector.print_summary()
    
    # Compare algorithms
    print("\n" + "="*70)
    print("ALGORITHM COMPARISON")
    print("="*70)
    
    comparison = dijkstra_collector.compare_with(aodv_collector)
    
    print(f"\nComparing: {comparison['algorithms'][0]} vs {comparison['algorithms'][1]}")
    print(f"\nDelivery Rate:")
    print(f"  Difference: {comparison['delivery_rate_diff']*100:+.2f}%")
    print(f"  Winner: {comparison['winner']['delivery_rate']}")
    
    print(f"\nLatency:")
    print(f"  Difference: {comparison['latency_diff']*1000:+.2f}ms")
    print(f"  Winner: {comparison['winner']['latency']}")
    
    print(f"\nHop Count:")
    print(f"  Difference: {comparison['hops_diff']:+.2f}")
    print(f"  Winner: {comparison['winner']['hops']}")
    
    print(f"\nNetwork Efficiency:")
    print(f"  Difference: {comparison['efficiency_diff']:+.4f}")
    print(f"  Winner: {comparison['winner']['efficiency']}")
    
    print(f"\nThroughput:")
    print(f"  Difference: {comparison['throughput_diff']:+.2f} pkt/s")
    print(f"  Winner: {comparison['winner']['throughput']}")
    
    print("\n" + "="*70)
    print("Overall Winner by Metric:")
    print("="*70)
    
    winners_count = {}
    for metric, winner in comparison['winner'].items():
        winners_count[winner] = winners_count.get(winner, 0) + 1
        print(f"  {metric:<20}: {winner}")
    
    print("\n" + "="*70)
    overall_winner = max(winners_count.items(), key=lambda x: x[1])
    print(f"Overall Best Algorithm: {overall_winner[0]} ({overall_winner[1]}/5 metrics)")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
