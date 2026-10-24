# -*- coding: utf-8 -*-
"""Consultazione degli esercizi di carteggio e correnti."""
import json
import os

import streamlit as st

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "dati", "carteggio_completo_parsed.json")


@st.cache_data
def _load():
    with open(DATA_FILE, encoding="utf-8") as f:
        return json.load(f)


def render():
    st.markdown("## 📐 Esercizi di carteggio")
    st.caption("Consultazione: scenario e soluzioni. Nessuna correzione automatica.")

    data = _load()
    sezioni = {"CARTEGGIO": "Carteggio (50)", "CORRENTI": "Correnti (134)"}
    scelta = st.radio("Sezione", list(sezioni.values()), horizontal=True, key="cart_sezione")
    chiave = [k for k, v in sezioni.items() if v == scelta][0]
    items = [x for x in data if x.get("sezione") == chiave]

    if not items:
        st.info("Nessun esercizio disponibile.")
        return

    def label(i):
        testo = items[i].get("scenario", "").replace(chr(10), " ")
        return f"{items[i]['id']} — {testo[:70]}..."

    idx = st.selectbox("Scegli esercizio", range(len(items)), format_func=label, key="cart_ex")
    ex = items[idx]

    st.markdown("### Scenario")
    st.write(ex.get("scenario", ""))

    soluzioni = ex.get("soluzioni_parsed") or []
    with st.expander(f"✅ Soluzioni ({len(soluzioni)})", expanded=False):
        for n, p in enumerate(soluzioni, 1):
            st.markdown(f"**{n}.** {p.get('raw','')}")
            if p.get("tipo") in ("intervallo", "durata", "orario", "coordinata"):
                st.caption(
                    f"{p.get('tipo')} · min {p.get('min')} · max {p.get('max')} · {p.get('unita','')}"
                )

    st.write("---")
    if st.button("⬅️ Torna ai quiz", type="primary"):
        st.session_state.carteggio_mode = False
        st.rerun()
