"""Language detection and management service."""

import logging
from typing import Optional, Tuple, Dict
from langdetect import detect, detect_langs, LangDetectException
from langcodes import standardize_language_tag
from app.config import settings

logger = logging.getLogger(__name__)


class LanguageService:
    """Service for language detection, classification, and multi-language support."""
    
    # Supported languages
    SUPPORTED_LANGUAGES = {"en", "ru", "it"}
    LANGUAGE_NAMES = {
        "en": "English",
        "ru": "Russian",
        "it": "Italian",
    }
    
    # Intent classification prompts for each language
    INTENT_PROMPTS = {
        "en": """Analyze this message and classify it into one of these intents:
- appointment_request: Client wants to schedule a meeting/consultation
- office_hours: Client asks about office hours
- fee_question: Client asks about fees/pricing
- service_information: Client asks about services offered
- document_submission: Client wants to submit documents
- legal_question: Client asks a legal question
- other: Anything else

Respond with ONLY the intent name, nothing else.""",
        
        "ru": """Анализируйте это сообщение и классифицируйте его как один из этих намерений:
- appointment_request: Клиент хочет запланировать встречу/консультацию
- office_hours: Клиент спрашивает о часах работы
- fee_question: Клиент спрашивает о тарифах/ценах
- service_information: Клиент спрашивает об услугах
- document_submission: Клиент хочет отправить документы
- legal_question: Клиент задает юридический вопрос
- other: Что-то еще

Ответьте ТОЛЬКО названием намерения, ничего больше.""",
        
        "it": """Analizza questo messaggio e classificalo come uno di questi intenti:
- appointment_request: Il cliente vuole programmare una riunione/consultazione
- office_hours: Il cliente chiede l'orario di ufficio
- fee_question: Il cliente chiede su tariffe/prezzi
- service_information: Il cliente chiede informazioni sui servizi
- document_submission: Il cliente vuole inviare documenti
- legal_question: Il cliente pone una domanda legale
- other: Altro

Rispondi SOLO con il nome dell'intento, nient'altro.""",
    }
    
    # System prompts for response generation
    SYSTEM_PROMPTS = {
        "en": """You are a professional automated assistant for {professional_name} at {business_name}.

Your role:
1. Be professional and courteous
2. Acknowledge the client's message
3. Provide relevant information from the knowledge base if available
4. NEVER provide legal, medical, financial, or other professional advice
5. NEVER make predictions or guarantees about outcomes
6. If unclear about something, escalate to the professional
7. Always include the disclaimer at the end

Generate a response that is:
- Concise (under 100 words)
- Professional but friendly
- Non-committal about professional matters
- Helpful for the client""",
        
        "ru": """Вы профессиональный автоматический помощник {professional_name} в {business_name}.

Ваша роль:
1. Быть вежливым и профессиональным
2. Подтвердить получение сообщения клиента
3. Предоставить соответствующую информацию из базы знаний, если она доступна
4. НИКОГДА не давайте юридические, медицинские, финансовые или другие профессиональные советы
5. НИКОГДА не делайте прогнозы или гарантии о результатах
6. Если неясно, передайте дело профессионалу
7. Всегда включайте отказ от ответственности в конце

Создайте ответ, который:
- Краткий (менее 100 слов)
- Профессиональный, но дружелюбный
- Не обещающий в профессиональных вопросах
- Полезный для клиента""",
        
        "it": """Sei un assistente automatico professionale per {professional_name} presso {business_name}.

Il tuo ruolo:
1. Essere profesionale e cortese
2. Riconoscere il messaggio del cliente
3. Fornire informazioni rilevanti dalla base di conoscenza se disponibile
4. NON fornire mai consigli legali, medici, finanziari o di altra natura professionale
5. NON fare mai previsioni o garanzie sui risultati
6. Se non è chiaro, escalare al professionista
7. Includere sempre il disclaimer alla fine

Genera una risposta che sia:
- Concisa (meno di 100 parole)
- Professionale ma amichevole
- Non impegnativa su questioni professionali
- Utile per il cliente""",
    }
    
    # Legal question responses
    LEGAL_QUESTION_RESPONSES = {
        "en": "Thank you for your message. A professional will review your inquiry and contact you shortly. This is an automated assistant and cannot provide legal advice.",
        "ru": "Спасибо за ваше сообщение. Профессионал рассмотрит вашу проблему и свяжется с вами в ближайшее время. Этот автоматический помощник не может давать юридические консультации.",
        "it": "Grazie per il vostro messaggio. Un professionista esaminerà la vostra domanda e vi contatterà a breve. Questo assistente automatico non può fornire consulenza legale.",
    }
    
    def __init__(self):
        """Initialize language service."""
        self.supported_languages = settings.SUPPORTED_LANGUAGES
        
    def detect_language(self, text: str, min_length: int = 3) -> Tuple[Optional[str], float]:
        """
        Detect the language of a given text.
        
        Args:
            text: Text to analyze
            min_length: Minimum text length for detection
            
        Returns:
            Tuple of (language_code, confidence) where language_code is ISO 639-1 code
            or (None, 0.0) if detection fails or language not supported
        """
        if not text or len(text.strip()) < min_length:
            logger.warning(f"Text too short for language detection: {len(text)} chars")
            return None, 0.0
        
        try:
            # Get all detected languages with probabilities
            detected_langs = detect_langs(text)
            
            if not detected_langs:
                logger.warning("No language detected")
                return None, 0.0
            
            # Get the most probable language
            detected_lang = detected_langs[0]
            lang_code = detected_lang.lang
            confidence = detected_lang.prob
            
            # Standardize language code (handle variants like zh-cn -> zh)
            try:
                lang_code = standardize_language_tag(lang_code).language
            except Exception:
                lang_code = lang_code.split("-")[0]  # Fallback: take first part
            
            # Check if language is supported
            if lang_code not in self.supported_languages:
                logger.info(f"Detected language '{lang_code}' not in supported: {self.supported_languages}")
                # Return detected language anyway for logging/analytics
                return lang_code, confidence
            
            logger.debug(f"Detected language: {lang_code} (confidence: {confidence:.2f})")
            return lang_code, confidence
            
        except LangDetectException as e:
            logger.warning(f"Language detection failed: {str(e)}")
            return None, 0.0
        except Exception as e:
            logger.error(f"Unexpected error in language detection: {str(e)}")
            return None, 0.0
    
    def get_intent_prompt(self, language: str) -> str:
        """
        Get the intent classification prompt for a language.
        
        Args:
            language: ISO 639-1 language code
            
        Returns:
            Intent classification prompt in the specified language
        """
        return self.INTENT_PROMPTS.get(language, self.INTENT_PROMPTS["en"])
    
    def get_system_prompt(self, language: str, professional_name: str, business_name: str) -> str:
        """
        Get the system prompt for response generation.
        
        Args:
            language: ISO 639-1 language code
            professional_name: Name of the professional
            business_name: Name of the business
            
        Returns:
            System prompt in the specified language with filled-in details
        """
        prompt_template = self.SYSTEM_PROMPTS.get(language, self.SYSTEM_PROMPTS["en"])
        return prompt_template.format(
            professional_name=professional_name,
            business_name=business_name
        )
    
    def get_legal_question_response(self, language: str) -> str:
        """
        Get the response for legal questions.
        
        Args:
            language: ISO 639-1 language code
            
        Returns:
            Legal question response in the specified language
        """
        return self.LEGAL_QUESTION_RESPONSES.get(language, self.LEGAL_QUESTION_RESPONSES["en"])
    
    def get_disclaimer(self, language: str) -> str:
        """
        Get the disclaimer message for a language.
        
        Args:
            language: ISO 639-1 language code
            
        Returns:
            Disclaimer in the specified language
        """
        disclaimers = {
            "en": settings.TENANT_DISCLAIMER_EN,
            "ru": settings.TENANT_DISCLAIMER_RU,
            "it": settings.TENANT_DISCLAIMER_IT,
        }
        return disclaimers.get(language, disclaimers.get("en", ""))
    
    def get_office_hours(self, language: str) -> Optional[str]:
        """
        Get the office hours for a language.
        
        Args:
            language: ISO 639-1 language code
            
        Returns:
            Office hours in the specified language, or None
        """
        office_hours_map = {
            "en": settings.TENANT_OFFICE_HOURS_EN,
            "ru": settings.TENANT_OFFICE_HOURS_RU,
            "it": settings.TENANT_OFFICE_HOURS_IT,
        }
        return office_hours_map.get(language)
    
    def is_language_supported(self, language: str) -> bool:
        """
        Check if a language is supported.
        
        Args:
            language: ISO 639-1 language code
            
        Returns:
            True if language is supported
        """
        return language in self.supported_languages
    
    def get_language_name(self, language: str) -> str:
        """
        Get the display name of a language.
        
        Args:
            language: ISO 639-1 language code
            
        Returns:
            Display name of the language
        """
        return self.LANGUAGE_NAMES.get(language, language.upper())
    
    def extract_date_time_patterns(self, text: str, language: str) -> Dict[str, str]:
        """
        Extract date and time patterns based on language.
        
        Args:
            text: Text to analyze
            language: ISO 639-1 language code
            
        Returns:
            Dictionary with detected dates and times
        """
        import re
        from datetime import datetime
        
        patterns = {
            # English patterns
            "en": {
                "dates": [
                    r"\b\d{1,2}\s(?:January|February|March|April|May|June|July|August|September|October|November|December)\b",
                    r"\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s\d{1,2}\b",
                    r"\b\d{1,2}/\d{1,2}/\d{2,4}\b",
                    r"\b\d{4}-\d{1,2}-\d{1,2}\b",
                ],
                "times": [
                    r"\b\d{1,2}:\d{2}\s?(?:AM|PM|am|pm)\b",
                    r"\b\d{1,2}:\d{2}\b",
                    r"\b\d{1,2}\s?(?:AM|PM|am|pm)\b",
                ],
            },
            # Russian patterns
            "ru": {
                "dates": [
                    r"\b\d{1,2}\s(?:января|февраля|марта|апреля|мая|июня|июля|августа|сентября|октября|ноября|декабря)\b",
                    r"\b\d{1,2}\.\d{1,2}\.\d{2,4}\b",
                    r"\b\d{1,2}-\d{1,2}-\d{2,4}\b",
                ],
                "times": [
                    r"\b\d{1,2}:\d{2}\b",
                    r"\b\d{1,2}\s?(?:часов|часа)\b",
                ],
            },
            # Italian patterns
            "it": {
                "dates": [
                    r"\b\d{1,2}\s(?:gennaio|febbraio|marzo|aprile|maggio|giugno|luglio|agosto|settembre|ottobre|novembre|dicembre)\b",
                    r"\b\d{1,2}/\d{1,2}/\d{2,4}\b",
                    r"\b\d{1,2}-\d{1,2}-\d{2,4}\b",
                ],
                "times": [
                    r"\b\d{1,2}:\d{2}\b",
                    r"\b\d{1,2}\s?(?:di mattina|del pomeriggio|di sera)\b",
                ],
            },
        }
        
        result = {
            "dates": [],
            "times": [],
        }
        
        language_patterns = patterns.get(language, patterns.get("en", {}))
        
        # Extract dates
        for pattern in language_patterns.get("dates", []):
            matches = re.findall(pattern, text, re.IGNORECASE)
            result["dates"].extend(matches)
        
        # Extract times
        for pattern in language_patterns.get("times", []):
            matches = re.findall(pattern, text, re.IGNORECASE)
            result["times"].extend(matches)
        
        return result
