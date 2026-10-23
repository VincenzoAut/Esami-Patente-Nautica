# Pannello istruttore - sola lettura dai dati Supabase
import pandas as pd
import streamlit as st

import database as db_engine


def _load_df():
    rows = db_engine.get_all_history()
    if not rows:
        return pd.DataFrame(columns=["user_id", "question_id", "score", "timestamp"])
    df = pd.DataFrame(rows)
    df["score"] = pd.to_numeric(df["score"], errors="coerce").fillna(0)
    df["user_id"] = df["user_id"].astype(str).str.strip().str.lower()
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    return df


def render_admin_dashboard():
    st.markdown("## 👑 Pannello istruttore")
    st.caption("Dati live da Supabase, sola lettura.")

    df = _load_df()
    if df.empty:
        st.info("Nessun dato nel database.")
        _logout()
        return

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Allievi", df["user_id"].nunique())
    c2.metric("Domande affrontate", len(df))
    c3.metric("Padroneggiate", int((df["score"] > 0).sum()))
    c4.metric("Da rivedere", int((df["score"] < 0).sum()))

    per_user = (
        df.groupby("user_id")
        .agg(
            domande=("question_id", "count"),
            padroneggiate=("score", lambda s: int((s > 0).sum())),
            critiche=("score", lambda s: int((s < 0).sum())),
            ultima=("timestamp", "max"),
        )
        .reset_index()
    )
    per_user["allievo"] = per_user["user_id"].str.title()
    per_user["ultima"] = per_user["ultima"].dt.strftime("%d/%m/%Y %H:%M")
    per_user = per_user.sort_values("padroneggiate", ascending=False)

    st.dataframe(
        per_user[["allievo", "domande", "padroneggiate", "critiche", "ultima"]],
        use_container_width=True,
        hide_index=True,
        column_config={
            "allievo": "Allievo",
            "domande": "Domande toccate",
            "padroneggiate": "Padroneggiate",
            "critiche": "Da rivedere",
            "ultima": "Ultima attivita",
        },
    )

    st.markdown("### Dettaglio per allievo")
    scelto = st.selectbox("Allievo", sorted(per_user["user_id"].tolist()))
    sub = df[df["user_id"] == scelto].copy()
    sub["argomento"] = sub["question_id"].astype(str).str.split("-").str[0]
    agg = (
        sub.groupby("argomento")
        .agg(
            domande=("question_id", "count"),
            padroneggiate=("score", lambda s: int((s > 0).sum())),
            critiche=("score", lambda s: int((s < 0).sum())),
        )
        .reset_index()
        .sort_values(["critiche", "domande"], ascending=False)
    )
    st.dataframe(agg, use_container_width=True, hide_index=True)

    st.download_button(
        "Scarica CSV completo",
        df.to_csv(index=False).encode("utf-8"),
        file_name="statistiche_allievi.csv",
        mime="text/csv",
    )

    _logout()


def _logout():
    st.write("---")
    if st.button("Esci dal pannello"):
        st.session_state.admin_mode = False
        st.session_state.unlocked = False
        st.session_state.current_user = "Comandante"
        st.rerun()
