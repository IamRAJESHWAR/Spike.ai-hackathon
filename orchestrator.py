"""
LangGraph-based Orchestrator with ReAct (Thought-Action-Observation) Loop.

This module implements a ReAct pattern where the agent:
1. THINKS about what action to take
2. ACTS by calling the appropriate tool/agent
3. OBSERVES the result and decides if complete
4. LOOPS back to THINK if more actions needed

Architecture:
                    ┌──────────────────┐
                    │      START       │
                    └────────┬─────────┘
                             │
                    ┌────────▼─────────┐
                    │      THINK       │◄─────────────────┐
                    │  (Reason about   │                  │
                    │   what to do)    │                  │
                    └────────┬─────────┘                  │
                             │                            │
                    ┌────────▼─────────┐                  │
                    │      ACTION      │                  │
                    │  (Execute tool)  │                  │
                    └────────┬─────────┘                  │
                             │                            │
                    ┌────────▼─────────┐                  │
                    │     OBSERVE      │                  │
                    │ (Process result) │                  │
                    └────────┬─────────┘                  │
                             │                            │
                    ┌────────▼─────────┐      No          │
                    │    COMPLETE?     ├──────────────────┘
                    └────────┬─────────┘
                             │ Yes
                    ┌────────▼─────────┐
                    │   FINAL ANSWER   │
                    └────────┬─────────┘
                             │
                    ┌────────▼─────────┐
                    │       END        │
                    └──────────────────┘
"""

import json
from typing import Dict, Any, Optional, List, Annotated
from operator import add

from langgraph.graph import StateGraph, END

from analytics_agent import AnalyticsAgent
from seo_agent import SEOAgent
from llm_utils import llm_client
import config


class AgentState(Dict):
    """
    State schema for the ReAct LangGraph workflow.
    
    This state is passed between all nodes and tracks:
    - Input query and context
    - Thought-Action-Observation history
    - Iteration tracking
    - Final response
    """
    # Input fields
    query: str
    property_id: Optional[str]
    
    # ReAct loop state
    thoughts: List[str]           # History of reasoning
    actions: List[Dict[str, Any]] # History of actions taken
    observations: List[str]       # History of observations
    
    # Current step
    current_thought: Optional[str]
    current_action: Optional[Dict[str, Any]]
    current_observation: Optional[str]
    
    # Control flow
    iteration: int
    max_iterations: int
    is_complete: bool
    
    # Final output
    final_response: Optional[str]
    error: Optional[str]


# Available tools/actions the agent can take
AVAILABLE_TOOLS = """
Available Tools:
1. analytics_query: Query Google Analytics 4 for traffic data, users, sessions, page views, etc.
   - Use when: User asks about traffic, users, sessions, page views, sources, devices, trends
   - Input: Natural language query about analytics

2. seo_query: Query SEO audit data for technical issues, accessibility, status codes, etc.
   - Use when: User asks about SEO issues, meta tags, titles, HTTPS, indexability, status codes
   - Input: Natural language query about SEO

3. final_answer: Provide the final answer to the user
   - Use when: You have enough information to fully answer the user's question
   - Input: The complete answer to return to the user
"""


class LangGraphOrchestrator:
    """
    LangGraph-based orchestrator with ReAct (Thought-Action-Observation) loop.
    
    The agent iteratively:
    1. Thinks about what information is needed
    2. Takes an action (calls a tool)
    3. Observes the result
    4. Decides if more actions are needed or if it can answer
    """
    
    MAX_ITERATIONS = 5  # Prevent infinite loops
    
    def __init__(self):
        """Initialize the orchestrator with agents and build the graph."""
        self.analytics_agent = AnalyticsAgent()
        self.seo_agent = SEOAgent()
        self.default_property_id = config.GA4_PROPERTY_ID
        
        # Build the LangGraph workflow with ReAct pattern
        self.graph = self._build_react_graph()
        self.app = self.graph.compile()
        
        print(f"[OK] LangGraph ReAct Orchestrator initialized (Default Property ID: {self.default_property_id})")
    
    def _build_react_graph(self) -> StateGraph:
        """
        Build the LangGraph StateGraph with ReAct loop pattern.
        
        Returns:
            Configured StateGraph with Think-Act-Observe cycle
        """
        workflow = StateGraph(AgentState)
        
        # Add nodes for ReAct cycle
        workflow.add_node("think", self._think_node)
        workflow.add_node("action", self._action_node)
        workflow.add_node("observe", self._observe_node)
        workflow.add_node("final_answer", self._final_answer_node)
        
        # Set entry point
        workflow.set_entry_point("think")
        
        # Think -> Action (always)
        workflow.add_edge("think", "action")
        
        # Action -> Observe (always)
        workflow.add_edge("action", "observe")
        
        # Observe -> conditional routing (loop or finish)
        workflow.add_conditional_edges(
            "observe",
            self._should_continue,
            {
                "continue": "think",        # Loop back for more reasoning
                "finish": "final_answer"    # Got enough info, generate answer
            }
        )
        
        # Final answer -> END
        workflow.add_edge("final_answer", END)
        
        return workflow
    
    def _think_node(self, state: AgentState) -> Dict[str, Any]:
        """
        THINK Node: Reason about what action to take next.
        
        The LLM analyzes:
        - The original query
        - Previous actions and observations
        - What information is still needed
        """
        query = state.get("query", "")
        iteration = state.get("iteration", 0)
        thoughts = state.get("thoughts", [])
        actions = state.get("actions", [])
        observations = state.get("observations", [])
        
        # Build context from history
        history = ""
        for i, (t, a, o) in enumerate(zip(thoughts, actions, observations)):
            history += f"\n--- Iteration {i+1} ---\n"
            history += f"Thought: {t}\n"
            history += f"Action: {a.get('tool')} - {a.get('input', '')[:100]}...\n"
            history += f"Observation: {o[:200]}...\n"
        
        prompt = f"""You are an intelligent AI assistant that answers questions about web analytics and SEO.
You have access to tools to gather information. Think step by step about what you need to do.

{AVAILABLE_TOOLS}

=== USER QUESTION ===
{query}

=== PREVIOUS ACTIONS AND OBSERVATIONS ===
{history if history else "None yet - this is the first iteration."}

=== CURRENT ITERATION ===
Iteration {iteration + 1} of {self.MAX_ITERATIONS}

=== YOUR TASK ===

Think about:
1. What is the user actually asking for?
2. What information have I gathered so far?
3. What information do I still need?
4. Which tool should I use next, OR do I have enough to answer?

If you have gathered enough information to fully answer the question, use the "final_answer" tool.
If you need more information, choose the appropriate tool (analytics_query or seo_query).

Respond in this JSON format:
{{
  "thought": "Your reasoning about what to do next",
  "action": {{
    "tool": "analytics_query|seo_query|final_answer",
    "input": "The query/input for the tool OR the final answer text"
  }}
}}

Respond with ONLY valid JSON."""

        try:
            response = llm_client.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            
            # Parse JSON response
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                response = response[json_start:json_end]
            
            result = json.loads(response)
            thought = result.get("thought", "")
            action = result.get("action", {"tool": "final_answer", "input": "Unable to process"})
            
            print(f"\n{'='*60}")
            print(f"🧠 THINK (Iteration {iteration + 1})")
            print(f"{'='*60}")
            print(f"💭 Thought: {thought}")
            print(f"🎯 Planned Action: {action.get('tool')}")
            
            return {
                "current_thought": thought,
                "current_action": action,
                "iteration": iteration + 1,
                "thoughts": thoughts + [thought]
            }
            
        except Exception as e:
            print(f"❌ Error in think node: {e}")
            return {
                "current_thought": f"Error occurred: {str(e)}",
                "current_action": {"tool": "final_answer", "input": f"I encountered an error: {str(e)}"},
                "iteration": iteration + 1,
                "thoughts": thoughts + [f"Error: {str(e)}"]
            }
    
    def _action_node(self, state: AgentState) -> Dict[str, Any]:
        """
        ACTION Node: Execute the chosen tool/action.
        
        Dispatches to:
        - analytics_query: Call Analytics Agent
        - seo_query: Call SEO Agent  
        - final_answer: Prepare final response
        """
        action = state.get("current_action", {})
        tool = action.get("tool", "final_answer")
        tool_input = action.get("input", "")
        property_id = state.get("property_id") or self.default_property_id
        actions = state.get("actions", [])
        
        print(f"\n⚡ ACTION: {tool}")
        print(f"   Input: {tool_input[:100]}...")
        
        observation = ""
        
        try:
            if tool == "analytics_query":
                print("   📊 Calling Analytics Agent...")
                observation = self.analytics_agent.handle_query(tool_input, property_id)
                
            elif tool == "seo_query":
                print("   🔍 Calling SEO Agent...")
                observation = self.seo_agent.handle_query(tool_input)
                
            elif tool == "final_answer":
                # For final_answer, the input IS the answer
                observation = f"FINAL_ANSWER: {tool_input}"
                
            else:
                observation = f"Unknown tool: {tool}. Available tools: analytics_query, seo_query, final_answer"
                
        except Exception as e:
            observation = f"Error executing {tool}: {str(e)}"
            print(f"   ❌ Error: {e}")
        
        return {
            "current_observation": observation,
            "actions": actions + [action]
        }
    
    def _observe_node(self, state: AgentState) -> Dict[str, Any]:
        """
        OBSERVE Node: Process the result of the action.
        
        Records the observation and prepares for next iteration
        or final answer.
        """
        observation = state.get("current_observation", "")
        observations = state.get("observations", [])
        current_action = state.get("current_action", {})
        
        print(f"\n👁️ OBSERVE")
        print(f"   Result length: {len(observation)} chars")
        print(f"   Preview: {observation[:200]}...")
        
        # Check if this was a final_answer action
        is_complete = (
            current_action.get("tool") == "final_answer" or 
            observation.startswith("FINAL_ANSWER:")
        )
        
        return {
            "observations": observations + [observation],
            "is_complete": is_complete
        }
    
    def _should_continue(self, state: AgentState) -> str:
        """
        Conditional edge: Decide whether to continue loop or finish.
        
        Returns:
            "continue" to loop back to think
            "finish" to generate final answer
        """
        is_complete = state.get("is_complete", False)
        iteration = state.get("iteration", 0)
        max_iterations = state.get("max_iterations", self.MAX_ITERATIONS)
        
        if is_complete:
            print(f"\n✅ Agent decided to finish with final answer")
            return "finish"
        
        if iteration >= max_iterations:
            print(f"\n⚠️ Max iterations ({max_iterations}) reached, forcing completion")
            return "finish"
        
        print(f"\n🔄 Continuing to next iteration ({iteration + 1}/{max_iterations})")
        return "continue"
    
    def _final_answer_node(self, state: AgentState) -> Dict[str, Any]:
        """
        FINAL ANSWER Node: Generate the final response.
        
        If the last action was final_answer, use that.
        Otherwise, synthesize from all observations.
        """
        query = state.get("query", "")
        observations = state.get("observations", [])
        thoughts = state.get("thoughts", [])
        current_observation = state.get("current_observation", "")
        
        print(f"\n{'='*60}")
        print(f"📝 GENERATING FINAL ANSWER")
        print(f"{'='*60}")
        
        # Check if last observation was already a final answer
        if current_observation.startswith("FINAL_ANSWER:"):
            final_response = current_observation.replace("FINAL_ANSWER:", "").strip()
        else:
            # Synthesize answer from all observations
            all_observations = "\n\n".join([
                f"Observation {i+1}:\n{obs}" 
                for i, obs in enumerate(observations)
                if not obs.startswith("FINAL_ANSWER:")
            ])
            
            prompt = f"""Based on the following observations gathered to answer the user's question, 
provide a comprehensive final answer.

=== USER QUESTION ===
{query}

=== GATHERED INFORMATION ===
{all_observations}

=== YOUR TASK ===
Synthesize all the information into a clear, comprehensive answer.
Include specific numbers, insights, and recommendations where applicable.
"""

            try:
                final_response = llm_client.chat_completion(
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7,
                    max_tokens=3000
                )
            except Exception as e:
                final_response = f"Error generating final answer: {str(e)}\n\nRaw observations:\n{all_observations}"
        
        iteration = state.get("iteration", 0)
        print(f"\n✅ Answer generated after {iteration} iterations")
        
        return {
            "final_response": final_response
        }
    
    def route_query(self, query: str, property_id: Optional[str] = None) -> str:
        """
        Route a query through the ReAct LangGraph workflow.
        
        This is the main entry point, compatible with the original interface.
        
        Args:
            query: Natural language query
            property_id: Optional GA4 property ID
            
        Returns:
            Response string
        """
        if not property_id:
            property_id = self.default_property_id
        
        # Create initial state
        initial_state: AgentState = {
            "query": query,
            "property_id": property_id,
            "thoughts": [],
            "actions": [],
            "observations": [],
            "current_thought": None,
            "current_action": None,
            "current_observation": None,
            "iteration": 0,
            "max_iterations": self.MAX_ITERATIONS,
            "is_complete": False,
            "final_response": None,
            "error": None
        }
        
        print(f"\n{'='*60}")
        print(f"🚀 Starting ReAct Loop")
        print(f"{'='*60}")
        print(f"📨 Query: {query}")
        print(f"🔑 Property ID: {property_id}")
        print(f"🔄 Max Iterations: {self.MAX_ITERATIONS}")
        
        try:
            # Execute the graph
            final_state = self.app.invoke(initial_state)
            
            iterations = final_state.get("iteration", 0)
            print(f"\n{'='*60}")
            print(f"✅ ReAct Loop Complete")
            print(f"   Total Iterations: {iterations}")
            print(f"   Actions Taken: {len(final_state.get('actions', []))}")
            print(f"{'='*60}")
            
            return final_state.get("final_response", "No response generated.")
            
        except Exception as e:
            print(f"❌ Error in ReAct workflow: {e}")
            return f"I encountered an error processing your request: {str(e)}"
    
    def get_graph_visualization(self) -> str:
        """
        Get a text representation of the ReAct graph structure.
        
        Returns:
            ASCII representation of the graph
        """
        return """
ReAct LangGraph Workflow:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

                ┌──────────────────┐
                │      START       │
                └────────┬─────────┘
                         │
                ┌────────▼─────────┐
        ┌──────►│      THINK       │
        │       │  "What do I need │
        │       │   to do next?"   │
        │       └────────┬─────────┘
        │                │
        │       ┌────────▼─────────┐
        │       │      ACTION      │
        │       │  Execute tool:   │
        │       │  • analytics     │
        │       │  • seo           │
        │       │  • final_answer  │
        │       └────────┬─────────┘
        │                │
        │       ┌────────▼─────────┐
        │       │     OBSERVE      │
        │       │  Process result  │
        │       └────────┬─────────┘
        │                │
        │       ┌────────▼─────────┐
        │  No   │    COMPLETE?     │
        └───────┤  Have enough     │
                │  information?    │
                └────────┬─────────┘
                         │ Yes
                ┌────────▼─────────┐
                │   FINAL ANSWER   │
                │  Synthesize and  │
                │  respond         │
                └────────┬─────────┘
                         │
                ┌────────▼─────────┐
                │       END        │
                └──────────────────┘

Max Iterations: 5 (prevents infinite loops)
"""


# Create an alias for backward compatibility
Orchestrator = LangGraphOrchestrator
