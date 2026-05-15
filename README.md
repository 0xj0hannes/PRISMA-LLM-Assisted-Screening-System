# 🛡️ PRISMA LLM-Assisted Screening System

A high-precision screening assistant designed for **Systematic Literature Reviews**. This system leverages the Google Gemini API to accelerate the title/abstract screening phase of the PRISMA 2020 reporting guideline [[1]](#references), specifically optimized for research on **cybercriminal behavior** and the **human element** in cybersecurity.

The tool implements the *screening* stage described in PRISMA 2020 [[1]](#references); it does **not** replace any other PRISMA stage (protocol registration, eligibility assessment of full texts, risk-of-bias appraisal, synthesis, or reporting). All AI-suggested decisions are user-configurable inclusion criteria, fully logged for audit, and surfaced for human adjudication in the "Maybe" review queue.

---

## ✨ Key Features

- 🖥 **Premium Web Dashboard**: A sleek, dark-mode GUI natively powered by FastAPI for seamless visual ingestion, screening, and human-in-the-loop review.
- 🔬 **High-Precision AI Screening**: Strictly engineered to optimize precision—enforcing an objective standard that requires explicit evidence of the human element.
- 💾 **Hybrid Persistence**: Robust JSON databasing for CLI scripts and heavy-duty global deduplication SQLite persistence (`data/prisma.db`) for web operations.
- 🤝 **Interactive Human-in-the-loop**: Rapid-fire visual interface for the manual review of ambiguous AI decisions ("Maybe" cases).
- 🔄 **Stateful Execution**: Automatic background save-states guarantee you will never lose screening work from API limits or closed tabs.
- 📂 **Bulk BibTeX Uploads**: Visually drag-and-drop massive batches of `.bib` records directly into the unified screening queue with instant duplicate rejection.

---

## 🚀 Setup & Configuration

### 1. Prerequisites
- Python 3.8+
- [Google AI Studio API Key](https://aistudio.google.com/)

### 2. Installation
```bash
git clone <repository-url>
cd PRISMA-LLM-Assisted-Screening-System
pip install -r requirements.txt
```

### 3. Environment Setup
Create a `.env` file in the root directory:
```env
GEMINI_API_KEY=your_api_key_here
MODEL_NAME=gemini-2.5-flash
MAX_RETRIES=3
```

---

## ⚙️ Configuring Inclusion Criteria

The PRISMA Screening System is completely dynamic and allows you to configure arbitrary inclusion criteria limits for different projects!

To modify the criteria used by the AI to evaluate your literature, edit the `criteria.json` file located in the root directory. You can add or rename custom criteria endpoints simply by editing the JSON structure. 

For each block, you must provide:
- **`name`**: A short, human-readable identifier.
- **`definition`**: A primary description of the rule.
- **`signals`**: String patterns for the AI to understand what characteristics to actively look for.
- **`anti_patterns`**: Negative indicators that shouldn't be falsely conflated (useful for forcing high precision).

The system's entire stack—including the LLM Prompts, the CSV Export Analytics, the CLI Tools, and the Web GUI—will automatically parse your `criteria.json` and perfectly adapt to your experiment parameters without requiring any further code modifications!

---

## 🌐 Web GUI Usage (Recommended)

To launch the full interactive web experience:
```bash
.venv/bin/uvicorn app:app --reload --host 127.0.0.1 --port 8000
```
Then navigate to `http://127.0.0.1:8000` in your browser.

- **Ingestion**: Drag-and-drop multiple `.bib` files. The backend automatically unpacks, normalizes, and globally deduplicates the contents into the master SQL database.
- **Screening**: Start the silent AI automation task. The LLM processes criteria in the background and populates live statistics.
- **Review**: Dynamically filter out uncertain "Maybe" cases using integrated rapid-action toggle buttons.
- **Export**: Instantly download finalized CSV PRISMA records for mapping and external publication.

---

## 🛠️ CLI Usage Pipeline (Legacy/Scripting)

The system also retains terminal commands for headless pipeline scripting:

### Step 1: Ingestion & Deduplication
```bash
# Bulk directory ingestion
python3 main.py ingest /path/to/bib_files_directory/ --output data/deduplicated.json
```

### Step 2: AI-Powered Screening
```bash
python3 main.py screen --input data/deduplicated.json --output data/screened.json
```

### Step 3: Human-in-the-Loop Review
Review cases where the AI was uncertain ("Maybe").
```bash
python3 main.py review --input data/screened.json --output data/final_included.json
```

### Step 4: Export & Reporting
Generate a detailed CSV report for your analysis.
```bash
python3 main.py report --input data/final_included.json --output data/screening_report.csv
```

---

## 📂 Project Structure

| File | Description |
| :--- | :--- |
| `app.py` | FastAPI backend and REST server for the Web GUI. |
| `main.py` | Central CLI entry point for headless execution. |
| `src/db.py` | SQLite adapter mapping Pydantic records to persistent disk models. |
| `src/screening.py` | LLM orchestration natively utilizing the updated `google-genai` SDK. |
| `src/prompts.py` | Expert-tuned, high-precision criteria gating instructions. |
| `static/` | Custom vanilla HTML/CSS/JS frontend dashboard. |

---

## 📚 References

<a id="references"></a>

[1] Page M J, McKenzie J E, Bossuyt P M, Boutron I, Hoffmann T C, Mulrow C D et al. The PRISMA 2020 statement: an updated guideline for reporting systematic reviews BMJ 2021; 372 :n71 doi:10.1136/bmj.n71

The PRISMA 2020 statement and flow diagram are made available by the PRISMA Group at [prisma-statement.org](https://www.prisma-statement.org/).

> **Disclaimer.** This software is an independent screening-assistant tool and is *not* endorsed by, or affiliated with, the PRISMA Group. It implements one stage of the PRISMA-recommended workflow; users remain responsible for adherence to the full reporting guideline.

---

## 📝 License
Released under the MIT License — see [LICENSE](LICENSE). Intended for academic research; please cite the PRISMA references above when reporting reviews conducted with this tool.
