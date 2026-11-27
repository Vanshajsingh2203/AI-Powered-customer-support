
import asyncio
import logging
from typing import Type, TypeVar

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from pydantic import BaseModel

from app.ai.providers.gemini import get_gemini_model

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


async def generate_text(
    prompt: str,
    system_instruction: str = "You are a helpful customer support AI assistant.",
) -> str:
    """
    Generate a text response using LangChain and Gemini.
    """

    model = get_gemini_model()

    prompt_template = ChatPromptTemplate.from_messages(
        [
            ("system", "{system_instruction}"),
            ("human", "{prompt}"),
        ]
    )

    chain = prompt_template | model | StrOutputParser()

    response = await chain.ainvoke(
        {
            "system_instruction": system_instruction,
            "prompt": prompt,
        }
    )

    return response


async def generate_structured(
    prompt: str,
    output_model: Type[T],
    system_instruction: str = "You are a helpful AI assistant.",
    timeout_seconds: float = 30.0,
) -> T:
    """
    Generate a structured Pydantic output using LangChain's with_structured_output().

    Generic and reusable across AI components. Does not contain domain-specific
    prompts or logic.

    Args:
        prompt: The user prompt to send to the model.
        output_model: The Pydantic model class to parse the response into.
        system_instruction: System instruction for the model.
        timeout_seconds: Maximum seconds to wait for the model response.

    Returns:
        An instance of output_model populated from the model's response.

    Raises:
        ValueError: If the model fails to produce valid structured output.
        RuntimeError: If the model invocation fails entirely.
    """

    try:
        model = get_gemini_model()
        structured_model = model.with_structured_output(output_model)

        prompt_template = ChatPromptTemplate.from_messages(
            [
                ("system", "{system_instruction}"),
                ("human", "{prompt}"),
            ]
        )

        chain = prompt_template | structured_model

        try:
            response = await asyncio.wait_for(
                chain.ainvoke(
                    {
                        "system_instruction": system_instruction,
                        "prompt": prompt,
                    }
                ),
                timeout=timeout_seconds,
            )
        except asyncio.TimeoutError as exc:
            logger.error("Structured LLM invocation timed out after %ss", timeout_seconds)
            raise RuntimeError("AI model invocation timed out") from exc

    except Exception as exc:
        # Do not expose API keys or internal configuration in error messages.
        logger.error("Structured LLM invocation failed: %s", type(exc).__name__)
        raise RuntimeError("AI model invocation failed") from exc

    if not isinstance(response, output_model):
        raise ValueError(
            f"Model returned unexpected type {type(response).__name__}, "
            f"expected {output_model.__name__}"
        )

    return response
