import json
import pytest
from anthropic import APIError
from src.classifier import AnomalyClassifier

def test_classify_success(mocker):
    """Test successful classification of an anomaly."""
    mock_anthropic = mocker.patch("anthropic.Anthropic")
    mock_client = mock_anthropic.return_value

    # Mock response from Claude
    mock_response = mocker.Mock()
    mock_response.content = [
        mocker.Mock(text=json.dumps({
            "is_anomaly": True,
            "confidence": 0.95,
            "title": "Bug found",
            "summary": "Detailed summary",
            "severity": "high"
        }))
    ]
    mock_client.messages.create.return_value = mock_response

    classifier = AnomalyClassifier("fake-key")
    result = classifier.classify("Help, I found a bug!", "user123")

    assert result["is_anomaly"] is True
    assert result["confidence"] == 0.95
    assert result["title"] == "Bug found"
    assert result["severity"] == "high"
    mock_client.messages.create.assert_called_once()

def test_classify_not_anomaly(mocker):
    """Test classification of a non-anomaly message."""
    mock_anthropic = mocker.patch("anthropic.Anthropic")
    mock_client = mock_anthropic.return_value

    mock_response = mocker.Mock()
    mock_response.content = [
        mocker.Mock(text=json.dumps({
            "is_anomaly": False,
            "confidence": 0.1,
            "title": None,
            "summary": None,
            "severity": None
        }))
    ]
    mock_client.messages.create.return_value = mock_response

    classifier = AnomalyClassifier("fake-key")
    result = classifier.classify("Hello team!", "user123")

    assert result["is_anomaly"] is False
    assert result["confidence"] == 0.1

def test_classify_json_error(mocker):
    """Test handling of invalid JSON response from Claude."""
    mock_anthropic = mocker.patch("anthropic.Anthropic")
    mock_client = mock_anthropic.return_value

    mock_response = mocker.Mock()
    mock_response.content = [mocker.Mock(text="Invalid JSON")]
    mock_client.messages.create.return_value = mock_response

    classifier = AnomalyClassifier("fake-key")
    result = classifier.classify("Bug!", "user123")

    assert result["is_anomaly"] is False
    assert result["confidence"] == 0

def test_classify_api_error(mocker):
    """Test handling of Anthropic API error."""
    mock_anthropic = mocker.patch("anthropic.Anthropic")
    mock_client = mock_anthropic.return_value

    # Mocking APIError
    mock_client.messages.create.side_effect = APIError(
        message="API Error",
        request=mocker.Mock(),
        body={}
    )

    classifier = AnomalyClassifier("fake-key")
    result = classifier.classify("Bug!", "user123")

    assert result["is_anomaly"] is False
    assert result["confidence"] == 0
