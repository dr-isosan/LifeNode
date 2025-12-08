class RewardSystem:
    def __init__(self):
        self.w_success = 100.0
        self.w_failure = -1.0
        self.w_step_penalty = -5.0
        self.w_energy = -50.0
        """
        Ödül hesaplama için ağırlıklar:
        - w_success: Başarı ödülü
        - w_failure: Başarısızlık cezası
        - w_step_penalty: Her adım için ceza
        - w_energy: Kalan enerjiye bağlı ceza
        """

    def calculate_reward(self, success, energy_level, hop_count, failed=False):
        """
        success (bool): Paket hedefe ulaştı mı?
        energy_level (float): Seçilen komşunun kalan enerjisi (0.0 - 1.0 arası)
        hop_count (int): Kaçıncı sıçrama? (Gerekirse kullanılabilir)
        failed (bool): Paket kayboldu mu?
        """
        # 1. Senaryo: Paket Kayboldu (En kötü durum)
        if failed:
            return self.w_failure
        # 2. Senaryo: Paket Başarıyla Hedefe Ulaştı
        if success:
            return self.w_success
        # 3. Senaryo: Yolculuk Devam Ediyor (Standart durum)
        # Zaman cezası sabittir (Hızlı olmaya zorlar)
        step_reward = self.w_step_penalty
        # Enerji cezası: Enerjisi AZ olanı seçersen ceza BÜYÜR.
        # Eğer enerji 1.0 (Full) ise ceza 0 olur.
        # Eğer enerji 0.1 (Bitik) ise ceza -4.5 olur.
        energy_penalty = (1.0 - energy_level) * self.w_energy
        return step_reward + energy_penalty
