"""OpenTelemetry LlamaIndex instrumentation"""
import logging
from typing import Collection
from wrapt import wrap_function_wrapper

from opentelemetry.trace import get_tracer

from opentelemetry.instrumentation.instrumentor import BaseInstrumentor
from opentelemetry.instrumentation.utils import unwrap

from opentelemetry.instrumentation.llamaindex.task_wrapper import task_wrapper
from opentelemetry.instrumentation.llamaindex.workflow_wrapper import workflow_wrapper
from opentelemetry.instrumentation.llamaindex.version import __version__

from opentelemetry.semconv.ai import TraceloopSpanKindValues

logger = logging.getLogger(__name__)

_instruments = ("llamaindex >= 0.0.200",)

WRAPPED_METHODS = [
    {
        "package": "llamaindex.i.base",
        "object": "Chain",
        "method": "__call__",
        "wrapper": task_wrapper,
    },
    {
        "package": "llamaindex.chains.base",
        "object": "Chain",
        "method": "acall",
        "wrapper": task_wrapper,
    },
    {
        "package": "llamaindex.chains",
        "object": "SequentialChain",
        "method": "__call__",
        "span_name": "llamaindex.workflow",
        "wrapper": workflow_wrapper,
    },
    {
        "package": "llamaindex.chains",
        "object": "SequentialChain",
        "method": "acall",
        "span_name": "llamaindex.workflow",
        "wrapper": workflow_wrapper,
    },
    {
        "package": "llamaindex.agents",
        "object": "AgentExecutor",
        "method": "_call",
        "span_name": "llamaindex.agent",
        "kind": TraceloopSpanKindValues.AGENT.value,
        "wrapper": workflow_wrapper,
    },
    {
        "package": "llamaindex.tools",
        "object": "Tool",
        "method": "_run",
        "span_name": "llamaindex.tool",
        "kind": TraceloopSpanKindValues.TOOL.value,
        "wrapper": task_wrapper,
    },
    {
        "package": "llamaindex.chains",
        "object": "RetrievalQA",
        "method": "__call__",
        "span_name": "retrieval_qa.workflow",
        "wrapper": workflow_wrapper,
    },
    {
        "package": "llamaindex.chains",
        "object": "RetrievalQA",
        "method": "acall",
        "span_name": "retrieval_qa.workflow",
        "wrapper": workflow_wrapper,
    },
]


class LlamaIndexInstrumentor(BaseInstrumentor):
    """An instrumentor for LlamaIndex SDK."""

    def instrumentation_dependencies(self) -> Collection[str]:
        return _instruments

    def _instrument(self, **kwargs):
        tracer_provider = kwargs.get("tracer_provider")
        tracer = get_tracer(__name__, __version__, tracer_provider)
        for wrapped_method in WRAPPED_METHODS:
            wrap_package = wrapped_method.get("package")
            wrap_object = wrapped_method.get("object")
            wrap_method = wrapped_method.get("method")
            wrapper = wrapped_method.get("wrapper")
            wrap_function_wrapper(
                wrap_package,
                f"{wrap_object}.{wrap_method}" if wrap_object else wrap_method,
                wrapper(tracer, wrapped_method),
            )

    def _uninstrument(self, **kwargs):
        for wrapped_method in WRAPPED_METHODS:
            wrap_package = wrapped_method.get("package")
            wrap_object = wrapped_method.get("object")
            wrap_method = wrapped_method.get("method")
            unwrap(
                f"{wrap_package}.{wrap_object}" if wrap_object else wrap_package,
                wrap_method,
            )
