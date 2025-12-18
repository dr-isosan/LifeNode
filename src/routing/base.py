"""
Base interface for all routing algorithms in LifeNode.

This module defines the abstract base class that all routing algorithms
must implement to ensure consistency and interoperability.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
import networkx as nx


class RoutingAlgorithm(ABC):
    """
    Abstract base class for routing algorithms.
    
    All routing algorithms (classical or AI-based) must inherit from this class
    and implement the find_route method.
    """
    
    def __init__(self, name: str):
        """
        Initialize routing algorithm.
        
        Args:
            name: Human-readable name of the algorithm (e.g., "Dijkstra", "AODV", "DQN-AI")
        """
        self.name = name
        self.stats = {
            'total_routes_calculated': 0,
            'successful_routes': 0,
            'failed_routes': 0,
            'total_hops': 0,
            'total_latency': 0.0
        }
    
    @abstractmethod
    def find_route(self, graph: nx.Graph, source: int, destination: int, 
                   network_state: Optional[Dict[str, Any]] = None) -> Optional[List[int]]:
        """
        Find a route from source to destination node.
        
        Args:
            graph: NetworkX graph representing the current network topology
            source: Source node ID
            destination: Destination node ID
            network_state: Optional dictionary containing current network state
                          (e.g., link qualities, congestion, etc.)
        
        Returns:
            List of node IDs representing the route from source to destination,
            or None if no route exists.
        """
        pass
    
    def update_stats(self, route: Optional[List[int]], latency: float = 0.0):
        """
        Update routing statistics after calculating a route.
        
        Args:
            route: The calculated route (None if failed)
            latency: Time taken to calculate the route
        """
        self.stats['total_routes_calculated'] += 1
        
        if route is not None:
            self.stats['successful_routes'] += 1
            self.stats['total_hops'] += len(route) - 1
        else:
            self.stats['failed_routes'] += 1
        
        self.stats['total_latency'] += latency
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get routing statistics.
        
        Returns:
            Dictionary containing routing performance statistics
        """
        stats = self.stats.copy()
        
        # Calculate averages
        if stats['successful_routes'] > 0:
            stats['avg_hops'] = stats['total_hops'] / stats['successful_routes']
        else:
            stats['avg_hops'] = 0.0
        
        if stats['total_routes_calculated'] > 0:
            stats['success_rate'] = stats['successful_routes'] / stats['total_routes_calculated']
            stats['avg_latency'] = stats['total_latency'] / stats['total_routes_calculated']
        else:
            stats['success_rate'] = 0.0
            stats['avg_latency'] = 0.0
        
        return stats
    
    def reset_stats(self):
        """Reset all statistics to zero."""
        self.stats = {
            'total_routes_calculated': 0,
            'successful_routes': 0,
            'failed_routes': 0,
            'total_hops': 0,
            'total_latency': 0.0
        }
    
    def __str__(self) -> str:
        return f"{self.name} Routing Algorithm"
    
    def __repr__(self) -> str:
        return f"RoutingAlgorithm(name='{self.name}')"
