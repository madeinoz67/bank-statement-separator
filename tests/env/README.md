# Test Environment Configurations

This directory contains environment configuration files used for comprehensive LLM model testing conducted in Version 2.2.

## Files Overview

### Provider Configurations
- **`.env.openai`** - OpenAI GPT-4o-mini configuration (gold standard)
- **`.env.ollama`** - Base Ollama configuration 
- **`.env.fallback`** - Pattern-matching fallback configuration (no LLM)

### Ollama Model Configurations
All Ollama configurations use server at `http://10.0.0.150:11434`

#### Top Performing Models
- **`.env.ollama_gemma2`** - Gemma2:9B (6.65s) - Fastest model ⚡
- **`.env.ollama_mistral`** - Mistral:Instruct (7.63s) - Best segmentation
- **`.env.ollama_qwen25_coder`** - Qwen2.5-Coder (8.59s) - Code processing
- **`.env.ollama_openhermes`** - OpenHermes (8.66s) - Quality control

#### Other Tested Models
- **`.env.ollama_qwen25`** - Qwen2.5:latest (8.53s) - Most granular
- **`.env.ollama_deepseek_coder_v2_retest`** - DeepSeek-Coder-v2 (9.33s)
- **`.env.ollama_llama31`** - Llama3.1 (11.10s)
- **`.env.ollama_deepseek_r1_latest`** - DeepSeek-r1:latest (16.50s)
- **`.env.ollama_deepseek_r1_8b`** - DeepSeek-r1:8b (18.17s)
- **`.env.ollama_phi4`** / **`.env.ollama_phi4_fixed`** - Phi4:latest (20.08s)
- **`.env.ollama_qwen3`** - Qwen3:latest (30.90s)

#### Poor Performing / Broken Models  
- **`.env.ollama_qwen`** - Original Qwen configuration (testing)
- **`.env.ollama_deepseek`** - Original DeepSeek configuration (testing)
- **`.env.ollama_phi3_medium`** - Phi3:medium (broken - garbled output)
- **`.env.ollama_phi3_14b`** - Phi3:14b (broken - validation failures)

## Testing Results Summary

| Model | Time (s) | Quality | Status | Use Case |
|-------|----------|---------|--------|-----------|
| **OpenAI GPT-4o-mini** | 10.85 | ⭐⭐⭐⭐⭐ | ✅ Gold Standard | Production accuracy |
| **Gemma2:9B** | 6.65 | ⭐⭐⭐⭐⭐ | ✅ Best Speed | Fast processing |
| **Mistral:Instruct** | 7.63 | ⭐⭐⭐⭐⭐ | ✅ Best Segmentation | Boundary detection |
| **Qwen2.5-Coder** | 8.59 | ⭐⭐⭐⭐⭐ | ✅ Code Optimized | Document processing |
| **Pattern Fallback** | 1.0 | ⭐⭐ | ❌ Emergency Only | Over-segmentation |

## Security Note

⚠️ **These are template configurations only** - No real API keys are included. To use these configurations:

1. Copy the desired `.env.*` file to project root
2. Add your actual API keys where placeholders exist
3. Never commit real API keys to version control

## Usage

These configurations were used for comprehensive model testing documented in:
- `docs/reference/llm_model_testing.md` - Complete testing results
- `docs/reference/model_comparison_tables.md` - Performance comparisons
- `docs/user-guide/model-selection-guide.md` - Selection guidance

## Test Command Examples

```bash
# Test with specific model configuration
uv run python -m src.bank_statement_separator.main process \
  test/input/westpac_12_page_test.pdf \
  --env-file tests/env/.env.ollama_gemma2 \
  --verbose

# Compare multiple models
for config in tests/env/.env.ollama_*; do
  echo "Testing with $(basename $config)"
  uv run python -m src.bank_statement_separator.main process \
    test/input/westpac_12_page_test.pdf \
    --env-file $config \
    --dry-run
done
```

## Test Document

All configurations tested with:
- **Document**: `westpac_12_page_test.pdf` (12 pages, 2,691 words)
- **Expected Output**: 3 separate bank statements  
- **Test Environment**: Standardized testing for consistent comparison
- **Validation**: Page count, file integrity, PRD compliance checks

## Archive Purpose

These files are maintained for:
1. **Reproducible Testing** - Recreate exact testing conditions used in model evaluation
2. **Regression Testing** - Validate performance after code changes
3. **Benchmarking** - Compare new models against established baselines
4. **Documentation** - Reference configurations for model selection guidance

---

**Note**: These are testing configurations only. For production use, refer to the model selection guide and use appropriate configurations based on your deployment requirements.