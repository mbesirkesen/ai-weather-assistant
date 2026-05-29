"""Kurulum doğrulama scripti — API anahtarları ve bağlantıları kontrol eder."""
import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def check_env_vars():
    """Gerekli ortam değişkenlerini kontrol et."""
    from config import Config

    try:
        Config.validate()
        logger.info("✓ Tüm gerekli ortam değişkenleri tanımlı")
        return True
    except ValueError as e:
        logger.error("✗ Ortam değişkeni hatası: %s", e)
        logger.error("  .env.example dosyasını .env olarak kopyalayıp doldurun:")
        logger.error("  cp .env.example .env")
        return False


def check_mongodb():
    """MongoDB Atlas bağlantısını test et."""
    from config import Config
    from pymongo import MongoClient

    try:
        client = MongoClient(Config.MONGODB_ATLAS_URI, serverSelectionTimeoutMS=5000)
        client.admin.command("ping")
        db = client[Config.MONGODB_DATABASE_NAME]
        count = db[Config.MONGODB_COLLECTION_NAME].count_documents({})
        logger.info("✓ MongoDB bağlantısı başarılı (%d doküman)", count)
        if count == 0:
            logger.warning("  Vector store boş — 'python setup_database.py' çalıştırın")
        return True
    except Exception as e:
        logger.error("✗ MongoDB bağlantı hatası: %s", e)
        return False


def check_openai():
    """OpenAI API anahtarını test et."""
    from config import Config
    from langchain_openai import ChatOpenAI

    try:
        llm = ChatOpenAI(
            model=Config.OPENAI_MODEL,
            openai_api_key=Config.OPENAI_API_KEY,
        )
        response = llm.invoke("Say 'ok' only.")
        logger.info("✓ OpenAI API çalışıyor")
        return True
    except Exception as e:
        logger.error("✗ OpenAI API hatası: %s", e)
        return False


def check_openweathermap():
    """OpenWeatherMap API anahtarını test et."""
    from weather_api import WeatherAPI

    try:
        api = WeatherAPI()
        if api.check_api_health():
            logger.info("✓ OpenWeatherMap API çalışıyor")
            return True
        logger.error("✗ OpenWeatherMap API yanıt vermedi — key aktif olmayabilir (10 dk–2 saat bekleyin)")
        return False
    except Exception as e:
        logger.error("✗ OpenWeatherMap API hatası: %s", e)
        return False


def check_imports():
    """Temel modül importlarını test et (API key gerektirmez)."""
    try:
        from config import Config  # noqa: F401
        from data_loader import load_documentation
        from weather_api import WeatherAPI

        docs = load_documentation()
        assert len(docs) > 0, "Dokümantasyon yüklenemedi"

        api = WeatherAPI()
        formatted = api._format_weather_data({
            "name": "Istanbul",
            "sys": {"country": "TR"},
            "main": {"temp": 22, "feels_like": 20, "humidity": 65, "pressure": 1013},
            "weather": [{"description": "clear sky"}],
            "wind": {"speed": 3.2, "deg": 45},
            "clouds": {"all": 40},
            "visibility": 10000,
            "dt": 0,
        })
        assert formatted["city"] == "Istanbul"

        logger.info("✓ Modül importları ve temel fonksiyonlar OK")
        return True
    except Exception as e:
        logger.error("✗ Import hatası: %s", e)
        return False


def main():
    """Tüm kontrolleri çalıştır."""
    print("\n" + "=" * 60)
    print("AI Weather Assistant — Kurulum Kontrolü")
    print("=" * 60 + "\n")

    results = {"imports": check_imports()}

    if not results["imports"]:
        print("\n✗ Temel importlar başarısız — bağımlılıkları kontrol edin:")
        print("  pip install -r requirements.txt\n")
        sys.exit(1)

    if not check_env_vars():
        print("\n✗ .env dosyasını yapılandırın, ardından tekrar çalıştırın.\n")
        sys.exit(1)

    results["mongodb"] = check_mongodb()
    results["openai"] = check_openai()
    results["openweathermap"] = check_openweathermap()

    print("\n" + "=" * 60)
    passed = sum(results.values())
    total = len(results)
    print(f"Sonuç: {passed}/{total} kontrol başarılı")
    print("=" * 60 + "\n")

    if all(results.values()):
        print("Kurulum tamam! Şimdi çalıştırabilirsiniz:")
        print("  python test_assistant.py   # Asistan testi")
        print("  python server.py           # API sunucusu")
        print()
        sys.exit(0)

    if not results.get("mongodb"):
        print("MongoDB sorunu için SETUP_GUIDE.md dosyasına bakın.")
    sys.exit(1)


if __name__ == "__main__":
    main()
