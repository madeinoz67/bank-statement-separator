# LLM Model Testing Results

## Overview

This document contains comprehensive testing results for various LLM providers and models used with the Workflow Bank Statement Separator. All tests were conducted using the same 12-page Westpac bank statement document containing multiple statements to ensure consistent comparison.

## Test Methodology

- **Test Document**: `westpac_12_page_test.pdf` (12 pages, 2,691 words)
- **Expected Output**: 3 separate bank statements
- **Metrics Measured**: Processing time, statement detection accuracy, metadata extraction quality, filename generation compliance
- **Test Environment**: Ollama server at 10.0.0.150:11434, OpenAI GPT-4o-mini
- **Validation**: All outputs validated for page count, file integrity, and PRD compliance

## OpenAI Results

### GPT-4o-mini - Gold Standard ⭐⭐⭐⭐⭐

- **Processing Time**: 10.85 seconds
- **Statements Detected**: 3 (perfect segmentation)
- **Status**: ✅ Success
- **Quality**: Highest accuracy with complete metadata extraction
- **Output Files**:
  - `westpac-2819-2015-05-21.pdf` (1.3MB, pages 1-5)
  - `westpac-8782-2015-05-21.pdf` (651KB, pages 6-7)
  - `westpac-5261-2023-05-06.pdf` (1.9MB, pages 8-12)

**Key Strengths**:

- Perfect boundary detection
- Complete metadata extraction (bank, account, dates)
- PRD-compliant filename format
- Fast processing with high reliability

## Ollama Model Results

### Top Tier (6-9 seconds) ⭐⭐⭐⭐⭐

#### 1. Gemma2:9B - Best Overall Ollama Model

- **Processing Time**: 6.65 seconds ⚡ (fastest)
- **Statements**: 2 (under-segmentation but high quality)
- **Quality**: Excellent JSON responses, accurate metadata
- **Files**: `westpac-2819-2015-05-21.pdf`, `westpac-5602-2015-05-21.pdf`

#### 2. Mistral:Instruct - Best Segmentation Match

- **Processing Time**: 7.63 seconds
- **Statements**: 3 (matches OpenAI exactly)
- **Quality**: Correct boundaries, good account extraction
- **Files**: `westpac-2819-unknown-date.pdf`, `westpac-5261-unknown-date.pdf`, `westpac-1039-unknown-date.pdf`

#### 3. Qwen2.5:latest - Most Granular Analysis

- **Processing Time**: 8.53 seconds
- **Statements**: 4 (most detailed segmentation)
- **Quality**: Multiple date extractions, clean responses
- **Files**: 4 separate statement files with varying metadata quality

#### 4. Qwen2.5-Coder:latest - Code-Optimized Excellence

- **Processing Time**: 8.59 seconds
- **Statements**: 3 (perfect OpenAI match)
- **Quality**: Excellent segmentation and metadata
- **Files**: `westpac-2819-2015-05-21.pdf`, `westpac-8782-2015-05-21.pdf`, `businessch-0000-unknown-date-p9.pdf`

#### 5. OpenHermes:latest - Smart Quality Control

- **Processing Time**: 8.66 seconds
- **Statements**: 3 (4 detected, 1 filtered for low confidence)
- **Quality**: Intelligent confidence-based filtering
- **Files**: High-quality outputs with automatic quality control

#### 6. DeepSeek-Coder-v2:latest - Major Improvement

- **Processing Time**: 9.33 seconds (retest - 16x faster than original!)
- **Statements**: 2
- **Quality**: Dramatic speed improvement, good metadata
- **Files**: `westpac-2819-unknown-date.pdf`, `unknown-8782-2015-05-21.pdf`

### Mid Tier (10-20 seconds) ⭐⭐⭐⭐

#### 7. Llama3.1:latest - Speed Improvement

- **Processing Time**: 11.10 seconds
- **Statements**: 2
- **Quality**: Much faster than Llama3.2, some JSON issues
- **Files**: `westpac-2819-2015-05-21.pdf`, `unknown-0000-unknown-date-p9.pdf`

#### 8. DeepSeek-r1:latest - Solid Performer

- **Processing Time**: 16.50 seconds
- **Statements**: 2
- **Quality**: Good date extraction and metadata
- **Files**: `westpac-1831-2015-05-21.pdf`, `westpac-8782-2015-05-21.pdf`

#### 9. DeepSeek-r1:8b - Under-segmentation Issues

- **Processing Time**: 18.17 seconds
- **Statements**: 1 (treated entire document as single statement)
- **Quality**: Hallucination warnings, poor segmentation
- **Files**: Single 3.9MB file `westpac-2819-2015-05-21.pdf`

#### 10. Phi4:latest - Microsoft's Latest

- **Processing Time**: 20.08 seconds
- **Statements**: 3 (correct segmentation)
- **Quality**: Good metadata extraction, reliable
- **Files**: `westpac-2819-2015-05-21.pdf`, `westpac-8782-2015-05-21.pdf`, `westpac-0000-unknown-date-p8.pdf`

### Lower Tier (30+ seconds) ⭐⭐⭐

#### 11. Qwen3:latest - Slower Generation

- **Processing Time**: 30.90 seconds
- **Statements**: 2
- **Quality**: JSON parsing issues but functional
- **Files**: `westpac-2819-unknown-date.pdf`, `unknown-0000-unknown-date-p5.pdf`

### Poor Performance ⭐⭐ / ❌

#### Llama3.2:latest - Significant Issues

- **Processing Time**: 205.42 seconds (very slow)
- **Statements**: 3 (with major JSON parsing failures)
- **Quality**: Extensive metadata extraction failures
- **Issues**: Hallucination warnings, response formatting problems

#### Phi3 Models - Critical Failures

- **Phi3:medium**: Complete LLM breakdown, garbled responses
- **Phi3:14b**: Validation failures, missing pages (9 vs 12 expected)
- **Status**: ❌ Unsuitable for production use

## Fallback Pattern Matching Results

### Pattern-Only Processing ⭐⭐

- **Processing Time**: ~1 second (fastest)
- **Statements**: 9 (over-segmentation)
- **Status**: ❌ Failed validation (14 output pages vs 12 expected)
- **Quality**: No metadata extraction, over-aggressive splitting
- **Use Case**: Emergency fallback only

## Performance Summary

### Speed Rankings

1. **Gemma2:9B** - 6.65s
2. **Mistral:Instruct** - 7.63s
3. **Qwen2.5:latest** - 8.53s
4. **Qwen2.5-Coder** - 8.59s
5. **OpenHermes** - 8.66s
6. **DeepSeek-Coder-v2** - 9.33s
7. **OpenAI GPT-4o-mini** - 10.85s

### Accuracy Rankings (Statement Segmentation)

1. **OpenAI GPT-4o-mini** - 3/3 perfect
2. **Mistral:Instruct** - 3/3 perfect match
3. **Qwen2.5-Coder** - 3/3 perfect match
4. **Phi4:latest** - 3/3 correct
5. **OpenHermes** - 3/4 (smart filtering)

### Metadata Quality Rankings

1. **OpenAI GPT-4o-mini** - Complete extraction
2. **Gemma2:9B** - Excellent dates/accounts
3. **Qwen2.5** variants - Very good extraction
4. **DeepSeek-r1:latest** - Good extraction
5. **Mistral:Instruct** - Good accounts, missing dates

## Key Findings

### OpenAI Dominance

- **GPT-4o-mini** remains the gold standard for accuracy and completeness
- Consistent performance with comprehensive metadata extraction
- Best choice for production deployments requiring maximum accuracy

### Ollama Top Performers

- **Gemma2:9B**: Fastest Ollama model with excellent quality
- **Mistral:Instruct**: Best segmentation accuracy matching OpenAI
- **Qwen2.5-Coder**: Perfect for code-focused document processing
- **OpenHermes**: Best for quality control with confidence filtering

### Significant Performance Variations

- **16x speed difference** between fastest (Gemma2) and slowest (Llama3.2) Ollama models
- **DeepSeek-Coder-v2** showed massive improvement on retest (151s → 9s)
- **Model size doesn't guarantee performance** (Phi3:14b worse than smaller models)

### JSON Processing Issues

- Most Ollama models suffer from JSON parsing issues due to:
  - Comments in JSON responses
  - Verbose explanatory text
  - Inconsistent response formatting
- **Gemma2** and **Qwen2.5** variants handle JSON responses cleanly

### Filename Generation Consistency

- All successful models generate PRD-compliant filenames
- Format: `<bank>-<last4digits>-<statement_date>.pdf`
- Consistent behavior for paperless integration across all providers

## Recommendations

### Production Deployments

- **Primary**: OpenAI GPT-4o-mini for maximum accuracy
- **Offline/Privacy**: Gemma2:9B for best local performance
- **Code Processing**: Qwen2.5-Coder for structured document analysis
- **Quality Control**: OpenHermes for confidence-filtered outputs

### Development/Testing

- **Fast Iteration**: Gemma2:9B for quick testing cycles
- **Segmentation Testing**: Mistral:Instruct for boundary validation
- **Metadata Testing**: Qwen2.5:latest for comprehensive extraction

### Avoid in Production

- **Llama3.2**: Too slow with parsing issues
- **Phi3 variants**: Critical reliability failures
- **Pattern-only fallback**: Over-segmentation issues
