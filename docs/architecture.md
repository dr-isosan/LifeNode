# LifeNode - Proje Mimarisi

## Proje Özeti
LifeNode, afet durumlarında mesh network simülasyonu yapan bir projedir.

## Hafta 1: Kişi A Görevleri

### Modüller
1. **simulation/node.py** - Düğüm sınıfı
2. **simulation/topology.py** - Topoloji üretici (RGG)
3. **simulation/network.py** - Ağ yöneticisi
4. **visualization/plot_utils.py** - Görselleştirme
5. **main.py** - Ana simülasyon

### Özellikler
- Random Geometric Graph topolojisi
- Node failure modeli (%2-10 arıza)
- Dummy routing (rastgele + en yakın komşu)
- Matplotlib görselleştirme
- Paket takibi ve istatistikler

### Kullanım
```bash
python main.py --quick  # Hızlı test
python main.py          # Tam simülasyon
```