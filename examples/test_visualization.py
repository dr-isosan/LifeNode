"""
Test script for advanced routing comparison visualizations.

This script demonstrates all the visualization capabilities for
comparing routing algorithm performance.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import networkx as nx
import random
from src.routing import DijkstraRouting, AODVRouting
from src.utils import NetworkMetricsCollector
from visualization.plot_utils import RoutingComparisonVisualizer


def simulate_packet_transmission(graph: nx.Graph, route: list, 
                                 failure_probability: float = 0.1):
    """Simulate packet transmission through a route."""
    import time
    
    if not route or len(route) < 2:
        return False, 0, "invalid_route"
    
    base_latency = 0.01
    actual_time = 0
    
    for i in range(len(route) - 1):
        current_node = route[i]
        next_node = route[i + 1]
        
        if not graph.has_edge(current_node, next_node):
            return False, actual_time, "link_failure"
        
        if random.random() < failure_probability:
            return False, actual_time, "node_failure"
        
        hop_latency = base_latency + random.uniform(0, 0.005)
        actual_time += hop_latency
        time.sleep(0.0005)
    
    return True, actual_time, None


def run_performance_test(algorithm_name: str, routing_algo, 
                        graph: nx.Graph, test_routes: list,
                        failure_prob: float = 0.05):
    """Run performance test for a routing algorithm."""
    import time
    
    collector = NetworkMetricsCollector(algorithm_name)
    
    print(f"\nTesting {algorithm_name}...")
    
    packet_id = 0
    
    for source, destination in test_routes:
        route = routing_algo.find_route(graph, source, destination)
        
        if route is None:
            sent_time = time.time()
            collector.record_packet_sent(packet_id, source, destination, [], sent_time)
            collector.record_packet_lost(packet_id, "no_route")
            packet_id += 1
            continue
        
        sent_time = time.time()
        collector.record_packet_sent(packet_id, source, destination, route, sent_time)
        
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
    """Main visualization test."""
    import time
    
    print("\n" + "="*70)
    print("ADVANCED ROUTING VISUALIZATION TEST")
    print("="*70 + "\n")
    
    random.seed(42)
    
    # Create test network
    print("Creating test network...")
    graph = nx.random_geometric_graph(40, 0.23, seed=42)
    print(f"  Nodes: {graph.number_of_nodes()}")
    print(f"  Edges: {graph.number_of_edges()}")
    
    # Generate test routes
    print("\nGenerating test routes...")
    nodes = list(graph.nodes())
    test_routes = []
    for _ in range(80):
        source = random.choice(nodes)
        destination = random.choice(nodes)
        if source != destination:
            test_routes.append((source, destination))
    print(f"  Generated {len(test_routes)} routes")
    
    # Test algorithms
    dijkstra = DijkstraRouting()
    aodv = AODVRouting()
    
    dijkstra_collector = run_performance_test(
        "Dijkstra", dijkstra, graph, test_routes, failure_prob=0.08
    )
    dijkstra_collector.print_summary()
    
    aodv_collector = run_performance_test(
        "AODV", aodv, graph, test_routes, failure_prob=0.08
    )
    aodv_collector.print_summary()
    
    # Prepare collectors dictionary
    collectors_dict = {
        'Dijkstra': dijkstra_collector,
        'AODV': aodv_collector
    }
    
    # Create visualizer
    visualizer = RoutingComparisonVisualizer(output_dir="results/routing_comparison")
    
    print("\n" + "="*70)
    print("GENERATING VISUALIZATIONS")
    print("="*70)
    
    # 1. Metrics Comparison Bar Charts
    print("\n1. Creating metrics comparison chart...")
    visualizer.plot_metrics_comparison(collectors_dict)
    
    # 2. Latency Distribution
    print("2. Creating latency distribution histogram...")
    visualizer.plot_latency_distribution(collectors_dict)
    
    # 3. Link Utilization Heatmaps
    print("3. Creating link utilization heatmaps...")
    visualizer.plot_link_utilization_heatmap(collectors_dict, graph)
    
    # 4. Performance Radar Chart
    print("4. Creating performance radar chart...")
    visualizer.plot_performance_radar(collectors_dict)
    
    # 5. Comprehensive Dashboard
    print("5. Creating comprehensive dashboard...")
    visualizer.create_comparison_dashboard(collectors_dict, graph)
    
    print("\n" + "="*70)
    print("VISUALIZATION SUMMARY")
    print("="*70)
    
    print("\nGenerated visualizations:")
    print("  ✓ Metrics comparison bar charts (6 metrics)")
    print("  ✓ Latency distribution histograms")
    print("  ✓ Link utilization heatmap")
    print("  ✓ Performance radar chart (5D)")
    print("  ✓ Comprehensive dashboard (5 panels)")
    
    print("\nAll visualizations saved to: results/routing_comparison/")
    
    print("\n" + "="*70)
    print("Test completed successfully!")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
