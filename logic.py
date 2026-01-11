# FILE: logic.py
# VERSION: v104.0 (Universal Loader & Robust Stats)
# DATE: 2026-01-11

import pandas as pd
import random
import datetime
import os
import streamlit as st

# --- CONFIGURAZIONE COSTANTI ---
SRS_INTERVALS = {0: 0, 1: 3, 2: 7, 3: 15}

# Distribuzione domande esame (Regole Ministeriali Base)
RULES_BASE = {
    "Scafo": 1, "Motori": 1, "Sicurezza": 3, "Manovra": 4,
    "Colreg": 2, "Meteorologia": 2, "Navigazione": 4, "Normativa": 3
}

# --- 1. CARICAMENTO DATI INTELLIGENTE ---
@st.cache_data(show_spinner=False)
def smart_load_data(file_path_parquet, file_path_excel):
    """
    Carica il database provando prima il Parquet, poi Excel.
    Pulisce i dati e normalizza le colonne.
    """
    df = None
    
    # Tentativo 1: Parquet (Veloce)
    if os.path.exists(file_path_parquet):
        try:
            df = pd.read_parquet(file_path_parquet)
        except Exception:
            pass # Se fallisce, prova Excel

    # Tentativo 2: Excel (Fallback)
    if df is None and os.path.exists(file_path_excel):
        try:
            df = pd.read_excel(file_path_excel)
            # Pulizia specifica per Excel (che spesso ha NaN)
            df = df.fillna("")
            df = df.astype(str)
            # Rimuove le stringhe 'nan' se presenti
            df = df.replace(["nan", "NaN"], "")
        except Exception as e:
            st.error(f"Errore lettura Excel {file_path_excel}: {e}")
            return pd.DataFrame()

    if df is None:
        return pd.DataFrame() # Restituisce vuoto se nessun file trovato

    # --- PULIZIA FINALE COMUNE ---
    # 1. Normalizza nomi colonne (toglie spazi extra)
    df.columns = [str(c).strip() for c in df.columns]
    
    # 2. Pulisce ID Progressivo (toglie .0 finale se esiste)
    if 'ID Progressivo' in df.columns:
        df['ID Progressivo'] = df['ID Progressivo'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
    
    # 3. Assicura che la colonna Argomento esista
    if 'Argomento' not in df.columns:
        df['Argomento'] = 'Generale'

    return df


# --- 2. LOGICA SRS (SPACED REPETITION) ---
def get_days_diff(date_str):
    if not date_str: return 9999
    try:
        # Gestisce sia "YYYY-MM-DD HH:MM:SS" che "YYYY-MM-DD"
        clean_date = str(date_str).split()[0]
        last_date = datetime.datetime.strptime(clean_date, "%Y-%m-%d").date()
        return (datetime.date.today() - last_date).days
    except: return 9999

def is_due_for_review(item_data):
    """Decide se una domanda va riproposta in base all'algoritmo SRS"""
    score = item_data.get('score', 0)
    # Se punteggio <= 0 (mai fatta o sbagliata), va fatta subito
    if score <= 0: return True
    
    days_passed = get_days_diff(item_data.get('date', ''))
    # Se il punteggio è alto, l'intervallo è lungo (max 15 gg)
    interval = SRS_INTERVALS.get(min(score, 3), 15)
    return days_passed >= interval


# --- 3. GENERAZIONE QUIZ ---
def get_balanced_exam_questions(df):
    """Genera una scheda esame bilanciata secondo le regole ministeriali"""
    if df is None or df.empty: return pd.DataFrame()
    
    exam_questions = []
    work_df = df.copy()
    
    # Se non c'è la colonna Argomento, pesca a caso
    if 'Argomento' not in df.columns:
        return df.sample(min(len(df), 30))

    # Pesca per argomento
    for keyword, count in RULES_BASE.items():
        # Filtra le domande che contengono la parola chiave nell'Argomento
        subset = work_df[work_df['Argomento'].astype(str).str.contains(keyword, case=False, na=False)]
        
        if len(subset) >= count:
            exam_questions.append(subset.sample(n=count))
        else:
            # Se ce ne sono meno del necessario, prendile tutte
            if not subset.empty: exam_questions.append(subset)
    
    # Unisce tutto e mescola
    if exam_questions:
        final_exam = pd.concat(exam_questions)
        # Se mancano domande per arrivare a 30, riempi con casuali
        if len(final_exam) < 30:
            remaining = 30 - len(final_exam)
            # Esclude quelle già prese
            already_ids = final_exam['ID Progressivo'].tolist()
            pool_rest = work_df[~work_df['ID Progressivo'].isin(already_ids)]
            if not pool_rest.empty:
                extra = pool_rest.sample(min(len(pool_rest), remaining))
                final_exam = pd.concat([final_exam, extra])
        
        return final_exam.sample(frac=1).reset_index(drop=True)
    else:
        return df.sample(min(len(df), 30))

def get_next_session_questions(full_db, user_history, mode="Allenamento", num_questions=20):
    """Seleziona le prossime domande per allenamento o ripasso"""
    if full_db is None or full_db.empty: return pd.DataFrame()
    
    all_ids = full_db['ID Progressivo'].astype(str).tolist()
    
    # Pulisce le chiavi della history per il confronto
    clean_history = {str(k).replace('.0','').strip(): v for k, v in user_history.items()}
    
    due_ids = []  # Domande scadute (SRS)
    new_ids = []  # Domande mai viste
    error_ids = [] # Domande sbagliate (score < 0)

    for q_id in all_ids:
        if q_id in clean_history:
            item = clean_history[q_id]
            if item['score'] < 0:
                error_ids.append(q_id)
            elif is_due_for_review(item): 
                due_ids.append(q_id)
        else:
            new_ids.append(q_id)
            
    final_pool = []
    
    if mode == "Ripasso":
        # Priorità assoluta agli errori, poi alle scadenze SRS
        pool = list(set(error_ids + due_ids))
        if not pool: return pd.DataFrame() # Nulla da ripassare
        final_pool = pool
    else:
        # Modalità Allenamento Misto (Nuove + SRS)
        # 70% Nuove, 30% Ripasso
        n_review = int(num_questions * 0.3)
        n_new = num_questions - n_review
        
        # Prende un po' di ripasso se c'è
        if due_ids:
            final_pool.extend(random.sample(due_ids, min(len(due_ids), n_review)))
        
        # Riempie il resto con nuove
        needed = num_questions - len(final_pool)
        if new_ids:
            final_pool.extend(random.sample(new_ids, min(len(new_ids), needed)))
            
        # Se ancora non basta (es. finite le nuove), ripesca dal ripasso o a caso
        if len(final_pool) < num_questions:
            remaining = num_questions - len(final_pool)
            pool_all = all_ids
            final_pool.extend(random.sample(pool_all, min(len(pool_all), remaining)))

    # Estrae le righe dal DB corrispondenti agli ID scelti
    final_df = full_db[full_db['ID Progressivo'].isin(final_pool)]
    
    # Mescola e restituisce
    if len(final_df) > num_questions:
        return final_df.sample(num_questions).reset_index(drop=True)
    return final_df.sample(frac=1).reset_index(drop=True)


# --- 4. STATISTICHE ---
def calculate_topic_stats(full_db, user_history):
    """Calcola le statistiche aggregate per Argomento"""
    if full_db is None or full_db.empty or 'Argomento' not in full_db.columns:
        return pd.DataFrame()

    stats_data = []
    grouped = full_db.groupby('Argomento')
    
    # Pulisce la history una volta per tutte
    clean_history = {str(k).replace('.0','').strip(): v for k, v in user_history.items()}

    for topic, group in grouped:
        total = len(group)
        # Lista ID puliti per questo argomento
        ids = group['ID Progressivo'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip().tolist()
        
        answered = 0
        correct = 0
        
        for qid in ids:
            if qid in clean_history:
                answered += 1
                # Consideriamo "giusta" se lo score è > 0 (cioè almeno 1 volta corretta consecutiva)
                if clean_history[qid].get('score', 0) > 0: 
                    correct += 1
        
        wrong = answered - correct
        
        # Percentuali
        perc_comp = (answered / total * 100) if total > 0 else 0
        perc_acc = (correct / answered * 100) if answered > 0 else 0
        
        stats_data.append({
            "Argomento": topic,
            "Totali": total,
            "Svolte": answered,
            "Giuste": correct,
            "Errate": wrong,
            "% Completamento": round(perc_comp, 1),
            "% Precisione": round(perc_acc, 1)
        })
        
    return pd.DataFrame(stats_data).sort_values(by="% Completamento", ascending=False)