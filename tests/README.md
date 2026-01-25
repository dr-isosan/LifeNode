# LifeNode Test Suite

Bu dizin, LifeNode projesinin kapsamlı test paketini içerir.

## 📊 Test İstatistikleri

- **Toplam Test:** 42
- **Başarı Oranı:** 100%
- **Kod Kapsamı:** %62
- **Test Süresi:** ~0.7 saniye

## 🧪 Test Kategorileri

### 1. Routing Algoritmaları (`test_routing.py`) - 10 test
- Dijkstra (Quality & Hop) başlatma ve routing
- AODV başlatma ve routing
- RL Agent başlatma ve routing
- Router reset fonksiyonları
- Router karşılaştırması

### 2. Simülasyon (`test_simulation.py`) - 8 test
- World oluşturma ve başlatma
- Node oluşturma
- World step fonksiyonu
- Simülasyon tutarlılığı (seed kontrolü)
- MetricCollector testleri

### 3. Afet Senaryoları (`test_scenarios.py`) - 9 test
- Deprem senaryosu testleri
- Kademeli arıza senaryosu testleri
- Senaryo istatistikleri
- Birden fazla senaryo entegrasyonu

### 4. RL Agent (`test_rl_agent.py`) - 10 test
- Agent başlatma ve konfigürasyon
- Eğitim modu toggle
- Simülasyon ile eğitim
- Model kaydetme/yükleme
- Mevcut model yükleme

### 5. Entegrasyon (`test_integration.py`) - 5 test
- Tam simülasyon testleri
- Afetli simülasyon
- Tüm router'lar karşılaştırma
- JSON işlemleri
- Uçtan uca iş akışı

## 🚀 Testleri Çalıştırma

### Tüm testleri çalıştır
```bash
pytest tests/ -v
```

### Belirli bir test dosyasını çalıştır
```bash
pytest tests/test_routing.py -v
```

### Belirli bir test sınıfını çalıştır
```bash
pytest tests/test_routing.py::TestRoutingAlgorithms -v
```

### Belirli bir testi çalıştır
```bash
pytest tests/test_routing.py::TestRoutingAlgorithms::test_dijkstra_routing -v
```

### Kod kapsamı ile çalıştır
```bash
pytest tests/ --cov=lifenode --cov-report=html
```

### Detaylı hata mesajları ile çalıştır
```bash
pytest tests/ -v --tb=long
```

### Paralel test çalıştırma (hızlı)
```bash
pytest tests/ -n auto
```

### Test sonuçlarını kaydet
```bash
pytest tests/ -v --html=test_report.html --self-contained-html
```

## 📈 Kod Kapsamı Raporu

| Bileşen     | Kapsam  | Durum      |
| ----------- | ------- | ---------- |
| Config      | 100%    | ✅ Mükemmel |
| RL Agent    | 87%     | ✅ Çok İyi  |
| Scenarios   | 80%     | ✅ İyi      |
| Environment | 73%     | ✅ İyi      |
| Metrics     | 64%     | ⚠️ Orta     |
| Routing     | 63%     | ⚠️ Orta     |
| **TOPLAM**  | **62%** | ✅ İyi      |

## 🎯 Test Kalitesi

- ✅ Tüm kritik bileşenler test edilmiş
- ✅ Entegrasyon testleri mevcut
- ✅ Model kaydetme/yükleme test edilmiş
- ✅ Simülasyon tutarlılığı doğrulanmış
- ✅ Router karşılaştırmaları test edilmiş

## 📝 Yeni Test Ekleme

Yeni test eklemek için:

1. İlgili test dosyasını açın veya yeni bir tane oluşturun
2. Test sınıfı oluşturun (ör. `TestYeniOzellik`)
3. Test metodları ekleyin (`test_` ile başlamalı)
4. Testleri çalıştırın ve doğrulayın

Örnek:
```python
class TestYeniOzellik:
    def test_ozellik_1(self):
        """Test açıklaması"""
        # Test kodu
        assert result == expected
```

## 🔧 Gereksinimler

```bash
pip install pytest pytest-cov
```

## 📚 Daha Fazla Bilgi

- [pytest dokumentasyonu](https://docs.pytest.org/)
- [pytest-cov dokumentasyonu](https://pytest-cov.readthedocs.io/)
