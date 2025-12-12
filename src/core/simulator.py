# src/core/simulator.py
"""
Simulation Network Adapter
Kişi A'nın Network simülasyonunu Kişi B'nin AI Environment'ına bağlar
"""
from common.interfaces import (
    SimulationEngineInterface,
    NetworkObservation,
    NodeState,
    LinkState,
)


class SimulationNetworkAdapter(SimulationEngineInterface):
    """
    Network simülasyonunu AI Environment'a bağlayan adapter.
    SimulationEngineInterface'i implement eder.
    """

    def __init__(self, network):
        """
        Args:
            network: simulation.network.Network instance
        """
        self.network = network
        self.current_packet = None

    def get_observation(self, node_id: int, packet_dest: int) -> NetworkObservation:
        """
        Belirli bir node için AI'ın ihtiyaç duyduğu observation'ı döndür

        Args:
            node_id: Şu anda paketin bulunduğu node ID
            packet_dest: Paketin hedef node ID'si

        Returns:
            NetworkObservation: AI için hazırlanmış gözlem
        """
        if node_id not in self.network.nodes:
            raise ValueError(f"Node {node_id} ağda bulunamadı!")

        current_node = self.network.nodes[node_id]

        # 1. Current Node State
        current_node_state = NodeState(
            node_id=current_node.id,
            battery_level=current_node.battery_level,
            queue_occupancy=(current_node.queue_len / current_node.queue_capacity),
            position=current_node.position,
            is_active=current_node.is_active,
        )

        # 2. Destination Position
        destination_pos = (0.0, 0.0)
        if packet_dest in self.network.nodes:
            dest_node = self.network.nodes[packet_dest]
            destination_pos = dest_node.position

        # 3. Neighbors (sadece aktif olanlar)
        neighbor_links = []
        neighbor_nodes_dict = {}

        for neighbor_id in current_node.neighbors:
            if neighbor_id not in self.network.nodes:
                continue

            neighbor = self.network.nodes[neighbor_id]

            # Skip inactive neighbors
            if not neighbor.is_active:
                continue

            # Calculate signal strength based on distance
            distance = current_node.distance_to(neighbor)
            signal_strength = self._calculate_signal_strength(
                distance, communication_range=30.0
            )

            # Bandwidth capacity (mock for now, can be enhanced)
            bandwidth = 10.0

            # LinkState
            link = LinkState(
                target_node_id=neighbor_id,
                signal_strength=signal_strength,
                bandwidth_capacity=bandwidth,
            )
            neighbor_links.append(link)

            # Neighbor NodeState
            neighbor_state = NodeState(
                node_id=neighbor.id,
                battery_level=neighbor.battery_level,
                queue_occupancy=neighbor.queue_len / neighbor.queue_capacity,
                position=neighbor.position,
                is_active=neighbor.is_active,
            )
            neighbor_nodes_dict[neighbor_id] = neighbor_state

        # 4. NetworkObservation oluştur
        observation = NetworkObservation(
            current_node=current_node_state,
            neighbors=neighbor_links,
            neighbor_nodes=neighbor_nodes_dict,
            destination_pos=destination_pos,
        )

        return observation

    def execute_action(self, source_node_id: int, target_node_id: int) -> dict:
        """
        AI'nın seçtiği aksiyonu (komşu seçimi) simülasyonda uygula

        Args:
            source_node_id: Paketin şu anki konumu
            target_node_id: AI'nın seçtiği hedef komşu

        Returns:
            dict: {'success': bool, 'latency': float, 'energy_cost': float}
        """
        # Validation
        if source_node_id not in self.network.nodes:
            return {
                "success": False,
                "latency": 0.0,
                "energy_cost": 0.0,
                "reason": "source_not_found",
            }

        if target_node_id not in self.network.nodes:
            return {
                "success": False,
                "latency": 0.0,
                "energy_cost": 0.0,
                "reason": "target_not_found",
            }

        source_node = self.network.nodes[source_node_id]
        target_node = self.network.nodes[target_node_id]

        # Check if target is a neighbor
        if target_node_id not in source_node.neighbors:
            return {
                "success": False,
                "latency": 0.0,
                "energy_cost": 0.0,
                "reason": "not_a_neighbor",
            }

        # Check if target is active
        if not target_node.is_active:
            return {
                "success": False,
                "latency": 0.0,
                "energy_cost": 0.0,
                "reason": "target_inactive",
            }

        # Calculate latency based on distance
        distance = source_node.distance_to(target_node)
        latency = self._calculate_latency(distance)

        # Calculate energy cost
        energy_cost = self._calculate_energy_cost(distance)

        # Update node energies
        source_node.energy = max(0.0, source_node.energy - energy_cost)
        target_node.energy = max(0.0, target_node.energy - energy_cost * 0.5)

        return {
            "success": True,
            "latency": latency,
            "energy_cost": energy_cost,
            "reason": "success",
        }

    def _calculate_signal_strength(
        self, distance: float, communication_range: float
    ) -> float:
        """
        Mesafeye göre sinyal gücü hesapla (0.0 - 1.0 arası)

        Free Space Path Loss kullanır:
        Signal = 1.0 - (distance / max_range)^2
        """
        if distance >= communication_range:
            return 0.0

        # Normalized distance (0-1)
        norm_dist = distance / communication_range

        # Quadratic falloff (more realistic)
        signal = 1.0 - (norm_dist**2)

        return max(0.0, min(1.0, signal))

    def _calculate_latency(self, distance: float) -> float:
        """
        Mesafeye göre latency hesapla (saniye)

        Wireless mesh network'te:
        - Base latency: 1ms
        - Distance penalty: 0.1ms per meter
        """
        base_latency = 0.001  # 1ms
        distance_penalty = distance * 0.0001  # 0.1ms per meter

        return base_latency + distance_penalty

    def _calculate_energy_cost(self, distance: float) -> float:
        """
        Mesafeye göre enerji maliyeti hesapla (0-100 arası)

        Daha uzak mesafe = daha fazla enerji
        """
        # Base cost: 0.5 energy
        base_cost = 0.5

        # Distance cost: 0.01 per meter
        distance_cost = distance * 0.01

        return base_cost + distance_cost
