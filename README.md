# Multi-Agent Story Generation & Refinement Pipeline (Google ADK)

This repository contains an end-to-end implementation of a **multi-agent LLM workflow** using the **Google Agent Development Kit (ADK)**. The notebook demonstrates how to build, chain, and refine AI agents to generate higher-quality stories through iterative critique and improvement.

---

## 🚀 Highlights

### ✔️ Environment Setup

* Installed and configured **google-adk**
* Loaded essential Python libraries (NumPy, Pandas)
* Managed secrets securely using **Kaggle Secrets**

### ✔️ Custom Agent Implementations

The notebook defines multiple intelligent agents using ADK:

* **Story Generator** – Produces the initial story from a prompt
* **Critic Agent** – Evaluates the story and provides refinement notes
* **Refiner Agent** – Improves the story based on critic feedback
* **BaseAgent** – Shared reusable logic for agent behaviors

### ✔️ Loop-Based Refinement

A **LoopAgent** performs iterative improvement cycles:
**Critic → Refiner → Improved Story**
This ensures the final output is more coherent, polished, and creative.

### ✔️ Sequential Workflow

A **SequentialAgent** is built to connect all stages into a single automated pipeline:

1. Story generation
2. Critique + refinement loop
3. Final enhanced narrative

### ✔️ In-Memory Debug Runner

The notebook uses:
`InMemoryRunner(agent=root_agent).run_debug(...)`
to execute the full pipeline with detailed reasoning traces.

---

## 📂 Project Structure

```
/addk-1.ipynb     # Complete implementation of all agents and workflows
```

---

## 🧠 What the Notebook Solves

* How to build custom agents with Google ADK
* How to chain multiple agents into a workflow
* How to design an iterative refinement loop
* How to securely load API keys inside Kaggle
* How to run and debug an agent pipeline end-to-end
* How to generate improved stories using LLM feedback cycles

---

## 📝 How to Use

1. Open the notebook in Kaggle / Jupyter
2. Add your API key to Kaggle Secrets
3. Run all cells sequentially
4. Modify the prompt inside:

```python
runner.run_debug("Your story prompt here")
```

5. View the generated story, critic feedback, and refined final version.

---

## 📌 Example Prompt Used

> “Write a short story about a lighthouse keeper who discovers a mysterious glowing map.”

The system processes the prompt through the agent pipeline and outputs an improved, multi-stage refined story.

---

## 🔧 Future Enhancements

* Add domain-specific critic agents (mystery, sci-fi, fantasy)
* Add style transfer agents
* Export final outputs into files
* Build REST API / web UI on top of the pipeline

---

## 📜 License

Open for personal and academic use.
