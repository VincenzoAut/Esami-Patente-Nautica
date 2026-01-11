# FILE: database.py
# VERSION: v96.0 (Complete Fix - Threading + Dropdown + History)
# DATE: 2026-01-11

import streamlit as st
from supabase import create_client
import datetime
import threading

# Import magico per gestire i Thread in Streamlit senza errori
try:
    from streamlit.runtime.scriptrunner import add_script_run_ctx
except ImportError:
    from streamlit.scriptrunner import add_script_run_ctx

# --- 1. CONNESSIONE SUPABASE ---
@st.cache_resource
def init_connection():
    try:
        if "supabase" in st.secrets["connections"]:
            url = st.secrets["connections"]["supabase"]["url"]
            key = st.secrets["connections"]["supabase"]["key"]
            return create_client(url, key)
        else:
            print("❌ Manca [connections.supabase] in secrets.toml")
            return None
    except Exception as e:
        print(f"❌ Errore Configurazione Supabase: {e}")
        return None

# --- 2. WORKER (SALVATAGGIO IN BACKGROUND) ---
def _upsert_worker(username, question_id, result):
    supabase = init_connection()
    if not supabase: return

    try:
        user_clean = username.strip().lower()
        q_clean = str(question_id).strip()
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        data = {
            "user_id": user_clean,
            "question_id": q_clean,
            "score": result,
            "timestamp": ts
        }

        # Scrive su Supabase
        supabase.table("history").upsert(data, on_conflict="user_id, question_id").execute()
        print(f"✅ Saved: {user_clean} -> {q_clean}")

    except Exception as e:
        print(f"⚠️ Background Save Error: {e}")

# --- 3. FUNZIONE DI SALVATAGGIO (CHIAMATA DALL'APP) ---
def upsert_answer(username, question_id, result):
    # Avvia il thread separato per non bloccare l'app
    thread = threading.Thread(target=_upsert_worker, args=(username, question_id, result))
    add_script_run_ctx(thread)
    thread.start()
    return True

# --- 4. LETTURA STORICO (RECUPERO DATI UTENTE) ---
def get_user_history(username):
    supabase = init_connection()
    if not supabase: return {}

    try:
        user_clean = username.strip().lower()
        # Scarica tutte le risposte di questo utente
        response = supabase.table("history").select("*").eq("user_id", user_clean).execute()
        
        history = {}
        if response.data:
            for row in response.data:
                q_id = str(row["question_id"])
                history[q_id] = {
                    "score": row["score"],
                    "date": row["timestamp"]
                }
        return history

    except Exception as e:
        print(f"Errore lettura DB: {e}")
        return {}

# --- 5. RECUPERO LISTA UTENTI (PER IL MENU A TENDINA) ---
def get_all_users():
    """Scarica la lista di tutti gli utenti unici per il login"""
    supabase = init_connection()
    if not supabase: return []
    
    try:
        # Chiede solo la colonna user_id
        response = supabase.table("history").select("user_id").execute()
        
        if response.data:
            # Rimuove duplicati e ordina
            users = sorted(list(set(r['user_id'] for r in response.data)))
            # Filtra nomi vuoti o troppo corti
            return [u for u in users if u and len(u) > 2]
        return []
    except Exception as e:
        print(f"Errore get_users: {e}")
        return []

# --- 6. ALIAS (IMPORTANTE: QUESTO RISOLVE IL TUO ERRORE) ---
fetch_user_history = get_user_history