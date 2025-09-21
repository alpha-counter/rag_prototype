import os
from fastapi import FastAPI, HTTPException, Body
from fastapi.responses import StreamingResponse, HTMLResponse
from pathlib import Path
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from chat_service import graph
from langchain_core.messages import HumanMessage
import uvicorn

load_dotenv()

BRAND_NAME = os.getenv("BRAND_NAME", "aerasAI")

app = FastAPI(
    docs_url="/docs",
    redoc_url="/redocs",
    title="Chat Service API",
    description="",
    version="0.1.0",
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define input model
class ChatRequest(BaseModel):
    question: str

async def generate_response(inputs):
    metadata_set = set()
    try:
        async for event in graph.graph.astream_events(inputs, version="v1"):
            kind = event["event"]

            # Debug print to inspect event structure
            # print(f"Event data: {event}")

            if kind == "on_chat_model_stream":
                content = event["data"]["chunk"].content
                if content:
                    yield content
            
        #     if kind == "on_retriever_end" or kind == "on_chain_end":
        #         # Debug print to inspect the output data structure
        #         output_data = event["data"]["output"]
        #         # print(f"Output data: {output_data}")
                
        #         if isinstance(output_data, dict) and "documents" in output_data:
        #             documents = output_data["documents"]
        #             for doc in documents:
        #                 metadata = tuple(doc.metadata.items())  # Convert metadata to a hashable type (tuple of items)
        #                 metadata_set.add(metadata)
        #         #         yield f"Metadata: {dict(metadata)}\n\n"
        #         # else:
        #         #     print(f"No documents found in output data: {output_data}")

        # # Once streaming is complete, yield the unique metadata information at the end
        # if metadata_set:
        #     yield "\n\n"
        #     yield "Document References:\n"
        #     for metadata in metadata_set:
        #         yield f"{dict(metadata)}\n"

    except AttributeError as e:
        raise HTTPException(status_code=500, detail=f"Attribute error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat", response_model=None)
async def chat_endpoint(chat_request: ChatRequest = Body(...)):
    inputs = {
        "messages": [HumanMessage(content=chat_request.question)],  # Ensure proper initialization
        "question": chat_request.question
    }
    return StreamingResponse(generate_response(inputs), media_type="text/event-stream")

@app.get("/", response_class=HTMLResponse)
async def get():
    html_path = Path("static/index.html")
    html = html_path.read_text().replace("{{BRAND_NAME}}", BRAND_NAME)
    return HTMLResponse(content=html, status_code=200)

if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8004)
## uvicorn chat_service.main:app --reload --port 8004
