#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Thiết lập cấu hình mặc định cho n3n OS kết nối thẳng tới Ollama Local
"""
import os
import json

APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SETTINGS_PATH = os.path.join(APP_DIR, "server", "settings.json")

def setup_ollama_config():
    settings = {
        "workspace_name": "n3n OS",
        "setup_done": True,
        "auth": {
            "username": "",
            "password_hash": "",
            "salt": "",
            "totp": {"enabled": False, "secret": "", "recovery": [], "last_step": 0}
        },
        "branding": {"logo_ext": "", "logo_v": 0},
        "domain": {"custom": ""},
        "locale": {
            "ui_lang": "vi",
            "reply_lang": "vi",
            "tz": "Asia/Ho_Chi_Minh",
            "currency": "VND"
        },
        "voice": {
            "tts_provider": "edge",
            "openai_tts_voice": "alloy",
            "openai_tts_model": "gpt-4o-mini-tts",
            "elevenlabs_key": "",
            "elevenlabs_voice": "21m00Tcm4TlvDq8ikWAM",
            "elevenlabs_model": "eleven_multilingual_v2",
            "mode": "fast",
            "brain_provider": "",
            "brain_model": "",
            "stt_provider": "browser",
            "stt_model": "",
            "live_provider": "gemini",
            "live_model": "",
            "live_voice": ""
        },
        "model": {
            "main": {
                "provider": "ollama-local",
                "model": "qwen2.5:32b"
            },
            "auxiliary": {
                "model": "qwen2.5:14b"
            },
            "telegram": {
                "provider": "ollama-local",
                "model": "qwen2.5:32b"
            },
            "gia_goi_thang_usd": 0,
            "ngan_sach_thang_usd": 0,
            "tu_phanh": False,
            "tran_5h": 0,
            "bao_cao_tuan": "",
            "reasoning": "off",
            "claude_auth": "subscription",
            "openrouter_key": "",
            "anthropic_api_key": "",
            "openai_api_key": "",
            "gemini_api_key": "",
            "groq_api_key": "",
            "ollama_key": "",
            "openai_compat_base": "",
            "openai_compat_key": "",
            "ollama_local_endpoint": "http://127.0.0.1:11434",
            "ollama_local_key": "",
            "ollama_local_specs": {
                "source": "auto",
                "ram_gb": 32,
                "has_gpu": True,
                "vram_gb": 16
            },
            "openai_oauth": {
                "access_token": "", "refresh_token": "", "id_token": "",
                "account_id": "", "plan": "", "expires_at": 0
            },
            "engine": "ollama-local",
            "claude_model": "",
            "openrouter_model": "openai/gpt-4o-mini"
        }
    }

    with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
        json.dump(settings, f, ensure_ascii=False, indent=2)

    print(f"Đã tạo cấu hình sẵn sàng tại: {SETTINGS_PATH}")
    print("Main Model: qwen2.5:32b (Ollama Local)")
    print("Background Model: qwen2.5:14b (Ollama Local)")
    print("Endpoint: http://127.0.0.1:11434")

if __name__ == "__main__":
    setup_ollama_config()
