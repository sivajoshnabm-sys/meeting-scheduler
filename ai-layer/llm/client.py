from langchain_anthropic import ChatAnthropic

from config import settings


llm = ChatAnthropic(
    model="claude-sonnet-4-6",
    anthropic_api_key=settings.anthropic_api_key,
    max_tokens=1024
)