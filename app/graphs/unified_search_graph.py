"""
Unified Search Graph
Orchestrates document search, web search, and hybrid search workflows
"""

import asyncio
from typing import Dict, Any, List, Optional
try:
    from langgraph.graph import StateGraph, END
    from langgraph.prebuilt import ToolNode
except ImportError:
    # Fallback for development without langgraph
    class StateGraph:
        def __init__(self, state_class): pass
        def add_node(self, name, func): pass
        def add_edge(self, from_node, to_node): pass
        def add_conditional_edges(self, from_node, condition, mapping): pass
        def set_entry_point(self, node): pass
        def compile(self): return self
    
    END = "END"
    ToolNode = None

from app.graphs.base import BaseGraph, GraphState, NodeResult
from app.graphs.document_search_node import DocumentSearchNode, DocumentUploadNode
from app.graphs.search_graph import SearchGraph
from app.providers.document_search.document_router import DocumentSearchRouter
from app.core.logging import get_logger

logger = get_logger("graphs.unified_search")


class UnifiedSearchGraph(BaseGraph):
    """
    Unified search graph that intelligently routes between:
    - Document search (ideal-octo-goggles)
    - Web search (existing providers)
    - Hybrid search (both)
    """
    
    def __init__(self, model_manager, cache_manager, document_search_url: str = "http://localhost:8001"):
        super().__init__(model_manager, cache_manager)
        
        # Initialize components
        self.router = DocumentSearchRouter()
        self.document_node = DocumentSearchNode(document_search_url)
        self.upload_node = DocumentUploadNode(document_search_url)
        
        # Initialize existing search graph for web search
        self.web_search_graph = SearchGraph(model_manager, cache_manager)
        
        # Build the graph
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build the unified search workflow graph"""
        
        # Create the graph
        graph = StateGraph(GraphState)
        
        # Add nodes
        graph.add_node("router", self._route_query)
        graph.add_node("document_search", self.document_node.execute)
        graph.add_node("web_search", self._execute_web_search)
        graph.add_node("hybrid_search", self._execute_hybrid_search)
        graph.add_node("document_upload", self.upload_node.execute)
        graph.add_node("synthesis", self._synthesize_results)
        graph.add_node("fallback", self._handle_fallback)
        
        # Define edges
        graph.set_entry_point("router")
        
        # Router edges
        graph.add_conditional_edges(
            "router",
            self._determine_next_node,
            {
                "document_search": "document_search",
                "web_search": "web_search", 
                "hybrid_search": "hybrid_search",
                "document_upload": "document_upload",
                "fallback": "fallback"
            }
        )
        
        # Search node edges
        graph.add_conditional_edges(
            "document_search",
            self._handle_search_result,
            {
                "synthesis": "synthesis",
                "web_search": "web_search",  # For hybrid
                "fallback": "fallback",
                "end": END
            }
        )
        
        graph.add_conditional_edges(
            "web_search", 
            self._handle_search_result,
            {
                "synthesis": "synthesis",
                "fallback": "fallback",
                "end": END
            }
        )
        
        graph.add_conditional_edges(
            "hybrid_search",
            self._handle_search_result,
            {
                "synthesis": "synthesis", 
                "fallback": "fallback",
                "end": END
            }
        )
        
        # Terminal nodes
        graph.add_edge("synthesis", END)
        graph.add_edge("fallback", END)
        graph.add_edge("document_upload", END)
        
        return graph.compile()
    
    async def _route_query(self, state: GraphState) -> NodeResult:
        """Route the query to appropriate search method"""
        
        # Check if this is an upload operation
        if hasattr(state, 'operation') and state.operation == 'upload':
            return NodeResult(
                result={"route": "document_upload"},
                confidence=1.0,
                cost=0.0,
                next_node="document_upload"
            )
        
        # Analyze the query
        analysis = self.router.analyze_query(state.original_query)
        
        logger.info(
            f"Query routed to: {analysis.suggested_provider}",
            extra_fields={
                "query": state.original_query[:100],
                "confidence": analysis.confidence,
                "reasoning": analysis.reasoning,
                "correlation_id": state.correlation_id
            }
        )
        
        # Store analysis in state
        state.routing_analysis = analysis
        
        return NodeResult(
            result={
                "route": analysis.suggested_provider,
                "analysis": analysis
            },
            confidence=analysis.confidence,
            cost=0.001,  # Small routing cost
            next_node=analysis.suggested_provider
        )
    
    async def _execute_web_search(self, state: GraphState) -> NodeResult:
        """Execute web search using existing search graph"""
        
        try:
            # Use the existing search graph
            result = await self.web_search_graph.execute(state)
            
            # Mark result as web search
            if result.success and isinstance(result.result, dict):
                result.result["search_type"] = "web"
            
            return result
            
        except Exception as e:
            logger.error(f"Web search error: {str(e)}", exc_info=True)
            return NodeResult(
                result={"error": f"Web search failed: {str(e)}"},
                confidence=0.0,
                cost=0.0,
                success=False
            )
    
    async def _execute_hybrid_search(self, state: GraphState) -> NodeResult:
        """Execute hybrid search (both document and web)"""
        
        try:
            # Execute both searches concurrently
            doc_task = self.document_node.execute(state)
            web_task = self._execute_web_search(state)
            
            doc_result, web_result = await asyncio.gather(
                doc_task, web_task, return_exceptions=True
            )
            
            # Combine results
            combined_results = []
            total_cost = 0.0
            
            if isinstance(doc_result, NodeResult) and doc_result.success:
                doc_data = doc_result.result.get("search_results", [])
                for item in doc_data:
                    item["source_type"] = "document"
                    combined_results.append(item)
                total_cost += doc_result.cost
            
            if isinstance(web_result, NodeResult) and web_result.success:
                web_data = web_result.result.get("search_results", [])
                for item in web_data:
                    item["source_type"] = "web"
                    combined_results.append(item)
                total_cost += web_result.cost
            
            # Sort by relevance score
            combined_results.sort(key=lambda x: x.get("score", 0), reverse=True)
            
            # Limit results
            max_results = getattr(state, 'max_results', 10)
            combined_results = combined_results[:max_results]
            
            result_data = {
                "search_results": combined_results,
                "total_found": len(combined_results),
                "search_type": "hybrid",
                "component_results": {
                    "document_success": isinstance(doc_result, NodeResult) and doc_result.success,
                    "web_success": isinstance(web_result, NodeResult) and web_result.success
                }
            }
            
            # Update state
            state.search_results = combined_results
            state.search_metadata = result_data
            
            return NodeResult(
                result=result_data,
                confidence=0.8,  # High confidence for hybrid
                cost=total_cost,
                success=bool(combined_results),
                next_node="synthesis" if combined_results else "fallback"
            )
            
        except Exception as e:
            logger.error(f"Hybrid search error: {str(e)}", exc_info=True)
            return NodeResult(
                result={"error": f"Hybrid search failed: {str(e)}"},
                confidence=0.0,
                cost=0.0,
                success=False
            )
    
    async def _synthesize_results(self, state: GraphState) -> NodeResult:
        """Synthesize search results into a coherent response"""
        
        try:
            # Get search results from state
            search_results = getattr(state, 'search_results', [])
            search_metadata = getattr(state, 'search_metadata', {})
            
            if not search_results:
                return NodeResult(
                    result={"message": "No results found"},
                    confidence=0.0,
                    cost=0.0
                )
            
            # Create synthesis
            synthesis = {
                "summary": f"Found {len(search_results)} relevant results",
                "results": search_results[:5],  # Top 5 results
                "metadata": search_metadata,
                "response_type": "search_results"
            }
            
            # If we have content, we could use LLM to create a summary
            # For now, return structured results
            
            return NodeResult(
                result=synthesis,
                confidence=0.9,
                cost=0.002,  # Small synthesis cost
                success=True
            )
            
        except Exception as e:
            logger.error(f"Synthesis error: {str(e)}", exc_info=True)
            return NodeResult(
                result={"error": f"Result synthesis failed: {str(e)}"},
                confidence=0.0,
                cost=0.0,
                success=False
            )
    
    async def _handle_fallback(self, state: GraphState) -> NodeResult:
        """Handle cases where search fails"""
        
        return NodeResult(
            result={
                "message": "Sorry, I couldn't find relevant results for your query.",
                "suggestion": "Try rephrasing your question or using different keywords.",
                "response_type": "fallback"
            },
            confidence=0.1,
            cost=0.0
        )
    
    def _determine_next_node(self, state: GraphState) -> str:
        """Determine the next node based on routing result"""
        
        # Check for upload operation
        if hasattr(state, 'operation') and state.operation == 'upload':
            return "document_upload"
        
        # Get routing analysis
        analysis = getattr(state, 'routing_analysis', None)
        if not analysis:
            return "fallback"
        
        # Map provider to node
        provider_map = {
            "ultra_fast_search": "document_search",
            "web_search": "web_search", 
            "hybrid": "hybrid_search"
        }
        
        return provider_map.get(analysis.suggested_provider, "fallback")
    
    def _handle_search_result(self, state: GraphState) -> str:
        """Determine next step after search"""
        
        # Check if we have results
        search_results = getattr(state, 'search_results', [])
        
        if search_results:
            return "synthesis"
        else:
            return "fallback"
