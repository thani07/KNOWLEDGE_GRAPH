# kg_qa_langgraph.py

from typing import TypedDict, List, Dict, Any

from langgraph.graph import StateGraph, END
from langchain_core.messages import SystemMessage, HumanMessage

from services.llm_service import llm
from services.graph_query_service import graph_query_service
from services.keyword_service import keyword_extractor
from utils.logger import logger


# ---------- 1. STATE DEFINITION ----------

class QAState(TypedDict, total=False):
    question: str
    keywords: str
    results: List[Dict[str, Any]]
    answer: str
    attempts: int
    verdict: str  # "good" or "retry"


# ---------- 2. IMPROVED KEYWORD EXTRACTION ----------

def extract_keywords(state: QAState) -> QAState:
    """
    Extract keywords using improved algorithm.
    """
    question = state["question"]
    keywords = keyword_extractor.extract_keywords(question)
    state["keywords"] = keywords
    logger.info(f"Keywords extracted: {keywords}")
    return state


# ---------- 3. RUN MULTI-STRATEGY GRAPH QUERY ----------

def run_query(state: QAState) -> QAState:
    """
    Execute multi-strategy graph search.
    """
    keywords = state["keywords"]
    
    logger.info(f"🔍 Running graph query with keywords: {keywords}")
    
    results = graph_query_service.search_entities_multi_strategy(
        keywords=keywords,
        max_results=100
    )
    
    state["results"] = results
    logger.info(f"📊 Query returned {len(results)} results")
    
    return state


# ---------- 4. EXTRACT EVIDENCE FROM RESULTS ----------

def extract_evidence_from_results(rows: List[Dict[str, Any]]) -> str:
    """
    Build comprehensive evidence text from graph results.
    """
    if not rows:
        return "No matching information found in the knowledge graph."

    evidence_parts = []
    seen_entities = set()

    for row in rows[:30]:  # Limit to top 30
        try:
            e = row.get("e")
            if e:
                if isinstance(e, dict):
                    uid = e.get("uid", "")
                    name = e.get("name", "")
                    desc = e.get("description", "")
                    entity_type = e.get("type", "")
                    source_pdf = e.get("source_pdf", "")
                else:
                    uid = e.get("uid", "") if hasattr(e, "get") else ""
                    name = e.get("name", "") if hasattr(e, "get") else str(e)
                    desc = e.get("description", "") if hasattr(e, "get") else ""
                    entity_type = e.get("type", "") if hasattr(e, "get") else ""
                    source_pdf = e.get("source_pdf", "") if hasattr(e, "get") else ""

                if uid and uid not in seen_entities:
                    seen_entities.add(uid)
                    evidence_parts.append(
                        f"ENTITY: {name} ({entity_type})\n"
                        f"{desc}\n"
                        f"Source: {source_pdf}\n"
                    )

            r = row.get("r")
            x = row.get("x")
            
            if r and x:
                if isinstance(r, dict):
                    rel_type = r.get("type", "RELATED")
                else:
                    rel_type = type(r).__name__ if hasattr(r, "__name__") else "RELATED"

                if isinstance(x, dict):
                    target_name = x.get("name", "")
                else:
                    target_name = x.get("name", "") if hasattr(x, "get") else str(x)

                if target_name:
                    evidence_parts.append(f"→ {rel_type} → {target_name}\n")

        except Exception as e:
            logger.warning(f"Error extracting evidence: {e}")
            continue

    return "\n".join(evidence_parts) if evidence_parts else "No information found."


# ---------- 5. LLM ANSWER GENERATION ----------

def generate_answer(state: QAState) -> QAState:
    """
    Generate answer using LLM with graph evidence.
    """
    question = state["question"]
    rows = state.get("results", [])

    evidence = extract_evidence_from_results(rows)

    system_msg = SystemMessage(content="""
You are a Knowledge Graph QA assistant.

Rules:
- Answer ONLY using the provided evidence
- Be specific and comprehensive
- If evidence clearly answers the question, provide a detailed response
- If evidence is weak or missing, say "I don't have enough information about that"
- Never hallucinate facts
- Cite source PDFs when available in evidence at last of the chat 
""")

    user_msg = HumanMessage(content=f"""
Question: {question}

Evidence from Knowledge Graph:
{evidence}

Provide the best answer based on the evidence above.
""")

    try:
        resp = llm.invoke([system_msg, user_msg])
        answer = resp.content.strip()
    except Exception as e:
        logger.error(f"LLM generation error: {e}")
        answer = "Error generating answer."

    attempts = state.get("attempts", 0) + 1
    state["answer"] = answer
    state["attempts"] = attempts
    
    logger.info(f"Answer generated (attempt {attempts}): {answer[:100]}...")
    
    return state


# ---------- 6. ANSWER EVALUATION ----------

def evaluate_answer(state: QAState) -> QAState:
    """
    Evaluate if answer is good enough.
    """
    question = state["question"]
    answer = state["answer"]
    results_count = len(state.get("results", []))

    # Auto-accept if we have good results
    if results_count >= 5 and len(answer) > 50:
        state["verdict"] = "good"
        logger.info("✅ Answer accepted (sufficient results and length)")
        return state

    # LLM evaluation for edge cases
    system_msg = SystemMessage(content="""
You are an answer quality evaluator.

Reply with EXACTLY one word: "good" or "retry".

- "good" if the answer clearly addresses the question with specific information
- "retry" if the answer is vague, says "no information", or doesn't answer the question
""")

    user_msg = HumanMessage(content=f"""
Question: {question}
Answer: {answer}
Results found: {results_count}

Quality verdict (one word only)?
""")

    try:
        resp = llm.invoke([system_msg, user_msg])
        raw = resp.content.strip().lower()
        verdict = "good" if "good" in raw else "retry"
    except Exception as e:
        logger.warning(f"Evaluation error: {e}, defaulting to 'good'")
        verdict = "good"

    state["verdict"] = verdict
    logger.info(f"Verdict: {verdict}")
    
    return state


# ---------- 7. ROUTING LOGIC ----------

MAX_ATTEMPTS = 2


def route_after_evaluate(state: QAState) -> str:
    """
    Decide whether to retry or finish.
    """
    verdict = state.get("verdict", "good")
    attempts = state.get("attempts", 0)

    if verdict == "retry" and attempts < MAX_ATTEMPTS:
        logger.info(f"🔄 Retrying (attempt {attempts}/{MAX_ATTEMPTS})")
        return "retry"
    
    logger.info("✅ Finishing")
    return "good"


# ---------- 8. BUILD LANGGRAPH ----------

def build_kg_qa_graph():
    graph = StateGraph(QAState)

    # Add nodes
    graph.add_node("extract_keywords", extract_keywords)
    graph.add_node("run_query", run_query)
    graph.add_node("generate_answer", generate_answer)
    graph.add_node("evaluate_answer", evaluate_answer)

    # Entry point
    graph.set_entry_point("extract_keywords")

    # Linear flow
    graph.add_edge("extract_keywords", "run_query")
    graph.add_edge("run_query", "generate_answer")
    graph.add_edge("generate_answer", "evaluate_answer")

    # Conditional routing
    graph.add_conditional_edges(
        "evaluate_answer",
        route_after_evaluate,
        {
            "good": END,
            "retry": "generate_answer",
        },
    )

    return graph.compile()


# ✅ CRITICAL: Compile the app
kg_qa_app = build_kg_qa_graph()
