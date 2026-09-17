"""Server-owned configuration; no provider configuration is accepted from a browser."""
from dataclasses import dataclass, field
from pathlib import Path
import math
import os


@dataclass(frozen=True)
class Settings:
    analysis_url: str = "http://analysis:8001"
    mode: str = "deterministic"
    timeout_seconds: float = 30.0
    max_evidence: int = 100
    max_pages: int = 4
    enable_v04: bool = False
    mcp_context: str = "price_only"
    repo_root: Path = field(default_factory=lambda: Path(__file__).resolve().parents[1])
    provider_url: str = "https://api.featherless.ai/v1"
    provider_key: str = field(default="", repr=False)
    model: str = ""
    input_rate: float | None = None
    output_rate: float | None = None

    def __post_init__(self):
        if self.mode not in {"deterministic", "model"}:
            raise ValueError("REVIEWER_MODE must be deterministic or model")
        if self.mcp_context not in {"price_only", "rules"}:
            raise ValueError("REVIEWER_MCP_CONTEXT must be price_only or rules")
        if not 0 < self.timeout_seconds <= 30:
            raise ValueError("REVIEWER_TIMEOUT_SECONDS must be in (0,30]")
        if not 1 <= self.max_evidence <= 100 or not 1 <= self.max_pages <= 4:
            raise ValueError("Evidence limits must not exceed 100 records / 4 pages")
        for rate in (self.input_rate, self.output_rate):
            if rate is not None and (not math.isfinite(rate) or rate < 0):
                raise ValueError("Provider price assumptions must be finite and nonnegative")

    @classmethod
    def from_env(cls):
        def rate(name):
            return float(os.environ[name]) if os.environ.get(name) else None
        return cls(
            analysis_url=os.getenv("ANALYSIS_URL", "http://analysis:8001"),
            mode=os.getenv("REVIEWER_MODE", "deterministic"),
            timeout_seconds=float(os.getenv("REVIEWER_TIMEOUT_SECONDS", "30")),
            max_evidence=int(os.getenv("REVIEWER_MAX_EVIDENCE", "100")),
            max_pages=int(os.getenv("REVIEWER_MAX_PAGES", "4")),
            enable_v04=os.getenv("REVIEWER_ENABLE_PROPOSED_V04", "false").lower() == "true",
            mcp_context=os.getenv("REVIEWER_MCP_CONTEXT", "price_only"),
            provider_url=os.getenv("FEATHERLESS_BASE_URL", "https://api.featherless.ai/v1"),
            provider_key=os.getenv("FEATHERLESS_API_KEY", ""),
            model=os.getenv("REVIEWER_MODEL", ""),
            input_rate=rate("REVIEWER_INPUT_USD_PER_MILLION"),
            output_rate=rate("REVIEWER_OUTPUT_USD_PER_MILLION"),
        )
