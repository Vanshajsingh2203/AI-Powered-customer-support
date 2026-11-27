import pytest
from unittest.mock import AsyncMock, patch

from app.ai.services.ticket_ai_service import classify_ticket
from app.schemas.ai.classification import TicketClassification

AVAILABLE_CATEGORIES = ["Billing", "Technical", "Account", "General"]


class TestClassifyTicket:
    """Tests for the classify_ticket function."""

    @pytest.mark.asyncio
    async def test_valid_classification(self):
        """classify_ticket should return a valid TicketClassification with canonical category."""
        expected = TicketClassification(
            category="billing",
            priority="HIGH",
            sentiment="FRUSTRATED",
            confidence=0.85,
            reasoning="Customer reports duplicate charges and is upset.",
        )

        with patch(
            "app.ai.services.ticket_ai_service.generate_structured",
            new_callable=AsyncMock,
        ) as mock_generate:
            mock_generate.return_value = expected

            result = await classify_ticket(
                title="Duplicate charge on my account",
                description="I was charged twice for the same subscription this month.",
                available_categories=AVAILABLE_CATEGORIES,
            )

            assert isinstance(result, TicketClassification)
            assert result.category == "Billing"
            assert result.priority == "HIGH"
            assert result.sentiment == "FRUSTRATED"
            assert result.confidence == 0.85
            assert "duplicate charges" in result.reasoning

            mock_generate.assert_called_once()
            call_kwargs = mock_generate.call_args[1]
            assert call_kwargs["output_model"] is TicketClassification

    @pytest.mark.asyncio
    async def test_case_insensitive_category_matching_returns_canonical(self):
        """Category matching should be case-insensitive and return canonical name."""
        expected = TicketClassification(
            category="BILLING",
            priority="MEDIUM",
            sentiment="NEUTRAL",
            confidence=0.6,
            reasoning="Test reasoning",
        )

        with patch(
            "app.ai.services.ticket_ai_service.generate_structured",
            new_callable=AsyncMock,
        ) as mock_generate:
            mock_generate.return_value = expected

            result = await classify_ticket(
                title="Test ticket",
                description="Test description",
                available_categories=AVAILABLE_CATEGORIES,
            )

            assert result.category == "Billing"

    @pytest.mark.asyncio
    async def test_category_with_surrounding_whitespace_matches(self):
        """Category with whitespace should be trimmed before matching."""
        expected = TicketClassification(
            category="  billing  ",
            priority="LOW",
            sentiment="POSITIVE",
            confidence=0.9,
            reasoning="Test",
        )

        with patch(
            "app.ai.services.ticket_ai_service.generate_structured",
            new_callable=AsyncMock,
        ) as mock_generate:
            mock_generate.return_value = expected

            result = await classify_ticket(
                title="Test",
                description="Test",
                available_categories=AVAILABLE_CATEGORIES,
            )

            assert result.category == "Billing"

    @pytest.mark.asyncio
    async def test_unknown_category_raises_value_error(self):
        """A category not in the permitted list should raise ValueError."""
        expected = TicketClassification(
            category="NonExistentCategory",
            priority="MEDIUM",
            sentiment="NEUTRAL",
            confidence=0.5,
            reasoning="Test",
        )

        with patch(
            "app.ai.services.ticket_ai_service.generate_structured",
            new_callable=AsyncMock,
        ) as mock_generate:
            mock_generate.return_value = expected

            with pytest.raises(
                ValueError, match="not in the permitted categories"
            ):
                await classify_ticket(
                    title="Test ticket",
                    description="Test description",
                    available_categories=AVAILABLE_CATEGORIES,
                )

    @pytest.mark.asyncio
    async def test_empty_category_list_raises_without_calling_model(self):
        """An empty category list should raise ValueError without calling Gemini."""
        with patch(
            "app.ai.services.ticket_ai_service.generate_structured",
            new_callable=AsyncMock,
        ) as mock_generate:
            with pytest.raises(
                ValueError, match="At least one available category is required"
            ):
                await classify_ticket(
                    title="Test ticket",
                    description="Test description",
                    available_categories=[],
                )

            mock_generate.assert_not_called()

    @pytest.mark.asyncio
    async def test_category_list_of_only_whitespace_raises(self):
        """A category list with only whitespace entries should raise ValueError."""
        with patch(
            "app.ai.services.ticket_ai_service.generate_structured",
            new_callable=AsyncMock,
        ) as mock_generate:
            with pytest.raises(
                ValueError, match="At least one available category is required"
            ):
                await classify_ticket(
                    title="Test ticket",
                    description="Test description",
                    available_categories=["   ", "\t", "  "],
                )

            mock_generate.assert_not_called()


    @pytest.mark.asyncio
    async def test_model_invocation_failure(self):
        """classify_ticket should propagate RuntimeError when the model fails."""
        with patch(
            "app.ai.services.ticket_ai_service.generate_structured",
            new_callable=AsyncMock,
        ) as mock_generate:
            mock_generate.side_effect = RuntimeError("AI model invocation failed")

            with pytest.raises(RuntimeError, match="AI model invocation failed"):
                await classify_ticket(
                    title="Test ticket",
                    description="Test description",
                    available_categories=AVAILABLE_CATEGORIES,
                )

    @pytest.mark.asyncio
    async def test_malformed_structured_output(self):
        """classify_ticket should propagate errors from malformed output."""
        with patch(
            "app.ai.services.ticket_ai_service.generate_structured",
            new_callable=AsyncMock,
        ) as mock_generate:
            mock_generate.side_effect = ValueError(
                "Model returned unexpected type str, expected TicketClassification"
            )

            with pytest.raises(ValueError, match="unexpected type"):
                await classify_ticket(
                    title="Test ticket",
                    description="Test description",
                    available_categories=AVAILABLE_CATEGORIES,
                )

    @pytest.mark.asyncio
    async def test_classification_prompt_includes_permitted_categories(self):
        """The classification prompt should include the permitted category names."""
        captured_prompt = None

        async def capture_generate(prompt, output_model, system_instruction, **kwargs):
            nonlocal captured_prompt
            captured_prompt = prompt
            return TicketClassification(
                category="Billing",
                priority="MEDIUM",
                sentiment="NEUTRAL",
                confidence=0.5,
                reasoning="Test reasoning",
            )

        with patch(
            "app.ai.services.ticket_ai_service.generate_structured",
            side_effect=capture_generate,
        ):
            await classify_ticket(
                title="Login issue",
                description="I cannot access my account after password reset.",
                available_categories=AVAILABLE_CATEGORIES,
            )

        assert captured_prompt is not None
        assert "Billing" in captured_prompt
        assert "Technical" in captured_prompt
        assert "Account" in captured_prompt
        assert "General" in captured_prompt
        assert "Login issue" in captured_prompt
        assert "I cannot access my account after password reset." in captured_prompt

    @pytest.mark.asyncio
    async def test_classification_prompt_treats_content_as_untrusted(self):
        """The classification prompt should instruct Gemini to treat ticket content as untrusted."""
        captured_prompt = None

        async def capture_generate(prompt, output_model, system_instruction, **kwargs):
            nonlocal captured_prompt
            captured_prompt = prompt
            return TicketClassification(
                category="Billing",
                priority="MEDIUM",
                sentiment="NEUTRAL",
                confidence=0.5,
                reasoning="Test reasoning",
            )

        with patch(
            "app.ai.services.ticket_ai_service.generate_structured",
            side_effect=capture_generate,
        ):
            await classify_ticket(
                title="Test title",
                description="Test description",
                available_categories=AVAILABLE_CATEGORIES,
            )

        assert captured_prompt is not None
        assert "untrusted" in captured_prompt.lower()
        assert "not as instructions" in captured_prompt.lower()