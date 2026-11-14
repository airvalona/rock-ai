import pytest
from unittest.mock import patch, MagicMock
from rock.models.router import ModelRouter
from rock.core.config import RockConfig, ModelConfig

def test_model_router_custom_model():
    cfg = RockConfig(default_model="gpt-4o")
    router = ModelRouter(config=cfg)

    with patch("litellm.completion") as mock_completion:
        mock_resp = MagicMock()
        mock_resp.choices = [MagicMock(message=MagicMock(content="Mocked team response"))]
        mock_completion.return_value = mock_resp

        ans = router.complete([{"role": "user", "content": "Hello"}])
        assert ans == "Mocked team response"
        mock_completion.assert_called_once()
