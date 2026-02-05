#!/usr/bin/env python3
"""
DGC Backup Model Access
=======================

Provides fallback to Kimi 2.5 and Ollama models when Claude/Opus hits rate limits.
Integrates with dharmic_claw_heartbeat for always-on operation.

Usage:
    from dgc_backup_models import BackupModelClient
    
    client = BackupModelClient()
    response = client.generate(
        prompt="Your prompt here",
        preferred_model="kimi"  # or "ollama", "auto"
    )
"""

import os
import sys
import asyncio
from typing import Optional, Dict
from pathlib import Path

# Add night_cycle to path for openrouter_backend
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "night_cycle"))

class BackupModelClient:
    """
    Backup model client for DGC when primary models hit limits.
    
    Priority:
    1. Kimi K2.5 (via OpenRouter) - closest to Claude quality
    2. Ollama Cloud (free tier)
    3. Ollama Local (if available)
    """
    
    def __init__(self):
        self.openrouter_key = os.environ.get("OPENROUTER_API_KEY")
        self.ollama_cloud_key = os.environ.get("OLLAMA_API_KEY")
        self.preferred_backup = os.environ.get("DGC_BACKUP_MODEL", "kimi")
        
        # Model endpoints
        self.openrouter_url = "https://openrouter.ai/api/v1/chat/completions"
        self.ollama_cloud_url = "https://api.ollama.com/v1/chat/completions"
        self.ollama_local_url = "http://localhost:11434/api/generate"
        
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        preferred_model: Optional[str] = None,
        max_tokens: int = 2000,
        temperature: float = 0.7
    ) -> Dict:
        """
        Generate response using backup models.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            preferred_model: "kimi", "ollama_cloud", "ollama_local", or "auto"
            max_tokens: Max tokens to generate
            temperature: Sampling temperature
            
        Returns:
            Dict with 'success', 'model', 'content', 'error'
        """
        model = preferred_model or self.preferred_backup
        
        # Try in order of preference
        if model == "kimi" or model == "auto":
            result = self._try_kimi(prompt, system_prompt, max_tokens, temperature)
            if result["success"]:
                return result
        
        if model == "ollama_cloud" or model == "auto":
            result = self._try_ollama_cloud(prompt, system_prompt, max_tokens, temperature)
            if result["success"]:
                return result
        
        if model == "ollama_local" or model == "auto":
            result = self._try_ollama_local(prompt, system_prompt, max_tokens, temperature)
            if result["success"]:
                return result
        
        # All failed
        return {
            "success": False,
            "model": "none",
            "content": "",
            "error": "All backup models failed"
        }
    
    def _try_kimi(
        self,
        prompt: str,
        system_prompt: Optional[str],
        max_tokens: int,
        temperature: float
    ) -> Dict:
        """Try Kimi K2.5 via OpenRouter."""
        if not self.openrouter_key:
            return {"success": False, "model": "kimi", "content": "", "error": "No OpenRouter key"}
        
        try:
            headers = {
                "Authorization": f"Bearer {self.openrouter_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://dharmic-godel-claw.ai",
                "X-Title": "DGC Backup Models"
            }
            
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            data = {
                "model": "moonshotai/kimi-k2-instruct",
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature
            }
            
            import httpx
            response = httpx.post(
                self.openrouter_url,
                headers=headers,
                json=data,
                timeout=60.0
            )
            response.raise_for_status()
            
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            
            return {
                "success": True,
                "model": "kimi-k2.5",
                "content": content,
                "error": None
            }
            
        except Exception as e:
            return {"success": False, "model": "kimi", "content": "", "error": str(e)}
    
    def _try_ollama_cloud(
        self,
        prompt: str,
        system_prompt: Optional[str],
        max_tokens: int,
        temperature: float
    ) -> Dict:
        """Try Ollama Cloud models."""
        if not self.ollama_cloud_key:
            return {"success": False, "model": "ollama_cloud", "content": "", "error": "No Ollama Cloud key"}
        
        try:
            headers = {
                "Authorization": f"Bearer {self.ollama_cloud_key}",
                "Content-Type": "application/json"
            }
            
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            data = {
                "model": "gpt-oss:120b",
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature
            }
            
            import httpx
            response = httpx.post(
                self.ollama_cloud_url,
                headers=headers,
                json=data,
                timeout=60.0
            )
            response.raise_for_status()
            
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            
            return {
                "success": True,
                "model": "ollama-gpt-oss",
                "content": content,
                "error": None
            }
            
        except Exception as e:
            return {"success": False, "model": "ollama_cloud", "content": "", "error": str(e)}
    
    def _try_ollama_local(
        self,
        prompt: str,
        system_prompt: Optional[str],
        max_tokens: int,
        temperature: float
    ) -> Dict:
        """Try local Ollama instance."""
        try:
            import httpx
            
            # Check if Ollama is running
            response = httpx.get(f"{self.ollama_local_url}/api/tags", timeout=5.0)
            if response.status_code != 200:
                return {"success": False, "model": "ollama_local", "content": "", "error": "Ollama not running"}
            
            # Generate with local model
            full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
            
            data = {
                "model": "mistral:latest",
                "prompt": full_prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens
                }
            }
            
            response = httpx.post(
                self.ollama_local_url,
                json=data,
                timeout=120.0
            )
            response.raise_for_status()
            
            result = response.json()
            content = result.get("response", "")
            
            return {
                "success": True,
                "model": "ollama-mistral-local",
                "content": content,
                "error": None
            }
            
        except Exception as e:
            return {"success": False, "model": "ollama_local", "content": "", "error": str(e)}
    
    async def generate_async(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        preferred_model: Optional[str] = None,
        max_tokens: int = 2000,
        temperature: float = 0.7
    ) -> Dict:
        """Async version of generate."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self.generate,
            prompt,
            system_prompt,
            preferred_model,
            max_tokens,
            temperature
        )


class DGCFailsafeManager:
    """
    Manages DGC operation when primary models are unavailable.
    
    Automatically switches to backup models and logs the transition.
    """
    
    def __init__(self):
        self.backup_client = BackupModelClient()
        self.primary_available = True
        self.fallback_count = 0
        
    def generate_with_failsafe(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        force_backup: bool = False
    ) -> Dict:
        """
        Generate with automatic fallback to backup models.
        
        Args:
            prompt: The prompt
            system_prompt: Optional system context
            force_backup: Always use backup (for testing)
            
        Returns:
            Response dict with metadata
        """
        if force_backup or not self.primary_available:
            result = self.backup_client.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                preferred_model="auto"
            )
            
            if result["success"]:
                self.fallback_count += 1
                result["fallback_used"] = True
                result["fallback_count"] = self.fallback_count
            
            return result
        
        # Would normally try primary first
        # For now, just use backup
        return self.generate_with_failsafe(prompt, system_prompt, force_backup=True)


# =============================================================================
# CLI for testing
# =============================================================================

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python3 dgc_backup_models.py '<prompt>' [kimi|ollama_cloud|ollama_local]")
        sys.exit(1)
    
    prompt = sys.argv[1]
    model = sys.argv[2] if len(sys.argv) > 2 else "auto"
    
    print("🔌 DGC Backup Models")
    print(f"Prompt: {prompt[:50]}...")
    print(f"Preferred: {model}")
    print("-" * 50)
    
    client = BackupModelClient()
    result = client.generate(prompt, preferred_model=model)
    
    if result["success"]:
        print(f"✅ Success via {result['model']}")
        print(f"\n{result['content']}")
    else:
        print(f"❌ Failed: {result['error']}")
        sys.exit(1)
