"""
Example script to test routing algorithm comparison framework.

This script demonstrates how to use the RoutingComparator to compare
different routing algorithms on the same network scenarios.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import networkx as nx
from src.routing import DijkstraRouting, AODVRouting
from src.utils import RoutingComparator


def create_sample_network(num_nodes: int = 20, radius: float = 0.3) -> nx.Graph:
    """
    Create a sample random geometric graph.
    
    Args:
        num_nodes: Number of nodes
        radius: Connection radius
    
    Returns:
        NetworkX graph
    """
    graph = nx.random_geometric_graph(num_nodes, radius, seed=42)
    return graph


def generate_test_routes(graph: nx.Graph, num_routes: int = 10):
    """
    Generate random source-destination pairs for testing.
    
    Args:
        graph: Network graph
        num_routes: Number of routes to generate
    
    Returns:
        List of (source, destination) tuples
    """
    import random
    random.seed(42)
    
    nodes = list(graph.nodes())
    routes = []
    
    for _ in range(num_routes):
        source = random.choice(nodes)
        destination = random.choice(nodes)
        
        # Ensure source != destination
        while source == destination:
            destination = random.choice(nodes)
        
        routes.append((source, destination))
    
    return routes


def main():
    """Main function to test routing comparison."""
    
    print("\n" + "="*70)
    print("ROUTING ALGORITHM COMPARISON TEST")
    print("="*70 + "\n")
    
    # Create routing algorithms
    dijkstra = DijkstraRouting()
    aodv = AODVRouting(route_cache_timeout=50)
    
    print("Algorithms to compare:")
    print(f"  1. {dijkstra}")
    print(f"  2. {aodv}")
    print()
    
    # Create comparator
    comparator = RoutingComparator(
        algorithms=[dijkstra, aodv],
        output_dir="results/routing_comparison"
    )
    
    # Scenario 1: Small network
    print("Creating test scenarios...")
    graph_small = create_sample_network(num_nodes=15, radius=0.3)
    routes_small = generate_test_routes(graph_small, num_routes=20)
    comparator.add_test_scenario(
        name="Small Network (15 nodes)",
        graph=graph_small,
        routes=routes_small
    )
    
    # Scenario 2: Medium network
    graph_medium = create_sample_network(num_nodes=30, radius=0.25)
    routes_medium = generate_test_routes(graph_medium, num_routes=30)
    comparator.add_test_scenario(
        name="Medium Network (30 nodes)",
        graph=graph_medium,
        routes=routes_medium
    )
    
    # Scenario 3: Large network
    graph_large = create_sample_network(num_nodes=50, radius=0.2)
    routes_large = generate_test_routes(graph_large, num_routes=50)
    comparator.add_test_scenario(
        name="Large Network (50 nodes)",
        graph=graph_large,
        routes=routes_large
    )
    
    print(f"Created {len(comparator.test_scenarios)} test scenarios.\n")
    
    # Run comparison
    results = comparator.run_comparison(verbose=True)
    
    # Save results
    output_file = comparator.save_results()
    
    # Determine winners
    print("\n" + "="*70)
    print("WINNERS BY METRIC")
    print("="*70)
    
    metrics = [
        ('success_rate', 'Success Rate'),
        ('avg_route_length', 'Average Route Length'),
        ('computation_time', 'Computation Time')
    ]
    
    for metric_key, metric_name in metrics:
        winner, value = comparator.get_winner(metric_key)
        if metric_key == 'success_rate':
            print(f"{metric_name:<30}: {winner} ({value*100:.2f}%)")
        elif metric_key == 'avg_route_length':
            print(f"{metric_name:<30}: {winner} ({value:.2f} hops)")
        else:
            print(f"{metric_name:<30}: {winner} ({value:.4f}s)")
    
    print("\n" + "="*70)
    print("Test completed successfully!")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
