# Model Comparison Tables

## Performance Overview

| Rank | Model | Provider | Time (s) | Statements | Quality | Status |
|------|-------|----------|----------|------------|---------|---------|
| 1 | Gemma2:9B | Ollama | 6.65 | 2 | ⭐⭐⭐⭐⭐ | ✅ |
| 2 | Mistral:Instruct | Ollama | 7.63 | 3 | ⭐⭐⭐⭐⭐ | ✅ |
| 3 | Qwen2.5:latest | Ollama | 8.53 | 4 | ⭐⭐⭐⭐⭐ | ✅ |
| 4 | Qwen2.5-Coder | Ollama | 8.59 | 3 | ⭐⭐⭐⭐⭐ | ✅ |
| 5 | OpenHermes | Ollama | 8.66 | 3 | ⭐⭐⭐⭐ | ✅ |
| 6 | DeepSeek-Coder-v2 | Ollama | 9.33 | 2 | ⭐⭐⭐⭐⭐ | ✅ |
| 7 | GPT-4o-mini | OpenAI | 10.85 | 3 | ⭐⭐⭐⭐⭐ | ✅ |
| 8 | Llama3.1 | Ollama | 11.10 | 2 | ⭐⭐⭐ | ✅ |
| 9 | DeepSeek-r1:latest | Ollama | 16.50 | 2 | ⭐⭐⭐⭐ | ✅ |
| 10 | DeepSeek-r1:8b | Ollama | 18.17 | 1 | ⭐⭐ | ⚠️ |
| 11 | Phi4:latest | Ollama | 20.08 | 3 | ⭐⭐⭐⭐ | ✅ |
| 12 | Qwen3:latest | Ollama | 30.90 | 2 | ⭐⭐⭐ | ✅ |
| 13 | Llama3.2 | Ollama | 205.42 | 3 | ⭐⭐ | ⚠️ |
| - | Phi3:medium | Ollama | - | 7 | ⭐ | ❌ |
| - | Phi3:14b | Ollama | - | 3 | ⭐ | ❌ |
| - | Pattern Fallback | Local | 1.0 | 9 | ⭐⭐ | ❌ |

## Detailed Comparison by Provider

### OpenAI Models

| Model | Time (s) | Accuracy | Metadata Quality | Cost | Recommendation |
|-------|----------|----------|------------------|------|----------------|
| GPT-4o-mini | 10.85 | Perfect (3/3) | Complete | Medium | ✅ Production |

**Notes**: Gold standard for accuracy and completeness. Best choice when maximum precision is required.

### Ollama Models - Top Tier (< 10 seconds)

| Model | Time (s) | Statements | Date Extract | Account Extract | JSON Quality | Use Case |
|-------|----------|------------|--------------|----------------|--------------|----------|
| Gemma2:9B | 6.65 | 2 | ✅ Excellent | ✅ Complete | ✅ Clean | Speed priority |
| Mistral:Instruct | 7.63 | 3 | ❌ Missing | ✅ Complete | ⚠️ Some issues | Segmentation accuracy |
| Qwen2.5:latest | 8.53 | 4 | ✅ Multiple | ✅ Complete | ✅ Clean | Granular analysis |
| Qwen2.5-Coder | 8.59 | 3 | ✅ Excellent | ✅ Complete | ✅ Clean | Code processing |
| OpenHermes | 8.66 | 3 | ✅ Good | ✅ Complete | ✅ Clean | Quality control |
| DeepSeek-Coder-v2 | 9.33 | 2 | ⚠️ Partial | ✅ Complete | ✅ Clean | Development |

### Ollama Models - Mid Tier (10-30 seconds)

| Model | Time (s) | Issues | Strengths | Recommendation |
|-------|----------|--------|-----------|----------------|
| Llama3.1 | 11.10 | JSON parsing | Speed vs 3.2 | ⚠️ Limited use |
| DeepSeek-r1:latest | 16.50 | None major | Good metadata | ✅ Acceptable |
| DeepSeek-r1:8b | 18.17 | Under-segmentation | - | ❌ Avoid |
| Phi4:latest | 20.08 | Slower | Reliable | ⚠️ Limited use |
| Qwen3:latest | 30.90 | JSON issues | Functional | ❌ Avoid |

### Ollama Models - Poor Performance (> 30 seconds / Failed)

| Model | Time (s) | Primary Issues | Status |
|-------|----------|----------------|--------|
| Llama3.2 | 205.42 | Very slow, JSON failures | ❌ Avoid |
| Phi3:medium | - | Garbled output, fallback | ❌ Broken |
| Phi3:14b | - | Missing pages, validation failure | ❌ Broken |

## Feature Comparison Matrix

### Metadata Extraction Capabilities

| Model | Bank Name | Account Number | Statement Dates | Customer Info | Confidence |
|-------|-----------|----------------|-----------------|---------------|------------|
| GPT-4o-mini | ✅ Complete | ✅ Full digits | ✅ Perfect dates | ⚠️ Limited | High |
| Gemma2:9B | ✅ Complete | ✅ Last 4 digits | ✅ Perfect dates | ❌ None | High |
| Mistral:Instruct | ✅ Complete | ✅ Full numbers | ❌ Missing dates | ❌ None | Medium |
| Qwen2.5-Coder | ✅ Complete | ✅ Full numbers | ✅ Perfect dates | ❌ None | High |
| OpenHermes | ✅ Complete | ✅ Full numbers | ✅ Good dates | ❌ None | High |
| DeepSeek-Coder-v2 | ⚠️ Partial | ✅ Full numbers | ⚠️ Some dates | ❌ None | Medium |

### Document Segmentation Accuracy

| Model | Expected (3) | Detected | Accuracy | Notes |
|-------|--------------|----------|----------|-------|
| GPT-4o-mini | 3 | 3 | 100% | Perfect boundaries |
| Mistral:Instruct | 3 | 3 | 100% | Exact match |
| Qwen2.5-Coder | 3 | 3 | 100% | Exact match |
| Phi4:latest | 3 | 3 | 100% | Exact match |
| OpenHermes | 3 | 3 (4-1) | 100% | Smart filtering |
| Qwen2.5:latest | 3 | 4 | 75% | Over-segmentation |
| Gemma2:9B | 3 | 2 | 67% | Under-segmentation |
| DeepSeek models | 3 | 1-2 | 33-67% | Various issues |
| Llama models | 3 | 2-3 | 67-100% | With JSON issues |

## Processing Speed Comparison

### Speed Categories

| Category | Time Range | Models | Use Cases |
|----------|------------|--------|-----------|
| **Ultra Fast** | < 7s | Gemma2:9B | Real-time processing |
| **Fast** | 7-9s | Mistral, Qwen2.5 variants, OpenHermes | Production workflows |
| **Moderate** | 9-15s | DeepSeek-Coder-v2, GPT-4o-mini, Llama3.1 | Standard processing |
| **Slow** | 15-25s | DeepSeek-r1 variants, Phi4 | Batch processing |
| **Very Slow** | > 30s | Qwen3, Llama3.2 | Background tasks only |

## Resource Requirements

### Model Sizes and Memory Usage

| Model | Size (GB) | Memory Req | GPU Req | CPU Performance |
|-------|-----------|------------|---------|-----------------|
| Gemma2:9B | 5.4 | 8GB+ | Recommended | Good |
| Mistral:Instruct | 4.1 | 6GB+ | Recommended | Good |
| Qwen2.5:latest | 4.7 | 6GB+ | Recommended | Good |
| Qwen2.5-Coder | 4.7 | 6GB+ | Recommended | Good |
| OpenHermes | 4.1 | 6GB+ | Recommended | Good |
| DeepSeek-Coder-v2 | 8.9 | 12GB+ | Required | Poor |
| Llama3.1 | 4.7 | 6GB+ | Recommended | Good |
| Phi4 | 9.1 | 12GB+ | Required | Moderate |
| Qwen3 | 5.2 | 8GB+ | Recommended | Poor |

## Quality Scores Breakdown

### Overall Quality Rating System

- ⭐⭐⭐⭐⭐ Excellent: Perfect/near-perfect accuracy, fast processing
- ⭐⭐⭐⭐ Very Good: Minor issues, reliable performance  
- ⭐⭐⭐ Good: Some issues but usable
- ⭐⭐ Poor: Major issues, limited use
- ⭐ Broken: Unsuitable for production

### Quality Factor Weights

| Factor | Weight | Description |
|--------|--------|-------------|
| Segmentation Accuracy | 40% | Correct statement boundary detection |
| Metadata Extraction | 25% | Bank name, account, date extraction |
| Processing Speed | 20% | Time to complete processing |
| Response Quality | 10% | JSON formatting, parsing success |
| Reliability | 5% | Consistent performance, error rates |

## Use Case Recommendations

### High-Volume Production
1. **Gemma2:9B** - Best speed/quality balance
2. **Mistral:Instruct** - Best segmentation accuracy
3. **GPT-4o-mini** - Maximum accuracy required

### Development/Testing  
1. **Qwen2.5-Coder** - Code-focused processing
2. **OpenHermes** - Quality control testing
3. **DeepSeek-Coder-v2** - Development iteration

### Offline/Privacy-First
1. **Gemma2:9B** - Best local performance
2. **Qwen2.5 variants** - Feature-complete local
3. **Mistral:Instruct** - Segmentation priority

### Budget-Conscious
1. **OpenAI GPT-4o-mini** - Best accuracy per dollar
2. **Self-hosted Gemma2:9B** - Zero marginal cost
3. **Mistral:Instruct** - Good local alternative

### Experimental/Research
1. **Qwen2.5:latest** - Most granular analysis
2. **OpenHermes** - Confidence scoring research
3. **DeepSeek-r1:latest** - Reasoning model testing