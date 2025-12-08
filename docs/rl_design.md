# LifeNode - Reinforcement Learning Tasarımı

## 📋 Genel Bakış

**Kişi B (AI & Environment Architect)** tarafından tasarlanan Reinforcement Learning (RL) altyapısı, mesh network'te akıllı paket yönlendirme (intelligent routing) için DQN (Deep Q-Network) algoritmasını kullanır.

**Amaç**: Her düğümün, gelen bir paketi hangi komşusuna yönlendireceğine dair optimal kararlar almasını öğrenmek.

---

## 🏗️ AI Modül Yapısı

```
src/ai/
├── __init__.py
├── env.py              # RL Environment (Gymnasium tabanlı)
├── env_wrapper.py      # Environment sarmalayıcıları
├── agent.py            # DQN Agent implementasyonu
├── model.py            # Neural Network modeli
├── state_encoder.py    # State representation encoder
└── reward.py           # Reward fonksiyon sistemi
```

---

## 🔄 RL Environment (Gymnasium)

### `LifeNodeEnv` Sınıfı

**Dosya**: `src/ai/env.py`

Gymnasium API'sine uygun olarak tasarlanmış environment. Simülasyon ile AI arasındaki köprü görevini görür.

#### **Temel Özellikler**

```python
# Action Space: Komşu seçimi (Discrete)
action_space = Discrete(max_neighbors)  # 0-4 arası (5 komşu için)

# Observation Space: Normalize edilmiş state vektörü
observation_space = Box(low=0, high=1, shape=(state_dim,), dtype=float32)
```

#### **Ana Metodlar**

##### `reset(seed, options) → state, info`
Yeni bir episode başlatır. Paketi kaynak düğümde başlatır ve initial state döndürür.

**Dönen değerler:**
- `state`: Encode edilmiş durum vektörü (16 boyutlu)
- `info`: Ek bilgiler (debug için)

**Örnek kullanım:**
```python
env = LifeNodeEnv()
state, info = env.reset()
# state: [0.5, 0.8, 0.9, 0.2, ...] (16 float değer)
```

---

##### `step(action) → next_state, reward, done, truncated, info`
Agent'ın seçtiği aksiyonu (komşu seçimi) uygular ve sonuçları döndürür.

**Parametreler:**
- `action` (int): Seçilen komşunun indeksi (0-4)

**Dönen değerler:**
- `next_state`: Yeni durum vektörü
- `reward`: Ödül skoru (float)
- `done`: Episode bitti mi? (paket ulaştı/kayboldu)
- `truncated`: Zaman aşımı var mı?
- `info`: Ek bilgiler

**Akış:**
```
1. Paketi seçilen komşuya yönlendir
2. Simülasyonu 1 adım ilerlet
3. Reward hesapla
4. Yeni state oluştur
5. Terminal durumu kontrol et (done?)
```

**Örnek kullanım:**
```python
action = agent.act(state)  # Agent karar verir: 2 (komşu #2)
next_state, reward, done, truncated, info = env.step(action)

if done:
    print("Paket hedefe ulaştı!" if reward > 0 else "Paket kayboldu!")
```

---

## 🧠 State Representation (Durum Gösterimi)

### `StateEncoder` Sınıfı

**Dosya**: `src/ai/state_encoder.py`

Simülasyon dünyasındaki raw verileri (düğüm pozisyonları, komşu listesi, vb.) **normalize edilmiş sayısal vektöre** dönüştürür.

#### **State Vektör Yapısı**

```
State = [Hedefe_Uzaklık, Komşu1_Sinyal, Komşu1_Enerji, Komşu1_Kuyruk, ...]
        [    1 boyut   ,         3 boyut × 5 komşu = 15 boyut          ]

Toplam: 16 boyutlu vektör
```

#### **Özellik Detayları**

| Özellik                   | Açıklama                                 | Normalizasyon          | Değer Aralığı |
| ------------------------- | ---------------------------------------- | ---------------------- | ------------- |
| **Hedefe Uzaklık**        | Mevcut düğümün hedefe Euclidean mesafesi | `distance / 1000.0`    | [0.0, 1.0]    |
| **Komşu Sinyal Kalitesi** | RF sinyal gücü                           | RSSI → 0-1 arası       | [0.0, 1.0]    |
| **Komşu Enerji Seviyesi** | Batarya durumu                           | `battery / 100`        | [0.0, 1.0]    |
| **Komşu Kuyruk Doluluk**  | Paket buffer doluluk oranı               | `queue_len / capacity` | [0.0, 1.0]    |

#### **Padding Mekanizması**

Eğer bir düğümün 5'ten az komşusu varsa, eksik slotlar **dummy değerlerle** doldurulur:

```python
# Olmayan komşu için:
dummy_values = [0.0, 0.0, 1.0]  # Sinyal=0, Enerji=0, Kuyruk=Full
```

Bu sayede her state vektörü **sabit boyutlu** olur (Neural Network için gerekli).

#### **Örnek State**

```python
state = [
    0.45,      # Hedefe mesafe (normalize)
    0.85, 0.92, 0.1,   # Komşu 1: Güçlü sinyal, yüksek enerji, boş kuyruk
    0.62, 0.45, 0.6,   # Komşu 2: Orta sinyal, orta enerji, yarı dolu kuyruk
    0.0, 0.0, 1.0,     # Komşu 3: YOK (padding)
    0.0, 0.0, 1.0,     # Komşu 4: YOK (padding)
    0.0, 0.0, 1.0      # Komşu 5: YOK (padding)
]
```

---

## 🎁 Reward System (Ödül Fonksiyonu)

### `RewardSystem` Sınıfı

**Dosya**: `src/ai/reward.py`

Agent'ın davranışlarını şekillendiren ödül mekanizması. İyi kararlar ödüllendirilir, kötü kararlar cezalandırılır.

#### **Matematiksel Model**

```
R(s, a, s') = {
    +100                           if paket_hedefe_ulaştı
    -1                            if paket_kayboldu
    -5 - (1 - enerji) × 50        otherwise (yolculuk devam ediyor)
}
```

#### **Ödül Bileşenleri**

| Bileşen            | Değer  | Açıklama                        |
| ------------------ | ------ | ------------------------------- |
| **w_success**      | +100.0 | Paket başarıyla teslim edildi   |
| **w_failure**      | -1.0   | Paket kayboldu/timeout oldu     |
| **w_step_penalty** | -5.0   | Her hop için zaman cezası       |
| **w_energy**       | -50.0  | Enerji tüketim cezası katsayısı |

#### **Hesaplama Mantığı**

##### 1. Başarı Durumu (Terminal State)
```python
if success:
    return +100.0  # Maksimum ödül
```

##### 2. Başarısızlık Durumu (Terminal State)
```python
if failed:
    return -1.0  # Küçük ceza (Denemek iyidir)
```

##### 3. Devam Eden Durum (Intermediate State)
```python
# Zaman cezası (Hızlı olmayı teşvik eder)
step_reward = -5.0

# Enerji cezası (Düşük enerjili düğümleri seçmeyi cezalandırır)
energy_penalty = (1.0 - energy_level) * (-50.0)

# Toplam ödül
reward = step_reward + energy_penalty
```

**Örnek:**
- Komşu enerjisi **0.9** ise: `-5 - (0.1 × 50) = -10.0`
- Komşu enerjisi **0.2** ise: `-5 - (0.8 × 50) = -45.0`

#### **Tasarım Felsefesi**

1. **Hızlı teslim teşvik edilir**: Her adım -5 ceza
2. **Enerji dengesi önemli**: Düşük bataryalı düğümleri kullanmak maliyetli
3. **Başarı yüksek ödüllü**: Terminal başarı +100, diğer tüm cezaları telafi eder
4. **Başarısızlık cezası hafif**: Agent denemekten korkmamalı

---

## 🤖 DQN Agent

### `DQNAgent` Sınıfı

**Dosya**: `src/ai/agent.py`

Deep Q-Network algoritmasını uygulayan ana agent sınıfı.

#### **Hiperparametreler**

```python
lr = 1e-3              # Learning rate (Öğrenme hızı)
gamma = 0.99           # Discount factor (Geleceğe önem)
epsilon = 1.0          # Exploration rate (Başlangıç)
epsilon_min = 0.01     # Minimum exploration
epsilon_decay = 0.995  # Her episode'da epsilon çarpanı
buffer_size = 10000    # Replay memory kapasitesi
batch_size = 64        # Her eğitim adımında kullanılan sample sayısı
```

#### **Çift Ağ Mimarisi**

DQN'de **2 ayrı neural network** kullanılır:

1. **Policy Network** (`policy_net`): Sürekli eğitilen, aksiyon seçen ağ
2. **Target Network** (`target_net`): Sabit kalan, hedef Q-değerleri hesaplayan ağ

**Neden?** → Eğitim stabilitesi. Target network periyodik olarak güncellenir.

#### **Ana Metodlar**

##### `act(state) → action`
Epsilon-greedy strateji ile aksiyon seçer.

```python
if random() < epsilon:
    return random_action()  # Keşfet
else:
    return argmax(Q(state, a))  # En iyi bilinen aksiyonu seç
```

##### `remember(state, action, reward, next_state, done)`
Deneyimi replay buffer'a kaydeder.

```python
memory.append((s, a, r, s', done))
```

##### `learn()`
Replay buffer'dan batch çekerek ağı eğitir.

**Bellman Denklemi:**
```
Q(s, a) ← Q(s, a) + α[r + γ·max_a' Q(s', a') - Q(s, a)]
```

**PyTorch implementasyonu:**
```python
current_q = policy_net(states).gather(1, actions)
next_q = target_net(next_states).max(1)[0]
target_q = rewards + gamma * next_q * (1 - dones)

loss = MSE(current_q, target_q)
loss.backward()
optimizer.step()
```

##### `update_epsilon()`
Keşfetme oranını azaltır (exploitation'a geçiş).

```python
epsilon = max(epsilon_min, epsilon * epsilon_decay)
```

---

## 🧬 Neural Network Modeli

### `DQN` Sınıfı (Model)

**Dosya**: `src/ai/model.py`

3 katmanlı fully-connected neural network.

#### **Mimari**

```
Input Layer (16)  →  Hidden Layer 1 (64)  →  Hidden Layer 2 (64)  →  Output Layer (5)
                       [ReLU]                     [ReLU]                [Linear]
```

**Parametreler:**
- **Input**: State vektörü (16 boyut)
- **Output**: Q-değerleri (5 aksiyon için)

**Örnek çıktı:**
```python
Q_values = model(state)
# [0.23, 0.87, 0.45, 0.12, 0.34]
#   ↓     ↑     ↓     ↓     ↓
# Komşu 1'in en yüksek Q-değeri var → Seç!
```

#### **Aktivasyon Fonksiyonları**

- **ReLU** (Rectified Linear Unit): `f(x) = max(0, x)`
  - Avantaj: Hızlı öğrenme, gradient vanishing problemi yok
  - Gizli katmanlarda kullanılır

- **Linear** (Son katman): Ham Q-değerleri gerekli
  - Aktivasyon yok, çünkü Q-değerleri negatif olabilir

---

## 🔄 Eğitim Akışı (Training Loop)

```python
for episode in range(num_episodes):
    state, _ = env.reset()
    total_reward = 0

    while not done:
        # 1. Aksiyon seç (Epsilon-greedy)
        action = agent.act(state)

        # 2. Ortamda uygula
        next_state, reward, done, truncated, info = env.step(action)

        # 3. Deneyimi kaydet
        agent.remember(state, action, reward, next_state, done)

        # 4. Öğren (Replay buffer yeterliyse)
        agent.learn()

        # 5. State güncelle
        state = next_state
        total_reward += reward

    # Episode bitti
    agent.update_epsilon()
    print(f"Episode {episode}: Reward = {total_reward}, Epsilon = {agent.epsilon}")
```

---

## 📊 Beklenen Performans Metrikleri

### Eğitim Sırasında İzlenecek Metrikler

1. **Episode Reward**: Bölüm başına toplam ödül
   - Başlangıç: ~-100 (rastgele routing)
   - Hedef: +50-80 (akıllı routing)

2. **Success Rate**: Paketlerin teslim oranı
   - Başlangıç: %10-20
   - Hedef: %80-90

3. **Average Hop Count**: Ortalama sıçrama sayısı
   - Başlangıç: 15-20 hop
   - Hedef: 3-5 hop (optimal path)

4. **Epsilon Decay**: Keşfetme oranı
   - Başlangıç: 1.0 (tamamen rastgele)
   - Final: 0.01 (tamamen öğrenilmiş)

---

## 🔧 Entegrasyon Planı (Kişi A ile)

### Hafta 2+ Hedefleri

1. **Simülasyon-AI Köprüsü**
   - `Network` sınıfından gerçek düğüm verilerini çekme
   - Mock veriler yerine real-time state encoding

2. **Custom Callback Sistemi**
   - Her paket yönlendirmede agent'ı çağırma
   - `dummy_routing()` yerine `agent.act()` kullanımı

3. **Eğitim Pipeline'ı**
   - Otomatik test scenario üretimi
   - Batch training (1000+ episode)
   - Model checkpoint kaydetme

4. **Karşılaştırma Testleri**
   - Baseline: Rastgele routing
   - Baseline: Greedy (en yakın komşu)
   - DQN: Öğrenilmiş strateji

---

## 📚 Matematiksel Notasyon

### State Space
```
S ∈ ℝ^16  (16-boyutlu sürekli state uzayı)
```

### Action Space
```
A = {0, 1, 2, 3, 4}  (5 discrete aksiyon)
```

### Bellman Optimality Equation
```
Q*(s, a) = E[r + γ·max_a' Q*(s', a') | s, a]
```

### Loss Function (MSE)
```
L(θ) = E[(r + γ·max_a' Q(s', a'; θ⁻) - Q(s, a; θ))²]
```

Burada:
- `θ`: Policy network parametreleri
- `θ⁻`: Target network parametreleri (frozen)

---

## 🚀 Hızlı Başlangıç

### Environment Testi

```python
from src.ai.env import LifeNodeEnv

env = LifeNodeEnv()
state, _ = env.reset()

print(f"State boyutu: {len(state)}")  # 16
print(f"Action sayısı: {env.action_space.n}")  # 5

for _ in range(10):
    action = env.action_space.sample()  # Rastgele aksiyon
    next_state, reward, done, truncated, info = env.step(action)
    print(f"Action: {action}, Reward: {reward:.2f}, Done: {done}")
    if done:
        break
```

### Agent Eğitimi (Basitleştirilmiş)

```python
from src.ai.env import LifeNodeEnv
from src.ai.agent import DQNAgent

env = LifeNodeEnv()
agent = DQNAgent(state_dim=16, action_dim=5)

for episode in range(100):
    state, _ = env.reset()
    total_reward = 0

    while True:
        action = agent.act(state)
        next_state, reward, done, _, _ = env.step(action)

        agent.remember(state, action, reward, next_state, done)
        agent.learn()

        state = next_state
        total_reward += reward

        if done:
            break

    agent.update_epsilon()
    print(f"Episode {episode}: Reward = {total_reward:.2f}")
```

---

## 🎯 Sonuç

Bu RL tasarımı, LifeNode projesinin "akıllı yönlendirme" kısmını oluşturur. DQN algoritması sayesinde her düğüm, geçmiş deneyimlerden öğrenerek optimal routing kararları alabilecektir.

**Kişi A** ile entegre edildiğinde:
- Gerçek topoloji verileri kullanılacak
- Dinamik node failure senaryolarında test edilecek
- Performans metrikleri karşılaştırılacak

**Hafta 1 Tamamlanan Görevler:**
- ✅ Environment iskeleti (Gymnasium uyumlu)
- ✅ State representation (StateEncoder)
- ✅ Reward fonksiyonu (matematiksel model)
- ✅ DQN agent ve model implementasyonu
- ✅ RL tasarım dokümantasyonu

---

**Hazırlayan**: Kişi B (AI & Environment Architect)
**Tarih**: Hafta 1
**Versiyon**: 1.0
