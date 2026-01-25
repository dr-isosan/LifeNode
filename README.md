# LifeNode 🌐

**Afet Sonrası İletişim İçin RL Tabanlı Dayanıklı Yönlendirme**

## 📖 Genel Bakış

**LifeNode**, afet durumlarında (deprem, sel, altyapı çöküşü) iletişim ağlarının dayanıklılığını artırmayı hedefleyen bir simülasyon projesidir. Proje, **Pekiştirmeli Öğrenme (Reinforcement Learning - Q-Learning)** tabanlı yönlendirme mekanizmalarının, geleneksel protokoller (**AODV, Dijkstra**) ile karşılaştırmalı analizini sunar.

## 🎯 Hedefler

*   **Dayanıklılık (Resilience):** Düğüm arızaları ve dinamik topoloji değişimlerinde iletişimin sürdürülebilirliği.
*   **Adaptasyon:** Yerel gözlemlerle değişen ağ koşullarına uyum sağlama.
*   **Performans Analizi:** Paket iletim oranı (PDR), gecikme ve enerji verimliliği metriklerinin karşılaştırılması.

## 🚀 Başlarken

Hızlı kurulum ve çalıştırma talimatları için [QUICKSTART.md](QUICKSTART.md) dosyasına göz atın.

## 📂 Proje Yapısı

*   `lifenode/`: Ana kaynak kodları (RL ajanı, yönlendirme protokolleri, simülasyon ortamı).
*   `tests/`: Birim ve entegrasyon testleri.
*   `results/`: Simülasyon çıktıları ve analiz raporları.

Bu çalışma, afet sonrası iletişim senaryolarında deterministik algoritmaların sınırlarını aşarak, öğrenen ve adapte olan ağ yapılarının potansiyelini araştırmaktadır.
