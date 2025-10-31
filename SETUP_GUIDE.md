# Setup Guide - Türkçe

## MongoDB Atlas API Key Alma Rehberi

### Adım 1: MongoDB Atlas Hesabı Oluşturma
1. **Tarayıcınızda şu adrese gidin**: https://www.mongodb.com/cloud/atlas/register
2. **"Try Free"** butonuna tıklayın
3. Email ve şifre ile kayıt olun
4. Emailinizi onaylayın

### Adım 2: İlk Cluster Oluşturma
1. Giriş yaptıktan sonra **"Build a Database"** veya **"Create"** butonuna tıklayın
2. **"M0 Free"** (Free Tier) seçeneğini seçin
3. **Cloud Provider**: AWS seçin (önerilen)
4. **Region**: `N. Virginia (us-east-1)` gibi yakın bir bölge seçin
5. **Cluster Name**: "Cluster0" (varsayılan) veya istediğiniz bir isim
6. **"Create"** butonuna tıklayın
7. Cluster'ın oluşması 3-5 dakika sürebilir

### Adım 3: Database User Oluşturma
1. Cluster oluştuktan sonra **"Create Database User"** sekmesine geleceksiniz
2. **Authentication Method**: "Password" seçin
3. **Username**: Bir kullanıcı adı girin (örn: `admin`)
4. **Password**: Güçlü bir şifre girin (✓ işareti gördüğünüzde tamam demektir)
5. **"Create User"** butonuna tıklayın
6. **BİLMEYİN:** Username ve password'u bir yere kaydedin!

### Adım 4: IP Whitelist (Network Access)
1. **"My Local Environment"** veya **"Add My Current IP Address"** seçeneğini seçin
2. Eğer development için kullanacaksanız, **"Allow Access from Anywhere"** (0.0.0.0/0) seçebilirsiniz (sadece development için!)
3. **"Finish and Close"** butonuna tıklayın

### Adım 5: Connection String Alma
1. Cluster'ınızın ana sayfasında **"Connect"** butonuna tıklayın
2. **"Connect your application"** kartına tıklayın
3. **Driver**: "Python" seçin
4. **Version**: "3.6 or later" seçin
5. Aşağıdaki connection string'i göreceksiniz:
   ```
   mongodb+srv://<username>:<password>@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
   ```
6. **Kopyalayın** ve **username** ile **password** kısımlarını kendi bilgilerinizle değiştirin
   
   Örnek:
   ```
   mongodb+srv://admin:MySecurePassword123@cluster0.abc123.mongodb.net/?retryWrites=true&w=majority
   ```

### Adım 6: .env Dosyasına Ekleyin
1. Proje klasöründe `.env` dosyası oluşturun
2. MongoDB connection string'i ekleyin:
   ```env
   MONGODB_ATLAS_CONNECTION_STRING=mongodb+srv://admin:MySecurePassword123@cluster0.abc123.mongodb.net/?retryWrites=true&w=majority
   ```

---

## OpenWeatherMap API Key Alma Rehberi

### Adım 1: Hesap Oluşturma
1. **Tarayıcınızda şu adrese gidin**: https://openweathermap.org/api
2. Sayfanın üstünde **"Sign Up"** veya **"Sign In"** butonuna tıklayın
3. Yeni hesap oluşturuyorsanız:
   - Email ve şifre girin
   - Kullanıcı adı seçin
   - Hesap oluşturun

### Adım 2: API Key Alma
1. Giriş yaptıktan sonra, üst menüden **"API keys"** sekmesine tıklayın
2. **"Create key"** butonuna tıklayın
3. Bir **key name** verin (örn: "AI Assistant Project")
4. **"Generate"** butonuna tıklayın
5. **API Key**'iniz görünecek (örnek: `1234567890abcdef1234567890abcdef`)
6. **Hemen kopyalayın!** Bu key'i daha sonra göremezsiniz

### Adım 3: API Key Aktifleşmesi
- ⚠️ **ÖNEMLİ:** API key'in aktif hale gelmesi 10 dakika - 2 saat sürebilir
- Bu süre içinde API çağrıları hata verebilir
- Biraz beklemelisiniz

### Adım 4: .env Dosyasına Ekleyin
1. `.env` dosyanıza OpenWeatherMap API key'i ekleyin:
   ```env
   OPENWEATHERMAP_API_KEY=1234567890abcdef1234567890abcdef
   ```

### Adım 5: Test Etme
- API key'in çalışıp çalışmadığını test etmek için:
   ```
   https://api.openweathermap.org/data/2.5/weather?q=London&appid=YOUR_API_KEY
   ```
   Bu URL'i tarayıcınızda açın (YOUR_API_KEY yerine kendi key'inizi koyun)
   - JSON veri görürseniz → ✅ Başarılı!
   - Hata mesajı görürseniz → ⏰ Biraz bekleyin

---

## Tam .env Dosyası Örneği

`.env` dosyanız şöyle görünmeli:

```env
# OpenAI Configuration
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxx

# LangSmith Configuration
LANGSMITH_API_KEY=your_langsmith_api_key_here
LANGSMITH_PROJECT=ai-weather-assistant
LANGCHAIN_TRACING_V2=true

# MongoDB Atlas Configuration
MONGODB_ATLAS_CONNECTION_STRING=mongodb+srv://admin:MySecurePassword123@cluster0.abc123.mongodb.net/?retryWrites=true&w=majority
MONGODB_DATABASE_NAME=ai_assistant_db

# OpenWeatherMap API Configuration
OPENWEATHERMAP_API_KEY=1234567890abcdef1234567890abcdef
```

---

## MongoDB Atlas Database ve Collection Oluşturma

### İlk Önce: Database ve Collection Oluşturma

1. **Sol menüden "Database"** seçeneğine tıklayın
2. Cluster'ınıza tıklayın
3. **"Browse Collections"** butonuna tıklayın
4. **"Add My Own Data"** butonuna tıklayın
5. **Database name**: `ai_assistant_db` yazın
6. **Collection name**: `weather_docs` yazın
7. **"Create"** butonuna tıklayın

---

## MongoDB Atlas Vector Index Oluşturma

### ÖNEMLİ: Database ve Collection oluşturduktan sonra!

1. **Sol menüden "Search"** (Arama ve Vektör Arama) sekmesine tıklayın
2. **"+ Kendi verilerimi ekle"** (Add my own data) butonuna tıklayın
3. **"Vector Search"** seçeneğini seçin
4. **Database**: `ai_assistant_db` seçin
5. **Collection**: `weather_docs` seçin
6. **Index Name**: `vector_index` yazın
7. **"Next: Define vector mappings"** butonuna tıklayın
8. JSON Editor'da aşağıdaki JSON'u kopyalayıp yapıştırın:

```json
{
  "fields": [
    {
      "type": "vector",
      "path": "embedding",
      "numDimensions": 1536,
      "similarity": "cosine"
    }
  ]
}
```

9. **"Next: Review"** ve sonra **"Create Search Index"** butonuna tıklayın
10. İndex'in oluşturulması 1-5 dakika sürebilir

---

## Sonraki Adımlar

Tüm API key'leri `.env` dosyasına ekledikten ve vector index'i oluşturduktan sonra:

1. **setup_database.py çalıştırın**: `python setup_database.py`
2. **Test edin**: `python test_assistant.py`
3. **Server başlatın**: `python server.py`

---

## Sorun Giderme

### MongoDB Atlas Bağlantı Hatası
- Connection string'de özel karakterler varsa URL encode edin
- IP whitelist'inizde olduğunuzdan emin olun
- Database user oluşturduğunuzdan emin olun

### OpenWeatherMap Hatası
- API key 2 saat içinde aktifleşmeli
- Rate limit: Free tier'da 60 call/min
- "Invalid API key" hatası = bekleyin veya yeni key oluşturun

### Genel Hatalar
- `.env` dosyasının proje root'unda olduğundan emin olun
- Tüm değerlerde tırnak işareti olmamalı
- Boşluk karakterleri olmamalı

