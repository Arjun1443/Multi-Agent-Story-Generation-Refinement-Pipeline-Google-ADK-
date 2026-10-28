# Multi-Agent Story Generation and Refinement

A Google ADK notebook organizing story creation into generator, critic, and refiner stages.

## Why this project matters

Separating generation and critique illustrates how agent orchestration can structure a creative workflow and make intermediate outputs inspectable.

## Technical focus

Python · Google ADK · sequential orchestration · iterative refinement · in-memory execution

## Explore the implementation

Open [the notebook](<Multi-Agent Story Generation & Refinement Pipeline (Google ADK).ipynb>) to inspect preprocessing, implementation, and saved outputs.

## Run locally

```bash
git clone https://github.com/Arjun1443/Multi-Agent-Story-Generation-Refinement-Pipeline-Google-ADK-.git
cd Multi-Agent-Story-Generation-Refinement-Pipeline-Google-ADK-
python -m venv .venv
# Activate .venv before continuing.
python -m pip install google-adk google-genai jupyter
python -m jupyter notebook
```

Select `Multi-Agent Story Generation & Refinement Pipeline (Google ADK).ipynb` in Jupyter and review its configuration before executing cells in order.

## Reproducibility notes

Configure the Google API key through the notebook's Kaggle Secrets setup, or adapt that cell for environment variables in local Jupyter. Review the loop limit and prompt before running. Multiple agent calls can increase API usage. Improvements in story quality are subjective and should be assessed against explicit criteria.

Saved notebook outputs describe a prior execution; they are not an independently reproduced benchmark. Dependency versions are not locked, so compatibility may require adjustment.


## Author

[Naga Anweesh Reddy](https://github.com/Arjun1443/Naga-Anweesh-Reddy) · AI development and technical training
