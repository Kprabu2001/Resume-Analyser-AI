import logging
from typing import Optional

from groq import Groq
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from groq import  APIConnectionError, RateLimitError

from app.core.config import settings

logger = logging.getLogger(__name__)

client = Groq(api_key=settings.groq_api_key)


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=30),
    retry=retry_if_exception_type((APIConnectionError, RateLimitError)),
    before_sleep=lambda retry_state: logger.warning(
        "Groq API call failed (attempt %d/%d): %s",
        retry_state.attempt_number, 3, retry_state.outcome.exception(),
    ),
)
def chat_completion(
    model: str,
    messages: list,
    max_tokens: int = 2000,
    temperature: float = 0.7,
    timeout: Optional[float] = 30.0,
):
    return client.chat.completions.create(
        model=model,
        messages=messages,
        max_tokens=max_tokens,
        temperature=temperature,
        timeout=timeout,
    )