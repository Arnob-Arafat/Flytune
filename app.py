from pathlib import Path
import io
import pandas as pd
import streamlit as st
import networkx as nx
import matplotlib.pyplot as plt

ROOT = Path(__file__).parent
DATA = ROOT / "data"

st.set_page_config(page_title="FlyTune Connectome", page_icon="🧠", layout="wide")
st.title("FlyTune Connectome")
st.caption("Explore candidate pathways in the fruit-fly connectome — anatomy, not live neural activity.")

st.warning(
    "This tool finds paths in a wiring diagram. It does not measure dopamine release, "
    "neural activity, or whether a fly likes a song. Demo data are synthetic."
)

@st.cache_data(show_spinner=False)
def read_csv_bytes(raw: bytes):
    return pd.read_csv(io.BytesIO(raw), low_memory=False)

def read_demo(filename):
    return pd.read_csv(DATA / filename)

def col_guess(columns, terms, fallback=0):
    lower = {str(c).lower(): c for c in columns}
    for term in terms:
        for name, original in lower.items():
            if term in name:
                return original
    return columns[fallback] if len(columns) else None

def stringify_id(s):
    # String IDs avoid accidental float conversion for large numeric neuron IDs.
    return s.astype("string").str.replace(r"\.0$", "", regex=True)

with st.sidebar:
    st.header("1. Load data")
    use_demo = st.toggle("Use included demo data", value=True)
    edge_file = st.file_uploader("Connections CSV", type=["csv"], disabled=use_demo)
    ann_file = st.file_uploader("Neuron annotations CSV (optional)", type=["csv"], disabled=use_demo)
    st.caption("CSV upload keeps this starter simple; no API token is needed.")

if use_demo:
    edges = read_demo("demo_connections.csv")
    annotations = read_demo("demo_annotations.csv")
    st.info("Using invented demo data. Replace it with real FlyWire/Codex exports for scientific analysis.")
else:
    if edge_file is None:
        st.info("Upload a connection table CSV in the sidebar, or enable the demo data.")
        st.stop()
    edges = read_csv_bytes(edge_file.getvalue())
    annotations = read_csv_bytes(ann_file.getvalue()) if ann_file else None

st.subheader("2. Map the connection-table columns")
edge_cols = list(edges.columns)
if len(edge_cols) < 2:
    st.error("The connection table needs at least two columns: presynaptic and postsynaptic neuron IDs.")
    st.stop()

c1, c2, c3 = st.columns(3)
with c1:
    pre_col = st.selectbox("Presynaptic/source ID", edge_cols, index=edge_cols.index(col_guess(edge_cols, ["pre", "source", "upstream"], 0)))
with c2:
    post_col = st.selectbox("Postsynaptic/target ID", edge_cols, index=edge_cols.index(col_guess(edge_cols, ["post", "target", "downstream"], min(1, len(edge_cols)-1))))
with c3:
    weight_candidates = [None] + edge_cols
    default_weight = col_guess(edge_cols, ["synapse", "weight", "count", "size"], -1)
    weight_idx = edge_cols.index(default_weight) + 1 if default_weight in edge_cols else 0
    weight_col = st.selectbox("Synapse count/weight (optional)", weight_candidates, index=weight_idx, format_func=lambda x: "Unweighted (each row = edge)" if x is None else str(x))

# Standardize IDs and aggregate repeated edge rows.
clean = edges[[pre_col, post_col] + ([weight_col] if weight_col else [])].copy()
clean = clean.dropna(subset=[pre_col, post_col])
clean["source"] = stringify_id(clean[pre_col])
clean["target"] = stringify_id(clean[post_col])
if weight_col:
    clean["weight"] = pd.to_numeric(clean[weight_col], errors="coerce").fillna(1).clip(lower=1)
else:
    clean["weight"] = 1
clean = clean[["source", "target", "weight"]].groupby(["source", "target"], as_index=False)["weight"].sum()

min_syn = st.slider("Minimum synapses required for an edge", min_value=1, max_value=20, value=3)
filtered = clean[clean["weight"] >= min_syn]
G = nx.DiGraph()
for row in filtered.itertuples(index=False):
    G.add_edge(row.source, row.target, weight=float(row.weight), cost=1.0)

m1, m2, m3 = st.columns(3)
m1.metric("Input rows", f"{len(edges):,}")
m2.metric("Unique directed connections", f"{len(clean):,}")
m3.metric("Edges after threshold", f"{len(filtered):,}")

st.subheader("3. Search for candidate source and target neurons")
if annotations is not None:
    st.write("Map annotation columns. Use the cell-type/name fields for keyword searches.")
    ann_cols = list(annotations.columns)
    ac1, ac2 = st.columns(2)
    with ac1:
        ann_id_col = st.selectbox("Annotation neuron ID", ann_cols, index=ann_cols.index(col_guess(ann_cols, ["root_id", "cell_id", "neuron_id", "id"], 0)))
    with ac2:
        text_cols = st.multiselect(
            "Annotation text columns",
            ann_cols,
            default=[c for c in ann_cols if any(t in str(c).lower() for t in ["type", "name", "class", "label", "transmitter", "region"])][:4] or ann_cols[:1]
        )
    ann = annotations.copy()
    ann["_id"] = stringify_id(ann[ann_id_col])
    ann["_search"] = ann[text_cols].fillna("").astype(str).agg(" | ".join, axis=1) if text_cols else ""
    q1, q2 = st.columns(2)
    with q1:
        source_query = st.text_input("Source keyword(s)", value="auditory|mechanosensory|AMMC", help="Use | to separate alternative terms; case-insensitive.")
    with q2:
        target_query = st.text_input("Target keyword(s)", value="dopamine|DAN|reward", help="Use | to separate alternative terms; review matches before analysis.")
    source_matches = ann[ann["_search"].str.contains(source_query, case=False, na=False, regex=True)] if source_query.strip() else ann.iloc[0:0]
    target_matches = ann[ann["_search"].str.contains(target_query, case=False, na=False, regex=True)] if target_query.strip() else ann.iloc[0:0]
    a, b = st.columns(2)
    with a:
        st.markdown(f"**Source candidates: {len(source_matches)}**")
        st.dataframe(source_matches[[ann_id_col] + text_cols].head(100), use_container_width=True, height=220)
    with b:
        st.markdown(f"**Target candidates: {len(target_matches)}**")
        st.dataframe(target_matches[[ann_id_col] + text_cols].head(100), use_container_width=True, height=220)
    source_options = source_matches["_id"].dropna().astype(str).unique().tolist()
    target_options = target_matches["_id"].dropna().astype(str).unique().tolist()
    st.caption("Select exact neurons from the annotation matches. A keyword match is only a starting point, not a biological validation.")
else:
    st.info("No annotation table supplied. Enter known neuron IDs below, or upload annotations to search by labels.")
    source_options, target_options = [], []

with st.expander("Manual neuron IDs (use if annotations are unavailable or you want exact seeds)"):
    manual_sources = st.text_input("Source neuron IDs, comma-separated", placeholder="e.g. 12345,67890")
    manual_targets = st.text_input("Target neuron IDs, comma-separated", placeholder="e.g. 24680,13579")

if annotations is not None:
    source_selected = st.multiselect("Selected source neurons", source_options, max_selections=20)
    target_selected = st.multiselect("Selected target neurons", target_options, max_selections=20)
else:
    source_selected, target_selected = [], []

sources = list(dict.fromkeys(source_selected + [x.strip() for x in manual_sources.split(",") if x.strip()]))
targets = list(dict.fromkeys(target_selected + [x.strip() for x in manual_targets.split(",") if x.strip()]))

max_hops = st.slider("Maximum path length (synaptic hops)", 1, 8, 4)
max_paths = st.slider("Maximum source-target pairs to inspect", 1, 100, 25)

if st.button("Find candidate pathways", type="primary"):
    if not sources or not targets:
        st.error("Select at least one source neuron and one target neuron, or enter manual neuron IDs.")
    elif G.number_of_edges() == 0:
        st.error("No edges remain after filtering. Lower the synapse threshold or check the mapped columns.")
    else:
        rows = []
        examined = 0
        for src in sources:
            for dst in targets:
                if examined >= max_paths:
                    break
                examined += 1
                if src not in G or dst not in G:
                    rows.append({"source": src, "target": dst, "status": "ID absent from filtered graph", "hops": None, "path": ""})
                    continue
                try:
                    path = nx.shortest_path(G, source=src, target=dst)
                    hops = len(path) - 1
                    if hops > max_hops:
                        rows.append({"source": src, "target": dst, "status": f"Path exists but exceeds {max_hops} hops", "hops": hops, "path": " → ".join(path)})
                    else:
                        rows.append({"source": src, "target": dst, "status": "Candidate path", "hops": hops, "path": " → ".join(path)})
                except (nx.NetworkXNoPath, nx.NodeNotFound):
                    rows.append({"source": src, "target": dst, "status": "No path at current threshold", "hops": None, "path": ""})
            if examined >= max_paths:
                break
        result = pd.DataFrame(rows)
        st.session_state["path_results"] = result
        st.session_state["path_graph"] = G

if "path_results" in st.session_state:
    result = st.session_state["path_results"]
    st.subheader("4. Results")
    st.dataframe(result, use_container_width=True)
    st.download_button("Download pathway results CSV", result.to_csv(index=False).encode("utf-8"), "flytune_candidate_paths.csv", "text/csv")
    candidates = result[result["status"] == "Candidate path"]
    if not candidates.empty:
        chosen_idx = st.selectbox("Visualize a candidate path", candidates.index.tolist(), format_func=lambda i: f'{result.loc[i, "source"]} → {result.loc[i, "target"]} ({result.loc[i, "hops"]} hops)')
        path_ids = result.loc[chosen_idx, "path"].split(" → ")
        sub = st.session_state["path_graph"].subgraph(path_ids)
        fig, ax = plt.subplots(figsize=(max(7, len(path_ids) * 1.6), 3))
        pos = {node: (i, 0) for i, node in enumerate(path_ids)}
        nx.draw_networkx(sub, pos=pos, ax=ax, node_size=1600, font_size=8, arrows=True, with_labels=True)
        ax.set_axis_off()
        st.pyplot(fig)
        plt.close(fig)

st.divider()
st.caption("FlyTune Connectome • research prototype • cite the source dataset and validate cell identities before interpreting pathways.")
