import httpx
from typing import Dict, Any, Optional
from fastapi import HTTPException
from app.core.config import settings

class A2AClient:
    """
    Agent-to-Agent (A2A) Communication Client.
    Handles asynchronous HTTP requests to other specialized agents.
    """
    
    def __init__(self):
        # Timeouts are crucial in multi-agent systems to prevent bottlenecks
        self.timeout = httpx.Timeout(timeout=30.0)

    async def _post_request(self, url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Internal method to send async POST requests to target agents.
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as exc:
                # Handle error responses from target agents
                raise HTTPException(
                    status_code=exc.response.status_code,
                    detail=f"Agent Error: {exc.response.text}"
                )
            except httpx.RequestError as exc:
                # Handle connection errors (e.g., agent is down)
                raise HTTPException(
                    status_code=503,
                    detail=f"Failed to communicate with agent at {exc.request.url}. Service unavailable."
                )

    async def forward_to_search(self, query: str, filters: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Forward the user request to the Search Agent (Semantic/Image search for tech products).
        """
        endpoint = f"{settings.search_agent_url}/api/search"
        payload = {"query": query, "filters": filters or {}}
        return await self._post_request(endpoint, payload)

    async def forward_to_advisor(self, session_id: str, message: str) -> Dict[str, Any]:
        """
        Forward the user request to the Advisor Agent (RAG-based tech consultant).
        """
        endpoint = f"{settings.advisor_agent_url}/api/chat"
        payload = {"session_id": session_id, "message": message}
        return await self._post_request(endpoint, payload)
    
    async def forward_image_to_search(self, image_bytes: bytes, filename: str, content_type: str) -> Dict[str, Any]:
        """
        Forward uploaded image to Search Agent for CLIP processing.
        """
        endpoint = f"{settings.search_agent_url}/api/search/image"
        files = {"file": (filename, image_bytes, content_type)}
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(endpoint, files=files)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as exc:
                raise HTTPException(status_code=exc.response.status_code, detail=f"Search Agent Error: {exc.response.text}")

# Singleton instance
a2a_client = A2AClient()