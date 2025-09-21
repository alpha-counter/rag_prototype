import os

from dotenv import load_dotenv
from langgraph.graph import END, StateGraph

from chat_service.chains.answer_grader import answer_grader
from chat_service.chains.hallucination_grader import hallucination_grader
from chat_service.chains.router import question_router, RouteQuery
from chat_service.consts import GENERATE, GRADE_DOCUMENTS, RETRIEVE, WEBSEARCH
from chat_service.nodes import generate, grade_documents, retrieve, web_search
from chat_service.state import GraphState

load_dotenv()


def decide_to_generate(state):
    print("---ASSESS GRADED DOCUMENTS---")

    if state["web_search"]:
        print(
            "---DECISION: NO RELEVANT DOCUMENTS FOUND, EXECUTE WEB SEARCH---"
        )
        return WEBSEARCH
    else:
        print("---DECISION: GENERATE---")
        return GENERATE


def grade_generation_grounded_in_documents_and_question(state: GraphState) -> str:
    print("---CHECK HALLUCINATIONS---")
    question = state["question"]
    documents = state["documents"]
    generation = state["generation"]

    score = hallucination_grader.invoke(
        {"documents": documents, "generation": generation}
    )

    if hallucination_grade := score.binary_score:
        print("---DECISION: GENERATION IS GROUNDED IN DOCUMENTS---")
        print("---GRADE GENERATION vs QUESTION---")
        score = answer_grader.invoke({"question": question, "generation": generation})
        if answer_grade := score.binary_score:
            print("---DECISION: GENERATION ADDRESSES QUESTION---")
            return "useful"
        else:
            print("---DECISION: GENERATION DOES NOT ADDRESS QUESTION---")
            return "not useful"
    else:
        print("---DECISION: GENERATION IS NOT GROUNDED IN DOCUMENTS, RE-TRY---")
        return "not supported"


def route_question(state: GraphState) -> str:
    print("---ROUTE QUESTION---")
    question = state["question"]
    source: RouteQuery = question_router.invoke({"question": question})
    if source.datasource == WEBSEARCH:
        print("---ROUTE QUESTION TO WEB SEARCH---")
        return WEBSEARCH
    elif source.datasource == "vectorstore":
        print("---ROUTE QUESTION TO RAG---")
        return RETRIEVE

# Define a new graph
workflow = StateGraph(GraphState)
workflow.add_node(RETRIEVE, retrieve)
workflow.add_node(GRADE_DOCUMENTS, grade_documents)
workflow.add_node(GENERATE, generate)
workflow.add_node(WEBSEARCH, web_search)

#  Define a conditional entry point for graph flow
workflow.set_conditional_entry_point(
    route_question,
    {
        WEBSEARCH: WEBSEARCH,
        RETRIEVE: RETRIEVE,
    },
)
# Add an edge and connect RETRIEVE to GRADE_DOCUMENTS
workflow.add_edge(RETRIEVE, GRADE_DOCUMENTS)

# Add a conditional edge. Conditional flows are dotted lines in graph image
workflow.add_conditional_edges(
    # Define the start node and then the handler for the decision logic
    GRADE_DOCUMENTS,
    decide_to_generate,
    {
        WEBSEARCH: WEBSEARCH,
        GENERATE: GENERATE,
    },
)

# Add an edge and connect WEBSEARCH to GENERATE
workflow.add_edge(WEBSEARCH, GENERATE)

# Add a conditional edge to decide what happens after answer is generated
workflow.add_conditional_edges(
    # Define the start node and then the handler for the decision logic
    GENERATE,
    grade_generation_grounded_in_documents_and_question,
    {
        "not supported": GENERATE, # probably better to summerise or rephrase
        "useful": END,
        "not useful": WEBSEARCH,
    },
)


graph = workflow.compile()

if os.getenv("CHAT_SERVICE_EXPORT_GRAPH", "false").lower() == "true":
    output_path = os.getenv("CHAT_SERVICE_GRAPH_PATH", "graph.png")
    graph.get_graph().draw_mermaid_png(output_file_path=output_path)
