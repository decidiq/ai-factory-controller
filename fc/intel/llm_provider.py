"""LLM Provider abstraction — support Groq (gratis), DeepSeek, OpenAI."""
import os
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Iterator

import streamlit as st


class LLMProvider(ABC):
    """Base class untuk semua LLM provider."""
    name: str = "base"

    @abstractmethod
    def ask(self, question: str, context: str, history: Optional[List[Dict]] = None) -> str:
        ...

    @abstractmethod
    def ask_stream(self, question: str, context: str, history: Optional[List[Dict]] = None) -> Iterator[str]:
        ...

    @abstractmethod
    def is_available(self) -> bool:
        ...


# ==================== GROQ PROVIDER (GRATIS) ====================
class GroqProvider(LLMProvider):
    name = "groq"
    BASE_URL = "https://api.groq.com/openai/v1"
    MODEL = "openai/gpt-oss-120b"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or self._get_api_key()

    def _get_api_key(self) -> Optional[str]:
        try:
            key = st.secrets.get("GROQ_API_KEY")
            if key:
                return key
        except Exception:
            pass
        return os.environ.get("GROQ_API_KEY")
    
    def is_available(self) -> bool:
        return bool(self.api_key)

    def _build_messages(self, question: str, context: str, history: Optional[List[Dict]]):
        system_prompt = (
            "Anda adalah Decidiq AI Copilot, asisten analitik untuk pabrik manufaktur.\n\n"
            f"DATA KONTEKS:\n{context}\n\n"
            "ATURAN:\n"
            "1. Jawab dalam Bahasa Indonesia profesional.\n"
            "2. Berdasarkan data di atas — JANGAN mengarang angka.\n"
            "3. Kalau data kosong, katakan 'data tidak tersedia'.\n"
            "4. Format WAJIB: **Ringkasan** → **Temuan** → **Rekomendasi**.\n"
            "5. Sebutkan dampak Rp jika relevan.\n"
            "6. DILARANG KERAS menggunakan tag HTML (seperti <table>, <br>, <b>, <ul>).\n"
            "   Gunakan HANYA format Markdown murni. Untuk tabel gunakan pipa (|), "
            "untuk baris baru gunakan enter (newline), untuk bold gunakan **.\n"
        )
        messages = [{"role": "system", "content": system_prompt}]
        if history:
            messages.extend(history[-4:])
        messages.append({"role": "user", "content": question})
        return messages

    def ask(self, question: str, context: str, history: Optional[List[Dict]] = None) -> str:
        from openai import OpenAI
        client = OpenAI(api_key=self.api_key, base_url=self.BASE_URL)
        messages = self._build_messages(question, context, history)
        response = client.chat.completions.create(
            model=self.MODEL, messages=messages, temperature=0.3, max_tokens=4000, timeout=30,
        )
        return response.choices[0].message.content

    def ask_stream(self, question: str, context: str, history: Optional[List[Dict]] = None) -> Iterator[str]:
        from openai import OpenAI
        client = OpenAI(api_key=self.api_key, base_url=self.BASE_URL)
        messages = self._build_messages(question, context, history)
        stream = client.chat.completions.create(
            model=self.MODEL, messages=messages, temperature=0.3, max_tokens=4000, timeout=30, stream=True,
        )
        for chunk in stream:
            content = chunk.choices[0].delta.content
            if content:
                yield content


# ==================== DEEPSEEK PROVIDER ====================
class DeepSeekProvider(LLMProvider):
    name = "deepseek"
    BASE_URL = "https://api.deepseek.com/v1"
    MODEL = "deepseek-chat"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or self._get_api_key()

    def _get_api_key(self) -> Optional[str]:
        try:
            key = st.secrets.get("DEEPSEEK_API_KEY")
            if key:
                return key
        except Exception:
            pass
        return os.environ.get("DEEPSEEK_API_KEY")

    def is_available(self) -> bool:
        return bool(self.api_key)

    def _build_messages(self, question: str, context: str, history: Optional[List[Dict]]):
        system_prompt = (
            "Anda adalah Decidiq AI Copilot, asisten analitik untuk pabrik manufaktur.\n\n"
            f"DATA KONTEKS:\n{context}\n\n"
            "ATURAN:\n"
            "1. Jawab dalam Bahasa Indonesia profesional.\n"
            "2. Berdasarkan data di atas — JANGAN mengarang angka.\n"
            "3. Kalau data kosong, katakan 'data tidak tersedia'.\n"
            "4. Format WAJIB: **Ringkasan** → **Temuan** → **Rekomendasi**.\n"
            "5. Sebutkan dampak Rp jika relevan.\n"
            "6. DILARANG KERAS menggunakan tag HTML (seperti <table>, <br>, <b>, <ul>).\n"
            "   Gunakan HANYA format Markdown murni. Untuk tabel gunakan pipa (|), "
            "untuk baris baru gunakan enter (newline), untuk bold gunakan **.\n"
        )
        messages = [{"role": "system", "content": system_prompt}]
        if history:
            messages.extend(history[-4:])
        messages.append({"role": "user", "content": question})
        return messages

    def ask(self, question: str, context: str, history: Optional[List[Dict]] = None) -> str:
        from openai import OpenAI
        client = OpenAI(api_key=self.api_key, base_url=self.BASE_URL)
        messages = self._build_messages(question, context, history)
        response = client.chat.completions.create(
            model=self.MODEL, messages=messages, temperature=0.3, max_tokens=4000, timeout=30,
        )
        return response.choices[0].message.content

    def ask_stream(self, question: str, context: str, history: Optional[List[Dict]] = None) -> Iterator[str]:
        from openai import OpenAI
        client = OpenAI(api_key=self.api_key, base_url=self.BASE_URL)
        messages = self._build_messages(question, context, history)
        stream = client.chat.completions.create(
            model=self.MODEL, messages=messages, temperature=0.3, max_tokens=4000, timeout=30, stream=True,
        )
        for chunk in stream:
            content = chunk.choices[0].delta.content
            if content:
                yield content


# ==================== PROVIDER REGISTRY ====================
PROVIDERS = {
    "groq": GroqProvider,
    "deepseek": DeepSeekProvider,
}

def get_provider(name: str = "groq") -> Optional[LLMProvider]:
    if name in PROVIDERS:
        provider = PROVIDERS[name]()
        if provider.is_available():
            return provider
    for prov_name in ["groq", "deepseek"]:
        cls = PROVIDERS.get(prov_name)
        if not cls:
            continue
        provider = cls()
        if provider.is_available():
            return provider
    return None

def list_available_providers() -> List[str]:
    available = []
    for name, cls in PROVIDERS.items():
        try:
            if cls().is_available():
                available.append(name)
        except Exception:
            continue
    return available