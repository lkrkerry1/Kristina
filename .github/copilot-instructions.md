# Kristina AI Coding Assistant Instructions

This repository is a thin wrapper around the [Open-LLM-VTuber](https://github.com/Open-LLM-VTuber/Open-LLM-VTuber) project, adding customized personality, PowerMem integration, Windows desktop support, and additional resources.

For the complete set of guidelines you should read the instructions located inside the submodule:

```
Open-LLM-VTuber/.github/copilot-instructions.md
```

That file has been extended with **root-specific sections** covering:

- how `main.py` links resources and launches the server
- `uv` workspace workflow and dependency management
- custom agents under `custom_agents/` and configuration inheritance
- commands used during development (`uv run main.py`, `python test_ollama.py`, etc.)

When writing code or adding features, start by consulting the submodule instructions and then check the root sections above for anything that affects the whole repository.

Feel free to open a PR against either instructions file if you notice missing information.