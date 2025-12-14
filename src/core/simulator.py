# src/core/simulator.py
"""
Simulation Network Adapter
Kişi A'nın Network simülasyonunu Kişi B'nin AI Environment'ına bağlar
"""
from src.common.interfaces import (
    SimulationEngineInterface,
    NetworkObservation,
    NodeState,
    LinkState,
)
from src.config.constants import SignalThresholds, BandwidthRatios, PhysicsConstants


class SimulationNetworkAdapter(SimulationEngineInterface):
    """
    Network simülasyonunu AI Environment'a bağlayan adapter.
    SimulationEngineInterface'i implement eder.
    """

    def __init__(self, network, communication_range: float = None):
        """
        Args:
            network: simulation.network.Network instance
            communication_range: İletişim menzili (None ise network'ten alınır)
        """
        self.network = network
        self.current_packet = None

        # Communication range'i network'ten al veya parametreyi kullan
        if communication_range is None:
            self.communication_range = getattr(network, 'communication_range', 30.0)
        else:
            self.communication_range = communication_range

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
                distance, communication_range=self.communication_range
            )

            # Bandwidth capacity - dinamik olarak hesapla
            bandwidth = self._calculate_bandwidth(
                distance, signal_strength, communication_range=self.communication_range
            )

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
        base_latency = PhysicsConstants.BASE_LATENCY_MS / 1000.0  # Convert to seconds
        distance_penalty = distance * (PhysicsConstants.LATENCY_PER_METER_MS / 1000.0) / 10.0

        return base_latency + distance_penalty

    def _calculate_energy_cost(self, distance: float) -> float:
        """
        Mesafeye göre enerji maliyeti hesapla (0-100 arası)

        Daha uzak mesafe = daha fazla enerji
        """
        # Base cost
        base_cost = PhysicsConstants.BASE_ENERGY_COST

        # Distance cost
        distance_cost = distance * PhysicsConstants.ENERGY_COST_PER_METER

        return base_cost + distance_cost

    def _calculate_bandwidth(
        self,
        distance: float,
        signal_strength: float,
        communication_range: float,
    ) -> float:
        """
        Mesafe ve sinyal gücüne göre bandwidth hesapla (Mbps)

        Wireless mesh network bandwidth modeli:
        - Max bandwidth: 54 Mbps (802.11g standardı)
        - Sinyal gücü ve mesafeye göre adaptive modulation
        - SNR'a göre farklı modulation schemes (BPSK, QPSK, 16-QAM, 64-QAM)
        """
        # Sinyal gücüne göre bandwidth oranı
        # Yüksek sinyal = yüksek bandwidth
        if signal_strength >= SignalThresholds.EXCELLENT:
            # Excellent signal: 64-QAM modulation
            bandwidth_ratio = BandwidthRatios.EXCELLENT_RATIO
        elif signal_strength >= SignalThresholds.GOOD:
            # Good signal: 16-QAM modulation
            bandwidth_ratio = BandwidthRatios.GOOD_RATIO
        elif signal_strength >= SignalThresholds.FAIR:
            # Fair signal: QPSK modulation
            bandwidth_ratio = BandwidthRatios.FAIR_RATIO
        elif signal_strength >= SignalThresholds.WEAK:
            # Weak signal: BPSK modulation
            bandwidth_ratio = BandwidthRatios.WEAK_RATIO
        else:
            # Very weak signal: minimum bandwidth
            bandwidth_ratio = BandwidthRatios.MINIMUM_RATIO

        # Mesafe penalty (iletişim range'ine göre)
        distance_factor = 1.0 - (distance / communication_range) * PhysicsConstants.DISTANCE_PENALTY_FACTOR
        distance_factor = max(BandwidthRatios.MINIMUM_RATIO, distance_factor)

        # Final bandwidth hesaplama
        bandwidth = PhysicsConstants.MAX_BANDWIDTH_MBPS * bandwidth_ratio * distance_factor

        return max(PhysicsConstants.MIN_BANDWIDTH_MBPS, bandwidth)
