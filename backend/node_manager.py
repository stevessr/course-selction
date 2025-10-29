import asyncio
import httpx
from typing import Dict, List, Optional
from .settings import settings
from .config import NODES, CONSENSUS
from fastapi import HTTPException
import time
import threading
from contextlib import asynccontextmanager


class NodeManager:
    """
    Manages node discovery, health checks, and master/slave coordination
    """
    
    def __init__(self):
        self.nodes = NODES.copy()
        self.current_master = None
        self.other_nodes = self.parse_other_nodes()
        self.is_master = True  # Initially assume this node is master
        self.lock = threading.Lock()
        
    def parse_other_nodes(self) -> List[str]:
        """Parse the other_nodes setting into a list"""
        if settings.other_nodes:
            return [node.strip() for node in settings.other_nodes.split(',')]
        return []
    
    async def register_with_cluster(self):
        """Register this node with the cluster"""
        # In a real implementation, this would register with a service discovery mechanism
        # like Consul or etcd
        pass
    
    async def discover_nodes(self):
        """Discover other nodes in the cluster"""
        # In a real implementation, this would query a service discovery mechanism
        # For now, we'll use the statically configured nodes
        for service, config in self.nodes.items():
            primary = config["primary"]
            if primary != f"http://localhost:{self.get_port_for_service(service)}":
                # This is another node, check if it's healthy
                if await self.is_node_healthy(primary):
                    print(f"Discovered healthy node: {primary} for {service}")
    
    def get_port_for_service(self, service: str) -> int:
        """Get the port for a given service"""
        service_ports = {
            "course_data": 8001,
            "login": 8002,
            "teacher": 8003,
            "student": 8004,
            "queue": 8005
        }
        return service_ports.get(service, 8000)
    
    async def is_node_healthy(self, node_url: str) -> bool:
        """Check if a node is healthy"""
        try:
            async with httpx.AsyncClient() as client:
                # Adjust the health check endpoint based on the node type
                # For this implementation, we'll just try to reach the base path
                response = await client.get(f"{node_url}/", timeout=5.0)
                return response.status_code < 500
        except:
            return False
    
    async def elect_master(self) -> str:
        """Elect a master node using consensus algorithm"""
        # In a real implementation, this would use Raft or another consensus algorithm
        # For now, we'll just elect the node with the lowest ID as master
        # This is a simplified version
        all_nodes = [f"http://localhost:{port}" for port in [8001, 8002, 8003, 8004, 8005]]
        
        healthy_nodes = []
        for node in all_nodes:
            if await self.is_node_healthy(node):
                healthy_nodes.append(node)
        
        if healthy_nodes:
            # Sort by URL to get consistent results
            healthy_nodes.sort()
            return healthy_nodes[0]  # The first one is the "master"
        
        return None
    
    async def get_master_node(self, service: str) -> str:
        """Get the current master node for a service"""
        # If we have consensus enabled, use it to determine the master
        if self.is_consensus_enabled():
            master = await self.elect_master()
            if master:
                return master
        
        # Fallback to configured primary
        return self.nodes[service]["primary"]
    
    async def get_slave_nodes(self, service: str) -> List[str]:
        """Get slave nodes for a service"""
        # For now, return all nodes except the master
        # In a real implementation, this would return replica nodes
        return self.nodes[service]["replicas"]
    
    def is_consensus_enabled(self) -> bool:
        """Check if consensus is enabled"""
        return True  # For now, always return True
    
    async def setup_master_slave(self):
        """Set up master-slave configuration for this node"""
        self.current_master = await self.elect_master()
        if self.current_master:
            self.is_master = (self.current_master == f"http://localhost:{self.get_current_port()}")
            print(f"Node setup: Master={self.current_master}, Is Master={self.is_master}")
    
    def get_current_port(self) -> int:
        """Get the port this instance is running on (simplified)"""
        # This would be determined dynamically in a real implementation
        # For now, we'll determine it based on the settings
        if settings.course_data_url in f"http://localhost":
            return 8001
        elif settings.login_url in f"http://localhost":
            return 8002
        elif settings.teacher_url in f"http://localhost":
            return 8003
        elif settings.student_url in f"http://localhost":
            return 8004
        elif settings.queue_url in f"http://localhost":
            return 8005
        else:
            return 8000  # default


# Global node manager instance
node_manager = NodeManager()


async def initialize_node():
    """Initialize the node on startup"""
    await node_manager.register_with_cluster()
    await node_manager.discover_nodes()
    await node_manager.setup_master_slave()


def verify_protection_token(required_token: str = None):
    """Verify protection token for API endpoints"""
    if required_token != settings.protection_token:
        raise HTTPException(status_code=403, detail="Invalid protection token")