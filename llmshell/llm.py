"""LLM integration for translating natural language to bash commands."""

import json
from dataclasses import dataclass
from typing import Any, Dict, Optional

import httpx

from .config import LLMConfig


@dataclass
class LLMResponse:
    """Response from LLM translation."""

    command: str
    explanation: Optional[str] = None
    confidence: Optional[float] = None
    error: Optional[str] = None


class LLMProvider:
    """Base class for LLM providers."""

    def __init__(self, config: LLMConfig):
        self.config = config
        self.client = httpx.Client(timeout=config.timeout)

    async def translate(
        self, natural_language: str, context: Optional[Dict[str, Any]] = None
    ) -> LLMResponse:
        """Translate natural language to bash command."""
        raise NotImplementedError

    async def list_models(self) -> list[str]:
        """List available models."""
        raise NotImplementedError

    async def test_connection(self) -> bool:
        """Test if the provider is accessible."""
        raise NotImplementedError

    def close(self):
        """Close the HTTP client."""
        self.client.close()


class OllamaProvider(LLMProvider):
    """Ollama LLM provider for local model inference."""

    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self.base_url = config.base_url.rstrip("/")

    def _build_prompt(
        self, natural_language: str, context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Build the prompt for the LLM."""
        system_prompt = """You are a Linux/Unix shell command translator. Your job is to convert natural language descriptions into precise, safe bash commands.

Rules:
1. Return ONLY the bash command, nothing else
2. Do not include explanations unless specifically asked
3. Use the most common and portable Unix commands
4. Prefer safer options when multiple approaches exist
5. If the request is unclear or potentially dangerous, suggest the safest interpretation
6. Do not execute or simulate command execution
7. Focus on commonly available commands (bash, coreutils, findutils, etc.)

Examples:
"list all files" -> ls -la
"find python files" -> find . -name "*.py"
"show disk usage" -> df -h
"show running processes" -> ps aux"""

        context_info = ""
        if context:
            if "cwd" in context:
                context_info += f"Current directory: {context['cwd']}\n"
            if "user" in context:
                context_info += f"Current user: {context['user']}\n"
            if "files" in context:
                context_info += (
                    f"Files in current directory: {', '.join(context['files'][:10])}\n"
                )

        prompt = f"{system_prompt}\n\n"
        if context_info:
            prompt += f"Context:\n{context_info}\n"
        prompt += f"Human request: {natural_language}\nBash command:"

        return prompt

    async def translate(
        self, natural_language: str, context: Optional[Dict[str, Any]] = None
    ) -> LLMResponse:
        """Translate natural language to bash command using Ollama."""
        try:
            prompt = self._build_prompt(natural_language, context)

            payload = {
                "model": self.config.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": self.config.temperature,
                },
            }

            if self.config.max_tokens:
                payload["options"]["num_predict"] = self.config.max_tokens

            response = self.client.post(
                f"{self.base_url}/api/generate",
                json=payload,
                headers={"Content-Type": "application/json"},
            )

            if response.status_code != 200:
                return LLMResponse(
                    command="",
                    error=f"Ollama API error: {response.status_code} - {response.text}",
                )

            result = response.json()
            command = result.get("response", "").strip()

            # Clean up the command - remove any markdown formatting or explanations
            if "```" in command:
                # Extract command from code blocks
                lines = command.split("\n")
                command_lines = []
                in_code_block = False
                for line in lines:
                    if line.strip().startswith("```"):
                        in_code_block = not in_code_block
                        continue
                    if in_code_block or (
                        not in_code_block and not line.startswith("#")
                    ):
                        command_lines.append(line)
                command = "\n".join(command_lines).strip()

            # Take only the first line if multiple lines (unless it's a proper multi-line command)
            if "\n" in command and not any(
                op in command for op in ["&&", "||", "|", "\\"]
            ):
                command = command.split("\n")[0].strip()

            return LLMResponse(
                command=command,
                confidence=1.0,  # Ollama doesn't provide confidence scores
            )

        except httpx.RequestError as e:
            return LLMResponse(
                command="", error=f"Network error connecting to Ollama: {str(e)}"
            )
        except json.JSONDecodeError as e:
            return LLMResponse(
                command="", error=f"Invalid JSON response from Ollama: {str(e)}"
            )
        except Exception as e:
            return LLMResponse(command="", error=f"Unexpected error: {str(e)}")

    async def list_models(self) -> list[str]:
        """List available Ollama models."""
        try:
            response = self.client.get(f"{self.base_url}/api/tags")
            response.raise_for_status()

            data = response.json()
            models = []
            for model in data.get("models", []):
                if "name" in model:
                    models.append(model["name"])

            return sorted(models)

        except Exception as e:
            print(f"Error listing models: {e}")
            return []

    async def test_connection(self) -> bool:
        """Test if Ollama is accessible."""
        try:
            response = self.client.get(f"{self.base_url}/api/tags")
            return response.status_code == 200
        except Exception:
            return False


def create_llm_provider(config: LLMConfig) -> LLMProvider:
    """Factory function to create appropriate LLM provider."""
    if config.provider.lower() == "ollama":
        return OllamaProvider(config)
    else:
        raise ValueError(f"Unsupported LLM provider: {config.provider}")


async def test_llm_connection(provider: LLMProvider) -> bool:
    """Test if the LLM provider is accessible."""
    return await provider.test_connection()


if __name__ == "__main__":
    # Example usage
    import asyncio

    from .config import LLMConfig

    async def main():
        config = LLMConfig()
        provider = create_llm_provider(config)

        # Test connection
        if await test_llm_connection(provider):
            print("✓ LLM connection successful")

            # Test translation
            response = await provider.translate("list all python files")
            if response.error:
                print(f"✗ Translation error: {response.error}")
            else:
                print(f"✓ Translation: '{response.command}'")
        else:
            print("✗ LLM connection failed")

        provider.close()

    asyncio.run(main())
