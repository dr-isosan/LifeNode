"""
AODV-like (Ad hoc On-Demand Distance Vector) routing algorithm.

This is a simplified implementation of AODV routing protocol,
adapted for our simulation environment. AODV is a reactive routing
protocol commonly used in mobile ad hoc networks (MANETs).
"""

import networkx as nx
from typing import List, Optional, Dict, Any, Tuple
import time
from collections import deque

from .base import RoutingAlgorithm


class AODVRouting(RoutingAlgorithm):
    """
    Simplified AODV routing algorithm implementation.
    
    AODV is a reactive (on-demand) routing protocol that discovers routes
    only when needed. It maintains a routing table and uses route discovery
    (RREQ/RREP) when no route is available.
    
    In this simplified version:
    - We simulate route discovery using BFS
    - Routes are cached with expiration
    - Considers link quality and node failures
    """
    
    def __init__(self, route_cache_timeout: int = 100):
        """
        Initialize AODV routing algorithm.
        
        Args:
            route_cache_timeout: Number of timesteps before a cached route expires
        """
        super().__init__("AODV")
        self.route_cache_timeout = route_cache_timeout
        self.route_cache: Dict[Tuple[int, int], Tuple[List[int], int]] = {}
        self.current_timestep = 0
    
    def update_timestep(self, timestep: int):
        """
        Update current timestep and clean expired routes from cache.
        
        Args:
            timestep: Current simulation timestep
        """
        self.current_timestep = timestep
        
        # Remove expired routes
        expired_routes = []
        for (src, dst), (route, timestamp) in self.route_cache.items():
            if self.current_timestep - timestamp > self.route_cache_timeout:
                expired_routes.append((src, dst))
        
        for key in expired_routes:
            del self.route_cache[key]
    
    def find_route(self, graph: nx.Graph, source: int, destination: int,
                   network_state: Optional[Dict[str, Any]] = None) -> Optional[List[int]]:
        """
        Find route using AODV-like algorithm.
        
        First checks route cache, then performs route discovery if needed.
        
        Args:
            graph: NetworkX graph representing the network topology
            source: Source node ID
            destination: Destination node ID
            network_state: Optional dict containing 'timestep', 'link_qualities', etc.
        
        Returns:
            List of node IDs representing the route, or None if no route exists
        """
        start_time = time.time()
        
        try:
            # Update timestep if provided
            if network_state and 'timestep' in network_state:
                self.update_timestep(network_state['timestep'])
            
            # Check if nodes exist
            if source not in graph.nodes() or destination not in graph.nodes():
                self.update_stats(None, time.time() - start_time)
                return None
            
            # Same source and destination
            if source == destination:
                route = [source]
                self.update_stats(route, time.time() - start_time)
                return route
            
            # Check route cache
            cache_key = (source, destination)
            if cache_key in self.route_cache:
                cached_route, timestamp = self.route_cache[cache_key]
                
                # Verify cached route is still valid (all nodes and edges exist)
                if self._is_route_valid(graph, cached_route):
                    self.update_stats(cached_route, time.time() - start_time)
                    return cached_route
                else:
                    # Route is no longer valid, remove from cache
                    del self.route_cache[cache_key]
            
            # Perform route discovery (simulated RREQ/RREP process)
            route = self._route_discovery(graph, source, destination, network_state)
            
            # Cache the route if found
            if route is not None:
                self.route_cache[cache_key] = (route, self.current_timestep)
            
            self.update_stats(route, time.time() - start_time)
            return route
        
        except Exception as e:
            print(f"Error in AODV routing: {e}")
            self.update_stats(None, time.time() - start_time)
            return None
    
    def _route_discovery(self, graph: nx.Graph, source: int, destination: int,
                        network_state: Optional[Dict[str, Any]] = None) -> Optional[List[int]]:
        """
        Simulate AODV route discovery process using BFS with quality awareness.
        
        Args:
            graph: Network graph
            source: Source node
            destination: Destination node
            network_state: Network state including link qualities
        
        Returns:
            Route as list of nodes or None
        """
        try:
            # Extract link qualities if available
            link_qualities = None
            if network_state and 'link_qualities' in network_state:
                link_qualities = network_state['link_qualities']
            
            # BFS-based route discovery with quality awareness
            queue = deque([(source, [source])])
            visited = {source}
            
            # Track multiple routes and choose best one
            candidate_routes = []
            
            while queue:
                current_node, path = queue.popleft()
                
                # Found destination
                if current_node == destination:
                    route_quality = self._calculate_route_quality(path, link_qualities)
                    candidate_routes.append((path, route_quality))
                    
                    # If we found enough candidates, break early
                    if len(candidate_routes) >= 3:
                        break
                    continue
                
                # Explore neighbors
                for neighbor in graph.neighbors(current_node):
                    if neighbor not in visited:
                        visited.add(neighbor)
                        new_path = path + [neighbor]
                        queue.append((neighbor, new_path))
            
            # Return best route from candidates
            if candidate_routes:
                # Sort by quality (higher is better) and path length (shorter is better)
                candidate_routes.sort(key=lambda x: (-x[1], len(x[0])))
                return candidate_routes[0][0]
            
            return None
        
        except Exception as e:
            print(f"Error in route discovery: {e}")
            return None
    
    def _calculate_route_quality(self, route: List[int], 
                                 link_qualities: Optional[Dict] = None) -> float:
        """
        Calculate overall quality of a route.
        
        Args:
            route: List of nodes in the route
            link_qualities: Dictionary of link qualities
        
        Returns:
            Quality score (higher is better)
        """
        if link_qualities is None or len(route) < 2:
            return 1.0  # Default quality
        
        total_quality = 0.0
        valid_links = 0
        
        for i in range(len(route) - 1):
            u, v = route[i], route[i + 1]
            quality = link_qualities.get((u, v), link_qualities.get((v, u), 1.0))
            total_quality += quality
            valid_links += 1
        
        return total_quality / valid_links if valid_links > 0 else 0.0
    
    def _is_route_valid(self, graph: nx.Graph, route: List[int]) -> bool:
        """
        Check if a cached route is still valid in the current topology.
        
        Args:
            graph: Current network graph
            route: Cached route to verify
        
        Returns:
            True if route is valid, False otherwise
        """
        if not route or len(route) < 2:
            return len(route) == 1 and route[0] in graph.nodes()
        
        # Check all nodes exist
        for node in route:
            if node not in graph.nodes():
                return False
        
        # Check all edges exist
        for i in range(len(route) - 1):
            if not graph.has_edge(route[i], route[i + 1]):
                return False
        
        return True
    
    def clear_cache(self):
        """Clear the entire route cache."""
        self.route_cache.clear()
    
    def get_cache_stats(self) -> Dict[str, int]:
        """
        Get statistics about route cache.
        
        Returns:
            Dictionary with cache statistics
        """
        return {
            'cached_routes': len(self.route_cache),
            'cache_timeout': self.route_cache_timeout,
            'current_timestep': self.current_timestep
        }
    
    def __str__(self) -> str:
        cache_info = f"cache={len(self.route_cache)}"
        return f"AODV ({cache_info})"
