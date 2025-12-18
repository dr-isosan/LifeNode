"""
Generate comprehensive final report for Week 3 routing algorithms.

This script runs full benchmark tests and generates detailed
markdown reports with analysis and visualizations.
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
                       TopologyType, FailureLevel)
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
        time.sleep(0.0001)
    
    return True, actual_time, None


def run_scenario_test(scenario, algorithms_dict):
    """Run a single test scenario for all algorithms."""
    collectors = {}
    
    for algo_name, algo in algorithms_dict.items():
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
    
    return collectors


def generate_markdown_report(all_results, algorithms, total_time, output_file):
    """Generate comprehensive markdown report."""
    
    with open(output_file, 'w', encoding='utf-8') as f:
        # Header
        f.write("# LifeNode Week 3 - Routing Algorithms Performance Report\n\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"**Total Test Duration:** {total_time:.2f}s\n\n")
        f.write("---\n\n")
        
        # Executive Summary
        f.write("## 📊 Executive Summary\n\n")
        f.write("This report presents the performance analysis of classical routing algorithms ")
        f.write("(Dijkstra and AODV) tested on LifeNode mesh network simulator. ")
        f.write("These results will serve as baseline for comparison with AI-based routing algorithms in Week 4.\n\n")
        
        # Algorithms Tested
        f.write("### Algorithms Tested\n\n")
        for algo_name in algorithms.keys():
            f.write(f"- **{algo_name}**: {get_algorithm_description(algo_name)}\n")
        f.write("\n")
        
        # Test Scenarios Overview
        f.write("### Test Scenarios Overview\n\n")
        f.write(f"Total scenarios tested: **{len(all_results)}**\n\n")
        f.write("| Scenario | Nodes | Edges | Routes | Pattern | Failure Rate |\n")
        f.write("|----------|-------|-------|--------|---------|-------------|\n")
        
        for scenario_name, result in all_results.items():
            s = result['scenario']
            f.write(f"| {s['name']} | {s['num_nodes']} | {s['num_edges']} | ")
            f.write(f"{s['num_routes']} | {s['route_pattern']} | {s['failure_probability']*100:.1f}% |\n")
        
        f.write("\n---\n\n")
        
        # Detailed Results Per Scenario
        f.write("## 📈 Detailed Results by Scenario\n\n")
        
        for scenario_name, result in all_results.items():
            f.write(f"### {scenario_name}\n\n")
            f.write(f"**Description:** {result['scenario']['description']}\n\n")
            
            f.write("| Algorithm | Delivery Rate | Avg Latency | Avg Hops | Efficiency | Throughput |\n")
            f.write("|-----------|---------------|-------------|----------|------------|------------|\n")
            
            for algo_name, collector in result['collectors'].items():
                stats = collector.get_summary_stats()
                f.write(f"| {algo_name} | {stats['delivery_rate']*100:.2f}% | ")
                f.write(f"{stats['latency']['mean']*1000:.2f}ms | ")
                f.write(f"{stats['hops']['mean']:.2f} | ")
                f.write(f"{stats['network_efficiency']:.4f} | ")
                f.write(f"{stats['throughput']:.2f} pkt/s |\n")
            
            f.write("\n")
        
        f.write("---\n\n")
        
        # Overall Statistics
        f.write("## 🎯 Overall Performance Statistics\n\n")
        
        aggregate_stats = calculate_aggregate_stats(all_results, algorithms)
        
        f.write("### Aggregated Metrics Across All Scenarios\n\n")
        f.write("| Algorithm | Overall Delivery | Avg Latency | Avg Hops | Scenarios Won |\n")
        f.write("|-----------|------------------|-------------|----------|---------------|\n")
        
        for algo_name, stats in aggregate_stats.items():
            f.write(f"| {algo_name} | {stats['overall_delivery']*100:.2f}% | ")
            f.write(f"{stats['avg_latency']*1000:.2f}ms | ")
            f.write(f"{stats['avg_hops']:.2f} | ")
            f.write(f"{stats['scenarios_won']}/{len(all_results)} |\n")
        
        f.write("\n")
        
        # Winner Analysis
        f.write("### Winner by Metric\n\n")
        winners = determine_winners(aggregate_stats)
        
        for metric, winner in winners.items():
            f.write(f"- **{metric}**: {winner}\n")
        
        f.write("\n---\n\n")
        
        # Performance Analysis
        f.write("## 🔍 Performance Analysis\n\n")
        f.write("### Key Findings\n\n")
        f.write(generate_key_findings(aggregate_stats, all_results))
        
        f.write("\n### Algorithm Comparison\n\n")
        f.write(generate_algorithm_comparison(aggregate_stats))
        
        f.write("\n---\n\n")
        
        # Conclusions
        f.write("## 💡 Conclusions and Recommendations\n\n")
        f.write(generate_conclusions(aggregate_stats, winners))
        
        f.write("\n---\n\n")
        
        # Next Steps
        f.write("## 🚀 Next Steps (Week 4)\n\n")
        f.write("1. **AI-based Routing Implementation**\n")
        f.write("   - Train DQN agent on similar network topologies\n")
        f.write("   - Optimize reward function based on these baseline metrics\n\n")
        f.write("2. **Comparative Analysis**\n")
        f.write("   - Test AI routing on identical scenarios\n")
        f.write("   - Compare against Dijkstra and AODV baselines\n")
        f.write("   - Identify scenarios where AI excels or underperforms\n\n")
        f.write("3. **Performance Optimization**\n")
        f.write("   - Fine-tune AI model hyperparameters\n")
        f.write("   - Implement hybrid approaches if beneficial\n\n")
        
        f.write("---\n\n")
        f.write(f"*Report generated by LifeNode Routing Benchmark Suite - {datetime.now().year}*\n")


def get_algorithm_description(algo_name):
    """Get description for algorithm."""
    descriptions = {
        'Dijkstra': 'Shortest path algorithm based on hop count',
        'AODV': 'On-demand distance vector routing with route caching'
    }
    return descriptions.get(algo_name, 'Classical routing algorithm')


def calculate_aggregate_stats(all_results, algorithms):
    """Calculate aggregate statistics across all scenarios."""
    aggregate = {algo_name: {
        'total_packets': 0,
        'total_delivered': 0,
        'total_latency': 0,
        'total_hops': 0,
        'scenarios_won': 0
    } for algo_name in algorithms.keys()}
    
    for scenario_name, result in all_results.items():
        best_delivery = -1
        best_algo = None
        
        for algo_name, collector in result['collectors'].items():
            stats = collector.get_summary_stats()
            
            aggregate[algo_name]['total_packets'] += stats['total_packets']
            aggregate[algo_name]['total_delivered'] += stats['packets_delivered']
            aggregate[algo_name]['total_latency'] += stats['latency']['mean'] * stats['packets_delivered']
            aggregate[algo_name]['total_hops'] += stats['hops']['mean'] * stats['packets_delivered']
            
            if stats['delivery_rate'] > best_delivery:
                best_delivery = stats['delivery_rate']
                best_algo = algo_name
        
        if best_algo:
            aggregate[best_algo]['scenarios_won'] += 1
    
    # Calculate averages
    for algo_name, stats in aggregate.items():
        if stats['total_delivered'] > 0:
            stats['overall_delivery'] = stats['total_delivered'] / stats['total_packets']
            stats['avg_latency'] = stats['total_latency'] / stats['total_delivered']
            stats['avg_hops'] = stats['total_hops'] / stats['total_delivered']
        else:
            stats['overall_delivery'] = 0
            stats['avg_latency'] = 0
            stats['avg_hops'] = 0
    
    return aggregate


def determine_winners(aggregate_stats):
    """Determine winner for each metric."""
    winners = {}
    
    # Delivery rate (higher is better)
    best = max(aggregate_stats.items(), key=lambda x: x[1]['overall_delivery'])
    winners['Overall Delivery Rate'] = best[0]
    
    # Latency (lower is better)
    valid = {k: v for k, v in aggregate_stats.items() if v['avg_latency'] > 0}
    if valid:
        best = min(valid.items(), key=lambda x: x[1]['avg_latency'])
        winners['Average Latency'] = best[0]
    
    # Hops (lower is better)
    valid = {k: v for k, v in aggregate_stats.items() if v['avg_hops'] > 0}
    if valid:
        best = min(valid.items(), key=lambda x: x[1]['avg_hops'])
        winners['Average Hops'] = best[0]
    
    # Scenarios won
    best = max(aggregate_stats.items(), key=lambda x: x[1]['scenarios_won'])
    winners['Scenarios Won'] = best[0]
    
    return winners


def generate_key_findings(aggregate_stats, all_results):
    """Generate key findings text."""
    findings = []
    
    # Best overall performer
    best = max(aggregate_stats.items(), key=lambda x: x[1]['overall_delivery'])
    findings.append(f"1. **Best Overall Performer**: {best[0]} achieved the highest overall delivery rate at {best[1]['overall_delivery']*100:.2f}%\n")
    
    # Latency analysis
    valid = {k: v for k, v in aggregate_stats.items() if v['avg_latency'] > 0}
    if valid:
        best_latency = min(valid.items(), key=lambda x: x[1]['avg_latency'])
        findings.append(f"2. **Lowest Latency**: {best_latency[0]} with average {best_latency[1]['avg_latency']*1000:.2f}ms\n")
    
    # Efficiency
    findings.append(f"3. **Network Efficiency**: Algorithms show varying efficiency based on network density and failure rates\n")
    
    # Scalability
    findings.append(f"4. **Scalability**: Performance tested across {len(all_results)} different network sizes and conditions\n")
    
    return "\n".join(findings)


def generate_algorithm_comparison(aggregate_stats):
    """Generate algorithm comparison text."""
    comparison = []
    
    algo_names = list(aggregate_stats.keys())
    
    if len(algo_names) >= 2:
        algo1, algo2 = algo_names[0], algo_names[1]
        stats1, stats2 = aggregate_stats[algo1], aggregate_stats[algo2]
        
        comparison.append(f"**{algo1} vs {algo2}**\n\n")
        
        # Delivery rate
        if stats1['overall_delivery'] > stats2['overall_delivery']:
            diff = (stats1['overall_delivery'] - stats2['overall_delivery']) * 100
            comparison.append(f"- {algo1} delivers {diff:.2f}% more packets successfully\n")
        else:
            diff = (stats2['overall_delivery'] - stats1['overall_delivery']) * 100
            comparison.append(f"- {algo2} delivers {diff:.2f}% more packets successfully\n")
        
        # Latency
        if stats1['avg_latency'] > 0 and stats2['avg_latency'] > 0:
            if stats1['avg_latency'] < stats2['avg_latency']:
                diff = (stats2['avg_latency'] - stats1['avg_latency']) * 1000
                comparison.append(f"- {algo1} has {diff:.2f}ms lower average latency\n")
            else:
                diff = (stats1['avg_latency'] - stats2['avg_latency']) * 1000
                comparison.append(f"- {algo2} has {diff:.2f}ms lower average latency\n")
        
        # Scenarios won
        comparison.append(f"- {algo1} won {stats1['scenarios_won']} scenarios\n")
        comparison.append(f"- {algo2} won {stats2['scenarios_won']} scenarios\n")
    
    return "".join(comparison)


def generate_conclusions(aggregate_stats, winners):
    """Generate conclusions text."""
    conclusions = []
    
    overall_winner = winners.get('Overall Delivery Rate', 'Unknown')
    
    conclusions.append(f"### Summary\n\n")
    conclusions.append(f"Based on comprehensive testing across multiple scenarios, **{overall_winner}** ")
    conclusions.append(f"emerged as the strongest performer overall, demonstrating superior packet delivery rates ")
    conclusions.append(f"and consistent performance across varying network conditions.\n\n")
    
    conclusions.append(f"### Recommendations\n\n")
    conclusions.append(f"1. **Use {overall_winner} as primary baseline** for AI routing comparison\n")
    conclusions.append(f"2. **Focus AI training** on scenarios where classical algorithms struggle (high failure rates, sparse networks)\n")
    conclusions.append(f"3. **Consider hybrid approaches** that combine classical routing reliability with AI adaptability\n")
    conclusions.append(f"4. **Optimize for specific use cases** based on whether low latency or high delivery rate is priority\n\n")
    
    return "".join(conclusions)


def main():
    """Main function to run comprehensive tests and generate report."""
    
    print("\n" + "="*70)
    print("WEEK 3 FINAL REPORT GENERATION")
    print("="*70)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70 + "\n")
    
    # Create algorithms
    algorithms = {
        'Dijkstra': DijkstraRouting(),
        'AODV': AODVRouting()
    }
    
    print(f"Algorithms: {list(algorithms.keys())}")
    
    # Generate comprehensive test scenarios
    generator = TestScenarioGenerator(seed=42)
    scenarios = generator.create_benchmark_suite()
    
    print(f"Test scenarios: {len(scenarios)}\n")
    
    # Run all tests
    print("Running comprehensive tests...")
    print("This may take a few moments...\n")
    
    all_results = {}
    start_time = time.time()
    
    for idx, scenario in enumerate(scenarios, 1):
        print(f"[{idx}/{len(scenarios)}] Testing {scenario['name']}...", end=" ", flush=True)
        collectors = run_scenario_test(scenario, algorithms)
        all_results[scenario['name']] = {
            'scenario': scenario,
            'collectors': collectors
        }
        
        # Print quick stats
        for algo_name, collector in collectors.items():
            stats = collector.get_summary_stats()
            print(f"{algo_name}={stats['delivery_rate']*100:.1f}%", end=" ")
        print("✓")
    
    total_time = time.time() - start_time
    
    print(f"\nAll tests completed in {total_time:.2f}s")
    
    # Generate markdown report
    print("\nGenerating markdown report...")
    report_dir = Path("results/reports")
    report_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = report_dir / f"week3_final_report_{timestamp}.md"
    
    generate_markdown_report(all_results, algorithms, total_time, report_file)
    
    print(f"Report saved to: {report_file}")
    
    # Generate visualizations for selected scenarios
    print("\nGenerating visualizations...")
    visualizer = RoutingComparisonVisualizer()
    
    # Visualize last 2 scenarios
    vis_scenarios = list(all_results.items())[-2:]
    for scenario_name, result in vis_scenarios:
        print(f"  - {scenario_name}")
        collectors_dict = result['collectors']
        visualizer.plot_metrics_comparison(collectors_dict)
    
    # Create final dashboard
    final_collectors = list(all_results.values())[-1]['collectors']
    visualizer.create_comparison_dashboard(final_collectors)
    
    print("\n" + "="*70)
    print("FINAL REPORT GENERATION COMPLETED!")
    print("="*70)
    print(f"\n📄 Report: {report_file}")
    print(f"📊 Visualizations: results/routing_comparison/")
    print("\n" + "="*70 + "\n")


if __name__ == "__main__":
    main()
