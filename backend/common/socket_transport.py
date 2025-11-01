"""
Socket-based transport for inter-service communication
Provides Unix socket support for better performance in development
"""
import os
import socket
import json
import asyncio
from typing import Optional, Dict, Any
from pathlib import Path
import httpx
from urllib.parse import urlparse


class SocketTransport:
    """Transport layer that can use HTTP or Unix sockets"""
    
    def __init__(self, use_sockets: bool = None):
        """
        Initialize socket transport
        
        Args:
            use_sockets: If True, use Unix sockets. If None, auto-detect from env
        """
        if use_sockets is None:
            # Auto-detect: use sockets in dev mode
            use_sockets = os.getenv('USE_SOCKETS', 'true').lower() == 'true'
        
        self.use_sockets = use_sockets
        self.socket_dir = Path(os.getenv('SOCKET_DIR', '/tmp/course-selection-sockets'))
        
        if self.use_sockets:
            self.socket_dir.mkdir(parents=True, exist_ok=True)
    
    def get_socket_path(self, service_name: str) -> Path:
        """Get Unix socket path for a service"""
        return self.socket_dir / f"{service_name}.sock"
    
    def get_service_url(self, service_name: str, default_http_url: str) -> str:
        """
        Get service URL (HTTP or socket)
        
        Args:
            service_name: Name of service (data_node, auth_node, etc.)
            default_http_url: Default HTTP URL if not using sockets
        
        Returns:
            URL string (http:// or unix://)
        """
        if self.use_sockets:
            socket_path = self.get_socket_path(service_name)
            if socket_path.exists():
                return f"unix://{socket_path}"
        
        # Fallback to HTTP
        env_var = f"{service_name.upper()}_URL"
        return os.getenv(env_var, default_http_url)
    
    async def request(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> httpx.Response:
        """
        Make HTTP request with socket support
        
        Args:
            method: HTTP method (GET, POST, etc.)
            url: URL (http:// or unix://)
            headers: Optional headers
            json_data: Optional JSON body
            params: Optional query parameters
        
        Returns:
            httpx.Response object
        """
        if url.startswith('unix://'):
            # Use Unix socket
            return await self._socket_request(method, url, headers, json_data, params)
        else:
            # Use HTTP
            async with httpx.AsyncClient(timeout=30.0) as client:
                return await client.request(
                    method, url, headers=headers, json=json_data, params=params
                )
    
    async def _socket_request(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]],
        json_data: Optional[Dict[str, Any]],
        params: Optional[Dict[str, Any]]
    ) -> httpx.Response:
        """Make request via Unix socket"""
        # Parse unix:// URL
        socket_path = url[7:].split('/', 1)[0]  # Remove unix:// prefix
        path = '/' + url[7:].split('/', 1)[1] if '/' in url[7:] else '/'
        
        # Build query string
        if params:
            query_string = '&'.join(f"{k}={v}" for k, v in params.items())
            path = f"{path}?{query_string}"
        
        # Use httpx with Unix socket transport
        transport = httpx.HTTPTransport(uds=socket_path)
        async with httpx.AsyncClient(transport=transport, timeout=30.0) as client:
            return await client.request(
                method,
                f"http://localhost{path}",
                headers=headers,
                json=json_data
            )


class SocketClient:
    """Client for making requests to services via HTTP or sockets"""
    
    def __init__(self, internal_token: str, use_sockets: Optional[bool] = None):
        """
        Initialize socket client
        
        Args:
            internal_token: Internal authentication token
            use_sockets: Whether to use Unix sockets
        """
        self.transport = SocketTransport(use_sockets)
        self.internal_token = internal_token
        self.base_headers = {"Internal-Token": internal_token}
    
    def get_service_url(self, service: str) -> str:
        """Get URL for a service"""
        default_urls = {
            'data_node': 'http://localhost:8001',
            'auth_node': 'http://localhost:8002',
            'teacher_node': 'http://localhost:8003',
            'student_node': 'http://localhost:8004',
            'queue_node': 'http://localhost:8005',
        }
        return self.transport.get_service_url(service, default_urls.get(service, ''))
    
    async def get(self, service: str, path: str, headers: Optional[Dict] = None, **kwargs):
        """Make GET request to service"""
        url = self.get_service_url(service)
        full_url = f"{url}{path}"
        
        req_headers = {**self.base_headers}
        if headers:
            req_headers.update(headers)
        
        return await self.transport.request('GET', full_url, headers=req_headers, **kwargs)
    
    async def post(self, service: str, path: str, headers: Optional[Dict] = None, json_data: Optional[Dict] = None, **kwargs):
        """Make POST request to service"""
        url = self.get_service_url(service)
        full_url = f"{url}{path}"
        
        req_headers = {**self.base_headers}
        if headers:
            req_headers.update(headers)
        
        return await self.transport.request('POST', full_url, headers=req_headers, json_data=json_data, **kwargs)
    
    async def put(self, service: str, path: str, headers: Optional[Dict] = None, json_data: Optional[Dict] = None, **kwargs):
        """Make PUT request to service"""
        url = self.get_service_url(service)
        full_url = f"{url}{path}"
        
        req_headers = {**self.base_headers}
        if headers:
            req_headers.update(headers)
        
        return await self.transport.request('PUT', full_url, headers=req_headers, json_data=json_data, **kwargs)
    
    async def delete(self, service: str, path: str, headers: Optional[Dict] = None, **kwargs):
        """Make DELETE request to service"""
        url = self.get_service_url(service)
        full_url = f"{url}{path}"
        
        req_headers = {**self.base_headers}
        if headers:
            req_headers.update(headers)
        
        return await self.transport.request('DELETE', full_url, headers=req_headers, **kwargs)


def get_socket_config() -> Dict[str, Any]:
    """Get socket configuration from environment"""
    return {
        'use_sockets': os.getenv('USE_SOCKETS', 'true').lower() == 'true',
        'socket_dir': os.getenv('SOCKET_DIR', '/tmp/course-selection-sockets'),
    }


def create_socket_server_config(service_name: str, port: int) -> Dict[str, Any]:
    """
    Create uvicorn server config with socket support
    
    Args:
        service_name: Name of service
        port: HTTP port (used if sockets disabled)
    
    Returns:
        Config dict for uvicorn
    """
    config = get_socket_config()
    
    if config['use_sockets']:
        socket_path = Path(config['socket_dir']) / f"{service_name}.sock"
        socket_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Remove existing socket
        if socket_path.exists():
            socket_path.unlink()
        
        return {
            'uds': str(socket_path),
            'log_level': 'info',
        }
    else:
        return {
            'host': '0.0.0.0',
            'port': port,
            'log_level': 'info',
        }
