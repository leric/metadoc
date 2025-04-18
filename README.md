# Airic - Personal AI Work Partner

Airic is a personal AI work partner that enables closer, more natural human-AI collaboration through innovative concepts like "Meta Documents" and "Guided Problem Decomposition".

## Concept

Airic is built around these core concepts:

- **Meta Document as Collaboration Cornerstone**: Documents are not just static records but the dynamic "source code" driving AI work – a shared, evolving "brain" for the human-AI team.

- **Guided Problem Decomposition as Thinking Partner**: Airic actively assists users in breaking down complex problems through structured questioning and framework suggestions.

- **Everything is Document**: Inspired by Linux, the system treats core components like Agents, Tasks, Workflows, and even type definitions as structured Markdown documents within a workspace.

## Installation

```bash
# Install from the repository
git clone https://github.com/yourusername/airic.git
cd airic
pip install -e .

# Or using Poetry
poetry install
```

## Quick Start

```bash
# Initialize a new Airic workspace
airic init my_workspace
cd my_workspace

# Create and edit documents with your preferred Markdown editor
# Then open them with Airic
airic open README.md
```

## Project Status

This project is currently in MVP (Minimum Viable Product) development phase, focusing on validating the core "Everything is Document" mechanism through a CLI interface.

## Development Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/airic.git
cd airic

# Install development dependencies
poetry install

# Run tests
pytest
```

## License

MIT
