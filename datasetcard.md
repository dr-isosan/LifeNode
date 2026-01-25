---
# Dataset Card
---

# Dataset Card for LifeNode Simulation Data

Reinforcement Learning routing simülasyon verileri ve afet senaryosu metrikleri.

## Dataset Details

### Dataset Description

LifeNode projesi, ad-hoc mesh network'lerde dinamik routing protokollerini test etmek için simülasyon verileri üretir. Bu veri seti, RL tabanlı routing ajanının eğitim episodlarından ve çeşitli afet senaryolarındaki performans metriklerinden oluşur.

- **Curated by:** LifeNode Research Team (dr-isosan)
- **License:** MIT

### Dataset Sources

- **Repository:** https://github.com/dr-isosan/LifeNode
- **Paper:** N/A
- **Demo:** CLI-based interactive simulation

## Uses

### Direct Use

Bu veri seti şu amaçlarla kullanılabilir:
- Reinforcement Learning routing algoritmalarının performans analizi
- Klasik routing protokolleri (AODV, Dijkstra) ile RL karşılaştırması
- Afet senaryolarında (deprem, gradual failure) network dayanıklılığı araştırması
- Mesh network simülasyon benchmark'ları

## Dataset Structure

### Simülasyon Sonuçları (JSON)

```json
{
  "scenario": "normal|earthquake|gradual_failure",
  "timestamp": "YYYYMMDD_HHMMSS",
  "results": {
    "RL Agent": {
      "pdr": 0.95,
      "avg_latency_ms": 25.3,
      "avg_hop_count": 3.2,
      "energy_efficiency": 0.87
    },
    "AODV": {...},
    "Dijkstra": {...}
  }
}
```

### RL Training Data

Her episode'da üretilen state-action-reward tuple'ları:
- **State**: Node pozisyonu, komşu sayısı, enerji seviyesi, kuyruk boyutu
- **Action**: Sonraki hop seçimi (komşu ID)
- **Reward**: PDR, latency, hop count'a dayalı karma ödül

## Dataset Creation

### Source Data

#### Data Collection and Processing

Veriler `run_experiments.py` ve `cli.py` kullanılarak üretilir:
1. **Simülasyon Parametreleri**: 20-50 düğüm, 300-1000 adım
2. **Network Yapısı**: Rastgele dağılım, 75m iletim menzili
3. **Trafik**: Sabit CBR (Constant Bit Rate) paket oluşturma
4. **Afet Modelleri**: Düğüm başarısızlıkları, bağlantı kopmalar

**Özellikler:**
- Deterministik seed ile tekrarlanabilir
- JSON formatında kaydedilmiş sonuçlar
- Pickle formatında kaydedilmiş RL modelleri

#### Features and Target

**State Features (RL Agent için):**
- `position_x`, `position_y`: Düğüm koordinatları (0-500m)
- `neighbor_count`: Komşu düğüm sayısı (0-15)
- `energy_level`: Kalan enerji (0-100)
- `queue_size`: Kuyruk doluluk oranı (0-50)
- `distance_to_dest`: Hedefe uzaklık (normalized)

**Target:**
- Optimal next-hop seçimi (discrete action space)
- Maksimum PDR (Packet Delivery Ratio)
- Minimum latency ve hop count

### Annotations

#### Annotation Process

Veri seti otomatik olarak simülasyon motoru tarafından üretilir. Manuel annotation bulunmamaktadır.

**Metriklerin Hesaplanması:**
- PDR: Teslim edilen paket / Gönderilen paket
- Latency: End-to-end zaman (ms)
- Hop Count: Ortalama atlama sayısı
- Energy Efficiency: Tüketilen enerji / Teslim edilen paket

#### Who are the Annotators?

Otomatik simülasyon motoru (lifenode/metrics/analyzer.py).

## Bias, Risks, and Limitations

**Limitasyonlar:**
- Simülasyon gerçek dünya koşullarını tam olarak yansıtmaz
- Trafik modeli basittir (sadece CBR)
- Mobility modeli henüz aktif değil
- Düğüm sayısı küçük-orta ölçekli (20-50)

**Bias:**
- RL Agent eğitim verisine overfit olabilir
- Afet senaryoları belirli pattern'lere dayanır

**Riskler:**
- Gerçek deployment'ta performans farklılık gösterebilir
- Network koşulları (gürültü, parazit) basitleştirilmiş

## Citation

```bibtex
@misc{lifenode2026,
  author = {LifeNode Research Team},
  title = {LifeNode: AI-Driven Dynamic Routing Simulation for Ad-Hoc Networks},
  year = {2026},
  publisher = {GitHub},
  url = {https://github.com/dr-isosan/LifeNode}
}
```
