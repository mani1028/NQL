# nql File Management Guide

This document explains which files belong in the GitHub repository and which should stay local. Proper Git hygiene ensures that the repository remains lightweight, secure, and easy to collaborate on.

## 1. What Stays on GitHub (The Shared Codebase)
These files are essential for other developers to build and run the project.

| File/Folder | Purpose |
| :--- | :--- |
| `nql/` | The core Python package (logic, engines, planners). |
| `api/` | FastAPI server implementation. |
| `frontend/` | React/Vite source code. |
| `tests/` | Automated test suite (`pytest`). |
| `requirements.txt` | Python dependencies. |
| `package.json` | JavaScript dependencies. |
| `pyproject.toml` | Build system configuration. |
| `README.md` | General project overview. |
| `GEMINI.md` | AI-specific architectural guidance. |
| `.github/workflows/` | CI/CD automation scripts. |

## 2. What Stays Local (Private/Heavy/Generated)
These files should **never** be committed to GitHub. They are ignored via `.gitignore`.

| File/Folder | Why it stays local |
| :--- | :--- |
| `path/to/venv/` | Virtual environments are specific to your OS and machine. |
| `nql/ml/models/*.pt` | Trained model weights (large binary files). They should be downloaded or trained, not stored in Git. |
| `nql/ml/data/*.json` | Large datasets (Spider, WikiSQL, generated data). |
| `.env` | **Security Risk**: Contains API keys, database URLs, and secrets. |
| `node_modules/` | Massive folders managed by `npm`. Re-installable via `npm install`. |
| `__pycache__/` | Temporary Python bytecode files. |
| `.DS_Store` | Mac-specific system files. |
| `build/`, `dist/` | Temporary build artifacts generated during packaging. |

## 3. Temporary Files & Their Uses
Temporary files are created during training or execution and are usually safe to delete.

- **`nql/ml/data/dataset.json`**: The raw training data. Used by the training script but not needed at runtime.
- **`nql/ml/data/mapping.json`**: A lookup table for the model. Essential for inference, but generated based on the current training data.
- **`nql/ml/logs/`**: Training progress logs (TensorBoard). Used to debug training quality.
- **`build/`**: Created when you run `pip install -e .`. It stores temporary metadata about the package installation.

## 4. How to Update GitHub
To keep your repository clean, follow these steps before committing:

1. **Verify your `.gitignore`**: Ensure it includes `venv/`, `*.pt`, `__pycache__/`, and `node_modules/`.
2. **Check status**: `git status` will show you which files are being tracked.
3. **Commit source only**:
   ```bash
   git add .
   git commit -m "feat: updated intent planner logic"
   git push origin main
   ```

## 5. Security Warning
**NEVER** commit `.env` files or hardcoded database passwords. If you accidentally commit a secret, use a tool like `git-filter-repo` to remove it from the history and rotate your passwords immediately.
