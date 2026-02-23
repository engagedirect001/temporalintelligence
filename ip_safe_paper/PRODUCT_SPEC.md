# SovereignAI — Product Specification

**Version**: 1.0 Draft
**Author**: Anand Karasi (karasi@alum.mit.edu)
**Date**: February 2026
**Status**: Design Phase

---

## 1. Executive Summary

SovereignAI is an open-source framework that enables enterprises to deploy AI with frontier-level performance while keeping all proprietary data on-premises. It consists of three integrated components:

1. **Domain Forge** — Training pipeline for domain-specific small models
2. **MaskLayer** — IP masking middleware between local and frontier agents
3. **ConfidenceRouter** — Intelligent query routing with escalation logic

Together, these components implement the Sovereign AI architecture described in our research paper, reducing enterprise AI costs by ~90% while guaranteeing zero IP leakage.

---

## 2. System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    SovereignAI Framework                         │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    API Gateway                            │   │
│  │              (REST / gRPC / WebSocket)                    │   │
│  └──────────────────────┬───────────────────────────────────┘   │
│                         │                                        │
│  ┌──────────────────────▼───────────────────────────────────┐   │
│  │               ConfidenceRouter                            │   │
│  │  ┌─────────┐  ┌──────────┐  ┌────────────┐              │   │
│  │  │ Classify │→ │ Estimate │→ │  Route     │              │   │
│  │  │ Query    │  │ Confid.  │  │  Decision  │              │   │
│  │  └─────────┘  └──────────┘  └─────┬──────┘              │   │
│  └────────────────────────────────────┼─────────────────────┘   │
│                    ┌──────────────────┼──────────┐               │
│                    │                  │          │               │
│              ┌─────▼─────┐     ┌─────▼─────┐   │               │
│              │  LOCAL     │     │ ESCALATE  │   │               │
│              │  PATH      │     │ PATH      │   │               │
│              └─────┬─────┘     └─────┬─────┘   │               │
│                    │                  │          │               │
│  ┌─────────────────▼──────────┐  ┌───▼──────────────────────┐  │
│  │       Domain Forge          │  │      MaskLayer           │  │
│  │  ┌──────────┐ ┌─────────┐  │  │  ┌────────┐ ┌────────┐  │  │
│  │  │ Local    │ │ Pattern │  │  │  │Sanitize│ │ Re-    │  │  │
│  │  │ Model    │ │ Memory  │  │  │  │ Query  │ │ context│  │  │
│  │  └──────────┘ └─────────┘  │  │  └───┬────┘ └────▲───┘  │  │
│  └────────────────────────────┘  │      │            │      │  │
│                                   │  ┌───▼────────────┴───┐  │  │
│                                   │  │ Frontier Provider  │  │  │
│                                   │  │ Adapter            │  │  │
│                                   │  └────────────────────┘  │  │
│                                   └──────────────────────────┘  │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                 Observability Layer                        │   │
│  │  Metrics │ Audit Log │ Cost Tracker │ IP Leak Scanner     │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Component 1: Domain Forge

### 3.1 Purpose
Training pipeline that takes an enterprise's proprietary data and produces a domain-specific small model augmented with pattern memory. The goal: an 8B model that performs like a 70B+ model on domain tasks.

### 3.2 Sub-Components

#### 3.2.1 Data Ingestion Pipeline

| Feature | Detail |
|---------|--------|
| **Input formats** | PDF, DOCX, TXT, CSV, JSON, Markdown, code repos, Confluence, Notion exports, Slack exports |
| **Data processors** | OCR for scanned docs, code parser (AST extraction), table extractor, conversation thread parser |
| **PII detector** | Scans ingested data for PII before training (names, SSN, emails, phone numbers) — flags or auto-redacts |
| **Deduplication** | MinHash-based dedup to avoid training on repeated content |
| **Output** | Cleaned, tokenized, categorized training corpus in JSONL format |

```yaml
# Config: data_ingestion.yaml
ingestion:
  sources:
    - type: directory
      path: /data/contracts
      formats: [pdf, docx]
      ocr: true
    - type: confluence
      base_url: https://company.atlassian.net
      space_keys: [ENG, LEGAL, RESEARCH]
    - type: git_repo
      url: git@github.com:company/core-platform.git
      include: ["*.py", "*.java", "*.md"]
  
  processing:
    pii_detection: true
    pii_action: redact  # redact | flag | skip
    dedup_threshold: 0.85
    min_doc_length: 100
    max_doc_length: 50000
    
  output:
    format: jsonl
    path: /data/processed/
    split: {train: 0.9, val: 0.05, test: 0.05}
```

#### 3.2.2 Model Training Engine

| Feature | Detail |
|---------|--------|
| **Base models supported** | Llama 3/3.1 (8B, 70B), Mistral (7B, 8x7B), Phi-3 (3.8B, 14B), Qwen 2.5 (7B, 72B), Gemma 2 (9B, 27B) |
| **Training methods** | Full fine-tune, LoRA, QLoRA, DoRA |
| **Hardware requirements** | Min: 1x RTX 4090 (QLoRA 8B), Recommended: 1x A100-80GB, Max: 8x H100 (full 70B fine-tune) |
| **Training features** | Gradient checkpointing, flash attention, DeepSpeed ZeRO Stage 2/3, FSDP |
| **Evaluation** | Auto-eval on held-out set, domain-specific benchmark generation, A/B comparison vs base model |

```yaml
# Config: training.yaml
training:
  base_model: meta-llama/Llama-3.1-8B-Instruct
  method: qlora
  
  qlora:
    r: 64
    alpha: 128
    dropout: 0.05
    target_modules: [q_proj, k_proj, v_proj, o_proj, gate_proj, up_proj, down_proj]
  
  hyperparameters:
    epochs: 3
    batch_size: 4
    gradient_accumulation: 8
    learning_rate: 2e-4
    warmup_ratio: 0.1
    lr_scheduler: cosine
    max_seq_length: 4096
    
  hardware:
    gpus: 1
    precision: bf16
    gradient_checkpointing: true
    flash_attention: true
    
  evaluation:
    eval_steps: 100
    metrics: [loss, accuracy, domain_benchmark]
    save_best: true
```

**CLI:**
```bash
# Full pipeline from data to model
sovereign forge train \
  --data /data/processed/ \
  --base-model meta-llama/Llama-3.1-8B-Instruct \
  --method qlora \
  --output /models/company-domain-v1/

# Evaluate
sovereign forge eval \
  --model /models/company-domain-v1/ \
  --benchmark /data/processed/test.jsonl \
  --compare-base  # also eval base model for comparison
```

#### 3.2.3 Pattern Memory Builder

Builds the Buffer-of-Thoughts-style pattern library from domain data.

| Feature | Detail |
|---------|--------|
| **Pattern types** | Thought templates, solution exemplars, domain heuristics, error patterns, decision trees |
| **Extraction methods** | LLM-assisted extraction from solved examples, expert interview transcription, existing SOP parsing |
| **Storage** | Vector DB (ChromaDB / Qdrant / Weaviate) + structured JSON index |
| **Retrieval** | Embedding similarity (top-k) + category filter + recency weighting |
| **Update** | Continuous learning from production — successful responses generate new patterns |

```yaml
# Config: pattern_memory.yaml
pattern_memory:
  storage:
    backend: qdrant  # qdrant | chroma | weaviate
    embedding_model: BAAI/bge-large-en-v1.5
    collection: domain_patterns
    
  extraction:
    method: llm_assisted
    extraction_model: local  # use the trained local model
    template_categories:
      - name: contract_analysis
        description: "Patterns for analyzing legal contracts"
        example_count: 50
      - name: risk_scoring
        description: "Risk assessment methodologies"
        example_count: 30
      - name: compliance_check
        description: "Regulatory compliance verification"
        example_count: 40
        
  retrieval:
    top_k: 5
    similarity_threshold: 0.75
    category_filter: true
    recency_weight: 0.1  # slight preference for newer patterns
    
  continuous_learning:
    enabled: true
    min_confidence: 0.9  # only learn from high-confidence successful responses
    human_review: true   # queue new patterns for expert review before adding
    max_patterns_per_day: 20
```

**CLI:**
```bash
# Build initial pattern library
sovereign forge patterns build \
  --from /data/solved_examples/ \
  --categories contract_analysis,risk_scoring,compliance \
  --output /patterns/v1/

# Add patterns from production logs
sovereign forge patterns learn \
  --from /logs/successful_responses/ \
  --min-confidence 0.9 \
  --review-queue
```

#### 3.2.4 Domain Benchmark Generator

Auto-generates evaluation benchmarks from proprietary data so you can measure model quality without manual test creation.

```bash
# Generate domain-specific benchmark
sovereign forge benchmark generate \
  --from /data/processed/ \
  --tasks 200 \
  --difficulty easy:80,medium:80,hard:40 \
  --output /benchmarks/domain-v1/

# Run benchmark
sovereign forge benchmark run \
  --model /models/company-domain-v1/ \
  --benchmark /benchmarks/domain-v1/ \
  --compare meta-llama/Llama-3.1-8B-Instruct \
  --report /reports/benchmark-v1.html
```

---

## 4. Component 2: MaskLayer

### 4.1 Purpose
Middleware that sanitizes outgoing queries (removing all proprietary IP) and re-contextualizes incoming responses (mapping abstract solutions back to domain-specific terms). Sits between ConfidenceRouter and frontier model APIs.

### 4.2 Sub-Components

#### 4.2.1 Entity Registry

Maintains a bidirectional mapping between proprietary entities and their abstract replacements.

```yaml
# Config: entity_registry.yaml
entity_registry:
  storage: /config/entity_maps/
  
  categories:
    - name: products
      entities:
        - original: "PatentScore™"
          masked: "scoring_function_A"
          type: product_name
        - original: "BioPharma-X"
          masked: "portfolio_collection_1"
          type: portfolio
          
    - name: people
      auto_detect: true  # NER-based auto detection
      mask_strategy: role_based  # "the CEO" instead of "John Smith"
      
    - name: financial
      auto_detect: true
      mask_strategy: differential_perturbation
      epsilon: 1.0  # differential privacy parameter
      
    - name: technical
      entities:
        - original: "XR-42 receptor"
          masked: "G-protein coupled receptor subtype"
          type: domain_term
          generalization_level: 2  # how many levels to generalize
          
  auto_detection:
    ner_model: dslim/bert-base-NER
    custom_patterns: /config/entity_maps/regex_patterns.yaml
    confidence_threshold: 0.85
```

#### 4.2.2 Masking Engine

Four masking strategies applied in sequence:

```python
# Masking pipeline (pseudocode)
class MaskingPipeline:
    def mask(self, query: str, context: QueryContext) -> MaskedQuery:
        # Stage 1: Variable Abstraction
        # Replace all known proprietary names/terms with generic equivalents
        query = self.variable_abstractor.apply(query, self.entity_registry)
        
        # Stage 2: NER-based Auto Detection
        # Catch any proprietary entities not in the registry
        detected = self.ner_detector.detect(query)
        query = self.auto_masker.apply(query, detected)
        
        # Stage 3: Problem Generalization
        # Convert domain-specific framing to abstract CS/math framing
        query = self.generalizer.apply(query, context.domain)
        
        # Stage 4: Context Stripping
        # Remove business context (why, who, strategic intent)
        query = self.context_stripper.apply(query)
        
        # Stage 5: Numerical Perturbation
        # Apply differential privacy to any remaining numbers
        query = self.numerical_perturber.apply(query, epsilon=self.config.epsilon)
        
        # Stage 6: Leak Detection (final check)
        leaks = self.leak_detector.scan(query, self.entity_registry)
        if leaks:
            raise IPLeakDetectedError(leaks)
        
        return MaskedQuery(
            sanitized_text=query,
            reverse_map=self.entity_registry.get_reverse_map(),
            masking_metadata=self.get_metadata()
        )
```

#### 4.2.3 Re-Contextualization Engine

Maps abstract frontier responses back to proprietary domain:

```python
class RecontextualizationEngine:
    def recontextualize(self, response: str, reverse_map: dict, 
                         original_context: QueryContext) -> str:
        # Stage 1: Reverse variable substitution
        response = self.reverse_substitutor.apply(response, reverse_map)
        
        # Stage 2: Domain re-framing
        # Convert abstract solutions back to domain-specific language
        response = self.domain_reframer.apply(response, original_context)
        
        # Stage 3: Validation
        # Ensure the re-contextualized response is coherent and complete
        validation = self.validator.check(response, original_context)
        
        return response
```

#### 4.2.4 IP Leak Scanner

Real-time scanner that validates every outgoing query before transmission:

| Check | Method | Action on Fail |
|-------|--------|----------------|
| **Entity leak** | Registry lookup + fuzzy matching | Block + alert |
| **NER detection** | BERT-NER on sanitized query | Block + alert |
| **Pattern detection** | Regex for IDs, codes, internal URLs | Block + alert |
| **Embedding similarity** | Compare query embedding to proprietary corpus | Warn if similarity > threshold |
| **Statistical fingerprint** | Detect if numerical distributions match proprietary data | Apply additional perturbation |

```yaml
# Config: leak_scanner.yaml
leak_scanner:
  checks:
    - name: entity_leak
      enabled: true
      action: block
      fuzzy_threshold: 0.85  # catch misspellings/abbreviations
      
    - name: ner_detection
      enabled: true
      action: block
      model: dslim/bert-base-NER
      entity_types: [PER, ORG, LOC, MISC]
      
    - name: pattern_detection
      enabled: true
      action: block
      patterns:
        - name: internal_urls
          regex: "(https?://[a-z]+\\.company\\.com[^ ]*)"
        - name: project_codes
          regex: "(PRJ-\\d{4,})"
        - name: employee_ids
          regex: "(EMP[A-Z]\\d{5,})"
          
    - name: embedding_similarity
      enabled: true
      action: warn
      threshold: 0.92
      reference_corpus: /data/processed/embeddings.npy
      
  on_block:
    retry_with_stronger_masking: true
    max_retries: 2
    alert_security_team: true
    log_level: CRITICAL
```

#### 4.2.5 Frontier Provider Adapters

Pluggable adapters for different frontier model APIs:

```yaml
# Config: providers.yaml
providers:
  - name: openai
    enabled: true
    api_key_env: OPENAI_API_KEY
    models:
      - gpt-4o
      - gpt-4o-mini
      - o3-mini
    default_model: gpt-4o-mini
    rate_limit: 100/min
    timeout: 60s
    
  - name: anthropic
    enabled: true
    api_key_env: ANTHROPIC_API_KEY
    models:
      - claude-sonnet-4-6
      - claude-haiku-4-5
    default_model: claude-sonnet-4-6
    rate_limit: 60/min
    timeout: 90s
    
  - name: google
    enabled: true
    api_key_env: GOOGLE_API_KEY
    models:
      - gemini-2.5-flash
      - gemini-2.5-pro
    default_model: gemini-2.5-flash
    rate_limit: 60/min
    timeout: 60s
    
  routing:
    strategy: cost_optimized  # cost_optimized | quality_first | round_robin | random
    # Distribute queries across providers to prevent accumulation
    max_queries_per_provider_per_hour: 500
    failover: true
```

**CLI:**
```bash
# Test masking on a sample query
sovereign mask test \
  --query "Analyze PatentScore™ for BioPharma-X portfolio Q4 2026" \
  --config /config/entity_registry.yaml \
  --verbose

# Output:
# Original:  "Analyze PatentScore™ for BioPharma-X portfolio Q4 2026"
# Masked:    "Analyze a weighted scoring function over a document portfolio for a recent fiscal quarter"
# Entities replaced: 2 (PatentScore™ → weighted scoring function, BioPharma-X → document)
# NER detections: 0
# Leak scan: PASS
# Reverse map saved: /tmp/reverse_map_20260223_143022.json
```

---

## 5. Component 3: ConfidenceRouter

### 5.1 Purpose
Intelligent query routing that decides whether each query should be handled locally (fast, free, IP-safe) or escalated to a frontier model (slower, paid, still IP-safe via MaskLayer).

### 5.2 Sub-Components

#### 5.2.1 Query Classifier

Classifies incoming queries by domain category, complexity, and type:

```yaml
# Config: classifier.yaml
classifier:
  model: local  # use the domain-trained model for classification
  categories:
    - name: contract_analysis
      keywords: [contract, clause, agreement, terms, liability]
    - name: risk_scoring
      keywords: [risk, score, assessment, exposure, probability]
    - name: code_review
      keywords: [code, function, bug, error, implement]
    - name: research
      keywords: [study, paper, finding, data, hypothesis]
    - name: general
      keywords: []  # fallback
      
  complexity_estimation:
    method: token_count + keyword_complexity + historical
    levels: [simple, moderate, complex, novel]
```

#### 5.2.2 Confidence Estimator

Three-signal confidence scoring:

```python
class ConfidenceEstimator:
    def estimate(self, query: str, model_output: ModelOutput) -> ConfidenceScore:
        # Signal 1: Token-level entropy
        # Low entropy = model is confident about its output
        entropy_score = self.compute_entropy(model_output.logits)
        
        # Signal 2: Pattern memory match
        # High similarity to known patterns = familiar territory
        pattern_score = self.pattern_memory.best_match_score(query)
        
        # Signal 3: Self-consistency (optional, costs extra inference)
        # Generate k responses, measure agreement
        if self.config.self_consistency_enabled:
            responses = [self.model.generate(query) for _ in range(self.config.k)]
            consistency_score = self.measure_agreement(responses)
        else:
            consistency_score = None
        
        # Weighted combination
        confidence = (
            self.config.entropy_weight * entropy_score +
            self.config.pattern_weight * pattern_score +
            self.config.consistency_weight * (consistency_score or entropy_score)
        )
        
        return ConfidenceScore(
            value=confidence,
            entropy=entropy_score,
            pattern_match=pattern_score,
            consistency=consistency_score,
            threshold=self.config.threshold
        )
```

```yaml
# Config: confidence.yaml
confidence:
  threshold: 0.85  # queries above this are handled locally
  
  signals:
    entropy:
      weight: 0.4
      normalize: true
      
    pattern_match:
      weight: 0.4
      top_k: 3
      similarity_metric: cosine
      
    self_consistency:
      enabled: false  # enable for higher accuracy, costs 3x inference
      weight: 0.2
      k: 3
      agreement_metric: rouge_l
      
  calibration:
    method: temperature_scaling  # temperature_scaling | platt | isotonic
    calibration_set: /data/processed/calibration.jsonl
    recalibrate_interval: 7d
    
  adaptive_threshold:
    enabled: true
    # Automatically adjust threshold based on observed accuracy
    target_local_accuracy: 0.92
    adjustment_rate: 0.01
    min_threshold: 0.70
    max_threshold: 0.95
```

#### 5.2.3 Routing Decision Engine

```python
class RoutingEngine:
    def route(self, query: str) -> RoutingDecision:
        # Step 1: Generate local response with confidence
        local_response = self.local_model.generate(query)
        confidence = self.confidence_estimator.estimate(query, local_response)
        
        # Step 2: Cost-benefit analysis
        escalation_cost = self.cost_estimator.estimate(query)  # API $ + latency
        expected_improvement = self.improvement_estimator.estimate(
            confidence.value, query_complexity
        )
        
        # Step 3: Route decision
        if confidence.value >= self.config.threshold:
            return RoutingDecision(
                path="local",
                response=local_response,
                confidence=confidence,
                cost=0
            )
        elif expected_improvement > escalation_cost:
            return RoutingDecision(
                path="escalate",
                local_response=local_response,  # keep as fallback
                confidence=confidence,
                estimated_cost=escalation_cost
            )
        else:
            # Not confident enough, but not worth escalating (low value query)
            return RoutingDecision(
                path="local_with_disclaimer",
                response=local_response,
                confidence=confidence,
                disclaimer="Low confidence response — review recommended"
            )
```

#### 5.2.4 Feedback Loop

Learns from outcomes to improve routing over time:

```yaml
# Config: feedback.yaml
feedback:
  enabled: true
  
  signals:
    # User feedback (thumbs up/down, edits)
    user_feedback:
      enabled: true
      weight: 1.0
      
    # Automated quality checks
    auto_eval:
      enabled: true
      method: self_judge  # local model judges its own output quality
      weight: 0.5
      
    # Escalation outcome tracking
    escalation_tracking:
      enabled: true
      # Did the frontier model produce a meaningfully different answer?
      difference_threshold: 0.3  # ROUGE-L difference
      
  actions:
    # If local model was wrong, add to training queue
    retrain_queue: true
    # If local model was right at low confidence, adjust threshold
    threshold_adjustment: true
    # If pattern was useful, boost its ranking
    pattern_reranking: true
    
  reporting:
    daily_summary: true
    weekly_accuracy_report: true
    monthly_cost_optimization_report: true
```

---

## 6. API Specification

### 6.1 Query API (Primary Interface)

```
POST /v1/query
```

**Request:**
```json
{
  "query": "Analyze the risk profile of CompoundX-7 interactions",
  "context": {
    "domain": "pharma",
    "priority": "normal",
    "max_latency_ms": 5000
  },
  "options": {
    "allow_escalation": true,
    "return_confidence": true,
    "return_routing_metadata": true
  }
}
```

**Response:**
```json
{
  "response": "Based on the molecular structure analysis...",
  "metadata": {
    "routed_to": "local",
    "confidence": 0.91,
    "model": "company-domain-v1",
    "latency_ms": 234,
    "cost_usd": 0.0,
    "patterns_used": ["drug_interaction_template_v3", "risk_scoring_heuristic_12"],
    "ip_safe": true
  }
}
```

**Escalated Response:**
```json
{
  "response": "The novel binding mechanism suggests...",
  "metadata": {
    "routed_to": "frontier",
    "confidence": 0.62,
    "local_confidence": 0.62,
    "frontier_model": "claude-sonnet-4-6",
    "masking_applied": true,
    "entities_masked": 4,
    "latency_ms": 3421,
    "cost_usd": 0.018,
    "ip_safe": true,
    "leak_scan": "PASS"
  }
}
```

### 6.2 Admin API

```
# Model management
GET    /v1/admin/models                    # List deployed models
POST   /v1/admin/models/deploy             # Deploy a new model version
DELETE /v1/admin/models/{model_id}         # Retire a model

# Pattern memory
GET    /v1/admin/patterns                  # List patterns
POST   /v1/admin/patterns                  # Add pattern
PUT    /v1/admin/patterns/{id}             # Update pattern
GET    /v1/admin/patterns/review-queue     # Patterns awaiting review

# Entity registry
GET    /v1/admin/entities                  # List entity mappings
POST   /v1/admin/entities                  # Add mapping
PUT    /v1/admin/entities/{id}             # Update mapping
POST   /v1/admin/entities/auto-detect      # Run NER on a text sample

# Metrics
GET    /v1/admin/metrics                   # Current metrics
GET    /v1/admin/metrics/cost              # Cost breakdown
GET    /v1/admin/metrics/routing           # Routing distribution
GET    /v1/admin/metrics/accuracy          # Accuracy tracking
GET    /v1/admin/metrics/leaks             # IP leak scan history

# Configuration
GET    /v1/admin/config                    # Current config
PUT    /v1/admin/config                    # Update config
POST   /v1/admin/config/validate           # Validate config
```

### 6.3 Streaming API

```
POST /v1/query/stream
```

Server-Sent Events (SSE) for streaming responses:
```
event: routing
data: {"path": "local", "confidence": 0.93}

event: token
data: {"text": "Based on", "index": 0}

event: token
data: {"text": " the analysis", "index": 1}

event: done
data: {"total_tokens": 342, "latency_ms": 1205}
```

---

## 7. Observability & Monitoring

### 7.1 Metrics Dashboard

| Metric | Description | Target |
|--------|-------------|--------|
| **Local resolution rate** | % of queries handled locally | ≥ 85% |
| **Local accuracy** | Accuracy of locally-resolved queries | ≥ 92% |
| **Escalation accuracy** | Accuracy of frontier-resolved queries | ≥ 95% |
| **Mean latency (local)** | Average response time for local queries | < 500ms |
| **Mean latency (escalated)** | Average response time for escalated queries | < 5000ms |
| **Daily cost** | Total frontier API spend | Budget-dependent |
| **IP leak detections** | Blocked queries due to IP detection | 0 (any is an alert) |
| **Pattern memory hit rate** | % of queries matching a stored pattern | ≥ 70% |
| **Confidence calibration error** | ECE of confidence estimates | < 0.05 |
| **User satisfaction** | Thumbs up rate on responses | ≥ 90% |

### 7.2 Audit Log

Every query generates an immutable audit record:

```json
{
  "timestamp": "2026-02-23T14:30:22Z",
  "query_id": "q_abc123",
  "user_id": "user_456",
  "route": "escalate",
  "local_confidence": 0.62,
  "masking_applied": true,
  "entities_masked": ["CompoundX-7", "XR-42", "FormulationMatrix-9"],
  "leak_scan_result": "PASS",
  "frontier_provider": "anthropic",
  "frontier_model": "claude-sonnet-4-6",
  "sanitized_query_hash": "sha256:a1b2c3...",  // hash, not the query itself
  "cost_usd": 0.018,
  "latency_ms": 3421,
  "user_feedback": null
}
```

### 7.3 Alerts

| Alert | Trigger | Severity |
|-------|---------|----------|
| **IP Leak Detected** | Leak scanner blocks a query | CRITICAL |
| **Escalation Rate Spike** | Escalation rate > 25% over 1hr window | WARNING |
| **Frontier Provider Down** | Provider API returning errors | HIGH |
| **Cost Budget Exceeded** | Daily/monthly spend exceeds threshold | WARNING |
| **Local Model Accuracy Drop** | Rolling accuracy drops below 88% | HIGH |
| **Confidence Miscalibration** | ECE exceeds 0.1 | MEDIUM |

---

## 8. Deployment Architecture

### 8.1 Minimum Viable Deployment

```yaml
# docker-compose.yaml (minimum)
version: '3.8'
services:
  sovereign-api:
    image: sovereignai/server:latest
    ports:
      - "8080:8080"
    environment:
      - MODEL_PATH=/models/domain-v1
      - PATTERN_DB_PATH=/data/patterns
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    volumes:
      - ./models:/models
      - ./data:/data
      - ./config:/config
    deploy:
      resources:
        reservations:
          devices:
            - capabilities: [gpu]
              count: 1

  pattern-db:
    image: qdrant/qdrant:latest
    ports:
      - "6333:6333"
    volumes:
      - ./qdrant_data:/qdrant/storage

  dashboard:
    image: sovereignai/dashboard:latest
    ports:
      - "3000:3000"
    environment:
      - API_URL=http://sovereign-api:8080
```

### 8.2 Production Deployment (Kubernetes)

```yaml
# Horizontal pod autoscaling for inference
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: sovereign-inference
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: sovereign-inference
  minReplicas: 2
  maxReplicas: 10
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
    - type: Pods
      pods:
        metric:
          name: inference_queue_depth
        target:
          type: AverageValue
          averageValue: "5"
```

### 8.3 Hardware Recommendations

| Scale | Queries/day | GPU | RAM | Storage | Monthly Cost |
|-------|------------|-----|-----|---------|-------------|
| **Starter** | < 1K | 1x RTX 4090 | 32GB | 100GB SSD | ~$200 |
| **Team** | 1K–10K | 1x A100-40GB | 64GB | 500GB SSD | ~$800 |
| **Department** | 10K–100K | 2x A100-80GB | 128GB | 1TB NVMe | ~$3,000 |
| **Enterprise** | 100K–1M+ | 4x H100 | 256GB | 2TB NVMe | ~$8,000 |

---

## 9. SDK & Integrations

### 9.1 Python SDK

```python
from sovereign import SovereignClient

client = SovereignClient(base_url="http://localhost:8080")

# Simple query
response = client.query("Analyze the contract terms for Project Alpha")
print(response.text)
print(f"Routed: {response.routing.path}, Confidence: {response.routing.confidence}")

# With options
response = client.query(
    "Evaluate compound interaction risks",
    domain="pharma",
    allow_escalation=True,
    max_latency_ms=3000
)

# Streaming
for chunk in client.query_stream("Summarize the Q4 risk report"):
    print(chunk.text, end="", flush=True)

# Admin
models = client.admin.list_models()
metrics = client.admin.get_metrics(period="7d")
client.admin.add_entity_mapping("NewProduct™", "product_category_B")
```

### 9.2 Integrations

| Integration | Method | Status |
|-------------|--------|--------|
| **LangChain** | Custom LLM wrapper | Planned |
| **LlamaIndex** | Custom LLM class | Planned |
| **OpenAI-compatible API** | Drop-in replacement for `/v1/chat/completions` | Planned |
| **Slack** | Bot integration | Planned |
| **VS Code** | Extension (code completion) | Planned |
| **Jupyter** | Magic commands (`%%sovereign`) | Planned |
| **REST/gRPC** | Native API | Core |

### 9.3 OpenAI API Compatibility

Drop-in replacement — change your base URL and you're running through SovereignAI:

```python
import openai

# Before (direct frontier, IP exposed):
# client = openai.OpenAI()

# After (sovereign, IP safe):
client = openai.OpenAI(
    base_url="http://localhost:8080/v1",
    api_key="sovereign-key"
)

# Same API, zero code changes
response = client.chat.completions.create(
    model="domain-v1",  # your local model
    messages=[{"role": "user", "content": "Analyze the Q4 risk report"}]
)
```

---

## 10. Security Model

### 10.1 Threat Model

| Threat | Mitigation |
|--------|------------|
| **Curious frontier provider** | MaskLayer strips all IP before transmission |
| **Provider data breach** | Only sanitized queries stored at provider; no reverse mapping possible |
| **Legal subpoena of provider** | Sanitized queries contain no proprietary information |
| **Man-in-the-middle** | TLS encryption for all API calls |
| **Insider threat (employee)** | RBAC, audit logging, entity registry access controls |
| **Composition attack** | Query distribution across providers, temporal decorrelation, query batching |
| **Model extraction** | Local model never exposed externally; API rate limiting |

### 10.2 Compliance Matrix

| Regulation | Requirement | SovereignAI Support |
|-----------|-------------|---------------------|
| **GDPR** | Data residency, right to deletion | All PII processed locally; frontier sees no personal data |
| **HIPAA** | PHI protection | Health data stays on-prem; only abstract medical queries escalated |
| **SOC 2** | Access controls, audit trails | Full audit log, RBAC, encryption at rest |
| **CCPA** | Consumer data protection | No consumer data leaves perimeter |
| **ITAR** | Export-controlled technical data | Technical data processed locally; only generalized queries exported |
| **PCI DSS** | Payment card data protection | Financial data never transmitted |

---

## 11. Project Roadmap

### Phase 1: Foundation (Months 1–3)
- [ ] Core inference server with local model support
- [ ] Basic ConfidenceRouter (entropy-based)
- [ ] MaskLayer v1 (entity registry + regex patterns)
- [ ] Single frontier provider (OpenAI)
- [ ] REST API
- [ ] CLI tools for training and deployment
- [ ] Basic metrics dashboard

### Phase 2: Production-Ready (Months 4–6)
- [ ] Domain Forge full pipeline (ingest → train → eval → deploy)
- [ ] Pattern Memory with vector DB
- [ ] MaskLayer v2 (NER + embedding similarity + differential perturbation)
- [ ] Multi-provider support (OpenAI, Anthropic, Google)
- [ ] Streaming API
- [ ] Python SDK
- [ ] Kubernetes deployment manifests
- [ ] Comprehensive audit logging

### Phase 3: Enterprise (Months 7–12)
- [ ] OpenAI-compatible API (drop-in replacement)
- [ ] Continuous learning from production
- [ ] Adaptive threshold calibration
- [ ] LangChain/LlamaIndex integrations
- [ ] Multi-model routing (different local models for different domains)
- [ ] Formal IP leak verification
- [ ] SOC 2 compliance toolkit
- [ ] Enterprise SSO/SAML integration
- [ ] Web-based admin console

### Phase 4: Ecosystem (Year 2)
- [ ] Pre-built domain packs (legal, healthcare, finance, engineering)
- [ ] Marketplace for pattern libraries
- [ ] Federated pattern sharing (anonymized cross-org learning)
- [ ] On-device deployment (edge/mobile)
- [ ] Multi-language support
- [ ] Confidential computing integration (Intel SGX, AMD SEV)

---

## 12. Technology Stack

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| **Language** | Python 3.11+ (core), Rust (performance-critical paths) | ML ecosystem + speed where needed |
| **Inference** | vLLM / llama.cpp / TGI | Production-grade model serving |
| **Training** | Hugging Face Transformers + PEFT + DeepSpeed | Standard fine-tuning stack |
| **Vector DB** | Qdrant (default), ChromaDB, Weaviate (pluggable) | Pattern memory storage |
| **API Framework** | FastAPI + uvicorn | Async, fast, OpenAPI docs |
| **Streaming** | Server-Sent Events (SSE) | Standard, widely supported |
| **Dashboard** | Grafana + custom React frontend | Metrics visualization |
| **Metrics** | Prometheus + custom collectors | Time-series metrics |
| **Container** | Docker + Kubernetes (Helm charts) | Standard deployment |
| **CI/CD** | GitHub Actions | Open-source friendly |
| **NER** | spaCy + custom models | Entity detection |
| **Embeddings** | BGE / E5 / Nomic (local) | No external embedding API needed |

---

## 13. Pricing Model (if commercialized)

### Open Source (Free)
- Full framework: Domain Forge + MaskLayer + ConfidenceRouter
- Community support
- Self-hosted only

### Sovereign Cloud ($X/month)
- Managed hosting of local model
- Pre-configured frontier provider connections
- Managed pattern memory
- Dashboard and monitoring
- SLA: 99.9% uptime

### Enterprise ($X/month)
- Everything in Cloud
- Custom domain pack development
- Dedicated support engineer
- Compliance certification assistance
- Custom integrations
- On-prem deployment support

---

## 14. Success Metrics

| Metric | Target (6 months) | Target (12 months) |
|--------|-------------------|---------------------|
| GitHub stars | 1,000 | 5,000 |
| Production deployments | 10 | 100 |
| Community contributors | 20 | 50 |
| Domain packs available | 3 | 10 |
| IP leaks in production | 0 | 0 |
| Average cost savings vs frontier | 80% | 90% |
| Local resolution rate | 80% | 88% |

---

## 15. Getting Started

```bash
# Install
pip install sovereignai

# Initialize a new project
sovereign init my-company --domain legal

# Ingest proprietary data
sovereign forge ingest --source /data/contracts/ --format pdf

# Train domain model
sovereign forge train --base meta-llama/Llama-3.1-8B-Instruct

# Build pattern memory
sovereign forge patterns build --from /data/solved_cases/

# Configure entity registry
sovereign mask entities add --file /config/proprietary_terms.csv

# Start serving
sovereign serve --port 8080

# Test a query
sovereign query "Analyze the indemnification clause in section 4.2"

# Check metrics
sovereign metrics show --period 24h
```

---

*SovereignAI — Frontier intelligence. Zero exposure.*
