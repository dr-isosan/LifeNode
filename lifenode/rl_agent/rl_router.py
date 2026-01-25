"""
RL Router (Düzeltilmiş Versiyon)

Q-Learning tabanlı yönlendirici.
Router arayüzünü uygular ve RL ajanını kullanarak routing kararları verir.

KRİTİK DÜZELTME: agent.update() artık her routing kararından sonra çağrılıyor.
"""

from typing import Optional, Dict, TYPE_CHECKING
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
        training_mode: bool = True,
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
            config=ql_config or QLearningConfig(), state_encoder=self.state_encoder
        )
        self.reward_calculator = RewardCalculator(reward_config)
        self.training_mode = training_mode

        # State builder (world atandığında oluşturulur)
        self._state_builder: Optional[StateBuilder] = None
        self._current_world: Optional["World"] = None

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
        self, current_node: str, destination: str, world: "World"
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

        # Kullanılabilir aksiyonlar (abstract indices: "0", "1", "2"...)
        # Komşular zaten hedefe uzaklığa göre sıralı (0 = en yakın)
        available_actions = [str(i) for i in range(len(state.neighbor_states))]

        # Aksiyon seç
        if not self.training_mode:
            q_values = self.agent.get_q_values(state)
            all_zero = all(
                q_values.get(action, 0.0) == 0.0 for action in available_actions
            )
            if not q_values or all_zero:
                # Bilinmeyen state: deterministik fallback (en yakın komşu)
                action_idx_str = "0"
            else:
                action_idx_str = self.agent.select_action(
                    state=state, available_actions=available_actions, explore=False
                )
        else:
            action_idx_str = self.agent.select_action(
                state=state, available_actions=available_actions, explore=True
            )

        if action_idx_str is None:
            return None

        self._decisions_made += 1

        # Abstract action -> Concrete Node ID
        action_idx = int(action_idx_str)
        if action_idx >= len(state.neighbor_states):
            return None

        next_hop = state.neighbor_states[action_idx].neighbor_id

        # Eğitim modunda state/action'ı kaydet
        if self.training_mode:
            pending_key = f"{current_node}_{destination}_{self._decisions_made}"
            self._pending_updates[pending_key] = PendingUpdate(
                state=state,
                action=action_idx_str,
                current_node=current_node,
                destination=destination,
            )

        return next_hop

    def on_packet_forwarded(self, packet: "Packet", next_hop: str):
        """Paket başarıyla iletildi - Q-update yap"""
        self._successful_forwards += 1

        if self._state_builder:
            current_node = packet.path[-2] if len(packet.path) >= 2 else packet.source
            self._state_builder.record_success(current_node, next_hop, True)

        if self.training_mode and self._current_world:
            # Ara ödül hesapla
            current_node = packet.path[-2] if len(packet.path) >= 2 else packet.source

            link = self._current_world.get_link(current_node, next_hop)
            neighbor = self._current_world.get_node(next_hop)

            # Döngü kontrolü
            is_loop = next_hop in packet.path[:-1] if len(packet.path) > 1 else False

            progress_ratio = None
            if self._current_world:
                current_node_obj = self._current_world.get_node(current_node)
                next_node_obj = self._current_world.get_node(next_hop)
                dest_node = self._current_world.get_node(packet.destination)

                if current_node_obj and next_node_obj and dest_node:
                    current_dist = current_node_obj.distance_to(dest_node)
                    next_dist = next_node_obj.distance_to(dest_node)
                    denom = current_dist if current_dist > 0 else 1.0
                    progress_ratio = (current_dist - next_dist) / denom

            reward = self.reward_calculator.calculate(
                event=RoutingEvent.FORWARDED,
                packet=packet,
                chosen_neighbor=neighbor,
                link=link,
                is_loop=is_loop,
                progress_ratio=progress_ratio,
            )

            # Q-Update
            self._do_q_update(packet, next_hop, reward, done=False)

    def on_packet_delivered(self, packet: "Packet"):
        """Paket hedefe ulaştı - büyük pozitif ödül ve Q-update"""
        if self.training_mode:
            reward = self.reward_calculator.calculate(
                event=RoutingEvent.DELIVERED,
                packet=packet,
            )
            # Terminal update - next_hop önemli değil çünkü done=True
            # Ancak _do_q_update için "hangi komşuyu seçmiştik" bilgisine ihtiyaç var (packet.destination)
            # Paket hedefe ulaştıysa son adım destination'dır.
            self._do_q_update(packet, packet.destination, reward, done=True)

    def on_packet_dropped(self, packet: "Packet"):
        """Paket kaybedildi - büyük negatif ödül ve Q-update"""
        self._failed_forwards += 1

        if self._state_builder and len(packet.path) >= 2:
            current_node = packet.path[-2]
            failed_hop = packet.path[
                -1
            ]  # Bu düğüme atıldı ve düştü (veya o düğümde düştü)
            self._state_builder.record_success(current_node, failed_hop, False)

        if self.training_mode:
            reward = self.reward_calculator.calculate(
                event=RoutingEvent.DROPPED,
                packet=packet,
            )

            # Packet nerede düştü?
            # Eğer path [A, B] ise ve B'de düştüyse, son karar A->B idi.
            # next_node burada "karar verilen düğüm" olmalı.
            last_hop = packet.path[-1] if packet.path else None
            self._do_q_update(packet, last_hop, reward, done=True)

    def _do_q_update(
        self, packet: "Packet", next_node: Optional[str], reward: float, done: bool
    ):
        """
        Q-table güncelleme (Abstract Actions ile)
        """
        if not self._current_world or not self._state_builder:
            return

        # Son yapılan kararı bul
        # Karar veren düğüm: path[-2] (veya source)
        # Seçilen düğüm: path[-1] (bu next_node ile aynı olmalı)

        if len(packet.path) < 1:
            return  # Henüz hop yok

        chosen_neighbor = packet.path[-1]
        current_node = packet.path[-2] if len(packet.path) >= 2 else packet.source

        # Önceki state'i RECONSTRUCT et
        prev_state = self._state_builder.build_state(current_node, packet.destination)
        if prev_state is None:
            return

        # Abstract Action'ı bul (chosen_neighbor kaçıncı sıradaydı?)
        action = None
        for i, ns in enumerate(prev_state.neighbor_states):
            if ns.neighbor_id == chosen_neighbor:
                action = str(i)
                break

        if action is None:
            return  # Komşu artık listede yok veya topoloji değişti

        # Sonraki state (eğer terminal değilse)
        next_state = None
        if not done and next_node:
            # next_node burada bir sonraki adımdaki current_node olur
            # Yani paket şu an next_node'da.
            next_state = self._state_builder.build_state(next_node, packet.destination)

        # Q-update
        self.agent.update(
            state=prev_state,
            action=action,
            reward=reward,
            next_state=next_state,
            done=done,
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
            "name": self.get_name(),
            "trainable": True,
            "training_mode": self.training_mode,
            "decisions_made": self._decisions_made,
            "successful_forwards": self._successful_forwards,
            "failed_forwards": self._failed_forwards,
            "q_updates": self._q_updates,
            "success_rate": (
                self._successful_forwards / self._decisions_made
                if self._decisions_made > 0
                else 0.0
            ),
            **agent_stats,
            **reward_stats,
        }
