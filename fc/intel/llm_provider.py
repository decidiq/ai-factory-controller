"""LLM Provider abstraction — support Groq (gratis), DeepSeek, OpenAI.

Provider utama sekarang: Groq (gratis, cepat, Bahasa Indonesia bagus).
Bisa ditambah provider lain dengan meng-extend LLMProvider.
"""
import os
from abc import ABC, abstractmethod
from typing import Dict, List, Optional

import streamlit as st


class LLMProvider(ABC):
    """Base class untuk semua LLM provider."""

    name: str = "base"

    @abstractmethod
    def ask(self, question: str, context: str,
            history: Optional[List[Dict]] = None) -> str:
        """Kirim pertanyaan + context ke LLM, kembalikan jawaban."""
        ...

    @abstractmethod
    def is_available(self) -> bool:
        """Cek apakah API key tersedia & provider siap."""
        ...


# ==================== GROQ PROVIDER (GRATIS) ====================
class GroqProvider(LLMProvider):
    """Groq API provider (OpenAI-compatible).

    Model: llama-3.3-70b-versatile
    - Gratis: 14.400 permintaan/hari
    - Cepat dan bagus untuk Bahasa Indonesia
    - Daftar: https://console.groq.com/
    """

    name = "groq"
    BASE_URL = "https://api.groq.com/openai/v1"
    MODEL = "openai/gpt-oss-120b"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or self._get_api_key()

    def _get_api_key(self) -> Optional[str]:
        # Prioritas: st.secrets > env var
        try:
            key = st.secrets.get("GROQ_API_KEY")
            if key:
                return key
        except Exception:
            pass
        return os.environ.get("GROQ_API_KEY")
    
    def is_available(self) -> bool:
        return bool(self.api_key)

    def ask(self, question: str, context: str,
            history: Optional[List[Dict]] = None) -> str:
        from openai import OpenAI

        client = OpenAI(api_key=self.api_key, base_url=self.BASE_URL)

        system_prompt = (
            "Anda adalah Decidiq AI Copilot, asisten analitik untuk pabrik "
            "manufaktur.\n\n"
            f"DATA KONTEKS (dari sistem Decidiq):\n{context}\n\n"
            "ATURAN:\n"
            "1. Jawab dalam Bahasa Indonesia yang profesional tapi ramah.\n"
            "2. Selalu berdasarkan data di atas — JANGAN mengarang angka.\n"
            "3. Kalau data tidak ada, katakan 'data tidak tersedia'.\n"
            "4. Jawaban singkat, padat, fokus ke insight & rekomendasi.\n"
            "5. Kalau relevan, sebutkan dampak Rp atau rekomendasi aksi.\n"
        )

        messages = [{"role": "system", "content": system_prompt}]
        if history:
            messages.extend(history[-4:])  # max 4 pesan terakhir
        messages.append({"role": "user", "content": question})

        response = client.chat.completions.create(
            model=self.MODEL,
            messages=messages,
            temperature=0.3,
            max_tokens=800,
            timeout=15,
        )
        return response.choices[0].message.content


# ==================== DEEPSEEK PROVIDER (BERBAYAR) ====================
class DeepSeekProvider(LLMProvider):
    """DeepSeek API provider (OpenAI-compatible).

    Model: deepseek-chat
    - Berbayar: ~Rp 10-20 per pertanyaan
    - Kualitas Bahasa Indonesia lebih bagus dari Groq
    - Daftar: https://platform.deepseek.com/
    """

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

    def ask(self, question: str, context: str,
            history: Optional[List[Dict]] = None) -> str:
        from openai import OpenAI

        client = OpenAI(api_key=self.api_key, base_url=self.BASE_URL)

        system_prompt = (
            "Anda adalah Decidiq AI Copilot, asisten analitik untuk pabrik "
            "manufaktur.\n\n"
            f"DATA KONTEKS (dari sistem Decidiq):\n{context}\n\n"
            "ATURAN:\n"
            "1. Jawab dalam Bahasa Indonesia yang profesional tapi ramah.\n"
            "2. Selalu berdasarkan data di atas — JANGAN mengarang angka.\n"
            "3. Kalau data tidak ada, katakan 'data tidak tersedia'.\n"
            "4. Jawaban singkat, padat, fokus ke insight & rekomendasi.\n"
            "5. Kalau relevan, sebutkan dampak Rp atau rekomendasi aksi.\n"
        )

        messages = [{"role": "system", "content": system_prompt}]
        if history:
            messages.extend(history[-4:])
        messages.append({"role": "user", "content": question})

        response = client.chat.completions.create(
            model=self.MODEL,
            messages=messages,
            temperature=0.3,
            max_tokens=800,
            timeout=15,
        )
        return response.choices[0].message.content


# ==================== PROVIDER REGISTRY ====================
PROVIDERS = {
    "groq": GroqProvider,
    "deepseek": DeepSeekProvider,
}


def get_provider(name: str = "groq") -> Optional[LLMProvider]:
    """Factory: kembalikan instance provider jika tersedia, else None.

    Default: Groq (gratis). Kalau Groq tidak tersedia, coba DeepSeek.
    """
    # Kalau user minta provider spesifik
    if name in PROVIDERS:
        provider = PROVIDERS[name]()
        if provider.is_available():
            return provider

    # Fallback: coba semua provider yang tersedia
    for prov_name in ["groq", "deepseek"]:
        cls = PROVIDERS.get(prov_name)
        if not cls:
            continue
        provider = cls()
        if provider.is_available():
            return provider

    return None


def list_available_providers() -> List[str]:
    """Return list nama provider yang tersedia (ada API key-nya)."""
    available = []
    for name, cls in PROVIDERS.items():
        try:
            if cls().is_available():
                available.append(name)
        except Exception:
            continue
    return available