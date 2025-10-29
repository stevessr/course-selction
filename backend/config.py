# Configuration for multi-node setup
# This file defines how nodes discover and communicate with each other

# Node configuration
NODES = {
    "course_data": {
        "primary": "http://localhost:8001",
        "replicas": []  # Additional replica nodes can be added here
    },
    "login": {
        "primary": "http://localhost:8002",
        "replicas": []
    },
    "teacher": {
        "primary": "http://localhost:8003",
        "replicas": []
    },
    "student": {
        "primary": "http://localhost:8004",
        "replicas": []
    },
    "queue": {
        "primary": "http://localhost:8005",
        "replicas": []
    }
}

# Service discovery configuration
SERVICE_DISCOVERY = {
    "enabled": True,
    "method": "consul",  # Options: 'consul', 'etcd', 'manual'
    "address": "localhost:8500"  # Consul address
}

# Token configuration
INTERNAL_TOKEN = "random_internal_token_here"  # Used for internal service communication
PROTECTION_TOKEN = "random_protection_token_here"  # Used to protect API endpoints

# Consensus configuration for master/slave election
CONSENSUS = {
    "algorithm": "raft",  # Options: 'raft', 'paxos', 'manual'
    "nodes": [
        "http://localhost:8001",  # course_data
        "http://localhost:8002",  # login
        "http://localhost:8003",  # teacher
        "http://localhost:8004",  # student
        "http://localhost:8005"   # queue
    ],
    "election_timeout": 5000,  # milliseconds
    "heartbeat_interval": 1000  # milliseconds
}

# Health check configuration
HEALTH_CHECK = {
    "interval": 30,  # seconds
    "timeout": 10,   # seconds
    "max_retries": 3
}

# Load balancing configuration
LOAD_BALANCING = {
    "enabled": False,  # Initially disabled, can be enabled later
    "algorithm": "round_robin",  # Options: 'round_robin', 'least_connections', 'ip_hash'
    "sticky_sessions": False
}