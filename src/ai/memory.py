# src/ai/memory.py
import random
import numpy as np
from collections import deque
import torch


class ReplayBuffer:
    def __init__(self, capacity, device):
        """
        capacity: Hafızada tutulacak maksimum anı sayısı (Örn: 10,000)
        device: CPU mu GPU mu? (Verileri ona göre hazırlayacağız)
        """
        self.buffer = deque(maxlen=capacity)
        self.device = device

    def push(self, state, action, reward, next_state, done):
        """Yeni bir deneyimi hafızaya ekle."""
        self.buffer.append((state, action, reward, next_state, done))

    def sample(self, batch_size):
        """
        Hafızadan rastgele 'batch_size' kadar anı çek.
        Öğrenme burada gerçekleşir.
        """
        state, action, reward, next_state, done = zip(
            *random.sample(self.buffer, batch_size)
        )

        # Verileri Tensor'a çevirip ilgili cihaza (GPU/CPU) gönderiyoruz
        return (
            torch.FloatTensor(np.array(state)).to(self.device),
            torch.LongTensor(action).unsqueeze(1).to(self.device),
            torch.FloatTensor(reward).unsqueeze(1).to(self.device),
            torch.FloatTensor(np.array(next_state)).to(self.device),
            torch.FloatTensor(done).unsqueeze(1).to(self.device),
        )

    def __len__(self):
        return len(self.buffer)
