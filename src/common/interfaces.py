# src/common/interfaces.py
from dataclasses import dataclass
from typing import List, Dict


# 1. DÜĞÜM DURUMU (Node State)
# Ajanın bir node hakkında bilmesi gereken her şey.
@dataclass
class NodeState:
    node_id: int
    battery_level: float  # 0.0 ile 1.0 arası
    queue_occupancy: float  # 0.0 ile 1.0 arası (Doluluk oranı)
    position: tuple  # (x, y) - Hedefe uzaklık hesabı için
    is_active: bool = True  # Node bozuk mu?


# 2. BAĞLANTI DURUMU (Link State)
# Komşularla aradaki ilişkinin kalitesi.
@dataclass
class LinkState:
    target_node_id: int
    signal_strength: float  # 0.0 ile 1.0 arası (Normalize edilmiş SNR)
    bandwidth_capacity: float  # Opsiyonel: Bant genişliği


# 3. GLOBAL GÖZLEM (Observation)
# AI'nın "encode" fonksiyonuna girecek ham paket.
@dataclass
class NetworkObservation:
    current_node: NodeState
    neighbors: List[LinkState]  # Sadece erişilebilir komşular
    neighbor_nodes: Dict[int, NodeState]  # Komşuların pil/kuyruk bilgileri
    destination_pos: tuple  # Paketin gitmeye çalıştığı yer (x, y)


# 4. SİMÜLASYON MOTORU ARAYÜZÜ (Soyut)
# Kişi A bu sınıfı "miras alıp" (inherit) içini doldurmak ZORUNDA.
class SimulationEngineInterface:
    def get_observation(self, node_id: int, packet_dest: int) -> NetworkObservation:
        raise NotImplementedError("Kişi A burayı henüz kodlamadı!")

    def execute_action(self, source_node_id: int, target_node_id: int) -> dict:
        """
        Returns: {'success': bool, 'latency': float, 'energy_cost': float}
        """
        raise NotImplementedError("Kişi A burayı henüz kodlamadı!")
