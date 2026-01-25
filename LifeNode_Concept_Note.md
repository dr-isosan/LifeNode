# Concept Note: LifeNode - Afet Sonrası İletişim İçin RL Tabanlı Dayanıklı Yönlendirme

## 1. Project Name
**LifeNode: Reinforcement Learning Based Resilient Routing for Post-Disaster Ad-hoc Networks**

## 2. Overview
Bu proje (**LifeNode**), geniş ölçekli afet senaryolarında iletişim ağlarının dayanıklılığını (resilience) artırmaya yönelik bir simülasyon çalışmasıdır. Proje kapsamında, Mobil Ad-hoc Ağlar (MANET) üzerinde çalışan geleneksel yönlendirme protokolleri ile Pekiştirmeli Öğrenme (Reinforcement Learning) tabanlı yaklaşımların performansı karşılaştırmalı olarak analiz edilecektir. Özellikle AODV ve Dijkstra gibi deterministik algoritmaların, düğüm arızaları ve dinamik topoloji değişimleri karşısındaki sınırlılıkları incelenecek; önerilen Q-Learning tabanlı adaptif yönlendirme mekanizrasının bu koşullar altındaki paket iletim oranı (PDR) ve enerji verimliliği üzerindeki etkileri simülasyon ortamında değerlendirilecektir.

## 3. Background
Afet durumlarında iletişim altyapısının sürdürülebilirliği, akademik ve teknik açıdan kritik bir araştırma problemidir. Literatürde, merkezi altyapıdan bağımsız MANET yapıları çözüm olarak önerilse de, bu ağların yönetimi karmaşık optimizasyon problemleri barındırır. Mevcut reaktif (örn. AODV) ve proaktif protokoller, genellikle idealize edilmiş veya yarı-statik ağ varsayımları üzerine kuruludur.

LifeNode projesi, bu varsayımların ötesine geçerek, belirsizlik içeren (stochastic) ve yüksek dinamizme sahip ağ ortamlarını simüle etmeyi hedefler. Çalışma, yönlendirme kararlarının yerel gözlemlere ve geçmiş deneyimlere dayalı olarak optimize edilip edilemeyeceğini araştırmaktadır.

## 4. Key Objectives / Business Objectives

### a. Research Questions
- Q-Learning tabanlı adaptif yönlendirme mekanizmalarının, yüksek paket kaybı ve düğüm arızası içeren simüle edilmiş afet ortamlarında, geleneksel algoritmalara kıyasla performansı nasıl değişmektedir?
- Enerji, kuyruk yoğunluğu ve topolojik mesafe gibi çoklu durum değişkenlerinin (multi-variable state space) öğrenme başarısı üzerindeki etkisi nedir?
- Sentetik olarak oluşturulan farklı afet senaryolarında, öğrenme tabanlı ajanın yakınsama süresi ve genelleştirme yeteneği ne düzeydedir?

### b. Key Steps
- **Simülasyon Çerçevesinin Geliştirilmesi:** Ağ dinamiklerini, paket trafiğini ve düğüm davranışlarını modelleyen Python tabanlı ayrık olay simülatörünün (Discrete Event Simulator) tasarlanması.
- **Protokol Implementasyonu:** Karşılaştırmalı analiz için AODV ve Dijkstra algoritmalarının simülasyon ortamına uyarlanması.
- **Model Geliştirme:** Q-Learning algoritmasının yönlendirme problemine uyarlanması; durum uzayı, aksiyon seti ve ödül fonksiyonunun (reward shaping) tanımlanması.
- **Deneysel Analiz:** Farklı stres testleri (kademeli arıza, ani topoloji değişimi) altında algoritmaların performansının istatistiksel olarak değerlendirilmesi.

## 5. Methods and Workflow

### a. Datasets (Simulation Scenarios)
Çalışma kapsamında, kontrollü deney ortamı sağlamak adına sentetik veri setleri ve topolojiler kullanılacaktır:
- **Baseline Scenario:** İdeal koşullar altında ağ davranışı.
- **Degradation Scenario:** Düğüm enerjilerinin stokastik bir süreçle azaldığı senaryolar.
- **Disruption Scenario:** Ağ topolojisinin belirli zaman aralıklarında aniden değiştiği ve parçalandığı afet modelleri.

### b. Data Cleaning/Preprocessing (State Representation)
Simülasyon ortamından toplanan ham veriler, RL modelinin girdisi olarak kullanılmak üzere işlenecektir:
- Sürekli değişkenlerin (enerji, mesafe) ayrıklaştırma (discretization) yöntemleri ile durum uzayına indirgenmesi.
- Komşuluk ilişkilerinin ve ağ yoğunluğunun matematiksel temsili.

### c. Modelling
- **Reinforcement Learning:** Ağ üzerindeki yönlendirme problemi, bir Markov Karar Süreci (MDP) olarak modellenmiş ve Tabular Q-Learning yöntemi ile çözümlenmiştir.
- **Comparative Algorithms:** Önerilen modelin başarısını ölçmek için literatürde yaygın kullanılan reaktif ve topoloji tabanlı algoritmalar referans alınmıştır.

### d. Deliverables
- Deneylerin tekrarlanabilirliğini sağlayan, modüler bir simülasyon yazılımı.
- Farklı parametre setleri ile eğitilmiş model ağırlıkları.
- Simülasyon sonuçlarını içeren, PDR (Packet Delivery Ratio), gecikme (Latency) ve enerji tüketimi metriklerini sunan kapsamlı analiz raporları.

## 6. Expected Outcomes and Impact
Simülasyon sonuçlarının şu potansiyel çıktıları sağlaması hedeflenmektedir:
- Önerilen RL tabanlı yaklaşımın, belirli afet koşulları altında klasik yöntemlere göre adaptasyon yeteneğinin nicel olarak ortaya konulması.
- Dinamik ağlarda yönlendirme optimizasyonu için hangi durum değişkenlerinin daha belirleyici olduğunun saptanması.
- Otonom ağ yönetimi alanındaki akademik literatüre, simülasyon temelli deneysel verilerle katkı sağlanması.

## 7. Timeline and Milestones
Projenin araştırma takvimi:
1.  **Literatür Taraması ve Tasarım:** Simülasyon mimarisinin belirlenmesi.
2.  **Geliştirme:** Temel simülatörün ve referans algoritmaların kodlanması.
3.  **RL Model Entegrasyonu:** Öğrenme algoritmasının simülasyona dahil edilmesi. (Tamamlandı)
4.  **Kalibrasyon:** Simülasyon parametrelerinin ve hiperparametrelerin optimize edilmesi. (Devam ediyor)
5.  **Deneysel Süreç:** Senaryo bazlı testlerin yürütülmesi ve veri toplama.
6.  **Analiz ve Raporlama:** Elde edilen bulguların değerlendirilmesi.

**Prepared by:** İshak Duran
