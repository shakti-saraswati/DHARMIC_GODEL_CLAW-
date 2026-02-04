#!/bin/bash
# Dharmic Agent Core - Setup Script
# Run this to prepare the development environment

set -e

echo "======================================"
echo "DHARMIC AGENT CORE - SETUP"
echo "======================================"

cd ~/DHARMIC_GODEL_CLAW

# Create Python virtual environment
echo "Creating virtual environment..."
python3 -m venv .venv
source .venv/bin/activate

# Install core requirements
echo "Installing core requirements..."
pip install -r src/core/requirements.txt

# Install Agno from local clone (for development)
echo "Installing Agno from local source..."
pip install -e cloned_source/agno/libs/agno

# Create memory directory
echo "Creating memory directory..."
mkdir -p memory

# Verify installation
echo ""
echo "Verifying installation..."
python3 -c "from agno.agent import Agent; print('✓ Agno imported successfully')"
python3 -c "import yaml; print('✓ YAML imported successfully')"
python3 -c "from pathlib import Path; t = yaml.safe_load(open('config/telos.yaml')); print(f'✓ Telos loaded: {t[\"ultimate\"][\"aim\"]}')" 

echo ""
echo "======================================"
echo "SETUP COMPLETE"
echo "======================================"
echo ""
echo "Next steps:"
echo "  1. source .venv/bin/activate"
echo "  2. Read CLAUDE.md for instructions"
echo "  3. Build src/core/dharmic_agent.py"
echo ""
echo "Telos: moksha"
echo "Method: code"
echo "======================================"
