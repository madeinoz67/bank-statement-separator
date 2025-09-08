#!/bin/bash
# Test script to validate release workflow steps locally

echo "🧪 Testing release workflow steps locally..."

echo "📦 Step 1: Install dependencies"
uv sync --group dev
if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies"
    exit 1
fi

echo "🧪 Step 2: Run tests"
uv run pytest tests/unit/ -v
if [ $? -ne 0 ]; then
    echo "❌ Tests failed"
    exit 1
fi

echo "🏗️ Step 3: Build package"
uv build
if [ $? -ne 0 ]; then
    echo "❌ Build failed"
    exit 1
fi

echo "✅ Step 4: Verify package"
uv run twine check dist/*
if [ $? -ne 0 ]; then
    echo "❌ Package verification failed"
    exit 1
fi

echo "📋 Step 5: Package contents"
ls -la dist/

echo "✅ All release workflow steps completed successfully!"
echo "📦 Package ready for PyPI publishing"