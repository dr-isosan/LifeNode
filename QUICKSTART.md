# 🚀 Hızlı Başlangıç Rehberi

LifeNode simülasyon ortamını kurmak ve çalıştırmak için aşağıdaki adımları izleyin.

## 1. Kurulum

Gerekli Python paketlerini yükleyin:

```bash
# Sanal ortam oluştur (Opsiyonel ama önerilir)
python3 -m venv venv
source venv/bin/activate  # Windows için: venv\Scripts\activate

# Bağımlılıkları yükle
pip install -r requirements.txt
```

## 2. Çalıştırma

Simülasyonu yönetmek için interaktif komut satırı arayüzünü (CLI) kullanın:

```bash
python cli.py
```

## 3. Temel İş Akışı

CLI menüsü üzerinden şunları yapabilirsiniz:

1.  **RL Eğitimi:** Ajanı farklı senaryolarda eğitin.
2.  **Karşılaştırma:** RL modelini AODV ve Dijkstra ile kıyaslayın.
3.  **Grafikler:** Sonuçları görselleştirin.
4.  **Afet Testi:** Zorlu koşullarda dayanıklılık testleri yapın.

Varsayılan ayarlarla hızlı bir test yapmak için menüden **[1] RL Eğitimi** seçeneği ile başlayıp, ardından **[2] Karşılaştırma** modunu kullanabilirsiniz.
