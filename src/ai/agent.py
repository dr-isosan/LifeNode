# src/ai/agent.py
import torch
import torch.optim as optim
import torch.nn.functional as F
import numpy as np
import random
from .model import DQN
from .memory import ReplayBuffer
from src.config.constants import AITrainingConfig


class DQNAgent:
    def __init__(self, state_dim, action_dim, lr=AITrainingConfig.LEARNING_RATE,
                 gamma=AITrainingConfig.GAMMA, buffer_size=AITrainingConfig.REPLAY_BUFFER_SIZE):
        # 1. TEMEL AYARLAR
        self.gamma = gamma
        self.epsilon = AITrainingConfig.EPSILON_START
        self.epsilon_min = AITrainingConfig.EPSILON_MIN
        self.epsilon_decay = AITrainingConfig.EPSILON_DECAY
        self.batch_size = AITrainingConfig.BATCH_SIZE
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        # 2. SİNİR AĞLARI (Brain)
        self.policy_net = DQN(state_dim, action_dim).to(self.device)
        self.target_net = DQN(state_dim, action_dim).to(self.device)
        self.target_net.load_state_dict(self.policy_net.state_dict())
        self.target_net.eval()  # Hedef ağ sadece izler, öğrenmez.

        self.optimizer = optim.Adam(self.policy_net.parameters(), lr=lr)

        # 3. PROFESYONEL HAFIZA MODÜLÜ
        self.memory = ReplayBuffer(capacity=buffer_size, device=self.device)

    def act(self, state):
        """Action seçimi: Keşfet (Random) veya Sömür (Model)"""
        if random.random() < self.epsilon:
            # Rastgele bir aksiyon döndür (Modelin çıktı sayısı kadar)
            return random.randrange(self.policy_net.fc3.out_features)

        # State'i Tensor'a çevir
        state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)

        with torch.no_grad():
            q_values = self.policy_net(state_tensor)

        return np.argmax(q_values.cpu().data.numpy())

    def remember(self, state, action, reward, next_state, done):
        """Deneyimi hafıza modülüne ilet"""
        self.memory.push(state, action, reward, next_state, done)

    def learn(self):
        """Öğrenme Döngüsü (Replay Experience)"""
        # Yeterli veri yoksa öğrenme
        if len(self.memory) < self.batch_size:
            return

        # 1. HAFIZADAN ÖRNEK ÇEK (Otomatik Tensor Olarak Gelir)
        states, actions, rewards, next_states, dones = self.memory.sample(
            self.batch_size
        )

        # 2. Q-DEĞERLERİNİ HESAPLA
        # Policy Net: "Bu durumda bu hareketi yapsaydım ne kazanırdım?"
        current_q = self.policy_net(states).gather(1, actions)

        # Target Net: "Gelecek durumda maksimum ne kazanabilirim?"
        # Not: Gelecek tahmini için Target Net kullanılır (Stabilite için)
        next_q = self.target_net(next_states).max(1)[0].detach().unsqueeze(1)

        # Bellman Hedefi: Ödül + (Gelecek * Gamma)
        target_q = rewards + (self.gamma * next_q * (1 - dones))

        # 3. HATAYI BUL VE GÜNCELLE
        loss = F.mse_loss(current_q, target_q)

        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()

    def update_epsilon(self):
        """Keşfetme oranını düşür"""
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay
