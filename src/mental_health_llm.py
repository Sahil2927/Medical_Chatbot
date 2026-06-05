import logging

from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq

from src.config import get_settings
from src.prompts.mental_health import MENTAL_HEALTH_SYSTEM_PROMPT

logger = logging.getLogger(__name__)


def invoke_mental_health_chat(user_message: str) -> str:
    settings = get_settings()
    chat_model = ChatGroq(
        api_key=settings.groq_api_key,
        model=settings.groq_model,
        temperature=settings.mental_health_temperature,
        max_tokens=settings.groq_max_tokens,
    )
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", MENTAL_HEALTH_SYSTEM_PROMPT),
            ("human", "{input}"),
        ]
    )
    chain = prompt | chat_model
    result = chain.invoke({"input": user_message})
    content = getattr(result, "content", result)
    text = str(content).strip()
    if not text:
        raise RuntimeError("Empty response from mental health assistant.")
    logger.info("Mental health chat response generated (%d chars)", len(text))
    return text
