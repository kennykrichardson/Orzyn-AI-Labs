# 🚀 Orzyn AI Research

> Research notebooks powering the development of **Orzyn AI**, an AI-powered GitHub Repository Intelligence Platform.

---

## 📖 Overview

This repository contains the complete research and experimentation process behind **Orzyn AI**.

Unlike the production repository, this project focuses entirely on:

- 🧠 AI experimentation
- 🔍 GitHub GraphQL exploration
- 📊 Repository intelligence
- 📈 Health score research
- 🤖 Developer intelligence
- 📚 Rapid prototyping with Jupyter Notebooks

Every notebook represents a milestone in designing the final Orzyn AI engine.

---

# 🏗 Repository Structure

```text
Orzyn-AI/
│
├── backend/
│   │
│   ├── notebooks/
│   │   ├── 01_config.ipynb
│   │   ├── 02_graphql.ipynb
│   │   ├── 03_repository.ipynb
│   │   ├── 04_commits.ipynb
│   │   ├── 05_pull_requests.ipynb
│   │   ├── 06_issues.ipynb
│   │   ├── 07_developer.ipynb
│   │   ├── 08_ai_models.ipynb
│   │   └── 09_health_score.ipynb
│   │
│   ├── cache/
│   ├── data/
│   ├── exports/
│   ├── models/
│   │
│   └── orzyn.py
│
├── requirements.txt
├── README.md
├── .gitignore
└── LICENSE
```

---

# ✨ Features

- 🔍 GitHub GraphQL API
- 📦 Repository Intelligence
- 📝 Commit Analytics
- 🔀 Pull Request Analytics
- 🐞 Issue Intelligence
- 👨‍💻 Developer Intelligence
- 🤖 AI-powered Repository Analysis
- ❤️ Context-aware Repository Health Scoring

---

# 📚 Notebook Roadmap

| Notebook | Description |
|----------|-------------|
| 01 | ⚙ Configuration |
| 02 | 🌐 GraphQL Validation |
| 03 | 📦 Repository Intelligence |
| 04 | 📝 Commit Intelligence |
| 05 | 🔀 Pull Request Intelligence |
| 06 | 🐞 Issue Intelligence |
| 07 | 👨‍💻 Developer Intelligence |
| 08 | 🤖 AI Models |
| 09 | ❤️ Health Score |

---

# ⚙ Prerequisites

Install:

- Python **3.12+**
- Git
- Visual Studio Code (recommended)

---

# 📥 Clone the Repository

```bash
git clone https://github.com/<your-username>/Orzyn-AI.git

cd Orzyn-AI
```

---

# 🐍 Create a Virtual Environment

### Windows

```powershell
python -m venv .venv
```

Activate:

```powershell
.venv\Scripts\activate
```

---

### Linux / macOS

```bash
python3 -m venv .venv

source .venv/bin/activate
```

---

# 📦 Install Dependencies

```bash
pip install --upgrade pip

pip install -r requirements.txt
```

---

# 📓 Create the Jupyter Kernel

Install the kernel into Jupyter:

```bash
python -m ipykernel install --user --name orzyn-ai --display-name "Python (Orzyn AI)"
```

After opening Jupyter or VS Code, select:

```
Python (Orzyn AI)
```

as the notebook kernel.

---

# 🔑 Environment Variables

Create a `.env` file in the project root.

```env
GITHUB_TOKEN=your_github_personal_access_token

HF_TOKEN=your_huggingface_token
```

---

# ▶ Running the Notebooks

Launch Jupyter:

```bash
jupyter notebook
```

or

```bash
jupyter lab
```

Open the notebooks in order:

```
01_config

↓

02_graphql

↓

03_repository

↓

04_commits

↓

05_pull_requests

↓

06_issues

↓

07_developer

↓

08_ai_models

↓

09_health_score
```

Each notebook builds upon the previous one.

---

# 🧪 Technologies

- 🐍 Python
- 📓 Jupyter Notebook
- 🌐 GitHub GraphQL API
- 🤗 Hugging Face
- 🐼 Pandas
- 📡 Requests
- 🔒 Python Dotenv

---

# 🎯 Purpose

This repository documents the research and experimentation that led to the Orzyn AI architecture.

The notebooks intentionally prioritize:

- experimentation
- validation
- rapid iteration
- algorithm development
- AI research

over production-ready software engineering.

The production implementation lives in a separate repository.

---

# 👨‍💻 Author

**Kenny Richardson**

Computer Science Engineering (AI & ML)

Developer • AI Engineer • Software Architect

---

# 📄 License

Licensed under the **MIT License**.