from tools.ai_sparring.providers.base import SparringProvider
from tools.ai_sparring.providers.fake_provider import FakeProvider

PROVIDERS = {
    "fake": FakeProvider,
}

__all__ = ["SparringProvider", "FakeProvider", "PROVIDERS"]
