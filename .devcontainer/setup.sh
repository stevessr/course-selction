#!/bin/bash
# Setup script for dev container

echo "🚀 Setting up Course Selection System development environment..."

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install -e .

# Install frontend dependencies
echo "📦 Installing frontend dependencies..."
cd frontend
npm install
cd ..

# Create environment files
echo "⚙️  Creating environment files..."
for dir in backend/data_node backend/auth_node backend/teacher_node backend/student_node backend/queue_node; do
    if [ ! -f "$dir/.env" ]; then
        cp "$dir/.env.example" "$dir/.env"
    fi
done

echo "✅ Development environment ready!"
echo ""
echo "Quick start:"
echo "  1. Start backend: ./start_backend.sh"
echo "  2. Start frontend: cd frontend && npm run dev"
echo "  3. Open http://localhost:3000"
echo ""
echo "Tools:"
echo "  - Generate users: python -m backend.common.user_generator 50 --output users.csv"
echo "  - Import users: python -m backend.common.csv_import users.csv"
echo "  - Run tests: pytest tests/ -v"
echo ""
