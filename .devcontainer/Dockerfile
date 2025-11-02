FROM mcr.microsoft.com/devcontainers/python:3.11

# Install Node.js 18
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs

# Install additional tools
RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install --no-install-recommends \
    git \
    vim \
    curl \
    wget \
    sqlite3 \
    && apt-get clean -y && rm -rf /var/lib/apt/lists/*

# Install Python package manager
RUN pip install --upgrade pip uv

# Set up workspace
WORKDIR /workspace

# Install global Python tools
RUN pip install black ruff pytest pytest-asyncio pytest-cov httpx pyotp

USER vscode
