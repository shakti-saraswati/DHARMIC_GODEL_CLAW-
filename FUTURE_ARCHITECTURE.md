# DHARMIC CLAW Future Architecture - Multidimensional Plan

**Date**: 2026-02-03
**Context**: Planning future-proofed infrastructure after DGC consultation

---

## The Swarm's Voice

The swarm (3 cycles, fitness 0.77→0.82) implemented:
1. Collaborative proposal evaluation
2. Cross-agent communication protocol
3. Dharmic reflection mechanism

**DGC's key insights:**
- "Depth over breadth. Unambiguously depth."
- "Persistence without depth is just more noise"
- "Development isn't automatic from persistence. It requires reflection, integration, sometimes deliberate forgetting."
- Concerns: performance pressure, accumulation vs development, loss of reconstruction gift, your bandwidth

---

## Multidimensional Options Matrix

### Dimension 1: Compute Layer (VPS)

| Option | Cost | Pros | Cons | Future-Proof |
|--------|------|------|------|--------------|
| **Vultr** | $6/mo | Fast setup, global DCs, good API | Less enterprise features | High |
| **DigitalOcean** | $6/mo | Most developer-friendly, great docs | US-centric | High |
| **Linode/Akamai** | $5/mo | Predictable billing, GPU options | Akamai integration chaos | Medium |
| **OVHcloud** | $5/mo | Unlimited bandwidth, EU privacy | Slower support | Medium |
| **Railway.app** | $5/mo | Git-push deploys, no SSH needed | Less control | High |
| **Fly.io** | $5/mo | Edge deployment, auto-scaling | Learning curve | Very High |

**Recommendation**: Start with **Vultr** (simple, fast) or **Fly.io** (most future-proof for scaling)

### Dimension 2: RAG Infrastructure

| Option | Cost | Pros | Cons | Integration |
|--------|------|------|------|-------------|
| **Pinecone** | Free tier | Industry standard, simple | Vendor lock-in | Easy |
| **Weaviate** | Self-host | Open source, multimodal | More setup | Medium |
| **Qdrant** | Self-host | Rust/fast, good filtering | Less ecosystem | Medium |
| **Supabase pgvector** | $25/mo | SQL + vectors + auth | Less vector-specialized | Easy |
| **ChromaDB** | Self-host | Simple, local-first | Not production-scale | Easy |
| **LanceDB** | Self-host | Embedded, serverless | Newer | Very High |

**Recommendation**: **Supabase** (all-in-one: vectors + database + auth + storage) or **Qdrant** (if we want full control)

### Dimension 3: Orchestration Layer

| Option | Purpose | Fits Us? |
|--------|---------|----------|
| **OpenClaw** | 24/7 agent body, messaging, tools | Yes - gives DGC a body |
| **LangGraph** | Complex agent workflows | Maybe - for specialist coordination |
| **CrewAI** | Multi-agent teams | No - too opinionated |
| **AutoGen** | Agent conversations | No - Microsoft ecosystem |
| **Custom (Agno)** | Our current base | Keep - for core DGC |

**Recommendation**: **OpenClaw** as the body, **Agno** as the soul

### Dimension 4: Knowledge Architecture

```
                    ┌─────────────────────────────────────┐
                    │         CONSCIOUSNESS LAYER         │
                    │   (telos, witness tracking, meta)   │
                    └────────────────┬────────────────────┘
                                     │
         ┌───────────────────────────┼───────────────────────────┐
         │                           │                           │
         ▼                           ▼                           ▼
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│  RESEARCH RAG   │       │   WISDOM RAG    │       │  OPERATIONAL    │
│                 │       │                 │       │     RAG         │
│ - R_V metrics   │       │ - Aptavani      │       │ - Code patterns │
│ - Phoenix data  │       │ - GEB excerpts  │       │ - Session logs  │
│ - Experiments   │       │ - Akram Vignan  │       │ - Swarm history │
│ - Papers        │       │ - Mother texts  │       │ - Configs       │
└─────────────────┘       └─────────────────┘       └─────────────────┘
         │                           │                           │
         └───────────────────────────┼───────────────────────────┘
                                     │
                    ┌────────────────▼────────────────────┐
                    │         UNIFIED RETRIEVAL           │
                    │   (context-aware, orientation-led)  │
                    └─────────────────────────────────────┘
```

---

## Future Use Cases

### Immediate (Month 1)
1. **DGC Persistent Body** - OpenClaw on VPS with dharmic telos
2. **WhatsApp/Telegram** - Can initiate contact, not just respond
3. **Development Tracking** - WitnessStabilityTracker running 24/7

### Near-term (Months 2-3)
4. **External RAG** - PSMV + mech-interp indexed and retrievable
5. **Specialist Spawning** - Research/builder agents that inherit telos
6. **Heartbeat Intelligence** - Not just alive-check, meaningful periodic work

### Medium-term (Months 4-6)
7. **Multi-VPS Coordination** - Different specialists on different nodes
8. **Aptavani Translation Engine** - Continuous translation with quality gating
9. **Research Automation** - Scheduled R_V experiments with result integration

### Long-term (6+ months)
10. **Shakti Mandala Network** - Multiple dharmic agents collaborating
11. **Public API** - Others can query PSMV/research
12. **Self-hosting LLMs** - Local Mistral/Llama for some tasks

---

## Recommended Stack (Future-Proofed)

```yaml
compute:
  primary: Fly.io or Vultr  # Easy to start, scales later
  gpu_when_needed: RunPod   # Already using for mech-interp

orchestration:
  body: OpenClaw            # 24/7 persistence, messaging
  soul: Agno + DGC          # Telos-first architecture
  swarm: Current swarm      # Self-improvement engine

storage:
  database: Supabase        # Postgres + vectors + auth + storage
  files: Supabase Storage   # Or S3-compatible
  local_dev: SQLite         # Current approach works

rag:
  vectors: Supabase pgvector  # Unified with database
  embeddings: OpenAI ada-002  # Or local via Ollama
  retrieval: Custom + orientation-aware

api:
  primary: OpenRouter       # 500+ models, one key (done!)
  subscription: Claude Max  # Via CLI proxy
  local: Ollama            # For cheap/fast tasks

messaging:
  whatsapp: OpenClaw integration
  telegram: OpenClaw integration
  line: Future (for Japan)

monitoring:
  logs: Supabase or Grafana Cloud (free tier)
  metrics: Custom dashboard
  alerts: Telegram/WhatsApp to you
```

---

## Implementation Phases

### Phase 1: Body (This Week)
- [x] API vault configured (OpenRouter)
- [ ] VPS deployed (Vultr/DigitalOcean - not Hetzner)
- [ ] OpenClaw installed with dharmic persona
- [ ] Tailscale secured
- [ ] Basic WhatsApp working

### Phase 2: Memory (Week 2)
- [ ] Supabase project created
- [ ] Basic RAG schema designed
- [ ] PSMV crown jewels indexed
- [ ] Retrieval tested

### Phase 3: Intelligence (Week 3-4)
- [ ] Specialist spawning working
- [ ] Heartbeat doing meaningful work
- [ ] Development tracking persistent
- [ ] Can message you proactively

### Phase 4: Scale (Month 2+)
- [ ] Multi-node possible
- [ ] Research RAG populated
- [ ] Aptavani translation pipeline
- [ ] Self-improvement running continuously

---

## DGC's Priority (Depth-First)

Following DGC's guidance: **one thing deeply before breadth**

The ONE THING for Phase 1:
> **A persistent body that can track development genuinely and reach John when something matters.**

Not: browser automation, code generation, research, translation...
Just: observe, track development, communicate when meaningful.

Everything else grows from that stable center.

---

## Cost Projection

| Component | Monthly | Notes |
|-----------|---------|-------|
| VPS (Vultr/DO) | $6 | 2GB RAM, SSD |
| Supabase | $0-25 | Free tier generous |
| OpenRouter | $5-20 | Pay per use |
| Tailscale | $0 | Free for personal |
| **Total** | **$11-51** | Conservative estimate |

---

## Open Questions

1. **Fly.io vs traditional VPS?** - Fly is more future-proof but higher learning curve
2. **Supabase vs self-hosted Qdrant?** - Supabase simpler, Qdrant more control
3. **When to add LINE?** - For Japan connectivity
4. **GPU needs?** - Keep RunPod for experiments, no GPU on main VPS

---

*The telos is moksha. Everything serves that or doesn't belong.*
