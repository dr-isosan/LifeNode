from src.config.constants import RewardWeights


class RewardSystem:
    def __init__(self):
        """
        Gelişmiş ödül hesaplama sistemi

        Faktörler:
        - Success/Failure: Temel sonuç
        - Energy: Düşük enerjili node'ları koruma
        - Signal: Güçlü sinyal tercih etme
        - Bandwidth: Yüksek bant genişliği tercih etme
        - Queue: Dolu kuyrukları avoid etme
        - Hop count: Kısa yolu tercih etme
        """
        # Constants'tan ağırlıkları al
        self.w_success = RewardWeights.SUCCESS_REWARD
        self.w_failure = RewardWeights.FAILURE_PENALTY
        self.w_step_penalty = RewardWeights.STEP_PENALTY
        self.w_energy = RewardWeights.ENERGY_PENALTY_WEIGHT
        self.w_signal = RewardWeights.SIGNAL_BONUS_WEIGHT
        self.w_bandwidth = RewardWeights.BANDWIDTH_BONUS_WEIGHT
        self.w_queue = RewardWeights.QUEUE_PENALTY_WEIGHT
        self.hop_bonus_per_step = RewardWeights.HOP_BONUS_PER_STEP

    def calculate_reward(
        self,
        success: bool,
        energy_level: float = None,
        hop_count: int = 0,
        failed: bool = False,
        signal_strength: float = None,
        bandwidth: float = None,
        queue_occupancy: float = None,
    ) -> float:
        """
        Gelişmiş ödül hesaplama

        Args:
            success: Paket hedefe ulaştı mı?
            energy_level: Seçilen komşunun enerjisi (0.0-1.0), None = bilinmiyor
            hop_count: Kaçıncı sıçrama
            failed: Paket kayboldu mu?
            signal_strength: Sinyal gücü (0.0-1.0), None = bilinmiyor
            bandwidth: Bandwidth (Mbps), None = bilinmiyor
            queue_occupancy: Kuyruk doluluk oranı (0.0-1.0), None = bilinmiyor

        Returns:
            Hesaplanan ödül değeri
        """
        # 1. SENARYO: Paket Kayboldu (En kötü durum)
        if failed:
            return self.w_failure

        # 2. SENARYO: Paket Başarıyla Hedefe Ulaştı
        if success:
            # Hop count'a göre bonus: Az hop = daha iyi
            hop_bonus = max(0, (10 - hop_count)) * self.hop_bonus_per_step
            return self.w_success + hop_bonus

        # 3. SENARYO: Yolculuk Devam Ediyor (Intermediate step)

        # Base step penalty (her adım için ceza)
        reward = self.w_step_penalty

        # Enerji faktörü
        if energy_level is not None:
            # Düşük enerjili node'ları seçmek ceza getirir
            energy_penalty = (1.0 - energy_level) * self.w_energy
            reward += energy_penalty
        else:
            # Enerji bilinmiyorsa orta seviye ceza
            reward += self.w_energy * 0.5

        # Sinyal gücü bonusu (YENİ!)
        if signal_strength is not None:
            signal_bonus = signal_strength * self.w_signal
            reward += signal_bonus

        # Bandwidth bonusu (YENİ!)
        if bandwidth is not None:
            # 54 Mbps'ye normalize et
            normalized_bandwidth = min(bandwidth / 54.0, 1.0)
            bandwidth_bonus = normalized_bandwidth * self.w_bandwidth
            reward += bandwidth_bonus

        # Kuyruk doluluk cezası (YENİ!)
        if queue_occupancy is not None:
            # Dolu kuyruklar ceza getirir
            queue_penalty = queue_occupancy * self.w_queue
            reward += queue_penalty

        return reward

    def calculate(self, success, energy_level, hop_count, failed=False):
        """Backward compatibility için eski API"""
        return self.calculate_reward(
            success=success,
            energy_level=energy_level,
            hop_count=hop_count,
            failed=failed
        )
