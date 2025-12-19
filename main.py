"""FastAPI application for AI Backend."""

import sys
import io

# Fix Windows console encoding issues
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, AsyncGenerator
import uvicorn
import config
from orchestrator import Orchestrator
import json
import asyncio


# Initialize FastAPI app
app = FastAPI(
    title="Spike AI Backend",
    description="Production-ready AI backend for analytics and SEO queries",
    version="1.0.0"
)

# Initialize orchestrator
orchestrator = Orchestrator()


class QueryRequest(BaseModel):
    """Request model for query endpoint."""
    query: str
    propertyId: Optional[str] = None


class QueryResponse(BaseModel):
    """Response model for query endpoint."""
    response: str


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "Spike AI Backend",
        "version": "1.0.0"
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok"}


@app.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    """
    Main query endpoint for natural language questions.
    
    Args:
        request: QueryRequest with query and optional propertyId
        
    Returns:
        QueryResponse with natural language answer
    """
    try:
        if not request.query or not request.query.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        
        # Route query through orchestrator
        response = orchestrator.route_query(
            query=request.query,
            property_id=request.propertyId
        )
        
        return QueryResponse(response=response)
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error processing query: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Internal server error: {str(e)}"
        )


@app.post("/query/stream")
async def query_stream(request: QueryRequest):
    """
    Streaming query endpoint that shows real-time progress.
    
    Args:
        request: QueryRequest with query and optional propertyId
        
    Returns:
        Server-Sent Events (SSE) stream with progress updates
    """
    async def event_generator() -> AsyncGenerator[str, None]:
        try:
            if not request.query or not request.query.strip():
                yield f"data: {json.dumps({'error': 'Query cannot be empty'})}\n\n"
                return
            
            # Step 1: Analyzing query
            yield f"data: {json.dumps({'step': 1, 'status': 'Analyzing your query...'})}\n\n"
            await asyncio.sleep(0.3)
            
            # Step 2: Intent classification
            yield f"data: {json.dumps({'step': 2, 'status': 'Identifying intent (Analytics/SEO/Multi-Agent)...'})}\n\n"
            await asyncio.sleep(0.3)
            
            # Step 3: Routing
            yield f"data: {json.dumps({'step': 3, 'status': 'Routing to specialized agent(s)...'})}\n\n"
            await asyncio.sleep(0.3)
            
            # Step 4: Processing
            yield f"data: {json.dumps({'step': 4, 'status': 'Fetching data and generating response...'})}\n\n"
            
            # Execute actual query
            response = await asyncio.to_thread(
                orchestrator.route_query,
                query=request.query,
                property_id=request.propertyId
            )
            
            # Step 5: Complete with response
            yield f"data: {json.dumps({'step': 5, 'status': 'Complete!', 'response': response})}\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


def start_server():
    """Start the FastAPI server."""
    print(f"\n{'='*60}")
    print("🚀 Starting Spike AI Backend")
    print(f"{'='*60}\n")
    
    uvicorn.run(
        app,
        host=config.HOST,
        port=config.PORT,
        log_level="info"
    )


if __name__ == "__main__":
    start_server()
