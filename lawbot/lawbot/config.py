from pathlib import Path

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Primary path: NVIDIA NIM / OpenAI-compatible (same as OpenClaw syncscript setup)
    nvidia_api_key: str = Field(
        default="",
        validation_alias=AliasChoices("NVIDIA_API_KEY", "nvidia_api_key"),
    )
    # Optional generic key if you use another OpenAI-compatible host
    openai_compatible_api_key: str = Field(
        default="",
        validation_alias=AliasChoices("OPENAI_COMPATIBLE_API_KEY", "openai_compatible_api_key"),
    )
    openai_base_url: str = Field(
        default="https://integrate.api.nvidia.com/v1",
        validation_alias=AliasChoices("OPENAI_BASE_URL", "openai_base_url"),
    )
    # Primary: strongest default for research, strategy, drafting (NVIDIA catalog).
    chat_model: str = Field(
        default="meta/llama-3.1-405b-instruct",
        validation_alias=AliasChoices("CHAT_MODEL", "chat_model", "NVIDIA_CHAT_MODEL"),
    )
    # Optional: lighter model for smoke/connectivity-only turns (see model_routing.select_chat_model).
    chat_model_fast: str = Field(
        default="meta/llama-3.3-70b-instruct",
        validation_alias=AliasChoices("CHAT_MODEL_FAST", "chat_model_fast"),
    )
    # Optional third tier (NVIDIA-only max): used for high-stakes OpenAI-compatible turns when set.
    # Same signals as Anthropic auto-escalation, but stays on NVIDIA (see model_routing.select_chat_model).
    chat_model_max: str = Field(
        default="",
        validation_alias=AliasChoices("CHAT_MODEL_MAX", "chat_model_max"),
    )

    # Anthropic (paid): used alone if no OpenAI-compatible key; else optional escalation (see model_routing).
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-20250514"
    # When escalating with both backends: model id (defaults to anthropic_model if unset).
    anthropic_escalation_model: str = Field(
        default="",
        validation_alias=AliasChoices("ANTHROPIC_ESCALATION_MODEL", "anthropic_escalation_model"),
    )
    # auto | never | always — when both NVIDIA/OpenAI-compatible and Anthropic keys exist.
    anthropic_escalation_mode: str = Field(
        default="auto",
        validation_alias=AliasChoices("LAWBOT_ANTHROPIC_ESCALATION", "anthropic_escalation_mode"),
    )
    # Max Anthropic turns per UTC day when OpenAI-compatible is also set (-1 = unlimited; 0 = never escalate).
    max_anthropic_escalations_per_day: int = Field(
        default=-1,
        validation_alias=AliasChoices(
            "LAWBOT_MAX_ANTHROPIC_ESCALATIONS_PER_DAY",
            "max_anthropic_escalations_per_day",
        ),
    )

    courtlistener_token: str = ""

    lawbot_db_path: Path = Path("./data/lawbot.db")

    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_validate_signature: bool = True

    hud_token: str = ""
    public_base_url: str = "http://127.0.0.1:8765"

    def openai_compatible_key(self) -> str:
        return self.nvidia_api_key or self.openai_compatible_api_key

    def llm_backend(self) -> str | None:
        """Which API credential(s) exist — for /health. Not the same as per-turn routing."""
        if self.openai_compatible_key():
            return "openai_compatible"
        if self.anthropic_api_key:
            return "anthropic"
        return None

    def anthropic_configured(self) -> bool:
        return bool((self.anthropic_api_key or "").strip())

    def both_llm_backends_configured(self) -> bool:
        return bool(self.openai_compatible_key()) and self.anthropic_configured()

    def resolved_anthropic_escalation_model(self) -> str:
        m = (self.anthropic_escalation_model or "").strip()
        return m if m else self.anthropic_model

    # Phase 3–8: reasoning, memory, rate limits (see docs/LAWBOT_PARITY_ROADMAP.md)
    lawbot_reasoning_pass: str = Field(
        default="auto",
        validation_alias=AliasChoices("LAWBOT_REASONING_PASS", "lawbot_reasoning_pass"),
    )
    lawbot_session_compaction: str = Field(
        default="auto",
        validation_alias=AliasChoices("LAWBOT_SESSION_COMPACTION", "lawbot_session_compaction"),
    )
    compaction_message_threshold: int = Field(
        default=48,
        validation_alias=AliasChoices("LAWBOT_COMPACTION_MESSAGE_THRESHOLD", "compaction_message_threshold"),
    )
    compaction_every_n_messages: int = Field(
        default=24,
        validation_alias=AliasChoices("LAWBOT_COMPACTION_EVERY_N_MESSAGES", "compaction_every_n_messages"),
    )
    # auto | never — Anthropic extended thinking (budget_tokens) on high-stakes Anthropic turns when API accepts it.
    lawbot_anthropic_thinking: str = Field(
        default="auto",
        validation_alias=AliasChoices("LAWBOT_ANTHROPIC_THINKING", "lawbot_anthropic_thinking"),
    )
    anthropic_thinking_budget_tokens: int = Field(
        default=8000,
        validation_alias=AliasChoices(
            "LAWBOT_ANTHROPIC_THINKING_BUDGET_TOKENS",
            "anthropic_thinking_budget_tokens",
        ),
    )
    # 0 = disabled. Applied to /v1/chat and /v1/chat/stream per client IP.
    lawbot_rate_limit_per_minute: int = Field(
        default=0,
        validation_alias=AliasChoices("LAWBOT_RATE_LIMIT_PER_MINUTE", "lawbot_rate_limit_per_minute"),
    )
    # Session RAG: embeddings over prior messages in the same chat (OpenAI-compatible embeddings API).
    # auto | never — when auto, requires openai key + non-empty lawbot_embedding_model.
    lawbot_session_rag: str = Field(
        default="auto",
        validation_alias=AliasChoices("LAWBOT_SESSION_RAG", "lawbot_session_rag"),
    )
    # NVIDIA catalog example: nvidia/nv-embedqa-e5-v5 — list models on your OPENAI_BASE_URL host.
    lawbot_embedding_model: str = Field(
        default="",
        validation_alias=AliasChoices("LAWBOT_EMBEDDING_MODEL", "lawbot_embedding_model"),
    )
    session_rag_top_k: int = Field(
        default=4,
        validation_alias=AliasChoices("LAWBOT_SESSION_RAG_TOP_K", "session_rag_top_k"),
    )
    session_rag_max_stored_chunks: int = Field(
        default=400,
        validation_alias=AliasChoices("LAWBOT_SESSION_RAG_MAX_STORED_CHUNKS", "session_rag_max_stored_chunks"),
    )
    session_rag_chunk_max_chars: int = Field(
        default=1200,
        validation_alias=AliasChoices("LAWBOT_SESSION_RAG_CHUNK_MAX_CHARS", "session_rag_chunk_max_chars"),
    )
    session_rag_min_message_chars: int = Field(
        default=24,
        validation_alias=AliasChoices("LAWBOT_SESSION_RAG_MIN_MESSAGE_CHARS", "session_rag_min_message_chars"),
    )
    # Embedding APIs often cap input tokens (~512); truncate long user messages before embed_query.
    session_rag_embed_max_chars: int = Field(
        default=1800,
        validation_alias=AliasChoices("LAWBOT_SESSION_RAG_EMBED_MAX_CHARS", "session_rag_embed_max_chars"),
    )
    # In-process cache for embed_query (same truncated text in one process hits cache; lowers latency/cost).
    session_rag_embed_cache_ttl_seconds: float = Field(
        default=300.0,
        validation_alias=AliasChoices(
            "LAWBOT_SESSION_RAG_EMBED_CACHE_TTL",
            "session_rag_embed_cache_ttl_seconds",
        ),
    )
    session_rag_embed_cache_max_entries: int = Field(
        default=256,
        validation_alias=AliasChoices(
            "LAWBOT_SESSION_RAG_EMBED_CACHE_MAX",
            "session_rag_embed_cache_max_entries",
        ),
    )
    # Cache CourtListener retrieval by augmented query key (see lawbot/research.py).
    cl_search_cache_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices("LAWBOT_CL_SEARCH_CACHE", "cl_search_cache_enabled"),
    )
    cl_search_cache_ttl_seconds: int = Field(
        default=3600,
        validation_alias=AliasChoices("LAWBOT_CL_SEARCH_CACHE_TTL_SECONDS", "cl_search_cache_ttl_seconds"),
    )
    # CourtListener ``opinions-cited`` forward counts for retrieved opinions — not Westlaw KeyCite.
    # auto | never — when auto, uses COURTLISTENER_TOKEN (required for typical API access).
    lawbot_citation_graph: str = Field(
        default="auto",
        validation_alias=AliasChoices("LAWBOT_CITATION_GRAPH", "lawbot_citation_graph"),
    )
    # OpenAI-compatible chat: retries on transient 429/5xx/connection errors (minimum 1 = single attempt).
    lawbot_llm_http_retries: int = Field(
        default=4,
        validation_alias=AliasChoices("LAWBOT_LLM_HTTP_RETRIES", "lawbot_llm_http_retries"),
    )
    # NVIDIA / OpenAI-compatible only: extra LLM calls (reasoning scaffold, session compaction, draft_judge).
    # primary = CHAT_MODEL (highest IQ, higher cost); fast = CHAT_MODEL_FAST (lower cost).
    lawbot_auxiliary_model_tier: str = Field(
        default="primary",
        validation_alias=AliasChoices("LAWBOT_AUXILIARY_MODEL_TIER", "lawbot_auxiliary_model_tier"),
    )

    def auxiliary_chat_model_id(self) -> str:
        """
        Model id for auxiliary passes when using NVIDIA / OpenAI-compatible (no Anthropic required).

        Use ``primary`` for maximum quality on reasoning scaffold, compaction, and draft judge.
        Use ``fast`` to save cost/latency on those passes; main chat still uses ``select_chat_model`` rules.
        """
        tier = (self.lawbot_auxiliary_model_tier or "primary").strip().lower()
        primary = (self.chat_model or "").strip()
        fast = (self.chat_model_fast or "").strip() or primary
        if tier == "fast":
            return fast
        return primary or fast

    def session_rag_enabled(self) -> bool:
        mode = (self.lawbot_session_rag or "auto").strip().lower()
        if mode == "never":
            return False
        if not self.openai_compatible_key():
            return False
        return bool((self.lawbot_embedding_model or "").strip())


settings = Settings()
