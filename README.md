# AI Weather Assistant

LangGraph, LangChain ve OpenAI API kullanılarak geliştirilmiş Python tabanlı bir AI asistan. Bu asistan, Retrieval-Augmented Generation (RAG) ile canlı API entegrasyonunu birleştirerek hava durumu API dokümantasyonu hakkında soruları cevaplar ve gerçek zamanlı hava durumu verisi sağlar.

## Proje Genel Bakış

AI Weather Assistant, şunları gösteren gelişmiş bir konuşmalı AI'dır:

1. **Retrieval-Augmented Generation (RAG)**: OpenWeatherMap API dokümantasyonuna dayalı soru-cevap
2. **Agentic Behavior**: OpenWeatherMap API'den canlı hava durumu verisi çeker
3. **Memory Management**: Hem kısa vadeli (konuşma bağlamı) hem uzun vadeli (kalıcı) bellek implementasyonu
4. **LangGraph Entegrasyonu**: Gelişmiş orchestration için LangGraph ile conditional routing, multi-step state management ve agentic workflow özellikleri

### Temel Yetenekler

- 📚 **Dokümantasyon Sorguları**: API anahtarları, endpoint'ler, parametreler ve kullanım hakkında soruları cevaplar
- 🌤️ **Canlı Hava Durumu Verisi**: Dünya çapında herhangi bir şehir için güncel hava durumu koşullarını çeker
- 🧠 **Bağlam Farkındalığı**: Konuşma geçmişini ve bağlamı hatırlar
- 🔄 **Akıllı Bellek**: Context limitlerini yönetmek için uzun konuşmaları otomatik olarak sıkıştırır
- 📊 **Tracing**: Debug ve monitoring için tam LangSmith entegrasyonu

## Mimari

```
┌─────────────────────────────────────────────────────────────────┐
│                         Kullanıcı Sorgusu                       │
└─────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│                    Niyet Sınıflandırma (Intent)                  │
│                   (LLM tabanlı routing)                          │
└─────────────────────────────────────────────────────────────────┘
            ↓                              ↓
┌─────────────────────┐         ┌────────────────────────┐
│   RAG Yolu          │         │   Weather API Yolu      │
│─────────────────────│         │────────────────────────│
│ 1. Vector DB'ye    │         │ 1. Şehir İsimlerini     │
│    Sorgu           │         │    Çıkar                │
│ 2. Dokümanları     │         │ 2. OpenWeatherMap'ı     │
│    Bul             │         │    Çağır                │
│ 3. Cevap Üret      │         │ 3. Cevabı Formatla      │
└─────────────────────┘         └────────────────────────┘
            ↓                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    Bellek Yöneticisi                            │
│  • Kısa vadeli: Konuşma Geçmişi                                 │
│  • Uzun vadeli: Kalıcı Depolama                                 │
│  • Sıkıştırma: Gerektiğinde Özetle                              │
└─────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│                      Son Cevap                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Bileşen Etkileşimi

1. **Agent Orchestrator**: Sorguları niyete göre uygun handler'lara yönlendirir
2. **Vector Store**: RAG için embeddings ile MongoDB Atlas
3. **Weather API**: OpenWeatherMap API ile doğrudan entegrasyon
4. **Memory Manager**: Konuşma bağlamı ve persistency'yi yönetir
5. **LangGraph**: Gelişmiş state management, conditional routing ve multi-step agentic workflow orchestration
6. **LangSmith**: Tracing ve monitoring

## Teknoloji Yığını

- **Dil**: Python 3.9+
- **LLM Sağlayıcı**: OpenAI (GPT-4o-mini, text-embedding-3-small)
- **Framework'ler**: 
  - LangGraph (orchestration)
  - LangChain (chain composition)
  - LangSmith (tracing)
- **Vector Veritabanı**: MongoDB Atlas
- **API Entegrasyonu**: OpenWeatherMap API
- **Server**: FastAPI + Uvicorn
- **Interface**: LangGraph Studio

## Kurulum Talimatları

### Önkoşullar

- Python 3.9 veya üzeri
- MongoDB Atlas hesabı (ücretsiz tier mevcut)
- OpenAI API anahtarı
- OpenWeatherMap API anahtarı
- LangSmith API anahtarı

### Kurulum Adımları

1. **Repository'yi klonlayın**:
```bash
git clone https://github.com/mbesirkesen/ai-weather-assistant.git
cd ai-weather-assistant
```

2. **Virtual environment oluşturun**:
```bash
python -m venv venv
source venv/bin/activate  # Windows'ta: venv\Scripts\activate
```

3. **Bağımlılıkları yükleyin**:
```bash
pip install -r requirements.txt
```

4. **Environment değişkenlerini ayarlayın**:
   - `.env` dosyası oluşturun ve tüm API anahtarlarını doldurun:
```env
OPENAI_API_KEY=sk-proj-...
LANGSMITH_API_KEY=lsv2_...
LANGSMITH_PROJECT=ai-weather-assistant
LANGCHAIN_TRACING_V2=true
MONGODB_ATLAS_CONNECTION_STRING=mongodb+srv://...
MONGODB_DATABASE_NAME=ai_assistant_db
OPENWEATHERMAP_API_KEY=...
```

5. **MongoDB Atlas'ı Ayarlayın** (Detaylı rehber için `SETUP_GUIDE.md` dosyasına bakın):
   - https://www.mongodb.com/atlas adresinden ücretsiz cluster oluşturun
   - Connection string'inizi alın
   - MongoDB Atlas UI'da vector search index'i oluşturun:
     - Cluster'ınızda "Atlas Search" sekmesine gidin
     - "Create Search Index" → "JSON Editor" seçin
     - Bu konfigürasyonu yapıştırın:
     ```json
     {
       "mappings": {
         "dynamic": true,
         "fields": {
           "embedding": {
             "type": "knnVector",
             "dimensions": 1536,
             "similarity": "cosine"
           }
         }
       }
     }
     ```
     - Index adı: `vector_index`
     - Collection: `weather_docs`

6. **Vector veritabanını doldurun**:
```bash
python setup_database.py
```

Bu işlem:
- OpenWeatherMap dokümantasyonunu indirir/yükler
- Embeddings oluşturur
- MongoDB Atlas'a depolar

## Yerel Olarak Çalıştırma

### Seçenek 1: LangGraph Server (LangGraph Studio için)

1. **LangGraph server'ı başlatın**:
```bash
python server.py
```

Server `http://127.0.0.1:20240` adresinde başlayacaktır

2. **LangGraph Studio ile bağlanın**:
   - LangGraph Studio CLI'yi yükleyin (yoksa):
```bash
npm install -g @langchain/langgraph-studio
```
   - LangGraph Studio'yu açın ve yerel server'a bağlanın

### Seçenek 2: LangGraph Test

LangGraph workflow'unu test edin:
```bash
python test_graph.py
```

Bu komut LangGraph'in conditional routing, multi-step state management ve agentic workflow özelliklerini test eder.

### Seçenek 3: Doğrudan Test

Asistanı doğrudan test edin:
```bash
python test_assistant.py
```

Bu komut önceden tanımlı test sorgularını çalıştırır ve cevapları gösterir.

### Seçenek 4: API Endpoint ile Test

LangGraph server çalışırken API endpoint'i kullanarak test edin:
```bash
# Server'ı başlatın
python server.py

# Başka bir terminal'de curl ile test edin
curl -X POST "http://127.0.0.1:20240/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "Istanbul'da hava nasıl?", "thread_id": "test1"}'
```

### Seçenek 5: İnteraktif Test

Python'da interaktif test için:
```python
from agent import WeatherAssistant
from config import Config

# Konfigürasyonu doğrula
Config.validate()

# Asistanı başlat
assistant = WeatherAssistant()

# Sorular sor
response = assistant.process_query("Istanbul'da hava nasıl?")
print(response)

response = assistant.process_query("API key nasıl alınır?")
print(response)
```

## Örnek Etkileşimler

### RAG Sorguları (Dokümantasyon)

**Soru 1**: "API key nasıl alınır?"

**Cevap**: 
```
OpenWeatherMap için API key almak:
1. openweathermap.org'da kayıt olun
2. E-posta adresinizi doğrulayın
3. Hesabınızdaki API keys bölümüne gidin
4. Yeni bir key oluşturun veya verilen varsayılan key'i kullanın

API key tüm isteklerde 'appid' parametresi olarak dahil edilmelidir.
Ücretsiz tier dakikada 60 çağrıya izin verir.
```

**Soru 2**: "Hangi endpoint güncel hava durumu verisi verir?"

**Cevap**:
```
Güncel hava durumu verisi endpoint'i:
api.openweathermap.org/data/2.5/weather

Ana parametreler:
- q: Şehir adı (örn: "London,uk" veya "Istanbul,tr")
- appid: API key'iniz (zorunlu)
- units: Sıcaklık birimi (standard, metric, imperial)
- lang: Açıklamalar için dil

Örnek istek:
GET https://api.openweathermap.org/data/2.5/weather?q=London,uk&appid=KEY&units=metric
```

### Weather API Sorguları (Canlı Veri)

**Soru 3**: "Istanbul'da hava şu anda nasıl?"

**Cevap**:
```
Istanbul, TR'de güncel hava durumu:

Sıcaklık: 22°C (hissedilen: 20°C)
Durum: Parçalı Bulutlu
Nem: 65%
Rüzgar: 3.2 m/s NE
Bulut: 40%
Basınç: 1013 hPa
Görüş: 10 km
```

**Soru 4**: "Paris ve London'da sıcaklığı ver"

**Cevap**:
```
Birden fazla şehir için hava durumu:

Paris, FR: 15°C, Hafif Yağmurlu
London, GB: 18°C, Bulutlu
```

## Bellek Implementasyonu

### Kısa Vadeli Bellek (Konuşma Bağlamı)

- **Depolama**: Mesaj sözlüklerinin memory listesi
- **Yönetim**: Context limite yaklaşırken otomatik sıkıştırma
- **Strateji**: Yeni bağlamı korurken eski mesajları özetle
- **Threshold**: Max context uzunluğunun %80'i sıkıştırmayı tetikler

**Nasıl Çalışır**:
```python
# Mesajlar şu şekilde saklanır:
[
  {"role": "user", "content": "Merhaba"},
  {"role": "assistant", "content": "Merhaba! Nasıl yardımcı olabilirim?"},
  ...
]

# Limite yaklaşıldığında:
# 1. Tüm konuşmayı özetle
# 2. Son %25 mesajı tut
# 3. Özeti bağlam olarak başa ekle
```

### Uzun Vadeli Bellek (Kalıcı Depolama)

- **Depolama**: Disk üzerinde JSON dosyaları
- **Özellikler**: Oturumlar arasında konuşma geçmişini kaydet/yükle
- **Metadata**: Özetleri ve istatistikleri içerir

**Kullanım**:
```python
# Belleği kaydet
assistant.memory_manager.save_to_disk("memory.json")

# Belleği yükle
assistant.memory_manager.load_from_disk("memory.json")
```

## LangGraph Gelişmiş Özellikleri

Bu proje LangGraph'in güçlü özelliklerini kullanarak geliştirilmiştir:

### 1. Conditional Routing (Koşullu Yönlendirme)

Intent classification sonucuna göre sorgu farklı node'lara yönlendirilir:
- **RAG Intent** → `retrieve_docs` node'u
- **Weather API Intent** → `fetch_weather` node'u  
- **General Intent** → `handle_general` node'u

```python
def route(state: GraphState) -> Literal["retrieve_docs", "fetch_weather", "handle_general"]:
    """Intent'e göre conditional routing"""
    intent = state.get("intent", "general")
    if intent == "rag":
        return "retrieve_docs"
    elif intent == "weather_api":
        return "fetch_weather"
    else:
        return "handle_general"
```

### 2. Multi-Step State Management (Çok Adımlı State Yönetimi)

State her node'da güncellenir ve bir sonraki node'a aktarılır:

**Workflow Adımları:**
1. `classify_intent` → Intent tespiti, state'e `intent` eklenir
2. `retrieve_docs` / `fetch_weather` / `handle_general` → Veri toplama, state'e veri eklenir
3. `generate_response` → Cevap üretimi, state'e `response` eklenir
4. `update_memory` → Bellek güncelleme, state'e metadata eklenir

**State Yapısı:**
```python
class GraphState(TypedDict):
    messages: List[str]              # Mesaj geçmişi
    query: str                       # Kullanıcı sorgusu
    intent: Optional[str]            # Tespit edilen intent
    retrieved_docs: Optional[List]   # RAG için bulunan dokümanlar
    weather_data: Optional[Dict]    # Weather API'den gelen veriler
    response: Optional[str]          # Final cevap
    next_action: str                 # Sonraki aksiyon
    context: Optional[Dict]          # İşlem metadata'sı
    error: Optional[str]             # Hata mesajları
```

### 3. Agentic Workflow (Ajan Tabanlı İş Akışı)

Her işlem adımı ayrı bir node'da gerçekleştirilir, bu sayede:
- **Modülerlik**: Her node bağımsız test edilebilir
- **İzlenebilirlik**: Her adım LangSmith'te ayrı ayrı izlenir
- **Esneklik**: Yeni node'lar kolayca eklenebilir
- **Hata Yönetimi**: Her node kendi hata yönetimine sahiptir

**Graph Yapısı:**
```
Entry Point
    ↓
classify_intent
    ↓
[Conditional Routing]
    ├─→ retrieve_docs ──┐
    ├─→ fetch_weather ──┤
    └─→ handle_general ──┘
            ↓
    generate_response
            ↓
    update_memory
            ↓
         END
```

### 4. Checkpointing (Durum Kaydetme)

MemorySaver ile state persistence:
- Thread bazlı state yönetimi
- Konuşma geçmişi korunur
- Hata durumunda state geri yüklenebilir

## LangGraph Studio Uyumluluğu

Asistan LangGraph Studio ile tam uyumludur:

1. **Graph Tanımı**: `graph.py` içinde gelişmiş state machine tanımı
2. **Server**: Graph endpoint'lerini açığa çıkaran FastAPI server (`/query` endpoint'i ile test edilebilir)
3. **State Management**: Type safety için TypedDict tabanlı state
4. **Tracing**: Otomatik LangSmith entegrasyonu
5. **Checkpointing**: MemorySaver ile state persistence

## LangSmith Tracing

Tüm işlemler LangSmith üzerinden izlenir:

- Sorgu işleme
- API çağrıları
- Vector aramaları
- Bellek işlemleri

İzlemeleri görmek için:
1. `.env` dosyasında `LANGCHAIN_TRACING_V2=true` olduğundan emin olun
2. `LANGSMITH_API_KEY` ve `LANGSMITH_PROJECT` ayarlayın
3. https://smith.langchain.com adresinden izlemelere erişin

## Proje Yapısı

```
ai-weather-assistant/
├── agent.py                 # Ana asistan mantığı
├── config.py               # Konfigürasyon yönetimi
├── data_loader.py          # Dokümantasyon yükleyici
├── graph.py                # LangGraph tanımı
├── memory_manager.py       # Bellek yönetimi
├── server.py              # LangGraph server
├── setup_database.py      # Veritabanı kurulum scripti
├── test_assistant.py      # Agent test scripti
├── test_graph.py          # LangGraph workflow test scripti
├── vector_store.py        # Vector store işlemleri
├── weather_api.py         # OpenWeatherMap API client
├── requirements.txt       # Python bağımlılıkları
├── .gitignore           # Git ignore kuralları
├── README.md           # Bu dosya
└── SETUP_GUIDE.md      # Kurulum rehberi (Türkçe)
```

## Bilinen Limitler ve Gelecek Çalışmalar

### Mevcut Limitler

1. **Rate Limitler**: OpenAI ve OpenWeatherMap rate limitleri geçerlidir
2. **Context Window**: OpenAI'nin context window'u ile sınırlıdır
3. **Tek Dil**: Şu anda İngilizce için optimize edilmiştir
4. **Dokümantasyon**: Web scraping başarısız olursa static fallback
5. **Çoklu Thread Yok**: Sadece sıralı işleme

### Gelecek İyileştirmeler

1. **🌍 Çoklu Dil Desteği**: Birden fazla dil desteği ekle
2. **⚡ Async İşleme**: Daha iyi performans için async/await implementasyonu
3. **📊 Gelişmiş Analitik**: Gelişmiş LangSmith dashboard'ları
4. **🔄 Retry Mantığı**: Daha iyi hata yönetimi ve tekrarlar
5. **💾 Veritabanı Belleği**: Uzun vadeli belleği MongoDB'ye taşı
6. **🎨 UI İyileştirmesi**: Web arayüzü ekle
7. **🧩 Araç Genişletme**: Daha fazla araç ekle (tahminler, geçmiş veri)
8. **🔒 Güvenlik**: Gelişmiş API key yönetimi

## Sorun Giderme

### MongoDB Bağlantı Sorunları

Bağlantı hatası alırsanız:
```bash
# Connection string'inizi kontrol edin
# MongoDB Atlas IP whitelist'inin IP'nize izin verdiğinden emin olun
# Veritabanı ve collection isimlerini doğrulayın
```

### OpenAI API Hataları

```bash
# API key'inizin doğru olduğunu doğrulayın
# Hesabın krediye sahip olduğunu kontrol edin
# Rate limit aşılmadığını onaylayın
```

### Vector Index Sorunları

```bash
# MongoDB Atlas'ta index oluşturulduğundan emin olun
# Index adının config ile eşleştiğini kontrol edin
# Embedding dimensions'ı doğrulayın (text-embedding-3-small için 1536)
```

## Lisans

Bu proje eğitim amaçlı oluşturulmuştur.

---

**Not**: Bu asistan şunlar için internet bağlantısı gerektirir:
- OpenAI API çağrıları
- OpenWeatherMap API çağrıları
- MongoDB Atlas bağlantısı
- LangSmith tracing

Çalıştırmadan önce tüm API key'lerin geçerli ve servislerin erişilebilir olduğundan emin olun.
