import httpx
from typing import Dict, Any, Optional
from fastapi import HTTPException
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type
from app.core.config import settings
from app.core.logging_config import setup_logging

logger = setup_logging(__name__)

class A2AClient:
    """
    Agent-to-Agent (A2A) Communication Client.
    Handles asynchronous HTTP requests to other specialized agents with Resilience (Retries).
    """
    
    def __init__(self):
        # Timeouts are crucial in multi-agent systems to prevent bottlenecks
        self.timeout = httpx.Timeout(timeout=30.0)

    # Retry mechanism: wait 2^x * 1 second between each retry, up to 10 seconds, max 3 attempts.
    # Only retry if it's a connection error or a 5xx server error, don't retry 4xx errors.
    @retry(
        wait=wait_exponential(multiplier=1, min=2, max=10),
        stop=stop_after_attempt(3),
        retry=retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError)),
        reraise=True
    )
    async def _post_request_with_retry(self, url: str, payload: Dict[str, Any], files: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Internal method to send async POST requests to target agents with Tenacity retry logic.
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                if files:
                    response = await client.post(url, files=files)
                else:
                    response = await client.post(url, json=payload)
                    
                # Raise exception for 4xx and 5xx status codes
                response.raise_for_status()
                return response.json()
                
            except httpx.HTTPStatusError as exc:
                # 4xx errors shouldn't be retried in business logic (but Tenacity doesn't natively filter by status code easily without custom callbacks)
                # So we manually raise a non-retriable exception if it's a 4xx client error
                if 400 <= exc.response.status_code < 500:
                    logger.warning(f"Client Error {exc.response.status_code} from {url}: {exc.response.text}")
                    # We raise FastAPI HTTPException directly to break out of Tenacity retry loop
                    raise HTTPException(
                        status_code=exc.response.status_code,
                        detail=f"Agent Error: {exc.response.text}"
                    )
                # 5xx errors will be caught by the @retry decorator
                logger.warning(f"Server Error {exc.response.status_code} from {url}, will retry...")
                raise
            except httpx.RequestError as exc:
                logger.warning(f"Connection Error to {url}: {exc}, will retry...")
                raise

    async def _safe_execute(self, url: str, payload: Dict[str, Any], files: Optional[Dict] = None) -> Dict[str, Any]:
        """Wrapper to translate HTTP/Retry exceptions to FastAPI HTTPExceptions for the user."""
        try:
            return await self._post_request_with_retry(url, payload, files)
        except httpx.HTTPStatusError as exc:
            # If all retries failed and we still get HTTPStatusError (5xx)
            logger.error(f"Agent at {url} failed repeatedly with status {exc.response.status_code}")
            raise HTTPException(
                status_code=exc.response.status_code,
                detail=f"Agent Gateway Error: {exc.response.text}"
            )
        except httpx.RequestError as exc:
            # If all retries failed due to connectivity
            logger.error(f"Agent at {url} is unreachable after multiple retries.")
            raise HTTPException(
                status_code=503,
                detail="The requested AI agent is currently unreachable. Please try again later."
            )

    async def forward_to_search(self, query: str, filters: Optional[Dict] = None) -> Dict[str, Any]:
        """Forward the user request to the Search Agent (Semantic/Image search for tech products)."""
        logger.info(f"Forwarding to Search Agent", extra={"query": query})
        endpoint = f"{settings.search_agent_url}/api/search"
        payload = {"query": query, "filters": filters or {}}
        return await self._safe_execute(endpoint, payload=payload)

    async def forward_to_advisor(self, session_id: str, message: str) -> Dict[str, Any]:
        """Forward the user request to the Advisor Agent (RAG-based tech consultant)."""
        logger.info(f"Forwarding to Advisor Agent", extra={"session_id": session_id})
        endpoint = f"{settings.advisor_agent_url}/api/chat"
        payload = {"session_id": session_id, "message": message}
        return await self._safe_execute(endpoint, payload=payload)
    
    async def forward_image_to_search(self, image_bytes: bytes, filename: str, content_type: str) -> Dict[str, Any]:
        """Forward uploaded image to Search Agent for CLIP processing."""
        logger.info(f"Forwarding Image to Search Agent", extra={"filename": filename})
        endpoint = f"{settings.search_agent_url}/api/search/image"
        files = {"file": (filename, image_bytes, content_type)}
        return await self._safe_execute(endpoint, payload={}, files=files)
            
    async def forward_to_order(self, session_id: str, message: str) -> Dict[str, Any]:
        """Forward request to Order Agent"""
        logger.info(f"Forwarding to Order Agent", extra={"session_id": session_id})
        endpoint = f"{settings.order_agent_url}/api/chat"
        payload = {"session_id": session_id, "message": message}
        return await self._safe_execute(endpoint, payload=payload)

# Singleton instance
a2a_client = A2AClient()