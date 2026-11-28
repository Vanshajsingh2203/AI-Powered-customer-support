import pytest
from pydantic import ValidationError

from app.schemas.ai.classification import TicketClassification, ClassificationInput


class TestTicketClassification:
    """Tests for the TicketClassification Pydantic schema."""

    def test_valid_classification(self):
        """A valid classification should be accepted."""
        data = TicketClassification(
            category="billing",
            priority="HIGH",
            sentiment="FRUSTRATED",
            confidence=0.85,
            reasoning="Customer reports duplicate charges and is upset.",
        )
        assert data.category == "billing"
        assert data.priority == "HIGH"
        assert data.sentiment == "FRUSTRATED"
        assert data.confidence == 0.85
        assert "duplicate charges" in data.reasoning

    def test_all_priority_values(self):
        """All four priority values should be accepted."""
        for priority in ["LOW", "MEDIUM", "HIGH", "URGENT"]:
            obj = TicketClassification(
                category="technical",
                priority=priority,
                sentiment="NEUTRAL",
                confidence=0.5,
                reasoning="Test",
            )
            assert obj.priority == priority

    def test_all_sentiment_values(self):
        """All four sentiment values should be accepted."""
        for sentiment in ["POSITIVE", "NEUTRAL", "NEGATIVE", "FRUSTRATED"]:
            obj = TicketClassification(
                category="account",
                priority="MEDIUM",
                sentiment=sentiment,
                confidence=0.5,
                reasoning="Test",
            )
            assert obj.sentiment == sentiment

    def test_confidence_boundary_zero(self):
        """Confidence of 0.0 should be accepted."""
        obj = TicketClassification(
            category="billing",
            priority="LOW",
            sentiment="NEUTRAL",
            confidence=0.0,
            reasoning="Test",
        )
        assert obj.confidence == 0.0

    def test_confidence_boundary_one(self):
        """Confidence of 1.0 should be accepted."""
        obj = TicketClassification(
            category="billing",
            priority="LOW",
            sentiment="NEUTRAL",
            confidence=1.0,
            reasoning="Test",
        )
        assert obj.confidence == 1.0

    def test_confidence_below_zero_rejected(self):
        """Confidence below 0 should raise ValidationError."""
        with pytest.raises(ValidationError):
            TicketClassification(
                category="billing",
                priority="LOW",
                sentiment="NEUTRAL",
                confidence=-0.1,
                reasoning="Test",
            )

    def test_confidence_above_one_rejected(self):
        """Confidence above 1 should raise ValidationError."""
        with pytest.raises(ValidationError):
            TicketClassification(
                category="billing",
                priority="LOW",
                sentiment="NEUTRAL",
                confidence=1.1,
                reasoning="Test",
            )

    def test_invalid_priority_rejected(self):
        """An invalid priority value should raise ValidationError."""
        with pytest.raises(ValidationError):
            TicketClassification(
                category="billing",
                priority="CRITICAL",
                sentiment="NEUTRAL",
                confidence=0.5,
                reasoning="Test",
            )

    def test_invalid_sentiment_rejected(self):
        """An invalid sentiment value should raise ValidationError."""
        with pytest.raises(ValidationError):
            TicketClassification(
                category="billing",
                priority="LOW",
                sentiment="ANGRY",
                confidence=0.5,
                reasoning="Test",
            )

    def test_missing_required_fields_rejected(self):
        """Missing required fields should raise ValidationError."""
        with pytest.raises(ValidationError):
            TicketClassification()

    def test_empty_category_rejected(self):
        """Empty category should raise ValidationError."""
        with pytest.raises(ValidationError):
            TicketClassification(
                category="",
                priority="LOW",
                sentiment="NEUTRAL",
                confidence=0.5,
                reasoning="Test",
            )

    def test_empty_reasoning_rejected(self):
        """Empty reasoning should raise ValidationError."""
        with pytest.raises(ValidationError):
            TicketClassification(
                category="billing",
                priority="LOW",
                sentiment="NEUTRAL",
                confidence=0.5,
                reasoning="",
            )


class TestClassificationInput:
    """Tests for the ClassificationInput Pydantic schema."""

    def test_valid_input(self):
        """Valid input should be accepted."""
        data = ClassificationInput(
            title="Duplicate charge",
            description="I was charged twice for the same subscription.",
        )
        assert data.title == "Duplicate charge"
        assert data.description == "I was charged twice for the same subscription."

    def test_empty_title_rejected(self):
        """Empty title should raise ValidationError."""
        with pytest.raises(ValidationError):
            ClassificationInput(title="", description="Some description")

    def test_empty_description_rejected(self):
        """Empty description should raise ValidationError."""
        with pytest.raises(ValidationError):
            ClassificationInput(title="Some title", description="")
