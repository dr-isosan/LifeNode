# src/ai/agent.py
import torch
import torch.optim as optim
import torch.nn.functional as F
import numpy as np
import random
from collections import deque
from .model import DQN


class DQNAgent:
    def __init__(self, state_dim, action_dim, lr=1e-3, gamma=0.99, buffer_size=10000):
        # HİPERPARAMETRELER
        self.gamma = gamma  # Geleceğe ne kadar önem veriyoruz? (0.99 = çok)
        self.epsilon = 1.0  # Keşfetme oranı (Başta %100 rastgele)
        self.epsilon_min = 0.01  # En az %1 rastgele kal
        self.epsilon_decay = 0.995  # Her bölümde epsilon ne kadar azalsın?
        self.batch_size = 64  # Bir kerede kaç anıdan ders çıkaralım?
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        # MODELLER (Çift ağ kullanıyoruz: Biri öğrenir, diğeri hedef gösterir)
        self.policy_net = DQN(state_dim, action_dim).to(self.device)
        self.target_net = DQN(state_dim, action_dim).to(self.device)

        # Hedef ağı, ana ağ ile eşitle (Başlangıçta aynı olsunlar)
        self.target_net.load_state_dict(self.policy_net.state_dict())
        self.target_net.eval()  # Hedef ağ eğitim yapmaz, sabittir.

        # OPTİMİZASYON (Adam algoritması standarttır)
        self.optimizer = optim.Adam(self.policy_net.parameters(), lr=lr)

        # HAFIZA (Deque: Dolunca eskileri otomatik siler)
        self.memory = deque(maxlen=buffer_size)

    def act(self, state):
        """
        Duruma göre hamle seç: Ya rastgele (Keşfet) ya da en iyisi (Sömür).
        """
        # Keşfetme zamanı (Epsilon şansı)
        if random.random() < self.epsilon:
            return random.randrange(
                self.policy_net.fc3.out_features
            )  # Rastgele aksiyon

        # Bildiğini okuma zamanı (Modeli kullan)
        state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)

        with torch.no_grad():  # Hesaplama yaparken gradyan tutma (Hızlandırır)
            q_values = self.policy_net(state_tensor)

        return np.argmax(
            q_values.cpu().data.numpy()
        )  # En yüksek Q değerine sahip indeksi ver

    def remember(self, state, action, reward, next_state, done):
        """
        Yaşanan deneyimi hafızaya at.
        """
        self.memory.append((state, action, reward, next_state, done))

    def learn(self):
        """
        Hafızadan rastgele anılar çekip modeli eğitir.
        """
        # Yeterince anı birikmediyse eğitim yapma
        if len(self.memory) < self.batch_size:
            return

        # 1. Rastgele bir "Batch" çek (Örn: 64 tane anı)
        batch = random.sample(self.memory, self.batch_size)

        # Verileri ayıkla ve Tensor'a çevir (Toplu işlem için)
        states, actions, rewards, next_states, dones = zip(*batch)

        states = torch.FloatTensor(np.array(states)).to(self.device)
        actions = torch.LongTensor(actions).unsqueeze(1).to(self.device)
        rewards = torch.FloatTensor(rewards).unsqueeze(1).to(self.device)
        next_states = torch.FloatTensor(np.array(next_states)).to(self.device)
        dones = torch.FloatTensor(dones).unsqueeze(1).to(self.device)

        # 2. Q-Değerlerini Hesapla
        # Şu anki durum için modelin tahmini:
        current_q = self.policy_net(states).gather(1, actions)

        # Gelecek durum için hedef ağın tahmini (Max Q):
        next_q = self.target_net(next_states).max(1)[0].detach().unsqueeze(1)

        # Bellman Denklemi: Hedef = Ödül + (Gelecek_Tahmini * Gamma)
        # Eğer oyun bittiyse (done), gelecek yoktur.
        target_q = rewards + (self.gamma * next_q * (1 - dones))

        # 3. Hatayı (Loss) Hesapla ve Geri Yay (Backpropagation)
        loss = F.mse_loss(current_q, target_q)

        self.optimizer.zero_grad()  # Önceki gradyanları temizle
        loss.backward()  # Hatayı geriye yay
        self.optimizer.step()  # Ağırlıkları güncelle

    def update_epsilon(self):
        """Keşfetme oranını azalt"""
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay
