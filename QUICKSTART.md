# 🚀 Hızlı Başlangıç Rehberi

## 5 Dakikada LifeNode

### 1️⃣ Kurulum (1 dakika)

```bash
cd /home/dr_iso/ab
pip install -r requirements.txt
```

### 2️⃣ CLI'ı Başlat

```bash
python cli.py
```

### 3️⃣ İlk Test (4 dakika)

```
┌─────────────────────────────────────────┐
│          Ana Menü                       │
├─────────────────────────────────────────┤
│ [1] 🧠 RL Eğitimi                       │  ← BURADAN BAŞLA
│ [2] 🔬 Karşılaştırma                    │  ← SONRA BU
│ [3] 📊 Grafikler                        │  ← EN SON BU
│ [4] 🌋 Afet Simülasyonu                 │
│ [5] ⚙️  Ayarlar                          │
│ [6] 📁 Sonuçları Görüntüle              │
│ [0] 🚪 Çıkış                            │
└─────────────────────────────────────────┘
```

---

## 📝 Adım Adım İlk Kullanım

### ADIM 1: Hızlı Ayarlar (30 saniye)

**Ana Menü → [5] Ayarlar**

```
Episode Sayısı → 10        (test için)
Simülasyon Adımı → 300     (hızlı test)
```

**Enter** → **[0] Geri Dön**

---

### ADIM 2: RL Eğitimi (2 dakika)

**Ana Menü → [1] RL Eğitimi**

1. Parametreleri göreceksiniz
2. "Parametreleri değiştirmek ister misiniz?" → **n** (hayır)
3. "Eğitimi başlat?" → **y** (evet)
4. ✨ Progress bar ile eğitimi izleyin:

```
⠙ Episode 5/10 | PDR: 32.1% | Best: 35.6%  50% ━━━━━━━━━━          1:23
```

5. Eğitim bitince:
   - ✅ **Eğitim Tamamlandı!**
   - Özet istatistikler görünür
   - Son 10 episode tablosu

6. "Modeli kaydetmek ister misiniz?" → **y** (evet)
7. Dosya adı (Enter ile varsayılan) → **Enter**

✅ **Tebrikler!** RL ajanınız eğitildi ve kaydedildi.

---

### ADIM 3: Karşılaştırma (1 dakika)

**Ana Menü → [2] Karşılaştırma**

1. "Senaryo seçin:" → **1** (Normal - Afetsiz)
2. "RL Agent dahil edilsin mi?" → **y** (evet)
3. "Kayıtlı model yüklensin mi?" → **y** (evet)
4. Model listesi → **1** (方才 kaydettiğiniz model)
5. "Karşılaştırmayı başlat?" → **y** (evet)

✨ Simülasyon çalışıyor...

```
⠙ Normal - RL-Agent  75% ━━━━━━━━━━━━━━  0:45
```

**Sonuç Tablosu:**

```
╭─────────────── 📊 Normal ───────────────╮
│ Algoritma        PDR    Latency  Hop   │
├──────────────────────────────────────────┤
│ RL-Agent        37.3% 🏆  11.2ms  3.6   │
│ Dijkstra-Quality 35.8%    11.2ms  2.8   │
│ AODV            31.2%    18.0ms  1.7   │
╰──────────────────────────────────────────╯

🏆 ŞAMPIYON: RL-Agent
```

6. "Sonuçları kaydetmek ister misiniz?" → **y** (evet)

---

### ADIM 4: Grafikleri Gör (30 saniye)

**Ana Menü → [3] Grafikler**

1. **[1]** Kayıtlı sonuçları görselleştir
2. Dosya seçin → **1** (son karşılaştırma)
3. Grafikler oluşturuluyor...
4. ✅ Grafik kaydedildi: `results/comparison_chart_*.png`
5. "Grafiği göstermek ister misiniz?" → **y** (evet)

📊 Matplotlib penceresi açılır → PDR ve Latency grafikleri

---

## 🎉 Tebrikler!

Artık şunları yaptınız:

✅ RL ajanını eğittiniz
✅ Routing algoritmalarını karşılaştırdınız
✅ Sonuçları görselleştirdiniz
✅ RL'nin Dijkstra ve AODV'den daha iyi performans gösterdiğini gördünüz

---

## 🚀 Sonraki Adımlar

### Daha İyi Sonuçlar İçin

**Ana Menü → [5] Ayarlar**

```
Episode Sayısı → 30 veya 50
Simülasyon Adımı → 500
Learning Rate → 0.1
Epsilon → 0.3
```

Sonra tekrar [1] → [2] → [3] yapın.

### Afet Testi

**Ana Menü → [4] Afet Simülasyonu**

1. **[2]** Deprem (Orta)
2. RL Agent ekle → Kaydedilmiş modeli yükle
3. Hangi algoritmanın afet koşullarında daha dayanıklı olduğunu görün!

### Tüm Senaryolar

**Ana Menü → [2] Karşılaştırma**

Senaryo → **[5]** Tüm Senaryolar

Normal, Kademeli Arıza, Deprem'i tek seferde test edin.

---

## 🆘 Sorun Giderme

### "Rich kütüphanesi bulunamadı"

```bash
pip install rich
```

### Eğitim çok yavaş

Ayarlar menüsünden Episode=5 ve Adım=200 yapın (test için).

### Grafikler açılmıyor

Matplotlib backend sorunu olabilir:

```bash
export MPLBACKEND=TkAgg
python cli.py
```

### Model kaydedilemedi

```bash
mkdir -p models results
```

---

## 📚 Daha Fazla Bilgi

- **Detaylı dokümantasyon:** [README.md](README.md)
- **Komut satırı kullanımı:** `python -m lifenode.main --help`
- **Kapsamlı test:** `python run_experiments.py`

---

## 💡 Pro Tips

1. **İlk test hızlı olsun:** Episode=10, Adım=300
2. **Modelleri saklayın:** Her eğitim sonrası kaydedin
3. **Karşılaştırma kayıtları:** JSON dosyalarını biriktirin
4. **Afet testleri:** Önce Normal ile başlayın
5. **Parametre tuning:** Learning rate ve epsilon'u deneyin

---

## 🎯 Tipik Kullanım Senaryoları

### Akademik Makale İçin

```
1. [5] Ayarlar → Episode=50, Düğüm=40
2. [1] RL Eğitimi → Model kaydet
3. [2] Karşılaştırma → Tüm senaryolar
4. [3] Grafikler → PNG kaydet
5. [6] Sonuçlar → JSON'ları analiz et
```

### Demo/Sunum İçin

```
1. [5] Ayarlar → Episode=10 (hızlı)
2. [1] RL Eğitimi
3. [2] Karşılaştırma → Normal
4. [3] Grafikler → Göster
5. [4] Afet → Deprem (Şiddetli) → Dramatik fark görün!
```

### Algoritma Geliştirme İçin

```
1. [5] Ayarlar → Parametreleri değiştir
2. [1] RL Eğitimi → Performansı gözle
3. [1] RL Eğitimi → Farklı parametre dene
4. [2] Karşılaştırma → En iyi modeli bul
```
