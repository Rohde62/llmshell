# Product Requirements Document (PRD)

**Project Name:** LLMShell\
**Author:** Jakob Rohde\
**Last Updated:** 2025-08-03\
**Status:** Draft

---

## 1. Objective

Build a **local, privacy-respecting Linux shell** that allows users to enter natural language instructions (e.g., "Make this file owned by me") which are translated into executable shell commands using a local LLM (e.g., via Ollama). The product aims to **augment** the traditional shell with AI-assisted command generation without sacrificing control, safety, or transparency.

---

## 2. Target Users

- Advanced users who want faster and more intuitive shell interactions.
- Developers, sysadmins, and power users running Linux or macOS.
- Privacy-conscious users who prefer **local-only LLM processing**.
- People learning shell scripting who want command suggestions with explanations.

---

## 3. Use Cases

- Translate natural language to shell:\
  *"List all hidden files and directories"* → `ls -a | grep '^\.'`

- Help with complex syntax:\
  *"Find all .log files modified in the last 24 hours"* → `find . -name "*.log" -mtime -1`

- Explain command before execution:\
  Show LLM output + allow user confirmation before execution.

- Switch between "AI-assisted" and "Raw Bash" mode.

- Run locally, optionally offline.

---

## 4. Features

### MVP Features

| Feature             | Description                                                                 |
| ------------------- | --------------------------------------------------------------------------- |
| Shell Loop          | CLI that accepts input, detects natural language, and routes to Bash or LLM |
| LLM Translation     | Sends user input to local LLM (e.g., via Ollama), returns bash command      |
| Command Preview     | User sees suggested command before execution                                |
| Confirmation Prompt | Require user confirmation before running any AI-generated command           |
| Bash Execution      | Executes valid shell commands using subprocess or direct execution          |
| Local Model Support | Integrates with Ollama-compatible models (e.g., llama3, codellama, mistral) |

### Stretch Goals / v1.1+

| Feature             | Description                                                            |
| ------------------- | ---------------------------------------------------------------------- |
| Command Explanation | LLM explains command before execution (optional toggle)                |
| Context Injection   | Include current working directory, ls, file info as part of LLM prompt |
| Memory & History    | Retains history of commands and previous translations in session       |
| LLM Model Selector  | Choose between available local models via config file                  |
| Safety Layer        | Detect dangerous commands (rm -rf, sudo) and require double opt-in     |
| TUI / GUI Frontend  | Optional textual-based interface or GUI for user-friendly interaction  |

---

## 5. Technical Requirements

### Runtime Environment

- OS: Linux (primary), macOS (secondary)
- Python 3.10+ or Rust (if going low-level)
- Optional: Dockerized setup for reproducibility

### LLM Backend

- **Local only** — no cloud LLM APIs
- Must support:
  - **Ollama**
  - Optionally: LM Studio, llamacpp REST APIs
- Prompt templates must be customizable

### Architecture Sketch

```
User Input → Input Handler
             ↓
         ┌────────────┐
         │ LLM Router │──→ Prompt Template → Ollama API
         └────────────┘
             ↓
       Translated Bash Command
             ↓
     → Confirmation Layer → Execution
             ↓
         Command Output
```

---

## 6. Non-Functional Requirements

- **Privacy:** No outbound network connections from the app
- **Extensibility:** Configurable backend and prompt logic
- **Security:** Never executes generated commands without confirmation
- **Portability:** Easy to install via pipx, .deb, or AppImage
- **Startup Time:** <1s for shell loop readiness (excluding model load time)

---

## 7. Out of Scope (for MVP)

- Remote model support (OpenAI, Claude, etc.)
- Windows support
- Interactive scripting (multiline Bash input)
- Shell autocompletion integration (e.g., ZSH, Fish)

---

## 8. Success Criteria

| Goal                      | Metric                                                                |
| ------------------------- | --------------------------------------------------------------------- |
| Local model integration   | Executes translations from at least one model (Ollama)                |
| Natural language handling | Accurately converts >80% of test phrases into usable Bash             |
| Safe execution            | No unconfirmed command is ever run                                    |
| Usability                 | User can switch between natural language and raw Bash in real time    |
| Performance               | Translation + execution cycle completes within 3s (with model loaded) |

---

## 9. Milestones

| Date (est.) | Milestone                                 |
| ----------- | ----------------------------------------- |
| Week 1      | Project scaffolding + LLM prompt tests    |
| Week 2      | Basic CLI loop with LLM translation       |
| Week 3      | Safe execution with confirmations         |
| Week 4      | Session history + context injection       |
| Week 5      | Packaging (pipx/AppImage) + documentation |

---

## 10. Open Questions

- Should commands be logged to a file or only retained in memory?
- Would multi-line command chaining be supported (`&&`, `|`, etc.)?
- Should commands be explained by default, or only when requested?
- Is support for other local models (e.g., LM Studio) needed from day one?

