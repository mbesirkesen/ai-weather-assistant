"""
Ana LangGraph agent dosyası - RAG, Weather API ve Memory yönetimini koordine eder.
"""
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import logging

from config import Config
from weather_api import WeatherAPI
from vector_store import VectorStoreManager
from memory_manager import MemoryManager

logger = logging.getLogger(__name__)


class WeatherAssistant:
    """
    Ana AI assistant sınıfı.
    
    Bu sınıf üç ana bileşeni koordine eder:
    1. RAG: Dokümantasyon sorularını cevaplar
    2. Weather API: Canlı hava durumu verisi çeker
    3. Memory: Konuşma geçmişini yönetir
    """
    
    def __init__(self):
        """Assistant'ın temel bileşenlerini initialize eder."""
        # LLM: Intent classification ve text generation için
        self.llm = ChatOpenAI(
            model=Config.OPENAI_MODEL,  # gpt-4o-mini: hızlı ve ucuz
            temperature=0.7,  # Yaratıcılık seviyesi (0-1 arası)
            openai_api_key=Config.OPENAI_API_KEY
        )
        
        # Diğer bileşenler
        self.weather_api = WeatherAPI()  # Canlı hava durumu verisi
        self.vector_store = VectorStoreManager()  # RAG için vector search
        self.memory_manager = MemoryManager()  # Konuşma geçmişi
        
        # System prompt: LLM'in kimliğini ve yeteneklerini tanımlar
        self.system_prompt = """You are a helpful AI weather assistant.
You have access to:
1. OpenWeatherMap API documentation (through RAG)
2. Live weather data from OpenWeatherMap API
3. Conversation history

Your capabilities:
- Answer questions about the OpenWeatherMap API (how to use it, endpoints, etc.)
- Fetch and report current weather data for any city
- Remember context from the conversation
- Provide friendly, accurate, and helpful responses

When the user asks about weather API documentation or usage, use your RAG knowledge.
When the user asks about actual weather in a city, call the weather API to get live data.

Always be concise but informative. If you don't know something, be honest about it."""
    
    def classify_intent(self, query: str) -> str:
        """
        Kullanıcı sorgusunun niyetini tespit eder.
        
        Rule-based yerine LLM kullanıyoruz çünkü:
        - Doğal dili daha iyi anlıyor
        - Her sorgu tipi için rule yazmaya gerek kalmıyor
        - Yeni soru kalıplarına otomatik adapte oluyor
        
        Returns:
            "rag": Dokümantasyon soruları
            "weather_api": Canlı hava durumu istekleri
            "general": Genel konuşma
        """
        classification_prompt = """Classify the user's intent based on their query.

User query: {query}

Classify as one of:
- "rag": Questions about API documentation, how to use the API, API endpoints, getting API keys, etc.
- "weather_api": Requests for actual/live weather data in specific cities
- "general": General conversation, greetings, questions about capabilities

Respond with ONLY the classification word (rag, weather_api, or general):"""

        prompt = ChatPromptTemplate.from_template(classification_prompt)
        
        try:
            # LLM'e prompt gönder ve intent'i al
            response = self.llm.invoke(prompt.format_messages(query=query))
            intent = response.content.strip().lower()
            logger.info(f"Intent classified as: {intent}")
            return intent
        except Exception as e:
            # Hata durumunda "general" döndür ki sistem çökmesin
            logger.error(f"Error classifying intent: {e}")
            return "general"
    
    def handle_rag_query(self, query: str) -> str:
        """
        RAG (Retrieval-Augmented Generation) sorgularını işler.
        
        RAG yaklaşımı şu avantajları sağlar:
        - Tüm dokümantasyonu prompt'a koymak çok token kullanır
        - Vector search sadece ilgili kısmı bulur
        - Maliyet ve hız optimizasyonu
        
        Adımlar:
        1. Vector search ile ilgili dokümanları bul
        2. Context olarak LLM'e gönder
        3. LLM context + soru ile cevap üretir
        """
        try:
            # MongoDB Atlas vector search ile en ilgili 3 dokümanı bul
            docs = self.vector_store.similarity_search(query, k=3)
            
            if not docs:
                return "I couldn't find relevant documentation. Please try rephrasing your question."
            
            # Bulunan dokümanları birleştir
            context = "\n\n".join([doc.page_content for doc in docs])
            
            # RAG prompt: System bilgisi + Context + Soru
            rag_prompt = ChatPromptTemplate.from_messages([
                ("system", self.system_prompt + "\n\nUse the following documentation to answer the question:"),
                ("system", "Documentation:\n{context}"),
                ("user", "{question}")
            ])
            
            # LangChain chain: prompt -> LLM -> string
            chain = rag_prompt | self.llm | StrOutputParser()
            response = chain.invoke({
                "context": context,
                "question": query
            })
            
            return response
            
        except Exception as e:
            logger.error(f"Error in RAG query: {e}")
            return f"An error occurred while searching documentation: {str(e)}"
    
    def handle_weather_query(self, query: str) -> str:
        """
        Canlı hava durumu sorgularını işler.
        
        Adımlar:
        1. LLM ile sorgudan şehir isimlerini çıkar
        2. Her şehir için OpenWeatherMap API'sini çağır
        3. Veriyi kullanıcı dostu formatta sun
        
        Neden LLM extraction? Regex kırılgan, doğal dil ifadeleri için iyi çalışmaz.
        """
        try:
            # LLM ile şehir isimlerini extract et
            extraction_prompt = ChatPromptTemplate.from_messages([
                ("system", "Extract city names from the user's weather query. Return ONLY the city names, separated by commas."),
                ("user", "{query}")
            ])
            
            extraction_chain = extraction_prompt | self.llm | StrOutputParser()
            cities_str = extraction_chain.invoke({"query": query})
            
            # Virgülle ayrılmış string'i list'e çevir
            cities = [city.strip() for city in cities_str.split(",") if city.strip()]
            
            if not cities:
                return "I couldn't identify which cities you're asking about. Please specify the city name(s)."
            
            # Her şehir için hava durumunu çek
            results = {}
            for city in cities:
                weather = self.weather_api.get_current_weather(city)
                results[city] = weather
            
            # Çıktıyı formatla: tek şehir detaylı, birden fazla şehir kompakt
            if len(cities) == 1:
                weather = results[cities[0]]
                if "error" in weather:
                    return f"Sorry, I couldn't get weather data: {weather['error']}"
                
                response_text = f"""Current weather in {weather['city']}, {weather['country']}:

Temperature: {weather['temperature']}°C (feels like {weather['feels_like']}°C)
Condition: {weather['description']}
Humidity: {weather['humidity']}%
Wind: {weather['wind_speed']} m/s {weather.get('wind_direction_desc', '')}
Cloud coverage: {weather['clouds']}%
Pressure: {weather['pressure']} hPa"""
                
                if weather['visibility']:
                    response_text += f"\nVisibility: {weather['visibility']} km"
                
                return response_text
            
            else:
                # Birden fazla şehir için kompakt format
                response_lines = ["Weather for multiple cities:"]
                for city in cities:
                    weather = results[city]
                    if "error" not in weather:
                        response_lines.append(
                            f"\n{weather['city']}, {weather['country']}: "
                            f"{weather['temperature']}°C, {weather['description']}"
                        )
                    else:
                        response_lines.append(
                            f"\n{city}: {weather['error']}"
                        )
                
                return "\n".join(response_lines)
                
        except Exception as e:
            logger.error(f"Error in weather query: {e}")
            return f"An error occurred while fetching weather data: {str(e)}"
    
    def process_query(self, query: str) -> str:
        """
        Ana query işleme metodu - tüm sorgular buradan geçer.
        
        İş akışı:
        1. Kullanıcı mesajını memory'e ekle
        2. Intent'i tespit et (RAG/Weather/General)
        3. Context dolmuşsa sıkıştır
        4. Intent'e göre uygun handler'ı çağır
        5. Cevabı memory'e ekle ve döndür
        """
        try:
            # 1. Memory'e ekle
            self.memory_manager.add_message("user", query)
            
            # 2. Intent classification
            intent = self.classify_intent(query)
            
            # 3. Context dolduysa sıkıştır (kullanıcı fark etmez)
            if self.memory_manager.should_summarize():
                logger.info("Compressing conversation history...")
                self.memory_manager.compress_history()
            
            # 4. Intent-based routing
            if intent == "rag":
                response = self.handle_rag_query(query)
            elif intent == "weather_api":
                response = self.handle_weather_query(query)
            else:
                # Genel konuşma - sadece LLM ile cevap ver
                general_prompt = ChatPromptTemplate.from_messages([
                    ("system", self.system_prompt),
                    ("user", "{query}")
                ])
                chain = general_prompt | self.llm | StrOutputParser()
                response = chain.invoke({"query": query})
            
            # 5. Cevabı memory'e ekle
            self.memory_manager.add_message("assistant", response)
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return f"I encountered an error: {str(e)}"

