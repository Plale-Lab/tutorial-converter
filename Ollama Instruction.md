# Ollama Setup Instructions

## Where Optimization Happens

| Layer | What It Handles | Relevant to 70B Model |
|-------|-----------------|----------------------|
| **Ollama** | Model loading, quantization, GPU memory, inference speed | ✅ **Primary** |
| **ConvertIt** | Prompt efficiency, chunking, routing | ✅ Secondary |

## For Running 70B Models

**Ollama handles the heavy lifting:**
- **Quantization**: Use Q4 or Q5 quantized versions to fit in VRAM
- **GPU Offloading**: Ollama automatically uses GPU layers
- **Context Window**: Ollama manages KV cache

**ConvertIt optimizations still help:**
- **Smaller chunks** (6K chars) = fewer tokens per call = faster inference
- **Prompt compression** = less input to process
- **Hybrid routing** won't matter much if you're running everything local

---

## Recommendation for 70B on 5090

### 1. Pull a Quantized Model

```bash
# Q4 quantized - good balance of quality and VRAM usage
ollama pull llama3:70b-q4_K_M

# Or Q5 for slightly better quality (needs more VRAM)
ollama pull llama3:70b-q5_K_M
```

### 2. Configure ConvertIt

Update your `.env` or use the Settings modal:

```ini
LLM_PROVIDER=local
OLLAMA_BASE_URL=http://localhost:11434
```

In the Settings modal, set **Ollama Model** to:
```
llama3:70b-q4_K_M
```

### 3. Start Ollama

```bash
ollama serve
```

### 4. VRAM Expectations

| Model | Quantization | Est. VRAM | 5090 (32GB) |
|-------|--------------|-----------|-------------|
| 70B | Q4_K_M | ~40GB | ⚠️ Partial offload |
| 70B | Q4_K_S | ~35GB | ⚠️ Tight fit |
| 70B | Q3_K_M | ~30GB | ✅ Should fit |
| 34B | Q4_K_M | ~20GB | ✅ Comfortable |

> **Note**: If 70B doesn't fully fit, Ollama will automatically offload some layers to CPU (slower but works).

### 5. Performance Tips

1. **Close other GPU apps** before running to maximize available VRAM
2. **Use Q3 quantization** if Q4 causes OOM errors
3. **Consider 34B models** (like `codellama:34b`) for faster inference with good quality
4. **Lower context length** if needed - edit `Modelfile`:
   ```
   PARAMETER num_ctx 4096
   ```

---

## Alternative: High-Quality Smaller Models

If 70B is too slow for your workflow:

| Model | Size | Quality | Speed |
|-------|------|---------|-------|
| `llama3.1:8b` | 8B | Good | ⚡ Fast |
| `mistral:7b` | 7B | Good | ⚡ Fast |
| `llama3:70b-q4` | 70B | Excellent | 🐢 Slower |
| `qwen2.5:32b` | 32B | Very Good | ⚡ Good balance |

**TL;DR**: Ollama does the GPU optimization. ConvertIt's optimizations reduce token count/prompt size, which indirectly helps but isn't GPU-specific.
