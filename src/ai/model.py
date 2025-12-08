import torch
import torch.nn as nn
import torch.nn.functional as F


class DQN(nn.Module):
    def __init__(self, input_dim, output_dim):
        super(DQN, self).__init__()

        # KATMANLAR (Layers)
        # Giriş Katmanı -> Gizli Katman 1 (64 Nöron)
        self.fc1 = nn.Linear(input_dim, 64)

        # Gizli Katman 1 -> Gizli Katman 2 (64 Nöron)
        self.fc2 = nn.Linear(64, 64)

        # Gizli Katman 2 -> Çıkış Katmanı (Komşu Sayısı kadar)
        self.fc3 = nn.Linear(64, output_dim)

    def forward(self, x):
        """
        Veri ağın içinden nasıl akar?
        x: State vektörü
        """
        # 1. Katman + ReLU Aktivasyonu (Negatifleri sıfırla)
        x = F.relu(self.fc1(x))

        # 2. Katman + ReLU
        x = F.relu(self.fc2(x))

        # 3. Çıkış Katmanı (Aktivasyon yok, ham Q değerleri lazım)
        return self.fc3(x)
