# LifeNode - Proje Mimarisi

## 📋 Proje Özeti

**LifeNode**, afet durumlarında altyapı çöktüğünde cihazların mesh network (düğüm ağı) oluşturarak birbirleriyle iletişim kurmasını simüle eden bir projedir. İlk haftada temel ağ simülasyonu ve görselleştirme yapısı kurulmuştur.

**Roller:**
- **Kişi A (Network & Simulation Architect)**: Ağ simülasyonu, topoloji, paket yönlendirme
- **Kişi B (AI Architect)**: Reinforcement Learning, DQN agent, akıllı routing

## 🏗️ Proje Yapısı

```
LifeNode/
│
├── simulation/              # Ağ simülasyon modülü
│   ├── __init__.py
│   ├── node.py             # Düğüm sınıfı
│   ├── topology.py         # Topoloji üretici (RGG)
│   └── network.py          # Ağ yönetici sınıfı
│
├── visualization/           # Görselleştirme modülü
│   ├── __init__.py
│   └── plot_utils.py       # Matplotlib görselleştirme
│
├── ai/                     # AI modülü (Hafta 2+)
│   └── (gelecekte eklenecek)
│
├── docs/                   # Dokümantasyon
│   └── architecture.md     # Bu dosya
│
├── main.py                 # Ana çalıştırma dosyası
├── requirements.txt        # Python bağımlılıkları
└── .gitignore             # Git ignore kuralları
```

## 📦 Modüller ve Sınıflar

### 1. `simulation/node.py` - Node Sınıfı

**Amaç**: Ağdaki tek bir düğümü (cihazı) temsil eder.

**Özellikler:**
- `id`: Benzersiz düğüm kimliği
- `position`: (x, y) koordinatları
- `is_active`: Düğüm durumu (aktif/pasif)
- `buffer`: Paket kuyruğu
- `neighbors`: Komşu düğüm ID listesi
- `energy`: Enerji seviyesi (0-100)

**Metodlar:**
- `send_packet()`: Paket gönderme
- `receive_packet()`: Paket alma
- `fail()`: Düğümü arızalı yap
- `repair()`: Düğümü tamir et
- `add_neighbor()`: Komşu ekle
- `remove_neighbor()`: Komşu çıkar
- `get_status()`: Durum bilgilerini al

**Kullanım Örneği:**
```python
from simulation.node import Node

node = Node(1, (10.0, 20.0))
node.add_neighbor(2)
node.send_packet("Hello", neighbor_id=2)
```

---

### 2. `simulation/topology.py` - TopologyGenerator Sınıfı

**Amaç**: Random Geometric Graph (RGG) topolojisi oluşturur.

**Özellikler:**
- `width`, `height`: Alan boyutları

**Metodlar:**
- `calculate_distance()`: İki nokta arası Euclidean mesafe
- `generate_random_positions()`: N düğüm için rastgele pozisyonlar
- `find_neighbors_within_range()`: İletişim menzili içindeki komşuları bul
- `create_networkx_graph()`: NetworkX graf objesi oluştur
- `create_random_topology()`: Ana topoloji üretim fonksiyonu
- `get_topology_stats()`: Topoloji istatistikleri

**RGG Algoritması:**
1. N adet düğümü alana rastgele yerleştir
2. Her düğüm çifti için mesafe hesapla
3. Mesafe ≤ R ise düğümleri birbirine bağla

**Kullanım Örneği:**
```python
from simulation.topology import TopologyGenerator

topo = TopologyGenerator(width=100, height=100)
nodes, graph = topo.create_random_topology(num_nodes=20, communication_range=25)
```

---

### 3. `simulation/network.py` - Network Sınıfı

**Amaç**: Ağın tamamını yöneten ana sınıf.

**Özellikler:**
- `nodes`: {node_id: Node} dictionary
- `graph`: NetworkX graf objesi
- `simulation_time`: Simülasyon zamanı
- `packet_counter`: Toplam paket sayacı
- `delivered_packets`: Teslim edilen paketler
- `lost_packets`: Kaybolan paketler

**Metodlar:**
- `create_network()`: Yeni ağ oluştur
- `add_node()`: Düğüm ekle
- `remove_node()`: Düğüm çıkar
- `simulate_node_failure()`: Rastgele düğüm arızası simüle et
- `dummy_routing()`: Basit paket yönlendirme
- `send_packet()`: Paket gönderme simülasyonu
- `step()`: Simülasyon adımı
- `get_network_stats()`: Ağ istatistikleri

**Dummy Routing Stratejisi:**
- %70 ihtimalle rastgele komşu seç
- %30 ihtimalle hedefe en yakın komşuyu seç
- Döngü önleme: Zaten geçilen düğümlere gitme

**Kullanım Örneği:**
```python
from simulation.network import Network

network = Network(width=100, height=100)
network.create_network(num_nodes=20, communication_range=25)
network.send_packet(source_id=0, destination_id=5)
network.step(failure_rate=0.05)
```

---

### 4. `visualization/plot_utils.py` - NetworkVisualizer Sınıfı

**Amaç**: Ağı görselleştirme ve animasyon.

**Metodlar:**
- `plot_network()`: Statik ağ görselleştirmesi
- `plot_packet_path()`: Paket yolunu göster
- `animate_simulation()`: Animasyon oluştur

**Renk Kodları:**
- 🟢 Yeşil: Aktif düğüm
- 🔴 Kırmızı: Pasif/Arızalı düğüm
- 🔵 Mavi: Paket yolundaki ara düğümler
- 🟠 Turuncu: Paket yolu bağlantıları

**Kullanım Örneği:**
```python
from visualization.plot_utils import NetworkVisualizer

visualizer = NetworkVisualizer(figsize=(14, 12))
visualizer.plot_network(network, title="LifeNode Ağı")
visualizer.plot_packet_path(network, [0, 3, 5, 9])
```

---

### 5. `main.py` - Ana Simülasyon

**Amaç**: Tüm bileşenleri birleştiren ana program.

**Modlar:**
- Normal mod: `python main.py` (görselleştirme ile)
- Hızlı test: `python main.py --quick` (görselleştirme yok)

**Simülasyon Akışı:**
1. Parametreleri ayarla
2. Network oluştur
3. Test paketleri gönder
4. N adım simülasyon çalıştır
5. İstatistikleri göster
6. Görselleştir

---

## 🔧 Teknolojiler ve Kütüphaneler

### Temel Kütüphaneler
- **Python 3.13+**: Ana programlama dili
- **NetworkX**: Graf/topoloji yönetimi
- **Matplotlib**: Görselleştirme
- **NumPy**: Sayısal hesaplamalar

### AI Kütüphaneleri (Hafta 2+)
- **PyTorch**: Derin öğrenme framework
- **PyTorch Geometric**: Graf neural networks
- **Gymnasium**: RL environment
- **Stable-Baselines3**: RL algoritmaları

---

## 📊 Simülasyon Metrikleri

### Ağ Metrikleri
- **Toplam düğüm sayısı**: Ağdaki tüm düğümler
- **Aktif düğüm sayısı**: Çalışır durumdaki düğümler
- **Toplam bağlantı**: Graf kenar sayısı
- **Ortalama komşu sayısı**: Düğüm başına ortalama bağlantı
- **Ağ bağlantılılığı**: Tüm düğümler birbirine ulaşabiliyor mu?

### Paket Metrikleri
- **Toplam paket**: Gönderilen tüm paketler
- **Teslim edilen paket**: Hedefe ulaşan paketler
- **Kayıp paket**: Hedefe ulaşamayan paketler
- **Başarı oranı**: Teslim edilen / Toplam paket

### Node Failure Modeli
- Her adımda her düğüm için arıza şansı (%2-10)
- Arızalı düğümler tamirde şansla (%50) tekrar aktif olabilir
- Afet ortamındaki kaotik durumu simüle eder

---

## 🎯 İlk Hafta Başarıları

### ✅ Tamamlanan Görevler

1. **Node Sınıfı**: Düğüm özellikleri ve metodları ✓
2. **Topoloji Üretici**: RGG algoritması ✓
3. **Ağ Yöneticisi**: Ağ yönetimi ve dummy routing ✓
4. **Görselleştirme**: Matplotlib ile çizim ✓
5. **Ana Simülasyon**: Tüm entegrasyon ✓
6. **Dokümantasyon**: Mimari açıklaması ✓

### 🧪 Test Sonuçları

**Test Senaryosu: 10 düğümlü ağ**
```
- Düğüm sayısı: 10
- İletişim menzili: 20.0
- Bağlantı sayısı: 16
- Ağ bağlantılı: ✓
- Paket başarı oranı: %100
```

---

## 🚀 Gelecek Adımlar (Hafta 2+)

### Hafta 2: AI Environment Hazırlığı (Kişi B)
- Gymnasium environment sınıfı
- State space tanımı
- Action space tanımı
- Reward fonksiyonu

### Hafta 3: DQN Agent (Kişi B)
- Neural network modeli
- Experience replay
- Training loop
- Hyperparameter tuning

### Hafta 4: Entegrasyon ve Karşılaştırma
- RL agent'ı ağa entegre et
- Dummy routing vs RL routing karşılaştırması
- Performans grafikleri
- Final raporu

---

## 📖 Kullanım Kılavuzu

### Kurulum

```bash
# Repository'yi klonla
git clone https://github.com/dr-isosan/LifeNode.git
cd LifeNode

# Virtual environment oluştur (opsiyonel)
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# Bağımlılıkları yükle
pip install -r requirements.txt
```

### Çalıştırma

```bash
# Normal mod (görselleştirme ile)
python main.py

# Hızlı test modu
python main.py --quick

# Node testi
python simulation/node.py

# Topology testi
python simulation/topology.py

# Network testi
python simulation/network.py
```

### Parametreleri Değiştirme

`main.py` içindeki parametreleri düzenle:
```python
NUM_NODES = 20              # Düğüm sayısı
COMMUNICATION_RANGE = 25.0  # İletişim menzili
AREA_WIDTH = 100.0          # Alan genişliği
AREA_HEIGHT = 100.0         # Alan yüksekliği
NODE_FAILURE_RATE = 0.05    # Node arıza oranı (%5)
```

---

## 🤝 Katkıda Bulunanlar

- **Kişi A**: Network & Simulation Architect
  - Ağ simülasyonu
  - Topoloji üretimi
  - Görselleştirme

- **Kişi B**: AI Architect
  - RL environment (gelecek)
  - DQN agent (gelecek)
  - Model eğitimi (gelecek)

---

## 📝 Lisans ve Referanslar

Bu proje eğitim amaçlıdır ve açık kaynak olarak paylaşılmaktadır.

**Referanslar:**
- NetworkX Documentation
- Matplotlib Documentation
- Reinforcement Learning: An Introduction (Sutton & Barto)
- Mesh Network Protocols (AODV, OLSR)

---

**Son Güncelleme**: 5 Aralık 2025  
**Versiyon**: 1.0 (İlk Hafta)