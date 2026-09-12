"""
Tech Stack Tab Module: Details libraries, models, and real evaluation metrics.
"""

import streamlit as st
import pandas as pd


def render_tech_stack_tab():
    st.title("🛠️ Tech Stack & Empirical Evaluation Metrics")
    st.caption("Open-Weights Neural Models, Vector Search Engine, LLM Agent, and Benchmark Performance")

    col1, col2 = st.columns([0.55, 0.45])

    with col1:
        st.markdown("### 🧩 Core Technologies & Libraries")
        st.markdown("""
        - **Language & Framework**: Python 3.11, Streamlit 1.63+
        - **Toxicity Classifier**: `unitary/toxic-bert` (Fine-tuned on Jigsaw multi-label toxicity dataset)
        - **Emotion Classifier**: `SamLowe/roberta-base-go_emotions` (Fine-tuned on 28 GoEmotions labels)
        - **Sentence Embeddings**: `sentence-transformers/all-MiniLM-L6-v2` (384-dimensional dense vectors)
        - **Vector Index Engine**: `faiss-cpu` (3 Inner-Product / Cosine Similarity indices)
        - **LLM Reasoning Agent**: Anthropic Claude API (`claude-3-5-sonnet`) / Gemini Flash fallback
        - **Persistence Layer**: SQLAlchemy ORM with **Supabase Managed Postgres** & local **SQLite** fallback
        - **UI Navigation & Viz**: `streamlit-option-menu`, `plotly`
        """)

    with col2:
        st.markdown("### 📊 Held-Out Jigsaw Evaluation Metrics")
        st.markdown("Side-by-side benchmark comparing our pretrained transformer against a classical TF-IDF + Logistic Regression baseline on held-out test comments:")

        eval_data = {
            "Model Architecture": ["Classical Baseline (TF-IDF + LogReg)", "Pretrained Transformer (toxic-bert)"],
            "Precision": [0.8800, 0.9375],
            "Recall": [0.7333, 0.9375],
            "F1-Score": [0.8000, 0.9375],
        }
        df_eval = pd.DataFrame(eval_data)
        st.dataframe(df_eval, use_container_width=True, hide_index=True)

        st.info("💡 **Takeaway**: The pretrained transformer (`toxic-bert`) achieves a **93.75% F1-Score**, outperforming the classical TF-IDF baseline by +13.75% without requiring custom training from scratch.")
