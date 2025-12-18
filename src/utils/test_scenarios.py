"""
Test scenario generator for routing algorithm benchmarks.

This module provides utilities to generate various network scenarios
for comprehensive routing algorithm testing.
"""

import networkx as nx
import random
from typing import List, Tuple, Dict, Any, Optional
from enum import Enum


class TopologyType(Enum):
    """Types of network topologies."""
    SMALL_SPARSE = "small_sparse"
    SMALL_DENSE = "small_dense"
    MEDIUM_SPARSE = "medium_sparse"
    MEDIUM_DENSE = "medium_dense"
    LARGE_SPARSE = "large_sparse"
    LARGE_DENSE = "large_dense"
    XLARGE_SPARSE = "xlarge_sparse"
    XLARGE_DENSE = "xlarge_dense"


class FailureLevel(Enum):
    """Node failure probability levels."""
    NONE = 0.0
    LOW = 0.02
    MEDIUM = 0.05
    HIGH = 0.10
    EXTREME = 0.20


class TestScenarioGenerator:
    """
    Generates comprehensive test scenarios for routing algorithms.
    
    Creates various network topologies and test cases to evaluate
    routing algorithm performance under different conditions.
    """
    
    def __init__(self, seed: Optional[int] = None):
        """
        Initialize scenario generator.
        
        Args:
            seed: Random seed for reproducibility
        """
        self.seed = seed
        if seed is not None:
            random.seed(seed)
    
    def generate_topology(self, topology_type: TopologyType) -> nx.Graph:
        """
        Generate a network topology based on type.
        
        Args:
            topology_type: Type of topology to generate
        
        Returns:
            NetworkX graph
        """
        # Topology configurations
        configs = {
            TopologyType.SMALL_SPARSE: {'n': 15, 'radius': 0.25},
            TopologyType.SMALL_DENSE: {'n': 15, 'radius': 0.40},
            TopologyType.MEDIUM_SPARSE: {'n': 30, 'radius': 0.20},
            TopologyType.MEDIUM_DENSE: {'n': 30, 'radius': 0.30},
            TopologyType.LARGE_SPARSE: {'n': 50, 'radius': 0.18},
            TopologyType.LARGE_DENSE: {'n': 50, 'radius': 0.25},
            TopologyType.XLARGE_SPARSE: {'n': 100, 'radius': 0.15},
            TopologyType.XLARGE_DENSE: {'n': 100, 'radius': 0.20},
        }
        
        config = configs[topology_type]
        graph = nx.random_geometric_graph(config['n'], config['radius'], seed=self.seed)
        
        return graph
    
    def generate_test_routes(self, graph: nx.Graph, num_routes: int,
                            pattern: str = "random") -> List[Tuple[int, int]]:
        """
        Generate test routes for the network.
        
        Args:
            graph: Network graph
            num_routes: Number of routes to generate
            pattern: Route pattern ('random', 'hub-spoke', 'edge-to-edge', 'hotspot')
        
        Returns:
            List of (source, destination) tuples
        """
        nodes = list(graph.nodes())
        routes = []
        
        if pattern == "random":
            # Completely random source-destination pairs
            for _ in range(num_routes):
                source = random.choice(nodes)
                destination = random.choice(nodes)
                while source == destination:
                    destination = random.choice(nodes)
                routes.append((source, destination))
        
        elif pattern == "hub-spoke":
            # Hub node (highest degree) communicates with others
            degrees = dict(graph.degree())
            hub = max(degrees, key=degrees.get)
            
            for _ in range(num_routes):
                if random.random() < 0.5:
                    # Hub to random node
                    destination = random.choice([n for n in nodes if n != hub])
                    routes.append((hub, destination))
                else:
                    # Random node to hub
                    source = random.choice([n for n in nodes if n != hub])
                    routes.append((source, hub))
        
        elif pattern == "edge-to-edge":
            # Peripheral nodes communicate (longest paths)
            degrees = dict(graph.degree())
            edge_nodes = [n for n, d in degrees.items() if d <= 2]
            
            if len(edge_nodes) < 2:
                edge_nodes = nodes
            
            for _ in range(num_routes):
                source = random.choice(edge_nodes)
                destination = random.choice(edge_nodes)
                while source == destination:
                    destination = random.choice(edge_nodes)
                routes.append((source, destination))
        
        elif pattern == "hotspot":
            # 20% of nodes handle 80% of traffic
            hotspot_size = max(2, int(len(nodes) * 0.2))
            hotspots = random.sample(nodes, hotspot_size)
            
            for _ in range(num_routes):
                # 80% chance of involving a hotspot
                if random.random() < 0.8:
                    source = random.choice(hotspots)
                    destination = random.choice(nodes)
                    while source == destination:
                        destination = random.choice(nodes)
                else:
                    source = random.choice(nodes)
                    destination = random.choice(nodes)
                    while source == destination:
                        destination = random.choice(nodes)
                
                routes.append((source, destination))
        
        return routes
    
    def create_test_scenario(self, name: str, topology_type: TopologyType,
                           num_routes: int, route_pattern: str = "random",
                           failure_level: FailureLevel = FailureLevel.NONE,
                           description: str = "") -> Dict[str, Any]:
        """
        Create a complete test scenario.
        
        Args:
            name: Scenario name
            topology_type: Type of network topology
            num_routes: Number of test routes
            route_pattern: Traffic pattern
            failure_level: Node failure probability
            description: Scenario description
        
        Returns:
            Scenario dictionary
        """
        graph = self.generate_topology(topology_type)
        routes = self.generate_test_routes(graph, num_routes, route_pattern)
        
        scenario = {
            'name': name,
            'description': description or f"{topology_type.value} network with {route_pattern} traffic",
            'topology_type': topology_type.value,
            'graph': graph,
            'routes': routes,
            'num_nodes': graph.number_of_nodes(),
            'num_edges': graph.number_of_edges(),
            'num_routes': len(routes),
            'route_pattern': route_pattern,
            'failure_probability': failure_level.value,
            'network_density': (2 * graph.number_of_edges()) / (graph.number_of_nodes() * (graph.number_of_nodes() - 1))
        }
        
        return scenario
    
    def create_benchmark_suite(self) -> List[Dict[str, Any]]:
        """
        Create a comprehensive benchmark suite with multiple scenarios.
        
        Returns:
            List of test scenarios
        """
        scenarios = []
        
        # 1. Small Network Tests
        scenarios.append(self.create_test_scenario(
            name="Small-Sparse-Random",
            topology_type=TopologyType.SMALL_SPARSE,
            num_routes=20,
            route_pattern="random",
            failure_level=FailureLevel.LOW,
            description="Small sparse network with random traffic and low failure rate"
        ))
        
        scenarios.append(self.create_test_scenario(
            name="Small-Dense-HubSpoke",
            topology_type=TopologyType.SMALL_DENSE,
            num_routes=25,
            route_pattern="hub-spoke",
            failure_level=FailureLevel.MEDIUM,
            description="Small dense network with hub-spoke traffic pattern"
        ))
        
        # 2. Medium Network Tests
        scenarios.append(self.create_test_scenario(
            name="Medium-Sparse-Random",
            topology_type=TopologyType.MEDIUM_SPARSE,
            num_routes=50,
            route_pattern="random",
            failure_level=FailureLevel.LOW,
            description="Medium sparse network with random traffic"
        ))
        
        scenarios.append(self.create_test_scenario(
            name="Medium-Dense-Hotspot",
            topology_type=TopologyType.MEDIUM_DENSE,
            num_routes=60,
            route_pattern="hotspot",
            failure_level=FailureLevel.MEDIUM,
            description="Medium dense network with hotspot traffic pattern"
        ))
        
        # 3. Large Network Tests
        scenarios.append(self.create_test_scenario(
            name="Large-Sparse-EdgeToEdge",
            topology_type=TopologyType.LARGE_SPARSE,
            num_routes=80,
            route_pattern="edge-to-edge",
            failure_level=FailureLevel.LOW,
            description="Large sparse network with edge-to-edge communication"
        ))
        
        scenarios.append(self.create_test_scenario(
            name="Large-Dense-Random",
            topology_type=TopologyType.LARGE_DENSE,
            num_routes=100,
            route_pattern="random",
            failure_level=FailureLevel.MEDIUM,
            description="Large dense network with random traffic"
        ))
        
        # 4. Stress Tests
        scenarios.append(self.create_test_scenario(
            name="StressTest-HighFailure",
            topology_type=TopologyType.MEDIUM_DENSE,
            num_routes=100,
            route_pattern="random",
            failure_level=FailureLevel.HIGH,
            description="Stress test with high failure rate"
        ))
        
        scenarios.append(self.create_test_scenario(
            name="StressTest-LargeScale",
            topology_type=TopologyType.XLARGE_SPARSE,
            num_routes=200,
            route_pattern="hotspot",
            failure_level=FailureLevel.MEDIUM,
            description="Large scale stress test with 100 nodes"
        ))
        
        # 5. Edge Cases
        scenarios.append(self.create_test_scenario(
            name="EdgeCase-ExtremeFailure",
            topology_type=TopologyType.SMALL_DENSE,
            num_routes=30,
            route_pattern="random",
            failure_level=FailureLevel.EXTREME,
            description="Edge case: extreme failure rate (20%)"
        ))
        
        return scenarios
    
    def print_scenario_summary(self, scenario: Dict[str, Any]):
        """
        Print a summary of a test scenario.
        
        Args:
            scenario: Scenario dictionary
        """
        print(f"\n{'='*70}")
        print(f"Scenario: {scenario['name']}")
        print(f"{'='*70}")
        print(f"Description: {scenario['description']}")
        print(f"Topology: {scenario['topology_type']}")
        print(f"Nodes: {scenario['num_nodes']}")
        print(f"Edges: {scenario['num_edges']}")
        print(f"Network Density: {scenario['network_density']:.4f}")
        print(f"Test Routes: {scenario['num_routes']}")
        print(f"Route Pattern: {scenario['route_pattern']}")
        print(f"Failure Probability: {scenario['failure_probability']*100:.1f}%")
        print(f"{'='*70}")


def create_quick_test_suite() -> List[Dict[str, Any]]:
    """
    Create a quick test suite with fewer scenarios for rapid testing.
    
    Returns:
        List of test scenarios
    """
    generator = TestScenarioGenerator(seed=42)
    
    scenarios = []
    
    scenarios.append(generator.create_test_scenario(
        name="Quick-Small",
        topology_type=TopologyType.SMALL_SPARSE,
        num_routes=15,
        route_pattern="random",
        failure_level=FailureLevel.LOW
    ))
    
    scenarios.append(generator.create_test_scenario(
        name="Quick-Medium",
        topology_type=TopologyType.MEDIUM_SPARSE,
        num_routes=30,
        route_pattern="random",
        failure_level=FailureLevel.MEDIUM
    ))
    
    scenarios.append(generator.create_test_scenario(
        name="Quick-Large",
        topology_type=TopologyType.LARGE_SPARSE,
        num_routes=50,
        route_pattern="random",
        failure_level=FailureLevel.MEDIUM
    ))
    
    return scenarios
