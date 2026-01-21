"""
Q-Learning Agent

Tabular Q-Learning implementasyonu.
State-action çiftleri için Q değerlerini öğrenir.
"""

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
import random
import json
import pickle

from .state import RoutingState, StateEncoder


@dataclass
class QLearningConfig:
    """Q-Learning yapılandırması"""

    learning_rate: float = 0.1          # α (alpha)
    discount_factor: float = 0.95       # γ (gamma)
    epsilon_start: float = 1.0          # Başlangıç exploration oranı
    epsilon_end: float = 0.01           # Minimum exploration oranı
    epsilon_decay: float = 0.995        # Her episode sonrası decay


class QLearningAgent:
    """
    Tabular Q-Learning Agent

    Discrete state space için Q-table kullanır.

    Attributes:
        config: Q-Learning yapılandırması
        epsilon: Mevcut exploration oranı
        q_table: State-action Q değerleri
    """

    def __init__(
        self,
        config: Optional[QLearningConfig] = None,
        state_encoder: Optional[StateEncoder] = None
    ):
        """
        Args:
            config: Q-Learning yapılandırması
            state_encoder: State encoder (discretization için)
        """
        self.config = config or QLearningConfig()
        self.state_encoder = state_encoder or StateEncoder()

        # Exploration oranı
        self.epsilon = self.config.epsilon_start

        # Q-Table: state_key -> {action: q_value}
        self.q_table: Dict[Tuple, Dict[str, float]] = defaultdict(
            lambda: defaultdict(float)
        )

        # İstatistikler
        self._episode_count: int = 0
        self._step_count: int = 0
        self._exploration_count: int = 0
        self._exploitation_count: int = 0

    def select_action(
        self,
        state: RoutingState,
        available_actions: List[str],
        explore: bool = True
    ) -> Optional[str]:
        """
        Epsilon-greedy action selection

        Args:
            state: Mevcut durum
            available_actions: Kullanılabilir aksiyonlar (komşu ID'leri)
            explore: Exploration yapılsın mı?

        Returns:
            Seçilen aksiyon (komşu ID) veya None
        """
        if not available_actions:
            return None

        self._step_count += 1

        # Exploration vs Exploitation
        if explore and random.random() < self.epsilon:
            self._exploration_count += 1
            return random.choice(available_actions)

        self._exploitation_count += 1

        # Greedy seçim (en yüksek Q değeri)
        state_key = self.state_encoder.discretize(state)
        q_values = self.q_table[state_key]

        # Kullanılabilir aksiyonlar arasından en iyisini seç
        best_action = None
        best_value = float('-inf')

        for action in available_actions:
            q_value = q_values[action]
            if q_value > best_value:
                best_value = q_value
                best_action = action

        # Eğer tüm Q değerleri 0 ise (yeni state), rastgele seç
        if best_value == 0.0:
            return random.choice(available_actions)

        return best_action

    def update(
        self,
        state: RoutingState,
        action: str,
        reward: float,
        next_state: Optional[RoutingState],
        done: bool
    ):
        """
        Q-value güncelleme (Bellman equation)

        Q(s,a) = Q(s,a) + α * (r + γ * max(Q(s',a')) - Q(s,a))

        Args:
            state: Mevcut durum
            action: Alınan aksiyon
            reward: Alınan ödül
            next_state: Sonraki durum (None ise terminal)
            done: Episode bitti mi?
        """
        state_key = self.state_encoder.discretize(state)

        # Mevcut Q değeri
        current_q = self.q_table[state_key][action]

        # Hedef Q değeri
        if done or next_state is None:
            # Terminal state
            target_q = reward
        else:
            # Max Q değeri sonraki state için
            next_state_key = self.state_encoder.discretize(next_state)
            next_q_values = self.q_table[next_state_key]

            if next_q_values:
                max_next_q = max(next_q_values.values()) if next_q_values.values() else 0.0
            else:
                max_next_q = 0.0

            target_q = reward + self.config.discount_factor * max_next_q

        # Q değeri güncelleme
        self.q_table[state_key][action] = current_q + self.config.learning_rate * (target_q - current_q)

    def decay_epsilon(self):
        """Episode sonunda epsilon'u azalt"""
        self._episode_count += 1
        self.epsilon = max(
            self.config.epsilon_end,
            self.epsilon * self.config.epsilon_decay
        )

    def reset_episode(self):
        """Yeni episode başlat (epsilon decay)"""
        self.decay_epsilon()

    # =========================================================================
    # KAYIT / YÜKLEME
    # =========================================================================

    def save(self, path: str):
        """
        Q-table'ı dosyaya kaydet

        Args:
            path: Kayıt yolu
        """
        data = {
            'q_table': dict(self.q_table),
            'epsilon': self.epsilon,
            'episode_count': self._episode_count,
            'step_count': self._step_count,
            'config': {
                'learning_rate': self.config.learning_rate,
                'discount_factor': self.config.discount_factor,
                'epsilon_start': self.config.epsilon_start,
                'epsilon_end': self.config.epsilon_end,
                'epsilon_decay': self.config.epsilon_decay,
            }
        }

        with open(path, 'wb') as f:
            pickle.dump(data, f)

    def load(self, path: str):
        """
        Q-table'ı dosyadan yükle

        Args:
            path: Yükleme yolu
        """
        with open(path, 'rb') as f:
            data = pickle.load(f)

        self.q_table = defaultdict(lambda: defaultdict(float))
        for state_key, actions in data['q_table'].items():
            self.q_table[state_key] = defaultdict(float, actions)

        self.epsilon = data.get('epsilon', self.config.epsilon_start)
        self._episode_count = data.get('episode_count', 0)
        self._step_count = data.get('step_count', 0)

    # =========================================================================
    # İSTATİSTİKLER
    # =========================================================================

    def get_stats(self) -> dict:
        """İstatistikleri döndür"""
        total_decisions = self._exploration_count + self._exploitation_count

        return {
            'epsilon': self.epsilon,
            'episode_count': self._episode_count,
            'step_count': self._step_count,
            'q_table_size': len(self.q_table),
            'total_decisions': total_decisions,
            'exploration_rate': self._exploration_count / total_decisions if total_decisions > 0 else 0.0,
            'exploitation_rate': self._exploitation_count / total_decisions if total_decisions > 0 else 0.0,
        }

    def get_q_values(self, state: RoutingState) -> Dict[str, float]:
        """
        Bir state için Q değerlerini döndür

        Args:
            state: Sorgulanacak state

        Returns:
            Action -> Q değeri sözlüğü
        """
        state_key = self.state_encoder.discretize(state)
        return dict(self.q_table[state_key])

    def reset(self):
        """Agent'ı sıfırla (Q-table dahil)"""
        self.q_table.clear()
        self.epsilon = self.config.epsilon_start
        self._episode_count = 0
        self._step_count = 0
        self._exploration_count = 0
        self._exploitation_count = 0

    def reset_stats(self):
        """Sadece istatistikleri sıfırla (Q-table korunur)"""
        self._step_count = 0
        self._exploration_count = 0
        self._exploitation_count = 0
