"""
Dijkstra's shortest path routing algorithm implementation.

This is a classical shortest-path algorithm that will serve as a baseline
for comparing against AI-based routing methods.
"""

import networkx as nx
from typing import List, Optional, Dict, Any
import time

from .base import RoutingAlgorithm


class DijkstraRouting(RoutingAlgorithm):
    """
    Dijkstra's algorithm for finding shortest paths in a network.
    
    This algorithm finds the shortest path based on edge weights.
    By default, it uses hop count (all edges weight 1), but can be
    configured to use other metrics like latency, bandwidth, etc.
    """
    
    def __init__(self, weight_metric: str = 'weight'):
        """
        Initialize Dijkstra routing algorithm.
        
        Args:
            weight_metric: The edge attribute to use as weight
                          ('weight', 'latency', 'bandwidth', etc.)
                          Default is 'weight' (hop count)
        """
        super().__init__("Dijkstra")
        self.weight_metric = weight_metric
    
    def find_route(self, graph: nx.Graph, source: int, destination: int,
                   network_state: Optional[Dict[str, Any]] = None) -> Optional[List[int]]:
        """
        Find shortest path from source to destination using Dijkstra's algorithm.
        
        Args:
            graph: NetworkX graph representing the network topology
            source: Source node ID
            destination: Destination node ID
            network_state: Optional network state (not used in basic Dijkstra)
        
        Returns:
            List of node IDs representing the shortest path, or None if no path exists
        """
        start_time = time.time()
        
        try:
            # Check if source and destination exist in the graph
            if source not in graph.nodes() or destination not in graph.nodes():
                self.update_stats(None, time.time() - start_time)
                return None
            
            # If source and destination are the same
            if source == destination:
                route = [source]
                self.update_stats(route, time.time() - start_time)
                return route
            
            # Use NetworkX's Dijkstra implementation
            # If weight_metric is not in edges, treat all edges as weight 1
            try:
                route = nx.shortest_path(graph, source, destination, weight=self.weight_metric)
            except (nx.NodeNotFound, nx.NetworkXNoPath):
                route = None
            except KeyError:
                # Weight attribute doesn't exist, use unweighted shortest path
                try:
                    route = nx.shortest_path(graph, source, destination)
                except nx.NetworkXNoPath:
                    route = None
            
            self.update_stats(route, time.time() - start_time)
            return route
        
        except Exception as e:
            print(f"Error in Dijkstra routing: {e}")
            self.update_stats(None, time.time() - start_time)
            return None
    
    def find_route_with_quality(self, graph: nx.Graph, source: int, destination: int,
                                link_qualities: Optional[Dict] = None) -> Optional[List[int]]:
        """
        Find shortest path considering link quality metrics.
        
        Args:
            graph: NetworkX graph
            source: Source node ID
            destination: Destination node ID
            link_qualities: Dictionary of (node1, node2) -> quality_score
        
        Returns:
            List of node IDs or None
        """
        if link_qualities is None:
            return self.find_route(graph, source, destination)
        
        start_time = time.time()
        
        try:
            # Create a temporary graph with quality-based weights
            temp_graph = graph.copy()
            
            for (u, v), quality in link_qualities.items():
                if temp_graph.has_edge(u, v):
                    # Convert quality (0-1) to cost (higher is worse)
                    # quality=1 (best) -> cost=1, quality=0.5 -> cost=2, etc.
                    cost = 1.0 / max(quality, 0.01)  # Avoid division by zero
                    temp_graph[u][v]['quality_cost'] = cost
            
            try:
                route = nx.shortest_path(temp_graph, source, destination, weight='quality_cost')
            except (nx.NodeNotFound, nx.NetworkXNoPath):
                route = None
            except KeyError:
                # Fallback to regular Dijkstra
                route = self.find_route(graph, source, destination)
            
            self.update_stats(route, time.time() - start_time)
            return route
        
        except Exception as e:
            print(f"Error in quality-aware Dijkstra: {e}")
            self.update_stats(None, time.time() - start_time)
            return None
    
    def __str__(self) -> str:
        return f"Dijkstra (weight={self.weight_metric})"
