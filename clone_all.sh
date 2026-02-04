#!/bin/bash
# DHARMIC GÖDEL CLAW - Clone All Source Repositories
# Phase 1: Total Reconnaissance

set -e

echo "🦞 DHARMIC GÖDEL CLAW - Cloning Source Repositories"
echo "===================================================="

cd ~/DHARMIC_GODEL_CLAW

# Create source directory
mkdir -p cloned_source
cd cloned_source

echo ""
echo "📦 Cloning OpenClaw (131k stars - the viral autonomous agent)..."
git clone --depth 1 https://github.com/openclaw/openclaw.git || echo "⚠️  OpenClaw clone failed or already exists"

echo ""
echo "🧬 Cloning Darwin Gödel Machine (Sakana AI official)..."
git clone --depth 1 https://github.com/jennyzzt/dgm.git || echo "⚠️  DGM clone failed or already exists"

echo ""
echo "🧠 Cloning Huxley-Gödel Machine (improved DGM variant)..."
git clone --depth 1 https://github.com/metauto-ai/HGM.git || echo "⚠️  HGM clone failed or already exists"

echo ""
echo "🌊 Cloning Claude-Flow (multi-agent orchestration)..."
git clone --depth 1 https://github.com/ruvnet/claude-flow.git || echo "⚠️  Claude-Flow clone failed or already exists"

echo ""
echo "⚡ Cloning Agno (10,000x faster than LangGraph)..."
git clone --depth 1 https://github.com/agno-agi/agno.git || echo "⚠️  Agno clone failed or already exists"

echo ""
echo "🔗 Cloning OpenClaw-Claude-Code skill..."
git clone --depth 1 https://github.com/Enderfga/openclaw-claude-code-skill.git || echo "⚠️  Skill clone failed or already exists"

echo ""
echo "🖥️ Cloning Local DGM variant (Ollama support)..."
git clone --depth 1 https://github.com/mmtmn/Darwin-Godel-Machine.git dgm-local || echo "⚠️  DGM-local clone failed or already exists"

echo ""
echo "===================================================="
echo "✅ Clone complete! Repositories in ~/DHARMIC_GODEL_CLAW/cloned_source/"
echo ""
ls -la
echo ""
echo "🔥 Next: Launch 10-agent analysis swarm in Claude Code"
