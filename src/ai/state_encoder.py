import numpy as np


class StateEncoder:
    def __init__(self, max_neighbors=5):
        self.max_neighbors = max_neighbors
        # Her komşu için 3 özellik: [Sinyal, Enerji, Kuyruk]
        self.features_per_neighbor = 3

        # Toplam State Boyutu:
        # [Hedefe_Uzaklık (1)] + [Komşular (max * 3)]
        self.state_dim = 1 + (self.max_neighbors * self.features_per_neighbor)

    def encode(self, current_node, neighbors, destination):
        """
        Simülasyon objelerini alır, Numpy Array (Vektör) döndürür.
        """
        # 1. HEDEFE UZAKLIK (Normalize edilmiş)
        # Örnek: Max harita boyutu 1000m ise 1000'e böl.
        dist_to_dest = current_node.distance_to(destination) / 1000.0

        # Vektörü başlat
        state_vector = [dist_to_dest]

        # 2. KOMŞU BİLGİLERİNİ İŞLE
        # Komşuları, hedefe yakınlıklarına göre sıralamak iyi bir pratiktir (Opsiyonel)
        # neighbors.sort(key=lambda n: n.distance_to(destination))

        count = 0
        for neighbor in neighbors:
            if count >= self.max_neighbors:
                break  # 5'ten fazla komşu varsa, gerisine bakma.

            # --- NORMALİZASYON (0 ile 1 arasına sıkıştır) ---

            # Sinyal (Örnek: -100dBm ile -40dBm arası) -> 0 ile 1 arası
            # Formül: (Signal + 100) / 60 gibi bir şey olabilir.
            # Şimdilik direkt attribute'dan geldiğini varsayalım:
            norm_signal = neighbor.signal_quality  # 0.8 gibi

            # Enerji (Zaten 0-1 arasıysa dokunma)
            norm_energy = neighbor.battery_level  # 0.5 gibi

            # Kuyruk Doluluğu (Queue Load)
            # Eğer kuyrukta 10 paket var ve kapasite 20 ise -> 0.5
            norm_queue = neighbor.queue_len / neighbor.queue_capacity

            # Listeye ekle
            state_vector.extend([norm_signal, norm_energy, norm_queue])
            count += 1

        # 3. PADDING (Eksik kalan yerleri doldur)
        # Eğer 2 komşu varsa, kalan 3 komşunun yerini -1 veya 0 ile doldur.
        remaining_slots = self.max_neighbors - count
        for _ in range(remaining_slots):
            # Olmayan komşu için değerler: Sinyal=0, Enerji=0, Kuyruk=1 (Dolu gibi göster ki seçmesin)
            state_vector.extend([0.0, 0.0, 1.0])

        return np.array(state_vector, dtype=np.float32)
