"""
Routing Comparison Framework for LifeNode.

This module provides tools to compare different routing algorithms
(classical and AI-based) under the same conditions and scenarios.
"""

import time
import json
from typing import List, Dict, Any, Optional, Tuple
import networkx as nx
from pathlib import Path
from datetime import datetime

from ..routing.base import RoutingAlgorithm


class RoutingComparator:
    """
    Manager class for comparing different routing algorithms.
    
    This class orchestrates the testing of multiple routing algorithms
    under identical network conditions, collecting and comparing their
    performance metrics.
    """
    
    def __init__(self, algorithms: List[RoutingAlgorithm], output_dir: str = "results/routing_comparison"):
        """
        Initialize routing comparator.
        
        Args:
            algorithms: List of routing algorithms to compare
            output_dir: Directory to save comparison results
        """
        self.algorithms = algorithms
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.test_scenarios: List[Dict[str, Any]] = []
        self.results: Dict[str, Dict[str, Any]] = {algo.name: {} for algo in algorithms}
        
        # Global statistics
        self.global_stats = {
            'total_tests': 0,
            'total_routes_tested': 0,
            'start_time': None,
            'end_time': None
        }
    
    def add_test_scenario(self, name: str, graph: nx.Graph, 
                         routes: List[Tuple[int, int]], 
                         network_state: Optional[Dict[str, Any]] = None):
        """
        Add a test scenario for routing comparison.
        
        Args:
            name: Name of the test scenario
            graph: NetworkX graph representing the network
            routes: List of (source, destination) pairs to test
            network_state: Optional network state information
        """
        scenario = {
            'name': name,
            'graph': graph.copy(),  # Copy to prevent modifications
            'routes': routes,
            'network_state': network_state or {},
            'num_nodes': graph.number_of_nodes(),
            'num_edges': graph.number_of_edges()
        }
        self.test_scenarios.append(scenario)
    
    def run_comparison(self, verbose: bool = True) -> Dict[str, Any]:
        """
        Run all test scenarios for all algorithms and collect results.
        
        Args:
            verbose: Whether to print progress information
        
        Returns:
            Dictionary containing comparison results
        """
        self.global_stats['start_time'] = time.time()
        
        if verbose:
            print(f"\n{'='*60}")
            print(f"ROUTING ALGORITHM COMPARISON")
            print(f"{'='*60}")
            print(f"Algorithms: {[algo.name for algo in self.algorithms]}")
            print(f"Test scenarios: {len(self.test_scenarios)}")
            print(f"{'='*60}\n")
        
        # Run each scenario
        for scenario_idx, scenario in enumerate(self.test_scenarios, 1):
            if verbose:
                print(f"\nScenario {scenario_idx}/{len(self.test_scenarios)}: {scenario['name']}")
                print(f"  Nodes: {scenario['num_nodes']}, Edges: {scenario['num_edges']}")
                print(f"  Routes to test: {len(scenario['routes'])}")
            
            scenario_results = self._run_scenario(scenario, verbose)
            
            # Store results for each algorithm
            for algo_name, results in scenario_results.items():
                if scenario['name'] not in self.results[algo_name]:
                    self.results[algo_name][scenario['name']] = results
        
        self.global_stats['end_time'] = time.time()
        self.global_stats['total_tests'] = len(self.test_scenarios)
        
        # Generate comparison report
        comparison_report = self._generate_comparison_report()
        
        if verbose:
            self._print_summary(comparison_report)
        
        return comparison_report
    
    def _run_scenario(self, scenario: Dict[str, Any], verbose: bool = True) -> Dict[str, Dict[str, Any]]:
        """
        Run a single test scenario for all algorithms.
        
        Args:
            scenario: Test scenario dictionary
            verbose: Print progress
        
        Returns:
            Results for each algorithm
        """
        scenario_results = {}
        
        for algo in self.algorithms:
            if verbose:
                print(f"    Testing {algo.name}...", end=" ")
            
            algo.reset_stats()  # Reset stats before testing
            
            routes_found = []
            routes_failed = []
            route_lengths = []
            computation_times = []
            
            start_time = time.time()
            
            # Test each route
            for source, destination in scenario['routes']:
                route_start = time.time()
                route = algo.find_route(
                    scenario['graph'], 
                    source, 
                    destination,
                    scenario['network_state']
                )
                route_time = time.time() - route_start
                
                computation_times.append(route_time)
                self.global_stats['total_routes_tested'] += 1
                
                if route is not None:
                    routes_found.append((source, destination, route))
                    route_lengths.append(len(route) - 1)  # Number of hops
                else:
                    routes_failed.append((source, destination))
            
            total_time = time.time() - start_time
            
            # Collect results
            algo_stats = algo.get_stats()
            
            scenario_results[algo.name] = {
                'routes_found': len(routes_found),
                'routes_failed': len(routes_failed),
                'total_routes': len(scenario['routes']),
                'success_rate': len(routes_found) / len(scenario['routes']) if scenario['routes'] else 0,
                'avg_route_length': sum(route_lengths) / len(route_lengths) if route_lengths else 0,
                'min_route_length': min(route_lengths) if route_lengths else 0,
                'max_route_length': max(route_lengths) if route_lengths else 0,
                'avg_computation_time': sum(computation_times) / len(computation_times) if computation_times else 0,
                'total_computation_time': total_time,
                'algorithm_stats': algo_stats,
                'found_routes': routes_found,
                'failed_routes': routes_failed
            }
            
            if verbose:
                print(f"✓ (Success: {scenario_results[algo.name]['success_rate']*100:.1f}%)")
        
        return scenario_results
    
    def _generate_comparison_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive comparison report.
        
        Returns:
            Comparison report dictionary
        """
        report = {
            'timestamp': datetime.now().isoformat(),
            'algorithms': [algo.name for algo in self.algorithms],
            'scenarios': len(self.test_scenarios),
            'total_computation_time': self.global_stats['end_time'] - self.global_stats['start_time'],
            'scenario_results': {},
            'overall_comparison': {}
        }
        
        # Per-scenario results
        for scenario in self.test_scenarios:
            scenario_name = scenario['name']
            report['scenario_results'][scenario_name] = {}
            
            for algo_name in self.results.keys():
                if scenario_name in self.results[algo_name]:
                    report['scenario_results'][scenario_name][algo_name] = self.results[algo_name][scenario_name]
        
        # Overall comparison (aggregated across all scenarios)
        for algo_name in self.results.keys():
            total_routes = 0
            total_success = 0
            total_hops = 0
            total_time = 0
            
            for scenario_results in self.results[algo_name].values():
                total_routes += scenario_results['total_routes']
                total_success += scenario_results['routes_found']
                total_hops += scenario_results['avg_route_length'] * scenario_results['routes_found']
                total_time += scenario_results['total_computation_time']
            
            report['overall_comparison'][algo_name] = {
                'total_routes_tested': total_routes,
                'total_routes_found': total_success,
                'overall_success_rate': total_success / total_routes if total_routes > 0 else 0,
                'avg_route_length': total_hops / total_success if total_success > 0 else 0,
                'total_computation_time': total_time
            }
        
        return report
    
    def _print_summary(self, report: Dict[str, Any]):
        """
        Print comparison summary to console.
        
        Args:
            report: Comparison report
        """
        print(f"\n{'='*60}")
        print(f"COMPARISON SUMMARY")
        print(f"{'='*60}\n")
        
        # Overall comparison table
        print(f"{'Algorithm':<20} {'Success Rate':<15} {'Avg Hops':<12} {'Total Time':<12}")
        print(f"{'-'*60}")
        
        for algo_name, stats in report['overall_comparison'].items():
            print(f"{algo_name:<20} "
                  f"{stats['overall_success_rate']*100:>6.2f}%{'':<8} "
                  f"{stats['avg_route_length']:>8.2f}{'':<4} "
                  f"{stats['total_computation_time']:>8.4f}s")
        
        print(f"\n{'='*60}\n")
    
    def save_results(self, filename: Optional[str] = None) -> str:
        """
        Save comparison results to JSON file.
        
        Args:
            filename: Optional custom filename
        
        Returns:
            Path to saved file
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"routing_comparison_{timestamp}.json"
        
        filepath = self.output_dir / filename
        
        # Generate report
        report = self._generate_comparison_report()
        
        # Remove non-serializable data (graphs, routes)
        clean_report = self._clean_report_for_json(report)
        
        with open(filepath, 'w') as f:
            json.dump(clean_report, f, indent=2)
        
        print(f"\nResults saved to: {filepath}")
        return str(filepath)
    
    def _clean_report_for_json(self, report: Dict[str, Any]) -> Dict[str, Any]:
        """
        Clean report by removing non-JSON-serializable data.
        
        Args:
            report: Raw report
        
        Returns:
            Cleaned report
        """
        clean_report = report.copy()
        
        # Remove found_routes and failed_routes (contain route details)
        for scenario_name, scenario_data in clean_report.get('scenario_results', {}).items():
            for algo_name, algo_data in scenario_data.items():
                if 'found_routes' in algo_data:
                    # Keep count but remove details
                    algo_data['found_routes_count'] = len(algo_data['found_routes'])
                    del algo_data['found_routes']
                if 'failed_routes' in algo_data:
                    algo_data['failed_routes_count'] = len(algo_data['failed_routes'])
                    del algo_data['failed_routes']
        
        return clean_report
    
    def get_winner(self, metric: str = 'success_rate') -> Tuple[str, float]:
        """
        Determine which algorithm performed best for a given metric.
        
        Args:
            metric: Metric to compare ('success_rate', 'avg_route_length', 'computation_time')
        
        Returns:
            Tuple of (algorithm_name, metric_value)
        """
        report = self._generate_comparison_report()
        
        best_algo = None
        best_value = None
        
        for algo_name, stats in report['overall_comparison'].items():
            if metric == 'success_rate':
                value = stats['overall_success_rate']
                if best_value is None or value > best_value:
                    best_value = value
                    best_algo = algo_name
            elif metric == 'avg_route_length':
                value = stats['avg_route_length']
                if best_value is None or value < best_value:  # Lower is better
                    best_value = value
                    best_algo = algo_name
            elif metric == 'computation_time':
                value = stats['total_computation_time']
                if best_value is None or value < best_value:  # Lower is better
                    best_value = value
                    best_algo = algo_name
        
        return best_algo, best_value
