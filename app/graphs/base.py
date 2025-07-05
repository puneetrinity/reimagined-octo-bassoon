# app/graphs/base.py
"""
Base graph classes for AI Search System
Foundation for all graph implementations - Complete fixed version
"""

import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

import structlog
from langgraph.graph import StateGraph, START, END
from pydantic import BaseModel

logger = structlog.get_logger(__name__)


class GraphType(Enum):
    """Graph type enumeration"""

    CHAT = "chat"
    SEARCH = "search"
    ANALYSIS = "analysis"
    SYNTHESIS = "synthesis"
    ORCHESTRATOR = "orchestrator"


class NodeType(Enum):
    """Node type enumeration"""

    PROCESSING = "processing"
    DECISION = "decision"
    IO = "io"
    TRANSFORM = "transform"


class NodeResult(BaseModel):
    """Standard result format for graph nodes"""

    success: bool
    data: dict[str, Any] = {}
    confidence: float = 0.0
    execution_time: float = 0.0
    cost: float = 0.0
    model_used: str | None = None
    error: str | None = None
    metadata: dict[str, Any] = {}


@dataclass
class GraphState:
    """Shared state across all graphs"""

    # Core request data
    query_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    correlation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    original_query: str = ""
    processed_query: Optional[str] = None
    # Intent and complexity
    query_intent: Optional[str] = None
    query_complexity: float = 0.5
    # Processing context
    conversation_history: List[Dict[str, Any]] = field(default_factory=list)
    search_results: List[Dict[str, Any]] = field(default_factory=list)
    intermediate_results: Dict[str, Any] = field(default_factory=dict)
    # User preferences and constraints
    user_preferences: Dict[str, Any] = field(default_factory=dict)
    cost_budget_remaining: float = 20.0
    max_cost: Optional[float] = None  # Maximum allowed cost
    max_execution_time: float = 30.0
    max_results: int = 10  # Maximum number of search results to return
    quality_requirement: str = "balanced"  # minimal, balanced, high, premium
    # Execution metadata
    start_time: datetime = field(default_factory=datetime.now)
    execution_path: List[str] = field(default_factory=list)
    confidence_scores: Dict[str, float] = field(default_factory=dict)
    costs_incurred: Dict[str, float] = field(default_factory=dict)
    # Enhanced execution tracking
    node_results: Dict[str, Dict] = field(default_factory=dict)
    execution_times: Dict[str, float] = field(default_factory=dict)
    # Cache and optimization
    cache_hits: List[str] = field(default_factory=list)
    routing_shortcuts_used: List[str] = field(default_factory=list)
    # Final output
    final_response: str = ""
    response_metadata: Dict[str, Any] = field(default_factory=dict)
    # Error handling
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def add_execution_step(self, step_name: str, result: NodeResult):
        """Add execution step to the path"""
        self.execution_path.append(step_name)
        self.confidence_scores[step_name] = result.confidence
        self.costs_incurred[step_name] = result.cost
        self.execution_times[step_name] = result.execution_time
        # Store complete result with timestamp
        self.node_results[step_name] = {
            "result": result,
            "timestamp": datetime.now().isoformat(),
        }
        if result.error:
            self.errors.append(f"{step_name}: {result.error}")

    def add_cost(self, component: str, cost: float):
        """Add cost for a specific component."""
        if component in self.costs_incurred:
            self.costs_incurred[component] += cost
        else:
            self.costs_incurred[component] = cost

    def set_confidence(self, component: str, confidence: float):
        """Set confidence score for a specific component."""
        self.confidence_scores[component] = confidence

    def is_within_budget(self, additional_cost: float = 0.0) -> bool:
        """Check if we're within budget constraints."""
        total_cost = self.calculate_total_cost() + additional_cost
        max_allowed = (
            self.max_cost if self.max_cost is not None else self.cost_budget_remaining
        )
        return total_cost <= max_allowed

    def calculate_total_cost(self) -> float:
        """Calculate total cost incurred"""
        return sum(self.costs_incurred.values())

    def calculate_total_time(self) -> float:
        """Calculate total execution time"""
        return (datetime.now() - self.start_time).total_seconds()

    def get_avg_confidence(self) -> float:
        """Calculate average confidence across all steps"""
        if not self.confidence_scores:
            return 0.0
        return sum(self.confidence_scores.values()) / len(self.confidence_scores)


class BaseGraphNode(ABC):
    """Base class for all graph nodes"""

    def __init__(self, name: str, node_type: str = "processing"):
        self.name = name
        self.node_type = node_type
        self.logger = structlog.get_logger(f"node.{name}")

    @abstractmethod
    async def execute(self, state: GraphState, **kwargs) -> NodeResult:
        """Execute the node logic"""
        pass

    async def __call__(self, state: GraphState, **kwargs) -> GraphState:
        """Node execution wrapper with error handling and timing"""
        start_time = datetime.now()
        try:
            self.logger.info(
                "Node execution started", node=self.name, query_id=state.query_id
            )
            # Execute the node logic
            result = await self.execute(state, **kwargs)
            # Calculate execution time
            execution_time = (datetime.now() - start_time).total_seconds()
            result.execution_time = execution_time
            # Update state
            state.add_execution_step(self.name, result)
            # Store result in intermediate results
            state.intermediate_results[self.name] = result.data
            self.logger.info(
                "Node execution completed",
                node=self.name,
                query_id=state.query_id,
                success=result.success,
                confidence=result.confidence,
                execution_time=execution_time,
                cost=result.cost,
            )
            return state
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            error_msg = f"Node {self.name} failed: {str(e)}"
            # Create error result
            error_result = NodeResult(
                success=False, error=error_msg, execution_time=execution_time
            )
            state.add_execution_step(self.name, error_result)
            self.logger.error(
                "Node execution failed",
                node=self.name,
                query_id=state.query_id,
                error=str(e),
                execution_time=execution_time,
                exc_info=e,
            )
            return state


class BaseGraph(ABC):
    """Base class for all graph implementations"""

    def __init__(self, graph_type: GraphType, name: str):
        self.graph_type = graph_type
        self.name = name
        self.logger = structlog.get_logger(f"graph.{name}")
        self.nodes: Dict[str, BaseGraphNode] = {}
        self.graph: Optional[StateGraph] = None

    @abstractmethod
    def define_nodes(self) -> Dict[str, BaseGraphNode]:
        """Define the nodes for this graph"""
        pass

    @abstractmethod
    def define_edges(self) -> List[tuple]:
        """Define the edges (connections) between nodes"""
        pass

    def build(self):
        """Build the LangGraph instance with explicit entrypoint handling."""
        try:
            # Define nodes
            self.nodes = self.define_nodes()
            # Create graph
            self.graph = StateGraph(GraphState)
            # Add nodes to graph
            for node_name, node_instance in self.nodes.items():
                self.graph.add_node(node_name, node_instance)
            # Add edges and track START target
            edges = self.define_edges()
            for edge in edges:
                if len(edge) == 2:
                    from_node, to_node = edge
                    self.graph.add_edge(from_node, to_node)
                elif len(edge) == 3:
                    from_node, condition_func, mapping = edge
                    self.graph.add_conditional_edges(from_node, condition_func, mapping)
            # Add START edge to first node
            first_node = (
                "context_manager"
                if "context_manager" in self.nodes
                else list(self.nodes.keys())[0]
            )
            self.graph.add_edge(START, first_node)
            self.graph.add_edge("end", END)
            # Compile the graph to enable execution
            self.graph = self.graph.compile()
            self.logger.info(
                "Graph built successfully",
                graph_type=self.graph_type.value,
                nodes=list(self.nodes.keys()),
                entrypoint=START,
            )
        except Exception as e:
            self.logger.error(
                "Failed to build graph",
                graph_type=self.graph_type.value,
                error=str(e),
                exc_info=e,
            )
            raise

    async def execute(self, state: GraphState) -> GraphState:
        """Execute the graph with global timeout and timing diagnostics."""
        if not self.graph:
            raise RuntimeError(f"Graph {self.name} not built. Call build() first.")
        import asyncio
        import time

        start_time = time.time()
        self.logger.info(
            "Graph execution started",
            graph_name=self.name,
            query_id=getattr(state, "query_id", None),
        )
        try:
            self.logger.info(
                f"DEBUG: About to call graph.ainvoke with state: {type(state)}"
            )
            self.logger.info(f"DEBUG: Graph object: {self.graph}")

            result = await asyncio.wait_for(self.graph.ainvoke(state), timeout=60.0)
            duration = time.time() - start_time

            self.logger.info(
                "Graph execution completed",
                graph_name=self.name,
                query_id=getattr(state, "query_id", None),
                duration=duration,
            )
            self.logger.info(f"DEBUG: Graph result type: {type(result)}")
            self.logger.info(f"DEBUG: Graph result: {result}")

            # Handle LangGraph result - it might be a different type
            if hasattr(result, "__dict__"):
                # Result is already a proper object, copy attributes to state
                for key, value in result.__dict__.items():
                    if hasattr(state, key):
                        setattr(state, key, value)
                return state
            elif isinstance(result, dict):
                # Result is a dict, copy dict values to state
                for key, value in result.items():
                    if hasattr(state, key):
                        setattr(state, key, value)
                return state
            else:
                # Fallback: return result as is
                return result
        except asyncio.TimeoutError:
            duration = time.time() - start_time
            self.logger.error(
                "Graph execution timeout",
                graph_name=self.name,
                query_id=getattr(state, "query_id", None),
                duration=duration,
            )
            state.errors.append("Graph execution timeout")
            if not state.final_response:
                state.final_response = "Request timed out. Please try again."
            return state
        except Exception as e:
            duration = time.time() - start_time
            self.logger.error(
                "Graph execution failed",
                graph_name=self.name,
                query_id=getattr(state, "query_id", None),
                error=str(e),
                duration=duration,
                exc_info=True,
            )
            self.logger.error(f"DEBUG: Full exception details: {e}")
            self.logger.error(f"DEBUG: Exception type: {type(e)}")
            state.errors.append(f"Graph execution failed: {str(e)}")
            if not state.final_response:
                state.final_response = "An error occurred during processing."
            return state

    def get_execution_plan(self, state: GraphState) -> List[str]:
        """Get the planned execution path for debugging"""
        # This is a simplified version - in practice, you'd analyze the graph structure
        return list(self.nodes.keys())

    def estimate_cost(self, state: GraphState) -> float:
        """Estimate the cost of executing this graph"""
        # Basic estimation - can be made more sophisticated
        base_cost = 0.001  # Base processing cost
        complexity_multiplier = len(self.nodes) * 0.002
        return base_cost + complexity_multiplier


class RoutingCondition:
    """Helper class for routing conditions in graphs"""

    @staticmethod
    def should_continue(state: GraphState) -> str:
        """Basic continue condition"""
        if state.errors:
            return "error_handler"
        return "continue"

    @staticmethod
    def check_budget(state: GraphState) -> str:
        """Check if budget allows continuation"""
        if state.calculate_total_cost() >= state.cost_budget_remaining:
            return "budget_exceeded"
        return "continue"

    @staticmethod
    def check_time_limit(state: GraphState) -> str:
        """Check if time limit allows continuation"""
        if state.calculate_total_time() >= state.max_execution_time:
            return "timeout"
        return "continue"

    @staticmethod
    def check_confidence(state: GraphState, threshold: float = 0.7) -> str:
        """Check if confidence is sufficient"""
        if state.get_avg_confidence() >= threshold:
            return "high_confidence"
        return "low_confidence"


# Common node implementations


class StartNode(BaseGraphNode):
    """Standard start node for all graphs"""

    def __init__(self):
        super().__init__("start", "control")

    async def execute(self, state: GraphState, **kwargs) -> NodeResult:
        """Initialize the graph execution"""
        return NodeResult(
            success=True,
            confidence=1.0,
            data={"message": "Graph execution started"},
            metadata={"timestamp": datetime.now().isoformat()},
        )


class EndNode(BaseGraphNode):
    """Standard end node for all graphs"""

    def __init__(self):
        super().__init__("end", "control")

    async def execute(self, state: GraphState, **kwargs) -> NodeResult:
        """Finalize the graph execution"""
        total_time = state.calculate_total_time()
        total_cost = state.calculate_total_cost()
        avg_confidence = state.get_avg_confidence()

        return NodeResult(
            success=True,
            confidence=1.0,
            data={
                "execution_summary": {
                    "total_time": total_time,
                    "total_cost": total_cost,
                    "avg_confidence": avg_confidence,
                    "steps_executed": len(state.execution_path),
                    "cache_hits": len(state.cache_hits),
                    "errors": len(state.errors),
                }
            },
            metadata={
                "completion_timestamp": datetime.now().isoformat(),
                "execution_path": state.execution_path,
            },
        )


class ErrorHandlerNode(BaseGraphNode):
    """Standard error handling node"""

    def __init__(self):
        super().__init__("error_handler", "control")

    async def execute(self, state: GraphState, **kwargs) -> NodeResult:
        """Handle errors gracefully"""
        error_count = len(state.errors)

        # Log errors
        for error in state.errors:
            self.logger.error("Graph error", error=error, query_id=state.query_id)

        # Attempt graceful degradation
        fallback_response = (
            "I encountered some issues processing your request. Please try again."
        )

        if state.final_response:
            # We have partial results
            fallback_response = (
                state.final_response
                + "\n\n(Note: Some features may have experienced issues)"
            )

        state.final_response = fallback_response
        state.response_metadata["error_recovery"] = True
        state.response_metadata["error_count"] = error_count

        return NodeResult(
            success=True,  # Recovery successful
            confidence=0.3,  # Low confidence due to errors
            data={"recovery_attempted": True, "error_count": error_count},
            metadata={"errors": state.errors},
        )
