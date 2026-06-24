"""AI service for message generation and intent detection."""

import json
import logging
from typing import Optional, List, Tuple

import requests
import structlog
from app.config import settings
from app.models import Intent, MessageSender, Message
from app.services.language_service import LanguageService
from sqlalchemy.orm import Session

logger = structlog.get_logger(__name__)


class AIService:
    """Service for AI-powered message generation and analysis."""

    def __init__(self):
        """Initialize AI service with Ollama as primary provider."""
        self.provider = settings.AI_PROVIDER.lower()
        self.max_tokens = settings.MAX_TOKENS
        self.temperature = settings.TEMPERATURE
        self.language_service = LanguageService()
        
        # Normalize and validate provider
        valid_providers = {"ollama", "openai", "gemini"}
        if self.provider not in valid_providers:
            logger.warning(
                f"Unknown AI provider: {self.provider}. Valid options: {valid_providers}. "
                f"Defaulting to ollama (recommended for local/offline use)."
            )
            self.provider = "ollama"
        
        # Initialize provider-specific configuration
        if self.provider == "ollama":
            self._init_ollama()
        elif self.provider == "openai":
            self._init_openai()
        elif self.provider == "gemini":
            self._init_gemini()
    
    def _init_ollama(self):
        """Initialize Ollama provider (local, offline, free)."""
        self.base_url = settings.OLLAMA_BASE_URL
        self.model = settings.OLLAMA_MODEL
        self.embedding_model = settings.OLLAMA_EMBEDDING_MODEL
        logger.info(
            f"Ollama provider initialized: {self.model} (offline/local, free)"
        )
    
    def _init_openai(self):
        """Initialize OpenAI provider (cloud-based, paid)."""
        if not settings.OPENAI_API_KEY:
            logger.warning(
                "OpenAI selected but API key not configured. "
                "Falling back to Ollama. "
                "See: https://platform.openai.com/account/api-keys"
            )
            self._init_ollama()
            self.provider = "ollama"
            return
        
        self.api_key = settings.OPENAI_API_KEY
        self.model = settings.OPENAI_MODEL
        self.embedding_model = settings.OPENAI_EMBEDDING_MODEL
        logger.info(
            f"OpenAI provider initialized: {self.model} (cloud-based, paid)"
        )
    
    def _init_gemini(self):
        """Initialize Google Gemini provider (cloud-based, free tier available)."""
        if not settings.GOOGLE_API_KEY:
            logger.warning(
                "Gemini selected but API key not configured. "
                "Falling back to Ollama. "
                "See: https://aistudio.google.com/apikey"
            )
            self._init_ollama()
            self.provider = "ollama"
            return
        
        self.api_key = settings.GOOGLE_API_KEY
        self.model = settings.GEMINI_MODEL
        self.embedding_model = "gemini-embedding"
        logger.info(
            f"Gemini provider initialized: {self.model} (cloud-based, free tier available)"
        )

    def detect_language_and_intent(self, message: str) -> Tuple[str, Intent, float]:
        """
        Detect message language and intent using AI.
        
        Args:
            message: Message content
            
        Returns:
            Tuple of (language_code, detected_intent, language_confidence)
        """
        if not message:
            logger.warning(
                "empty_message_received",
                operation="language_intent_detection"
            )
            return settings.TENANT_DEFAULT_LANGUAGE, Intent.OTHER, 0.0
        
        try:
            logger.debug(
                "language_intent_detection_started",
                message_length=len(message)
            )
            
            # Step 1: Detect language
            detected_lang, lang_confidence = self.language_service.detect_language(message)
            
            # If language not detected or not supported, use default
            if not detected_lang or not self.language_service.is_language_supported(detected_lang):
                logger.info(
                    "language_detection_inconclusive",
                    detected_lang=detected_lang,
                    using_default=settings.TENANT_DEFAULT_LANGUAGE
                )
                detected_lang = settings.TENANT_DEFAULT_LANGUAGE
                lang_confidence = 0.0
            
            logger.info(
                "language_detected",
                language=detected_lang,
                confidence=round(lang_confidence, 3)
            )
            
            # Step 2: Detect intent using language-aware prompt
            intent = self.detect_intent(message, detected_lang)
            
            logger.info(
                "language_intent_detection_completed",
                language=detected_lang,
                intent=intent.value,
                confidence=round(lang_confidence, 3)
            )
            
            return detected_lang, intent, lang_confidence
            
        except Exception as e:
            logger.error(
                "language_intent_detection_error",
                error=str(e),
                exc_info=True
            )
            return settings.TENANT_DEFAULT_LANGUAGE, Intent.OTHER, 0.0

    def detect_intent(self, message: str, language: str = "en") -> Intent:
        """
        Detect message intent using AI with language awareness.
        
        Uses configured provider (Ollama recommended for offline, local use).
        
        Args:
            message: Message content
            language: ISO 639-1 language code for the message
            
        Returns:
            Detected intent
        """
        try:
            logger.debug(
                "intent_detection_started",
                provider=self.provider,
                language=language,
                message_length=len(message)
            )
            
            # Get language-specific intent classification prompt
            prompt = self.language_service.get_intent_prompt(language)
            prompt += f"\n\nMessage: \"{message}\"\n\nRespond with ONLY the intent name in lowercase, nothing else."

            # Call appropriate provider
            intent_str = self._call_provider(
                prompt, 
                temperature=0.3, 
                max_tokens=50,
                operation="intent_detection"
            )
            
            if not intent_str:
                return Intent.OTHER
                
            intent_str = intent_str.strip().lower()
            
            # Map to Intent enum
            intent_map = {
                "appointment_request": Intent.APPOINTMENT_REQUEST,
                "office_hours": Intent.OFFICE_HOURS,
                "fee_question": Intent.FEE_QUESTION,
                "service_information": Intent.SERVICE_INFORMATION,
                "document_submission": Intent.DOCUMENT_SUBMISSION,
                "legal_question": Intent.LEGAL_QUESTION,
                "other": Intent.OTHER,
            }
            
            detected_intent = intent_map.get(intent_str, Intent.OTHER)
            
            logger.info(
                "intent_detected",
                intent=detected_intent.value,
                language=language,
                provider=self.provider,
                raw_response=intent_str
            )
            
            return detected_intent

        except Exception as e:
            logger.error(
                "intent_detection_error",
                language=language,
                provider=self.provider,
                error=str(e),
                exc_info=True
            )
            return Intent.OTHER

    def generate_response(
        self,
        conversation_id: str,
        message_content: str,
        detected_intent: Intent,
        detected_language: str,
        db: Session,
    ) -> Optional[str]:
        """
        Generate AI response for a message with language awareness.
        
        Uses configured provider (Ollama recommended for offline, local use).
        
        Args:
            conversation_id: Conversation ID
            message_content: Original message
            detected_intent: Detected intent
            detected_language: ISO 639-1 language code
            db: Database session
            
        Returns:
            Generated response in the detected language or None if error
        """
        try:
            from app.services.rag_service import RAGService
            from app.services.appointment_service import AppointmentService
            from app.config import settings
            
            # Use configured professional info
            business_name = settings.TENANT_BUSINESS_NAME
            professional_name = settings.TENANT_PROFESSIONAL_NAME
            
            # Get language-specific disclaimer and other settings
            disclaimer = self.language_service.get_disclaimer(detected_language)
            booking_url = settings.TENANT_BOOKING_URL
            office_hours = self.language_service.get_office_hours(detected_language)

            # Handle legal questions - never generate advice
            if detected_intent == Intent.LEGAL_QUESTION:
                base_response = self.language_service.get_legal_question_response(detected_language)
                return f"{base_response}\n\n{disclaimer}"

            # Handle appointment requests with possible auto-booking
            if detected_intent == Intent.APPOINTMENT_REQUEST:
                appointment_service = AppointmentService()
                
                if appointment_service.is_enabled():
                    # Extract appointment details from message (language-aware)
                    appt_info = appointment_service.extract_appointment_info(
                        message_content, 
                        language=detected_language
                    )
                    
                    # Try to create appointment
                    result = appointment_service.create_appointment(
                        client_phone=None,  # Should be passed from conversation
                        client_name=appt_info.get("client_name"),
                        preferred_date=appt_info.get("preferred_date"),
                        preferred_time=appt_info.get("preferred_time"),
                        notes=appt_info.get("notes")
                    )
                    
                    # Use result message if appointment creation succeeded
                    if result["status"] in ["confirmed", "pending"]:
                        base_response = result["message"]
                        logger.info(f"Auto-appointment created: {result.get('appointment_id')}")
                    else:
                        # Fall back to booking link with language-appropriate message
                        booking_messages = {
                            "en": f"I'd be happy to help you schedule an appointment. Please visit {booking_url or 'our booking page'} to schedule a time that works for you.",
                            "ru": f"Я с удовольствием помогу вам запланировать встречу. Пожалуйста, посетите {booking_url or 'нашу страницу бронирования'}, чтобы выбрать удобное для вас время.",
                            "it": f"Sarei felice di aiutarti a programmare un appuntamento. Visita {booking_url or 'la nostra pagina di prenotazione'} per scegliere un orario che ti conviene.",
                        }
                        base_response = booking_messages.get(detected_language, booking_messages["en"])
                else:
                    # Feature disabled - just provide booking link
                    booking_messages = {
                        "en": f"I'd be happy to help you schedule an appointment. Please visit {booking_url or 'our booking page'} to schedule a time that works for you.",
                        "ru": f"Я с удовольствием помогу вам запланировать встречу. Пожалуйста, посетите {booking_url or 'нашу страницу бронирования'}, чтобы выбрать удобное для вас время.",
                        "it": f"Sarei felice di aiutarti a programmare un appuntamento. Visita {booking_url or 'la nostra pagina di prenotazione'} per scegliere un orario che ti conviene.",
                    }
                    base_response = booking_messages.get(detected_language, booking_messages["en"])
                
                return f"{base_response}\n\n{disclaimer}"

            # Retrieve relevant knowledge (language-aware)
            rag_service = RAGService()
            relevant_context = rag_service.retrieve_context(
                query=message_content,
                db=db,
                language=detected_language
            )

            # Build context prompt
            context_prompt = ""
            if relevant_context:
                context_labels = {
                    "en": "Relevant Information:",
                    "ru": "Соответствующая информация:",
                    "it": "Informazioni rilevanti:",
                }
                context_prompt = f"\n{context_labels.get(detected_language, 'Relevant Information:')}:\n{relevant_context}\n"

            # Intent-specific prompts (language-aware)
            intent_instructions = {
                Intent.OFFICE_HOURS: self._get_office_hours_instruction(detected_language, office_hours),
                Intent.FEE_QUESTION: self._get_fee_question_instruction(detected_language),
                Intent.SERVICE_INFORMATION: self._get_service_info_instruction(detected_language),
                Intent.DOCUMENT_SUBMISSION: self._get_document_submission_instruction(detected_language),
                Intent.OTHER: self._get_general_instruction(detected_language),
            }

            instructions = intent_instructions.get(
                detected_intent,
                self._get_general_instruction(detected_language)
            )

            # Get language-specific system prompt
            system_prompt = self.language_service.get_system_prompt(
                detected_language,
                professional_name,
                business_name
            )

            prompt = f"""{system_prompt}

Client Message: "{message_content}"

Intent: {detected_intent.value}

Instructions: {instructions}

{context_prompt}

Response:"""

            # Call appropriate provider
            base_response = self._call_provider(
                prompt,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                operation="response_generation"
            )
            
            if not base_response:
                return None
            
            base_response = base_response.strip()
            
            # Add disclaimer
            final_response = f"{base_response}\n\n{disclaimer}"
            
            logger.debug(f"Generated response in {detected_language} using {self.provider}: {len(final_response)} chars")
            return final_response

        except Exception as e:
            logger.error(f"Error generating response: {str(e)}", exc_info=True)
            return None

    def _get_office_hours_instruction(self, language: str, office_hours: Optional[str]) -> str:
        """Get office hours instruction for a language."""
        instructions = {
            "en": f"Client is asking about office hours.\nOffice Hours: {office_hours or 'N/A'}",
            "ru": f"Клиент спрашивает о часах работы.\nЧасы работы: {office_hours or 'N/A'}",
            "it": f"Il cliente chiede l'orario di ufficio.\nOrari di ufficio: {office_hours or 'N/A'}",
        }
        return instructions.get(language, instructions["en"])

    def _get_fee_question_instruction(self, language: str) -> str:
        """Get fee question instruction for a language."""
        instructions = {
            "en": "Client is asking about fees/pricing. Use the provided information.",
            "ru": "Клиент спрашивает о тарифах/ценах. Используйте предоставленную информацию.",
            "it": "Il cliente chiede informazioni su tariffe/prezzi. Utilizza le informazioni fornite.",
        }
        return instructions.get(language, instructions["en"])

    def _get_service_info_instruction(self, language: str) -> str:
        """Get service information instruction for a language."""
        instructions = {
            "en": "Client is asking about services. Use the provided information.",
            "ru": "Клиент спрашивает об услугах. Используйте предоставленную информацию.",
            "it": "Il cliente chiede informazioni sui servizi. Utilizza le informazioni fornite.",
        }
        return instructions.get(language, instructions["en"])

    def _get_document_submission_instruction(self, language: str) -> str:
        """Get document submission instruction for a language."""
        instructions = {
            "en": "Client is submitting documents. Acknowledge receipt and provide next steps.",
            "ru": "Клиент отправляет документы. Подтвердите получение и укажите следующие шаги.",
            "it": "Il cliente sta inviando documenti. Riconosci la ricezione e fornisci i passaggi successivi.",
        }
        return instructions.get(language, instructions["en"])

    def _get_general_instruction(self, language: str) -> str:
        """Get general instruction for a language."""
        instructions = {
            "en": "General inquiry. Be helpful and professional.",
            "ru": "Общий запрос. Будьте полезны и профессиональны.",
            "it": "Domanda generale. Sii utile e professionale.",
        }
        return instructions.get(language, instructions["en"])

    def transcribe_audio(self, media_url: str, language: Optional[str] = None) -> Tuple[Optional[str], Optional[str]]:
        """
        Transcribe audio to text with language detection.
        
        NOTE: Audio transcription currently only supported with OpenAI (Whisper).
        For other providers, this will log a warning and return None.
        
        Args:
            media_url: URL of audio media
            language: Optional ISO 639-1 language code to guide transcription
            
        Returns:
            Tuple of (transcribed_text, detected_language) or (None, None) if error
        """
        # Audio transcription only works with OpenAI (Whisper model)
        if self.provider != "openai":
            logger.warning(
                f"Audio transcription only supported with OpenAI provider. "
                f"Current provider: {self.provider}. "
                f"Please switch to OpenAI for audio features."
            )
            return None, None
        
        if not settings.OPENAI_API_KEY:
            logger.warning("OpenAI API key not configured")
            return None, None

        try:
            from openai import OpenAI
            import tempfile
            
            # Download audio
            response = requests.get(media_url, timeout=30)
            if response.status_code != 200:
                logger.error(f"Failed to download audio: {response.status_code}")
                return None, None

            # Write to temp file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp.write(response.content)
                tmp_path = tmp.name

            try:
                # Transcribe using Whisper (multilingual)
                client = OpenAI(api_key=settings.OPENAI_API_KEY)
                with open(tmp_path, "rb") as audio_file:
                    # Language parameter helps guide transcription accuracy
                    transcription_params = {
                        "model": "whisper-1",
                        "file": audio_file,
                    }
                    
                    # Add language hint if provided and supported
                    if language and self.language_service.is_language_supported(language):
                        transcription_params["language"] = language
                    
                    transcript = client.audio.transcriptions.create(**transcription_params)
                    text = transcript.text
                
                # Auto-detect language from transcribed text if not provided
                detected_lang, lang_confidence = self.language_service.detect_language(text)
                
                logger.info(f"Audio transcribed: {len(text)} chars, detected language: {detected_lang} (confidence: {lang_confidence:.2f})")
                return text, detected_lang
                
            finally:
                # Clean up
                import os
                os.unlink(tmp_path)

        except Exception as e:
            logger.error(f"Error transcribing audio: {str(e)}")
            return None, None

    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """
        Generate embedding for text using configured provider.
        
        Ollama recommended for local/offline embeddings.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector or None if error
        """
        try:
            if not text or not text.strip():
                logger.warning("Empty text provided for embedding")
                return None
                
            if self.provider == "ollama":
                return self._get_ollama_embedding(text)
            elif self.provider == "openai":
                return self._get_openai_embedding(text)
            elif self.provider == "gemini":
                return self._get_gemini_embedding(text)
            else:
                logger.error(f"Unknown provider for embedding: {self.provider}")
                return None

        except Exception as e:
            logger.error(f"Error generating embedding with {self.provider}: {str(e)}")
            return None

    # ============ Unified Provider Interface ============
    
    def _call_provider(
        self, 
        prompt: str, 
        temperature: float = 0.7, 
        max_tokens: int = 500,
        operation: str = "generation"
    ) -> Optional[str]:
        """
        Call the configured AI provider for text generation.
        
        Unified interface supporting:
        - Ollama (local, offline, free - RECOMMENDED)
        - OpenAI (cloud-based, paid)
        - Gemini (cloud-based, free tier available)
        
        Args:
            prompt: Prompt to send to the model
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens in response
            operation: Description of the operation for logging
            
        Returns:
            Generated text or None if error
        """
        try:
            if self.provider == "ollama":
                logger.debug(f"Calling Ollama ({self.model}) for {operation}")
                return self._call_ollama(prompt, temperature, max_tokens)
            elif self.provider == "openai":
                logger.debug(f"Calling OpenAI ({self.model}) for {operation}")
                return self._call_openai(prompt, temperature, max_tokens)
            elif self.provider == "gemini":
                logger.debug(f"Calling Gemini ({self.model}) for {operation}")
                return self._call_gemini(prompt, temperature, max_tokens)
            else:
                logger.error(f"Unknown provider: {self.provider}")
                return None
        except Exception as e:
            logger.error(f"Provider call failed ({self.provider}, {operation}): {str(e)}")
            return None
    
    # ============ Provider-specific Methods ============
    
    def _call_ollama(self, prompt: str, temperature: float = 0.7, max_tokens: int = 500) -> Optional[str]:
        """
        Call Ollama API for text generation (local/offline).
        
        Ollama provides:
        - Local model execution (no internet required after setup)
        - Free (open source models)
        - Privacy (all data stays local)
        - Low latency
        - Works offline
        
        Models available:
        - mistral (7B - fast, balanced)
        - neural-chat (7B - optimized for chat)
        - orca-mini (3B - lightweight)
        - llama2 (7B-70B - various sizes)
        
        Setup: https://ollama.ai
        
        Args:
            prompt: Text prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response
            
        Returns:
            Generated text or None
        """
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "temperature": temperature,
                    "num_predict": max_tokens,
                    "stream": False,
                },
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("response", "").strip()
            else:
                logger.error(f"Ollama API error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Ollama API call failed: {str(e)}")
            return None
    
    def _call_openai(self, prompt: str, temperature: float = 0.7, max_tokens: int = 500) -> Optional[str]:
        """
        Call OpenAI API for text generation (cloud-based, paid).
        
        OpenAI provides:
        - Highest quality responses
        - Fast processing (cloud-based)
        - Wide model selection (GPT-4, GPT-4o mini, GPT-3.5)
        - Multimodal capabilities
        - Requires internet
        - Usage-based pricing ($0.001-0.05 per request typically)
        
        Models available:
        - gpt-4 (most capable)
        - gpt-4-turbo (fast + capable)
        - gpt-4o (optimized)
        - gpt-4o-mini (fast + cost-effective - RECOMMENDED)
        - gpt-3.5-turbo (legacy, cheap)
        
        Setup: https://platform.openai.com/account/api-keys
        
        Also supports audio transcription (Whisper API) - see transcribe_audio()
        
        Args:
            prompt: Text prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response
            
        Returns:
            Generated text or None
        """
        try:
            from openai import OpenAI
            
            client = OpenAI(api_key=settings.OPENAI_API_KEY)
            response = client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"OpenAI API call failed: {str(e)}")
            return None
    
    def _call_gemini(self, prompt: str, temperature: float = 0.7, max_tokens: int = 500) -> Optional[str]:
        """
        Call Google Gemini API for text generation (cloud-based, free tier available).
        
        Google Gemini provides:
        - Good quality responses
        - Free tier available (with usage limits)
        - Paid tier for higher usage
        - Fast processing (cloud-based)
        - Multimodal capabilities
        - Requires internet
        
        Free tier: 60 requests per minute (good for testing)
        Pricing: Low cost for high volume
        
        Models available:
        - gemini-pro (text generation)
        - gemini-pro-vision (multimodal)
        - gemini-1.5-pro (latest)
        - gemini-1.5-flash (fast, lightweight)
        
        Setup: https://aistudio.google.com/apikey
        
        Args:
            prompt: Text prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response
            
        Returns:
            Generated text or None
        """
        try:
            import google.generativeai as genai
            
            genai.configure(api_key=settings.GOOGLE_API_KEY)
            model = genai.GenerativeModel(self.model)
            
            response = model.generate_content(
                prompt,
                generation_config={
                    "temperature": temperature,
                    "max_output_tokens": max_tokens,
                }
            )
            
            return response.text.strip()
            
        except Exception as e:
            logger.error(f"Gemini API call failed: {str(e)}")
            return None
    
    def _get_ollama_embedding(self, text: str) -> Optional[List[float]]:
        """
        Generate embedding using Ollama (local, offline, free).
        
        Ollama embedding models:
        - nomic-embed-text (recommended, good quality)
        - sentence-transformers/all-minilm-l6-v2
        - neural-embed-text
        
        Setup: ollama pull nomic-embed-text
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector or None
        """
        try:
            response = requests.post(
                f"{self.base_url}/api/embeddings",
                json={
                    "model": self.embedding_model,
                    "prompt": text,
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("embedding", None)
            else:
                logger.error(f"Ollama embedding error: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Ollama embedding call failed: {str(e)}")
            return None
    
    def _get_openai_embedding(self, text: str) -> Optional[List[float]]:
        """
        Generate embedding using OpenAI (cloud-based, paid).
        
        OpenAI embedding models:
        - text-embedding-3-small (recommended, fast + quality)
        - text-embedding-3-large (highest quality)
        - text-embedding-ada-002 (legacy)
        
        Pricing: ~$0.02 per million tokens
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector or None
        """
        try:
            from openai import OpenAI
            
            client = OpenAI(api_key=settings.OPENAI_API_KEY)
            response = client.embeddings.create(
                model=self.embedding_model,
                input=text,
            )
            return response.data[0].embedding
            
        except Exception as e:
            logger.error(f"OpenAI embedding call failed: {str(e)}")
            return None
    
    def _get_gemini_embedding(self, text: str) -> Optional[List[float]]:
        """
        Generate embedding using Google Gemini (cloud-based, free tier available).
        
        Google Gemini embedding models:
        - models/embedding-001 (default)
        - models/embedding-latest
        
        Free tier: Included in Gemini API quota
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector or None
        """
        try:
            import google.generativeai as genai
            
            genai.configure(api_key=settings.GOOGLE_API_KEY)
            result = genai.embed_content(
                model="models/embedding-001",
                content=text
            )
            return result["embedding"]
            
        except Exception as e:
            logger.error(f"Gemini embedding call failed: {str(e)}")
            return None
