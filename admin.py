# Pannello istruttore - registro allievi e statistiche
import pandas as pd
import streamlit as st

import database as db_engine
import students_engine


def _admin_pin():
    value = st.session_state.get("admin_pin_value")
    if value:
        return str(value)
    try:
        return str(st.secrets["app"]["admin_pin"])
    except Exception:
        return ""


def _load_df():
    rows = db_engine.get_all_history()
    if not rows:
        return pd.DataFrame(columns=["user_id", "question_id", "score", "timestamp"])
    df = pd.DataFrame(rows)
    df["score"] = pd.to_numeric(df["score"], errors="coerce").fillna(0)
    df["user_id"] = df["user_id"].astype(str).str.strip().str.lower()
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    return df


def _registry(pin):
    rows = students_engine.admin_list_students(pin)
    if rows:
        out = [{"Allievo": str(r["display_name"]), "Email": str(r["email"] or "—")} for r in rows]
        return out, True
    try:
        reg = st.secrets["students"]
    except Exception:
        return [], False
    out = []
    for name, value in reg.items():
        if hasattr(value, "get"):
            email = str(value.get("email", "")).strip() or "—"
        else:
            email = "—"
        out.append({"Allievo": str(name).title(), "Email": email})
    return sorted(out, key=lambda r: r["Allievo"]), False


def _requests(pin):
    rows = students_engine.admin_list_requests(pin)
    return [
        {
            "id": r["id"],
            "Nome": r["display_name"],
            "Email": r["email"],
            "Stato": r["status"],
            "Data": str(r["created_at"])[:16].replace("T", " "),
        }
        for r in rows
    ]


def render_admin_dashboard():
    admin_pin = _admin_pin()
    st.markdown("## 👑 Pannello istruttore")
    st.caption("Registro allievi e statistiche. I dati arrivano da Supabase.")

    richieste = _requests(admin_pin)
    pendenti = [r for r in richieste if r["Stato"] == "pending"]
    if pendenti:
        st.error(f"🔔 {len(pendenti)} richiesta/e di accesso in attesa")
        st.dataframe(pd.DataFrame(pendenti)[["Nome", "Email", "Data"]], use_container_width=True, hide_index=True)
        _labels_p = [f'{r["Nome"]} — {r["Email"]}' for r in pendenti]
        _sel_p = st.selectbox("Richiesta da approvare", _labels_p, key="sel_pendente")
        _req_p = pendenti[_labels_p.index(_sel_p)]
        if st.button("✅ Approva con PIN 1234", type="primary", key="btn_approva_req"):
            _res_p = students_engine.admin_add_student(_req_p["Nome"], _req_p["Email"], "1234", admin_pin)
            if _res_p.get("ok"):
                st.success(f'{_req_p["Nome"]} approvato con PIN 1234.')
                st.rerun()
            else:
                st.error(_res_p.get("error", "Errore"))

    with st.expander("➕ Aggiungi allievo"):
        with st.form("form_nuovo_allievo", clear_on_submit=True):
            nome = st.text_input("Nome e cognome")
            email = st.text_input("Email")
            nuovo_pin = st.text_input("PIN (4 cifre)", value="1234", max_chars=8)
            inviato = st.form_submit_button("Aggiungi", type="primary")
        if inviato:
            if len(nome.strip()) < 3 or "@" not in email or len(nuovo_pin.strip()) < 4:
                st.error("Compila nome, email valida e PIN di almeno 4 caratteri.")
            else:
                res = students_engine.admin_add_student(nome.strip(), email.strip(), nuovo_pin.strip(), admin_pin)
                if res.get("ok"):
                    st.success(f"{nome.strip()} aggiunto. PIN: {nuovo_pin}")
                    st.rerun()
                else:
                    st.error(res.get("error", "Errore."))

    registro, da_db = _registry(admin_pin)
    if registro:
        st.markdown("### Registro allievi")
        st.dataframe(pd.DataFrame(registro), use_container_width=True, hide_index=True)
        if not da_db:
            st.caption("Registro locale (tabelle Supabase non ancora create).")
        st.write("")

        st.markdown("### Gestisci allievo")
        _nome_sel = st.selectbox(
            "Allievo da gestire", [r["Allievo"] for r in registro], key="gestione_allievo"
        )
        _c1, _c2 = st.columns(2)
        with _c1:
            st.markdown("**Reimposta PIN**")
            _new_pin = st.text_input("Nuovo PIN", max_chars=8, key="nuovo_pin_reset")
            if st.button("Reimposta PIN", key="btn_reset_pin"):
                if len(_new_pin.strip()) < 4:
                    st.error("Il PIN deve avere almeno 4 caratteri.")
                else:
                    _r = students_engine.admin_reset_pin(_nome_sel, _new_pin.strip(), admin_pin)
                    if _r.get("ok"):
                        st.success(f"PIN di {_nome_sel} reimpostato su {_new_pin.strip()}")
                    else:
                        st.error(_r.get("error", "Errore"))
        with _c2:
            st.markdown("**Sposta nel cestino**")
            st.warning(f"Stai per spostare nel cestino: {_nome_sel}")
            st.caption("Lo storico viene conservato. Potrai ripristinarlo.")
            _conf = st.text_input(
                f"Scrivi {_nome_sel} per confermare", key=f"conf_del_{_nome_sel}"
            )
            if st.button("Elimina allievo", key="btn_del"):
                if _conf.strip().lower() != _nome_sel.strip().lower():
                    st.warning("Il nome non coincide: eliminazione annullata.")
                else:
                    _r = students_engine.admin_delete_student(_nome_sel, admin_pin, False)
                    if _r.get("ok"):
                        st.success(f"{_nome_sel} spostato nel cestino.")
                        st.rerun()
                    else:
                        st.error(_r.get("error", "Errore"))
        st.write("")

    _cestino = students_engine.admin_list_deleted(admin_pin)
    if _cestino:
        with st.expander(f"🗑️ Cestino ({len(_cestino)})"):
            st.dataframe(
                pd.DataFrame([
                    {"Allievo": r["display_name"], "Email": r["email"],
                     "Eliminato": str(r["deleted_at"])[:16].replace("T", " ")}
                    for r in _cestino
                ]),
                use_container_width=True, hide_index=True,
            )
            _sel_c = st.selectbox("Allievo da ripristinare", [r["display_name"] for r in _cestino], key="restore_sel")
            if st.button("Ripristina", key="btn_restore"):
                _r = students_engine.admin_restore_student(_sel_c, admin_pin)
                if _r.get("ok"):
                    st.success(f"{_sel_c} ripristinato.")
                    st.rerun()
                else:
                    st.error(_r.get("error", "Errore"))

    df = _load_df()
    if df.empty:
        st.info("Nessuna statistica disponibile.")
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

    st.markdown("### Statistiche per allievo")
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
        st.session_state.admin_pin_value = ""
        st.session_state.current_user = "Comandante"
        st.rerun()
