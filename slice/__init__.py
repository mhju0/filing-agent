"""Bounded local application feasibility slice."""

import os

# Trace upload is outside the local-only boundary, even if inherited from a shell.
os.environ["LANGSMITH_TRACING"] = "false"
os.environ["LANGCHAIN_TRACING_V2"] = "false"
os.environ["LANGSMITH_OTEL_ENABLED"] = "false"
