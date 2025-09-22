# 🚀 PER Agent Setup Guide

## Prerequisites

- **Python 3.11+** (Python 3.12 recommended)
- **UV** package manager (fastest option) or pip/conda
- **Git** for version control
- **RTX 5070 Ti** or equivalent GPU with 16GB VRAM (recommended)
- **Internet connection** for literature search APIs

## ⚡ Quick Setup with UV (Recommended)

UV is the fastest Python package manager - perfect for AI/ML projects with large dependencies.

### 1. Install UV (if not already installed)
```bash
# Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Or via pip
pip install uv
```

### 2. Clone and Setup Project
```bash
# Clone the repository
git clone https://github.com/yourusername/per-agent.git
cd per-agent

# Create virtual environment
uv venv

# Activate environment (Windows)
.venv\Scripts\activate

# Install dependencies (⚡ Lightning fast!)
uv pip install -r requirements.txt
```

### 3. Verify Installation
```bash
# Test configuration system
python -c "from src.core.config import Config; print('✅ Setup complete!')"

# Launch CLI interface
python src/main.py
```

## 🐍 Alternative Setup Options

### Option 2: Standard Python + pip
```bash
# Create virtual environment
python -m venv per-agent
per-agent\Scripts\activate  # Windows
source per-agent/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt
```

### Option 3: Conda Environment
```bash
# Create conda environment
conda create -n per-agent python=3.11
conda activate per-agent

# Install dependencies
pip install -r requirements.txt
# or
conda install -c conda-forge langchain streamlit pandas numpy
```

## 🤖 Ollama Setup (Required for Local LLMs)

### 1. Install Ollama
Download from: https://ollama.ai/

### 2. Download Required Models
```bash
# Core models for PER Agent (adjust based on your VRAM)
ollama pull qwen2.5:32b-instruct-q4_k_m    # 14GB VRAM
ollama pull deepseek-r1:14b-q4_k_m         # 9GB VRAM  
ollama pull qwen2.5-math:7b                 # 7GB VRAM
ollama pull mistral-small:22b-q4_k_m        # 12GB VRAM
ollama pull qwen2.5-coder:7b                # 7GB VRAM
```

### 3. Verify Ollama
```bash
# Check Ollama is running
ollama list

# Test a model
ollama run qwen2.5-math:7b "Hello, can you help with physics?"
```

## 🎯 Usage

### CLI Interface
```bash
# Activate environment
.venv\Scripts\activate  # or your chosen environment

# Launch interactive CLI
python src/main.py
```

### API Usage
```python
from src.core.orchestrator import ResearchOrchestrator
from src.core.models import ResearchQuery

# Create research query
query = ResearchQuery(
    question="How effective are simulations in teaching wave physics?",
    max_sources=20
)

# Run research
orchestrator = ResearchOrchestrator()
result = await orchestrator.research(query)
print(result.get_summary())
```

## 📊 System Requirements

### Minimum Requirements
- **CPU**: Modern multi-core processor
- **RAM**: 16GB system RAM
- **GPU**: 8GB VRAM (will use smaller models)
- **Storage**: 10GB free space
- **Network**: Broadband internet

### Recommended Requirements
- **CPU**: Intel i7/AMD Ryzen 7 or better
- **RAM**: 32GB system RAM  
- **GPU**: RTX 5070 Ti (16GB VRAM) or equivalent
- **Storage**: 50GB free space (for models and cache)
- **Network**: High-speed internet

### Model Memory Usage
| Model | VRAM Usage | Purpose |
|-------|------------|---------|
| Qwen2.5-32B-Instruct | 14GB | Literature search, analysis |
| DeepSeek-R1-14B | 9GB | Reasoning, quality control |
| Qwen2.5-Math-7B | 7GB | Physics/math validation |
| Mistral-Small-22B | 12GB | Content synthesis |
| Qwen2.5-Coder-7B | 7GB | Report generation |

## 🔧 Configuration

### Environment Variables
Create a `.env` file in the project root:
```bash
# Ollama configuration
OLLAMA_HOST=http://localhost:11434

# Quality settings
MIN_QUALITY_SCORE=0.8
MAX_SOURCES=25

# API keys (optional - for enhanced features)
SEMANTIC_SCHOLAR_API_KEY=your_key_here
```

### Custom Configuration
Edit `src/core/config.py` to customize:
- Model selections and quantization levels
- Agent timeout and retry settings
- Output directories and formats
- Quality thresholds

## 🧪 Testing

### Run Tests
```bash
# Unit tests
pytest tests/ -v

# Test specific component
pytest tests/test_config.py -v

# Test with coverage
pytest tests/ --cov=src --cov-report=html
```

### Manual Testing
```bash
# Test configuration
python -c "from src.core.config import Config; Config().validate_system_requirements()"

# Test CLI
python src/main.py

# Test individual components (when implemented)
python -c "from src.agents.base_agent import BaseAgent; print('✅ Base agent working')"
```

## 🐛 Troubleshooting

### Common Issues

**1. Import Errors**
```bash
# Make sure virtual environment is activated
.venv\Scripts\activate

# Reinstall dependencies
uv pip install -r requirements.txt --force-reinstall
```

**2. Ollama Connection Issues**
```bash
# Check Ollama service
ollama list
curl http://localhost:11434/api/tags

# Restart Ollama if needed
ollama serve
```

**3. VRAM Issues**
- Use smaller models (7B instead of 32B)
- Enable quantization (Q4_K_M or Q8_0)
- Close other GPU applications
- Monitor with `nvidia-smi`

**4. Slow Package Installation**
```bash
# Use UV instead of pip
uv pip install -r requirements.txt

# Or update pip
python -m pip install --upgrade pip
```

### Performance Optimization

**1. GPU Memory**
```python
# In config.py, use smaller models:
"qwen_7b": ModelConfig(
    name="Qwen2.5-7B-Instruct", 
    model_id="qwen2.5:7b-instruct-q4_k_m",
    vram_usage=5
)
```

**2. CPU Performance**
- Increase `num_threads` in Ollama
- Use SSD storage for models
- Ensure adequate system RAM

**3. Network Optimization**
- Cache API responses
- Use local mirrors when available
- Implement request rate limiting

## 📚 Documentation

- **API Documentation**: `docs/api.md` (coming soon)
- **Agent Development**: `docs/agents.md` (coming soon)  
- **Workflow Guide**: `docs/workflow.md` (coming soon)
- **Examples**: `examples/` directory (coming soon)

## 🆘 Getting Help

- **Issues**: Create GitHub issue with detailed error info
- **Discussions**: Use GitHub Discussions for questions
- **Documentation**: Check `docs/` directory
- **Logs**: Review `logs/` directory for debugging

---

**Ready to revolutionize physics education research with AI!** 🚀