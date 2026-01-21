"""
RL Router (Düzeltilmiş Versiyon)

Q-Learning tabanlı yönlendirici.
Router arayüzünü uygular ve RL ajanını kullanarak routing kararları verir.

KRİTİK DÜZELTME: agent.update() artık her routing kararından sonra çağrılıyor.
"""

from typing import Optional, List, Dict, Tuple, TYPE_CHECKING
from dataclasses import dataclass

from ..routing.base import Router, TopologyEvent
from .state import RoutingState, StateEncoder, StateBuilder
from .reward import RewardCalculator, RewardConfig, RoutingEvent
from .qlearning import QLearningAgent, QLearningConfig

if TYPE_CHECKING:
    from ..environment.world import World
    from ..environment.packet import Packet


@dataclass
class PendingUpdate:
    """Bekleyen Q-update bilgisi"""
    state: RoutingState
    action: str
    current_node: str
    destination: str


class RLRouter(Router):
    """
    Reinforcement Learning Router (Düzeltilmiş)

    Q-Learning ajanı kullanarak sonraki hop kararları verir.
    Her routing kararından sonra Q-table güncellenir.
    """

    def __init__(
        self,
        ql_config: Optional[QLearningConfig] = None,
        reward_config: Optional[RewardConfig] = None,
        training_mode: bool = True
    ):
        """
        Args:
            ql_config: Q-Learning yapılandırması
            reward_config: Ödül yapılandırması
            training_mode: Eğitim modu (True = exploration aktif)
        """
        self.state_encoder = StateEncoder(
            max_neighbors=10,
            energy_bins=5,
            queue_bins=3,
            quality_bins=5,
        )
        self.agent = QLearningAgent(
            config=ql_config or QLearningConfig(),
            state_encoder=self.state_encoder
        )
        self.reward_calculator = RewardCalculator(reward_config)
        self.training_mode = training_mode

        # State builder (world atandığında oluşturulur)
        self._state_builder: Optional[StateBuilder] = None
        self._current_world: Optional['World'] = None

        # Bekleyen Q-updates (packet_id -> PendingUpdate)
        self._pending_updates: Dict[str, PendingUpdate] = {}

        # İstatistikler
        self._decisions_made: int = 0
        self._successful_forwards: int = 0
        self._failed_forwards: int = 0
        self._q_updates: int = 0

    def get_name(self) -> str:
        return "RL-Q"

    def is_trainable(self) -> bool:
        return True

    def get_next_hop(
        self,
        current_node: str,
        destination: str,
        world: 'World'
    ) -> Optional[str]:
        """
        RL ajanı ile sonraki hop seç

        Args:
            current_node: Mevcut düğüm
            destination: Hedef düğüm
            world: Simülasyon dünyası

        Returns:
            Sonraki hop düğüm ID'si veya None
        """
        # State builder'ı güncelle
        if self._state_builder is None or self._current_world != world:
            self._state_builder = StateBuilder(world)
            self._current_world = world

        # State oluştur
        state = self._state_builder.build_state(current_node, destination)
        if state is None or not state.has_neighbors:
            return None

        # Kullanılabilir aksiyonlar (komşular)
        available_actions = [ns.neighbor_id for ns in state.neighbor_states]

        # Aksiyon seç
        action = self.agent.select_action(
            state=state,
            available_actions=available_actions,
            explore=self.training_mode
        )

        if action is None:
            return None

        self._decisions_made += 1

        # Eğitim modunda state/action'ı kaydet (sonraki update için)
        if self.training_mode:
            # packet_id yerine benzersiz key oluştur
            pending_key = f"{current_node}_{destination}_{self._decisions_made}"
            self._pending_updates[pending_key] = PendingUpdate(
                state=state,
                action=action,
                current_node=current_node,
                destination=destination,
            )

        return action

    def on_packet_forwarded(self, packet: 'Packet', next_hop: str):
        """Paket başarıyla iletildi - Q-update yap"""
        self._successful_forwards += 1

        if self._state_builder:
            current_node = packet.path[-2] if len(packet.path) >= 2 else packet.source
            self._state_builder.record_success(current_node, next_hop, True)

        if self.training_mode and self._current_world:
            # Ara ödül hesapla
            link = self._current_world.get_link(
                packet.path[-2] if len(packet.path) >= 2 else packet.source,
                next_hop
            )
            neighbor = self._current_world.get_node(next_hop)

            # Döngü kontrolü
            is_loop = next_hop in packet.path[:-1] if len(packet.path) > 1 else False

            reward = self.reward_calculator.calculate(
                event=RoutingEvent.FORWARDED,
                packet=packet,
                chosen_neighbor=neighbor,
                link=link,
                is_loop=is_loop,
            )

            # Q-Update: mevcut state'den next_hop state'e geçiş
            self._do_q_update(packet, next_hop, reward, done=False)

    def on_packet_delivered(self, packet: 'Packet'):
        """Paket hedefe ulaştı - büyük pozitif ödül ve Q-update"""
        if self.training_mode:
            reward = self.reward_calculator.calculate(
                event=RoutingEvent.DELIVERED,
                packet=packet,
            )

            # Son hop için Q-update (terminal state)
            self._do_q_update(packet, packet.destination, reward, done=True)

    def on_packet_dropped(self, packet: 'Packet'):
        """Paket kaybedildi - büyük negatif ödül ve Q-update"""
        self._failed_forwards += 1

        if self._state_builder and len(packet.path) >= 2:
            current_node = packet.path[-2]
            failed_hop = packet.path[-1]
            self._state_builder.record_success(current_node, failed_hop, False)

        if self.training_mode:
            reward = self.reward_calculator.calculate(
                event=RoutingEvent.DROPPED,
                packet=packet,
            )

            # Terminal state (paket kayboldu)
            self._do_q_update(packet, None, reward, done=True)

    def _do_q_update(
        self,
        packet: 'Packet',
        next_node: Optional[str],
        reward: float,
        done: bool
    ):
        """
        Q-table güncelleme

        Bellman equation: Q(s,a) = Q(s,a) + α * (r + γ * max(Q(s',a')) - Q(s,a))
        """
        if not self._current_world or not self._state_builder:
            return

        # Son yapılan kararı bul
        current_node = packet.path[-2] if len(packet.path) >= 2 else packet.source
        action = packet.path[-1] if len(packet.path) >= 1 else None

        if action is None:
            return

        # Önceki state'i oluştur (mevcut düğümden)
        prev_state = self._state_builder.build_state(current_node, packet.destination)
        if prev_state is None:
            return

        # Sonraki state (eğer terminal değilse)
        next_state = None
        if not done and next_node:
            next_state = self._state_builder.build_state(next_node, packet.destination)

        # Q-update
        self.agent.update(
            state=prev_state,
            action=action,
            reward=reward,
            next_state=next_state,
            done=done
        )

        self._q_updates += 1

    def on_topology_change(self, event: TopologyEvent):
        """Topoloji değişti"""
        pass

    # =========================================================================
    # EĞİTİM
    # =========================================================================

    def set_training_mode(self, mode: bool):
        """Eğitim modunu ayarla"""
        self.training_mode = mode

    def end_episode(self):
        """Episode sonunda çağrılır"""
        self.agent.decay_epsilon()
        self._pending_updates.clear()

    def train_step(self):
        """Bir eğitim adımı"""
        self.end_episode()

    def save_model(self, path: str):
        """Modeli kaydet"""
        self.agent.save(path)

    def load_model(self, path: str):
        """Modeli yükle"""
        self.agent.load(path)
        self.training_mode = False

    # =========================================================================
    # SIFIRLAMA VE İSTATİSTİKLER
    # =========================================================================

    def reset(self):
        """Router'ı sıfırla (Q-table korunur)"""
        self._pending_updates.clear()
        self._decisions_made = 0
        self._successful_forwards = 0
        self._failed_forwards = 0
        # Q-updates sayısını SIFIRLAMA (toplam takip için)

        if self._state_builder:
            self._state_builder.reset()

        self.reward_calculator.reset()

    def get_stats(self) -> dict:
        """İstatistikleri döndür"""
        agent_stats = self.agent.get_stats()
        reward_stats = self.reward_calculator.get_stats()

        return {
            'name': self.get_name(),
            'trainable': True,
            'training_mode': self.training_mode,
            'decisions_made': self._decisions_made,
            'successful_forwards': self._successful_forwards,
            'failed_forwards': self._failed_forwards,
            'q_updates': self._q_updates,
            'success_rate': (
                self._successful_forwards / self._decisions_made
                if self._decisions_made > 0 else 0.0
            ),
            **agent_stats,
            **reward_stats,
        }
