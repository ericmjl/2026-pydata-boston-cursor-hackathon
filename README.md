# 2026 PyData Boston x Cursor Data Science Hackathon

Welcome! This repository is the starting point for participants in the **2026 PyData Boston x Cursor Data Science Hackathon**.

This guide helps you get your machine ready and confirms that Cursor can connect to a running Marimo notebook.

## Maintainer demos (paired notebook + chat)

This repo also includes reference marimo apps and transcripts from building them:

- **Dry run (first pass):** [`demos/dry-run/hackathon-demo.py`](demos/dry-run/hackathon-demo.py) with [`demos/dry-run/cursor-chat-f20cbaac.md`](demos/dry-run/cursor-chat-f20cbaac.md) — meta demo / golden-path scaffolding session.
- **Live run (final IRED analysis):** [`demos/live-run/demo.py`](demos/live-run/demo.py) with [`demos/live-run/session-log.md`](demos/live-run/session-log.md) — interactive Novartis IRED campaign analysis through commit of the final notebook.

To open a reference app from the repository root (paths assume `data/` at the repo root):

```bash
uvx marimo edit --sandbox --no-token demos/dry-run/hackathon-demo.py
```

```bash
uvx marimo edit --sandbox --no-token demos/live-run/demo.py
```

## Before the Hackathon

Please make sure you have the following:

- `uv` installed on your computer (installation guide: [Astral uv installation](https://docs.astral.sh/uv/getting-started/installation/)).
- `npm` available on your computer (installation guide: [Node.js download page](https://nodejs.org/en/download/)).
- Cursor downloaded from the [Cursor download page](https://cursor.com/download).
- A Cursor account created (**do not purchase a paid plan yet**).
- A working internet connection.

### Step 1: Create a Work Folder

Create a folder where you will do your hackathon work.

Use whichever term is familiar to you:

- **Folder**: a place on your computer for files.
- **Workspace**: the folder you open in Cursor.
- **Repository (repo)**: a folder tracked with Git (optional for now).

If you are unsure, just create a normal folder named `pydata-hackathon` anywhere convenient (for example, your Desktop or Documents folder).

### Step 2: Install the `marimo-pair` Skill

Open a terminal, move into your work folder, and run:

```bash
npx skills install marimo-team/marimo-pair
```

### Optional: Reuse This Repo's `AGENTS.md`

If you want the same notebook-focused agent guidance used in this repo, run this command inside your own project folder:

```bash
curl -fsSL "https://raw.githubusercontent.com/ericmjl/2026-pydata-boston-cursor-hackathon/main/AGENTS.md" -o AGENTS.md
```

If you want to avoid overwriting an existing `AGENTS.md`, use:

```bash
[ -e AGENTS.md ] || curl -fsSL "https://raw.githubusercontent.com/ericmjl/2026-pydata-boston-cursor-hackathon/main/AGENTS.md" -o AGENTS.md
```

### Step 3: Start the Marimo Notebook Server

In the same folder, run:

```bash
uvx marimo edit --sandbox --no-token hackathon-notebook.py
```

This should start Marimo locally at `http://localhost:2718`.

### Step 4: Open Cursor and Create an Agent

In Cursor:

1. Open your work folder.
2. Go to the latest Cursor Agent view.
3. Create a new agent in that folder.

### Step 5: Connect Cursor Agent to Marimo

Send this prompt to your Cursor agent:

```text
Using the marimo-pair skill, connect to my running marimo notebook at http://localhost:2718
```

Then paste this exact prompt into your Cursor agent:

```text
Using the marimo-pair skill, create a new Markdown cell in my connected marimo notebook that contains exactly: Hello!
```

## Success Check

You are set up correctly when:

- Cursor agent connects to your running Marimo notebook, and
- A new Markdown cell appears in the notebook containing `Hello!`.

At that point, you are ready to build during the hackathon.

## Hackathon Project Idea

Build a Marimo notebook that does something cool with a dataset:

- use `marimo-pair` to collaborate with Cursor Agent in a running notebook,
- use Marimo notebook cells to explore, model, and visualize the data, and
- present one clear "wow" insight, prediction, simulation, or interactive analysis.

Deliverable: one polished notebook that demonstrates a meaningful data science workflow and a compelling result.

## Suggested Datasets by Category

Use this menu as inspiration. Each category has two candidate datasets.
Participants are also welcome to use their own dataset.

### Biology

- [FLIP2: Expanding Protein Fitness Landscape Benchmarks](https://flip.protein.properties/)
- [ProteinGym](https://proteingym.org/)
- [1000 Genomes Project](https://www.internationalgenome.org/data)
- [GTEx Datasets](https://gtexportal.org/home/datasets)

### Climate

- [ERA5 Reanalysis (Copernicus)](https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels)
- [NOAA Climate Data Online Datasets](https://www.ncei.noaa.gov/cdo-web/datasets)

### Robotics

- [LeRobot Datasets (Hugging Face)](https://huggingface.co/lerobot)
- [UCI Wall-Following Robot Navigation](https://archive.ics.uci.edu/dataset/86/wall+following+robot+navigation+data)

### Business

- [UCI Bank Marketing](https://archive.ics.uci.edu/dataset/222/bank+marketing)
- [Kaggle Marketing Campaign Datasets](https://www.kaggle.com/search?q=marketing+campaign+dataset)
- [UCI Online Retail](https://archive.ics.uci.edu/dataset/352/online+retail)
- [Retailrocket E-commerce Dataset (Kaggle)](https://www.kaggle.com/datasets/retailrocket/ecommerce-dataset)

### Astronomy

- [NASA Exoplanet Archive](https://exoplanetarchive.ipac.caltech.edu/)
- [Sloan Digital Sky Survey Data Releases](https://www.sdss.org/dr18/)

### Civic/Government

- [Analyze Boston (City of Boston Open Data)](https://data.boston.gov/)
- [MBTA Open Data](https://www.mbta.com/developers)

## Join the Community

Stay connected with the local community by joining **PyData Boston-Cambridge** on Meetup:

- [PyData Boston-Cambridge Meetup](https://www.meetup.com/pydata-boston-cambridge/)
