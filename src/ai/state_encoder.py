# src/ai/state_encoder.py
import numpy as np
import math
from src.common.interfaces import NetworkObservation
from src.config.constants import StateEncoderConfig


class StateEncoder:
    def __init__(self, max_neighbors=5):
        self.max_neighbors = max_neighbors
        # Her komşu için 3 özellik: [Sinyal, Enerji, Kuyruk]
        self.features_per_neighbor = StateEncoderConfig.FEATURES_PER_NEIGHBOR

        # State Boyutu: [Hedefe_Uzaklık (1)] + [Komşular (max * 3)]
        self.state_dim = 1 + (self.max_neighbors * self.features_per_neighbor)

    def encode(self, observation: NetworkObservation):
        """
        Gelen 'NetworkObservation' veri paketini Numpy vektörüne çevirir.
        """
        # 1. HEDEFE UZAKLIK (Euclidean Distance)
        curr_pos = observation.current_node.position
        dest_pos = observation.destination_pos

        dist = math.sqrt(
            (dest_pos[0] - curr_pos[0]) ** 2 + (dest_pos[1] - curr_pos[1]) ** 2
        )

        # Normalizasyon
        norm_dist = dist / StateEncoderConfig.MAX_DISTANCE_METERS if dist < StateEncoderConfig.MAX_DISTANCE_METERS else 1.0

        state_vector = [norm_dist]

        # 2. KOMŞU BİLGİLERİNİ İŞLE
        count = 0

        for link in observation.neighbors:
            if count >= self.max_neighbors:
                break

            # Komşunun detay bilgilerini ID ile sözlükten çekiyoruz
            neighbor_node = observation.neighbor_nodes.get(link.target_node_id)

            if neighbor_node:
                # Sinyal Gücü (Zaten 0-1 arası geliyor)
                s_signal = link.signal_strength

                # Enerji (Zaten 0-1 arası)
                s_energy = neighbor_node.battery_level

                # Kuyruk (Zaten 0-1 arası)
                s_queue = neighbor_node.queue_occupancy

                state_vector.extend([s_signal, s_energy, s_queue])
                count += 1

        # 3. PADDING (Eksik kalan yerleri doldur)
        remaining_slots = self.max_neighbors - count
        for _ in range(remaining_slots):
            # Boş slot: Sinyal=0, Enerji=0, Kuyruk=1 (Dolu - Gitme!)
            state_vector.extend([0.0, 0.0, 1.0])

        return np.array(state_vector, dtype=np.float32)
