# FlyTune Connectome

A starter computational-neuroscience project for exploring candidate pathways in the adult *Drosophila* brain connectome.

**Important:** this project analyzes wiring/connectivity. It does not measure dopamine release, neural activity, or whether a fly likes a song. Connectome paths are hypotheses to investigate, not proof of functional responses.

## What it does

- Loads a connection table exported/downloaded from FlyWire/Codex.
- Optionally loads a neuron-annotation table.
- Lets you map the columns in those files instead of assuming one fixed schema.
- Searches annotations for candidate auditory/source neurons and dopamine/reward/target neurons.
- Finds shortest directed paths and exports the results as CSV.
- Includes a clearly synthetic demo dataset so you can test the app before downloading real data.

## 1. Install

Use Python 3.10–3.12 if possible.

```bash
python -m venv .venv
```

Windows:
```powershell
.venv\Scripts\Activate.ps1
```

macOS/Linux:
```bash
source .venv/bin/activate
```

Then:
```bash
python -m pip install -r requirements.txt
streamlit run app.py
```

Your browser should open the local app.

## 2. Try the demo first

The app includes `data/demo_connections.csv` and `data/demo_annotations.csv`. These are **invented toy data**, not actual fly-brain measurements. In the app, choose “Use included demo data” to test the workflow.

## 3. Get real FlyWire data

1. Open [FlyWire Codex](https://codex.flywire.ai/).
2. Select the adult female brain/FlyWire dataset.
3. Open the data-download area or export an appropriate connectivity/annotation table. See the [FlyWire data access tutorials](https://github.com/seung-lab/FlyConnectome) for current programmatic options.
4. Check the downloaded file's schema and licence/citation instructions.
5. Upload the connection table in the app. If you also have a neuron annotation table, upload that too.
6. Use the column selectors to map the pre-synaptic ID, post-synaptic ID, and synapse-count columns.

Some programmatic FlyWire access methods use CAVEclient and may require authentication. This starter deliberately begins with CSV upload so you can get started without API credentials.

## 4. Suggested analysis

Start with *candidate* sensory-to-dopamine/reward-related pathways. Search the annotations for terms such as `auditory`, ` Johnston`, `AMMC`, `mechanosensory`, `dopamine`, `DAN`, `reward`, or `mushroom body`, then inspect the actual cell types and evidence in the source annotations.

Do not assume every neuron containing “dopamine” or “auditory” in its label is the right biological target. Review the annotation documentation and relevant literature. The app does not decide which neurons are scientifically valid seeds.

## 5. Limitations

- Connectome edges are anatomical synaptic connections, not recordings of activity.
- A path does not establish that a signal travels along it under a given stimulus.
- Neurotransmitter annotations may be predictions and are not equivalent to measured release.
- A dopamine response is not, by itself, evidence of liking or pleasure.
- This version does not play audio to a fly, record a fly, or interface with a microscope.
- Large full-brain tables may need substantial RAM; begin with a smaller exported table or subnetwork.

## Citation and data use

If you publish or share results, cite the FlyWire dataset and relevant papers as instructed by Codex/the data release. See the [FlyWire connectome paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC11446842/) and [official data-access repository](https://github.com/seung-lab/FlyConnectome).
