# Physics Education Research (PER) Agent

A multi-agent AI system for automating physics education research tasks, from literature discovery to formatted report generation. Built with LangGraph and optimized for local LLMs on RTX 5070 Ti (16GB VRAM).

## 🎯 Features

- **Multi-Agent Architecture**: Six specialized agents working together
- **Local LLM Integration**: Optimized for RTX 5070 Ti with quantized models
- **Research Automation**: From literature search to report generation
- **Professional Output**: LaTeX/Markdown/PDF formatted reports
- **Quality Assurance**: Built-in validation and error correction
- **Streamlit GUI**: Professional web interface with real-time progress

## 🏗️ Architecture

### Agents
1. **Literature Scout**: Searches arXiv, Semantic Scholar, Google Scholar
2. **Document Analyzer**: Parses PDFs and extracts key findings
3. **Physics Specialist**: Validates concepts and mathematical accuracy
4. **Content Synthesizer**: Combines insights and identifies patterns
5. **Report Generator**: Creates formatted academic reports
6. **Quality Controller**: Reviews outputs for accuracy and standards

### Models
- **Qwen2.5-32B-Instruct**: Lead research and ranking
- **DeepSeek-R1-14B**: Reasoning and quality control
- **Qwen2.5-Math-7B**: Physics and mathematical validation
- **Mistral-Small-22B**: Content synthesis
- **Qwen2.5-Coder-7B**: Code and report generation

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- CUDA-compatible GPU (RTX 5070 Ti recommended)
- Ollama for local LLM management
- VSCode with GitHub Copilot Agent

### Installation
```bash
git clone https://github.com/yourusername/per-agent.git
cd per-agent
pip install -r requirements.txt
```

### Setup Ollama Models
```bash
ollama pull qwen2.5:32b-instruct-q4_k_m
ollama pull deepseek-r1:14b-q4_k_m
ollama pull qwen2.5-math:7b
ollama pull mistral-small:22b-q4_k_m
ollama pull qwen2.5-coder:7b
```

### Run the Application
```bash
# CLI Version
python src/main.py

# GUI Version
streamlit run gui/app.py
```

## 📊 Usage Example

```python
from src.core.orchestrator import ResearchOrchestrator

# Initialize the research system
orchestrator = ResearchOrchestrator()

# Start a research session
result = await orchestrator.research(
    question="Effectiveness of wave simulations in high school physics teaching"
)

# Get formatted report
report = result.generate_report(format="pdf")
```

## 🛠️ Development

### Project Structure
```
per-agent/
├── src/
│   ├── agents/          # Individual agent implementations
│   ├── core/            # Core orchestration and utilities
│   └── models/          # Data models and schemas
├── tests/               # Unit and integration tests
│   └── legacy/          # Historical demos and ad-hoc test scripts (moved from project root)
├── gui/                 # Streamlit web interface
├── docs/                # Documentation and examples
└── requirements.txt     # Python dependencies
```

### Running Tests
```bash
pytest tests/ -v
```

Note: several demo and quick-test scripts were moved from the repository root into `tests/legacy/` to keep the top-level clean. Developer utilities (GPU checks, small helpers) are in `scripts/`.

Repository root cleanup: demo and ad-hoc test scripts were moved into `tests/legacy/`. Use those scripts only for local interactive debugging; they are intentionally not part of automated tests.

## 📈 Performance

- **Memory Usage**: 12-16GB VRAM (depending on model selection)
- **Context Length**: Up to 64K tokens
- **Processing Speed**: ~2-5 minutes per research query
- **Quality Score**: 90%+ accuracy on physics education topics

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [LangGraph](https://github.com/langchain-ai/langgraph) for agent orchestration
- Powered by [Ollama](https://ollama.ai/) for local LLM management
- Enhanced with GitHub Copilot Agent integration
- UI created with [Streamlit](https://streamlit.io/)

## 📞 Support

For questions and support, please open an issue on GitHub or contact the development team.

---

**Ready to revolutionize physics education research with AI!** 🚀