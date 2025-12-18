"""
Comprehensive benchmark suite for routing algorithms.

This script runs all test scenarios and generates detailed
comparison reports and visualizations.
"""

import sys
from pathlib import Path
import time
import random
import json
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.routing import DijkstraRouting, AODVRouting
from src.utils import (NetworkMetricsCollector, TestScenarioGenerator, 
                       TopologyType, FailureLevel, create_quick_test_suite)
from visualization.plot_utils import RoutingComparisonVisualizer


def simulate_packet_transmission(graph, route, failure_probability=0.05):
    """Simulate packet transmission through a route."""
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
        time.sleep(0.0001)  # Minimal delay
    
    return True, actual_time, None


def run_scenario_test(scenario, algorithms_dict, verbose=True):
    """
    Run a single test scenario for all algorithms.
    
    Args:
        scenario: Test scenario dictionary
        algorithms_dict: {name: routing_algorithm}
        verbose: Print progress
    
    Returns:
        Dictionary of collectors for each algorithm
    """
    if verbose:
        print(f"\n{'='*70}")
        print(f"Running: {scenario['name']}")
        print(f"{'='*70}")
        print(f"Network: {scenario['num_nodes']} nodes, {scenario['num_edges']} edges")
        print(f"Routes: {scenario['num_routes']}, Pattern: {scenario['route_pattern']}")
        print(f"Failure Rate: {scenario['failure_probability']*100:.1f}%")
    
    collectors = {}
    
    for algo_name, algo in algorithms_dict.items():
        if verbose:
            print(f"\n  Testing {algo_name}...", end=" ", flush=True)
        
        collector = NetworkMetricsCollector(algo_name)
        packet_id = 0
        
        for source, destination in scenario['routes']:
            route = algo.find_route(scenario['graph'], source, destination)
            
            sent_time = time.time()
            
            if route is None:
                collector.record_packet_sent(packet_id, source, destination, [], sent_time)
                collector.record_packet_lost(packet_id, "no_route")
                packet_id += 1
                continue
            
            collector.record_packet_sent(packet_id, source, destination, route, sent_time)
            
            success, transmission_time, failure_reason = simulate_packet_transmission(
                scenario['graph'], route, scenario['failure_probability']
            )
            
            delivered_time = sent_time + transmission_time
            
            if success:
                collector.record_packet_delivered(packet_id, delivered_time)
            else:
                collector.record_packet_lost(packet_id, failure_reason)
            
            packet_id += 1
        
        collector.finalize()
        collectors[algo_name] = collector
        
        stats = collector.get_summary_stats()
        if verbose:
            print(f"✓ (Delivery: {stats['delivery_rate']*100:.1f}%, "
                  f"Latency: {stats['latency']['mean']*1000:.2f}ms)")
    
    return collectors


def run_full_benchmark(mode="quick"):
    """
    Run full benchmark suite.
    
    Args:
        mode: "quick" for quick test suite, "full" for comprehensive suite
    """
    print("\n" + "="*70)
    print("ROUTING ALGORITHM BENCHMARK SUITE")
    print("="*70)
    print(f"Mode: {mode.upper()}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    # Create algorithms
    algorithms = {
        'Dijkstra': DijkstraRouting(),
        'AODV': AODVRouting()
    }
    
    print(f"\nAlgorithms to test: {list(algorithms.keys())}")
    
    # Generate scenarios
    generator = TestScenarioGenerator(seed=42)
    
    if mode == "quick":
        scenarios = create_quick_test_suite()
        print(f"\nRunning {len(scenarios)} quick test scenarios...")
    else:
        scenarios = generator.create_benchmark_suite()
        print(f"\nRunning {len(scenarios)} comprehensive test scenarios...")
    
    # Run all scenarios
    all_results = {}
    start_time = time.time()
    
    for idx, scenario in enumerate(scenarios, 1):
        print(f"\n[{idx}/{len(scenarios)}] ", end="")
        collectors = run_scenario_test(scenario, algorithms, verbose=True)
        all_results[scenario['name']] = {
            'scenario': scenario,
            'collectors': collectors
        }
    
    total_time = time.time() - start_time
    
    # Generate summary report
    print("\n" + "="*70)
    print("BENCHMARK SUMMARY")
    print("="*70)
    
    # Aggregate results
    aggregate_stats = {algo_name: {
        'total_packets': 0,
        'total_delivered': 0,
        'total_latency': 0,
        'total_hops': 0,
        'scenarios_won': 0
    } for algo_name in algorithms.keys()}
    
    for scenario_name, result in all_results.items():
        print(f"\n{scenario_name}:")
        
        best_delivery = None
        best_algo = None
        
        for algo_name, collector in result['collectors'].items():
            stats = collector.get_summary_stats()
            
            # Aggregate
            aggregate_stats[algo_name]['total_packets'] += stats['total_packets']
            aggregate_stats[algo_name]['total_delivered'] += stats['packets_delivered']
            aggregate_stats[algo_name]['total_latency'] += stats['latency']['mean'] * stats['packets_delivered']
            aggregate_stats[algo_name]['total_hops'] += stats['hops']['mean'] * stats['packets_delivered']
            
            print(f"  {algo_name:<15}: Delivery={stats['delivery_rate']*100:>5.1f}%, "
                  f"Latency={stats['latency']['mean']*1000:>6.2f}ms, "
                  f"Hops={stats['hops']['mean']:>4.2f}")
            
            if best_delivery is None or stats['delivery_rate'] > best_delivery:
                best_delivery = stats['delivery_rate']
                best_algo = algo_name
        
        if best_algo:
            aggregate_stats[best_algo]['scenarios_won'] += 1
            print(f"  Winner: {best_algo}")
    
    # Overall statistics
    print("\n" + "="*70)
    print("OVERALL STATISTICS")
    print("="*70)
    
    for algo_name, stats in aggregate_stats.items():
        if stats['total_delivered'] > 0:
            overall_delivery = stats['total_delivered'] / stats['total_packets'] if stats['total_packets'] > 0 else 0
            avg_latency = stats['total_latency'] / stats['total_delivered']
            avg_hops = stats['total_hops'] / stats['total_delivered']
        else:
            overall_delivery = 0
            avg_latency = 0
            avg_hops = 0
        
        print(f"\n{algo_name}:")
        print(f"  Overall Delivery Rate: {overall_delivery*100:.2f}%")
        print(f"  Average Latency: {avg_latency*1000:.2f}ms")
        print(f"  Average Hops: {avg_hops:.2f}")
        print(f"  Scenarios Won: {stats['scenarios_won']}/{len(scenarios)}")
    
    print(f"\nTotal Benchmark Time: {total_time:.2f}s")
    
    # Save results to JSON
    results_dir = Path("results/benchmarks")
    results_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = results_dir / f"benchmark_{mode}_{timestamp}.json"
    
    # Prepare JSON-serializable results
    json_results = {
        'timestamp': datetime.now().isoformat(),
        'mode': mode,
        'total_time': total_time,
        'algorithms': list(algorithms.keys()),
        'scenarios': []
    }
    
    for scenario_name, result in all_results.items():
        scenario_data = {
            'name': scenario_name,
            'description': result['scenario']['description'],
            'num_nodes': result['scenario']['num_nodes'],
            'num_edges': result['scenario']['num_edges'],
            'num_routes': result['scenario']['num_routes'],
            'algorithms': {}
        }
        
        for algo_name, collector in result['collectors'].items():
            stats = collector.get_summary_stats()
            scenario_data['algorithms'][algo_name] = {
                'delivery_rate': stats['delivery_rate'],
                'packets_delivered': stats['packets_delivered'],
                'packets_lost': stats['packets_lost'],
                'avg_latency': stats['latency']['mean'],
                'avg_hops': stats['hops']['mean'],
                'network_efficiency': stats['network_efficiency'],
                'throughput': stats['throughput']
            }
        
        json_results['scenarios'].append(scenario_data)
    
    json_results['aggregate'] = aggregate_stats
    
    with open(results_file, 'w') as f:
        json.dump(json_results, f, indent=2)
    
    print(f"\nResults saved to: {results_file}")
    
    # Generate visualizations for last scenario
    if all_results:
        last_scenario_name = list(all_results.keys())[-1]
        last_collectors = all_results[last_scenario_name]['collectors']
        
        print("\nGenerating visualizations for last scenario...")
        visualizer = RoutingComparisonVisualizer()
        visualizer.plot_metrics_comparison(last_collectors)
        visualizer.create_comparison_dashboard(last_collectors)
    
    print("\n" + "="*70)
    print("BENCHMARK COMPLETED!")
    print("="*70 + "\n")


def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run routing algorithm benchmarks")
    parser.add_argument('--mode', choices=['quick', 'full'], default='quick',
                       help='Benchmark mode: quick or full')
    
    args = parser.parse_args()
    
    run_full_benchmark(mode=args.mode)


if __name__ == "__main__":
    main()
