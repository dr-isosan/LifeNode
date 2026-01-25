# LifeNode 🌐

**AI-Driven Dynamic Routing Simulation for Ad-Hoc Networks**

Afet koşullarında (deprem, sel, savaş, altyapı çöküşü) mesh network yönlendirmesini simüle eden ve Reinforcement Learning tabanlı routing ile klasik protokolleri karşılaştıran araştırma projesi.

## 🚀 Hızlı Başlangıç

```bash
# Sanal ortam oluştur
python3 -m venv venv
source venv/bin/activate

# Bağımlılıkları yükle
pip install -r requirements.txt

# İnteraktif CLI başlat (ÖNERİLEN)
python cli.py

# Veya komut satırından direkt
python -m lifenode.main --compare --episodes 20 --visualize
```

## 🖥️ İnteraktif CLI Kullanımı (Önerilen Yöntem)

```bash
python cli.py
```

### 📝 Kullanım Sırası (İlk Kez Kullanıcılar İçin)

#### **ADIM 1: Ayarları Kontrol Et** ⚙️

```
Ana Menü → [5] Ayarlar
```

- Düğüm sayısı (varsayılan: 40)
- Simülasyon adımı (varsayılan: 500)
- RL episode sayısı (varsayılan: 30)

#### **ADIM 2: RL Ajanını Eğit** 🧠

```
Ana Menü → [1] RL Eğitimi
```

- Eğitim parametrelerini gözden geçir
- "Eğitimi başlat?" → Evet
- İlerlemeyi izle (progress bar)
- Eğitim bitince modeli kaydet (önerilir)
- Dosya: `models/rl_model_YYYYMMDD_HHMMSS.pkl`

**Beklenen Süre:** ~5-10 dakika (30 episode için)

#### **ADIM 3: Karşılaştırma Yap** 🔬

```
Ana Menü → [2] Karşılaştırma
```

- Senaryoyu seç:
  - `[1]` Normal (Afetsiz) - RL performansını test et
  - `[3]` Deprem (Orta) - Adaptasyon yeteneğini gör
  - `[5]` Tüm Senaryolar - Kapsamlı analiz
- "RL Agent dahil edilsin mi?" → Evet
- "Kayıtlı model yüklensin mi?" → Evet (2. adımda kaydettiyseniz)
- Sonuçları kaydet → JSON dosyası oluşur

**Kazananı göreceksiniz:** 🏆

#### **ADIM 4: Grafikleri Görüntüle** 📊

```
Ana Menü → [3] Grafikler → [1] Kayıtlı sonuçları görselleştir
```

- 3. adımda oluşturulan JSON'u seç
- PDR, Latency, Hop grafikleri oluşturulur
- PNG dosyası kaydedilir: `results/comparison_chart_*.png`
- Grafiği görüntüle veya daha sonraya bırak

#### **ADIM 5 (Opsiyonel): Afet Testi** 🌋

```
Ana Menü → [4] Afet Simülasyonu
```

- Deprem şiddeti seç (Orta önerilir)
- RL Agent ekle (kaydedilmiş modeli yükle)
- Hangi algoritmanın afet koşullarında daha iyi olduğunu gör

### 🎯 Hızlı Senaryo Önerileri

**🔰 Yeni Başlayanlar (10 dakika)**

```
1. [5] Ayarlar → Episode=10, Adım=300 (hızlı test)
2. [1] RL Eğitimi → Modeli kaydet
3. [2] Karşılaştırma → Normal senaryo
4. [3] Grafikler → Sonucu görselleştir
```

**🎓 Araştırmacılar (30 dakika)**

```
1. [5] Ayarlar → Episode=50, Adım=500 (detaylı)
2. [1] RL Eğitimi → Learning rate=0.1, Epsilon=0.3
3. [2] Karşılaştırma → Tüm senaryolar
4. [3] Grafikler → Karşılaştırmalı analiz
5. [4] Afet → Şiddetli deprem testi
```

**🚀 Performans Testi (1 saat)**

```
1. [5] Ayarlar → Episode=100, Düğüm=50
2. [1] RL Eğitimi → Uzun eğitim
3. [2] Karşılaştırma → Her senaryo için ayrı ayrı
4. [6] Sonuçlar → Tüm JSON dosyalarını karşılaştır
```

### 💡 İpuçları

- **İlk çalıştırma:** Küçük parametre değerleriyle başlayın (Episode=10)
- **Model yeniden kullanımı:** Eğitilmiş modeli saklayın, her seferinde eğitmeyin
- **Grafik karşılaştırma:** Her test sonrası JSON kaydedin, sonra toplu görselleştir
- **Afet testleri:** Önce "Normal" senaryoda test edin, sonra afet ekleyin
- **Parametre tuning:** Ayarlar menüsünden learning rate ve epsilon'u optimize edin

### 📁 Çıktı Dosyaları

```
results/
├── comparison_20260121_143022.json      # Karşılaştırma sonuçları
├── comparison_chart_20260121_143045.png # Grafik
└── experiment_results_*.json            # Detaylı sonuçlar

models/
└── rl_model_20260121_142500.pkl        # Eğitilmiş RL modeli
```

## 📁 Proje Yapısı

```
lifenode/
├── config.py           # Simülasyon yapılandırması
├── main.py             # Ana giriş noktası
├── environment/        # Simülasyon ortamı
│   ├── node.py        # Düğüm modeli
│   ├── link.py        # Bağlantı modeli
│   ├── packet.py      # Paket modeli
│   ├── world.py       # Simülasyon motoru
│   └── traffic.py     # Trafik üreteci
├── routing/            # Yönlendirme protokolleri
│   ├── base.py        # Soyut arayüz
│   └── dijkstra.py    # Baseline (en kısa yol)
├── rl_agent/           # Reinforcement Learning
│   ├── state.py       # Durum temsili
│   ├── reward.py      # Ödül fonksiyonu
│   ├── qlearning.py   # Q-Learning ajanı
│   └── rl_router.py   # RL tabanlı router
├── metrics/            # Performans ölçümü
│   ├── collector.py   # Metrik toplama
│   ├── analyzer.py    # İstatistik analizi
│   └── visualizer.py  # Grafik oluşturma
└── experiments/        # Deney çalıştırma
    └── runner.py      # Deney yönetimi
```

## 🎮 Komut Satırı Kullanımı (Alternatif)

> 💡 İnteraktif CLI daha kolay olsa da, script otomasyonu için komut satırı kullanabilirsiniz.

### Temel Simülasyon

```bash
# 30 düğüm, 500 adım
python -m lifenode.main

# Özelleştirilmiş
python -m lifenode.main --nodes 50 --steps 1000 --seed 123
```

### RL Eğitimi

```bash
# 20 episode eğitim
python -m lifenode.main --train --episodes 20

# Modeli kaydet
python -m lifenode.main --train --episodes 50 --save-model models/rl_agent.pkl
```

### Karşılaştırma

```bash
# Dijkstra vs RL karşılaştırması
python -m lifenode.main --compare --episodes 20

# Görselleştirme ile
python -m lifenode.main --compare --visualize --save-plots results/
```

### Afet Senaryosu

```bash
# Rastgele düğüm arızaları
python -m lifenode.main --failures --failure-rate 0.02
```

### Kapsamlı Deney

```bash
# Tüm senaryoları test et
python run_experiments.py
```

## 📊 Metrikler

- **PDR (Packet Delivery Ratio)**: Başarıyla teslim edilen paket oranı
- **Latency**: Uçtan uca gecikme (ms)
- **Hop Count**: Ortalama atlama sayısı
- **Recovery Time**: Arıza sonrası kurtarma süresi

## 🧠 RL Ajanı

- **Algoritma**: Tabular Q-Learning
- **State Space**: Enerji, kuyruk, komşu kalitesi
- **Action Space**: Sonraki hop seçimi
- **Reward**: Teslimat (+10), Kayıp (-10), Hop cezası (-0.1)

## 🔧 Yapılandırma

`config.py` dosyasından tüm parametreleri ayarlayabilirsiniz:

- Dünya boyutları ve düğüm sayısı
- Enerji tüketim oranları
- Sinyal kalitesi modeli
- RL hiperparametreleri
- Görselleştirme ayarları

## 📈 Sonuçlar

Tipik bir karşılaştırma sonucu:

| Router   | PDR | Latency | Hops |
| -------- | --- | ------- | ---- |
| Dijkstra | 85% | 12ms    | 3.2  |
| RL-Q     | 82% | 15ms    | 3.5  |

> RL ajanı dinamik senaryolarda daha iyi performans gösterebilir.

## 🛠️ Geliştirme

```bash
# Testleri çalıştır
python -m pytest tests/ -v

# Coverage raporu
python -m pytest tests/ --cov=lifenode
```
