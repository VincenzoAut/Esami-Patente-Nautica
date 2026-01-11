# FILE: logic.py
# VERSION: v51.1 (Stats: Added Right/Wrong columns)
# DATE: 2026-01-10 20:00

import pandas as pd
import random
import datetime

RULES_BASE = {
    "Scafo": 1, "Motori": 1, "Sicurezza": 3, "Manovra": 4,
    "Colreg": 2, "Meteorologia": 2, "Navigazione": 4, "Normativa": 3
}

def get_balanced_exam_questions(df):
    exam_questions = []
    df.columns = [c.strip() for c in df.columns]
    
    if 'Argomento' not in df.columns:
        return df.sample(min(len(df), 20))

    work_df = df.copy()
    for keyword, count in RULES_BASE.items():
        subset = work_df[work_df['Argomento'].astype(str).str.contains(keyword, case=False, na=False)]
        if len(subset) >= count:
            exam_questions.append(subset.sample(n=count))
        else:
            if not subset.empty: exam_questions.append(subset)
    
    if exam_questions:
        final_exam = pd.concat(exam_questions)
        return final_exam.sample(frac=1).reset_index(drop=True)
    else:
        return df.sample(0)

def get_next_session_questions(df, history, mode="Allenamento"):
    df.columns = [c.strip() for c in df.columns]
    TARGET_QUESTIONS = 20
    
    if not history and mode == "Ripasso":
        return df.iloc[0:0]
    if not history and mode == "Allenamento":
        return df.sample(min(len(df), TARGET_QUESTIONS))

    today = datetime.datetime.now()
    ids_error = []
    ids_review_due = []
    
    for q_id, data in history.items():
        score = data['score']
        date_str = data['date']
        try:
            last_seen = datetime.datetime.strptime(str(date_str), "%Y-%m-%d %H:%M:%S")
            days_passed = (today - last_seen).days
        except: days_passed = 100

        if score <= -1: ids_error.append(q_id)
        elif score > 0:
            threshold = 3
            if score == 2: threshold = 7
            elif score >= 3: threshold = 15
            if days_passed >= threshold: ids_review_due.append(q_id)

    df['ID Str'] = df['ID Progressivo'].astype(str)

    if mode == "Ripasso":
        subset = df[df['ID Str'].isin(ids_error)]
        return subset.sample(frac=1).head(TARGET_QUESTIONS) if not subset.empty else subset

    else: # Allenamento
        q_errors = df[df['ID Str'].isin(ids_error)]
        q_reviews = df[df['ID Str'].isin(ids_review_due)]
        all_history_ids = set(history.keys())
        q_new = df[~df['ID Str'].isin(all_history_ids)]
        
        selection = []
        if not q_errors.empty: selection.append(q_errors.sample(min(len(q_errors), 5)))
        if not q_reviews.empty: selection.append(q_reviews.sample(min(len(q_reviews), 5)))
            
        current_len = sum([len(x) for x in selection])
        needed = TARGET_QUESTIONS - current_len
        if needed > 0 and not q_new.empty: selection.append(q_new.sample(min(len(q_new), needed)))
        if not selection and not q_new.empty: selection.append(q_new.sample(min(len(q_new), TARGET_QUESTIONS)))
             
        if selection:
            final_df = pd.concat(selection)
            if len(final_df) > TARGET_QUESTIONS:
                return final_df.sample(TARGET_QUESTIONS).reset_index(drop=True)
            return final_df.sample(frac=1).reset_index(drop=True)
        else:
            return df.sample(min(len(df), TARGET_QUESTIONS))

def calculate_topic_stats(full_db, user_history):
    if full_db is None or full_db.empty or 'Argomento' not in full_db.columns:
        return pd.DataFrame()

    stats_data = []
    grouped = full_db.groupby('Argomento')
    clean_history = {str(k).replace('.0','').strip(): v for k, v in user_history.items()}

    for topic, group in grouped:
        total = len(group)
        ids = group['ID Progressivo'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip().tolist()
        answered = 0
        correct = 0
        for qid in ids:
            if qid in clean_history:
                answered += 1
                if clean_history[qid].get('score', 0) > 0: correct += 1
        
        # Calcoli aggiuntivi
        wrong = answered - correct
        perc_comp = (answered / total * 100) if total > 0 else 0
        perc_acc = (correct / answered * 100) if answered > 0 else 0
        
        stats_data.append({
            "Argomento": topic,
            "Totali": total,
            "Svolte": answered,
            "Giuste": correct,     # Rinominato per chiarezza UI
            "Sbagliate": wrong,    # Nuova colonna
            "% Precisione": round(perc_acc, 1) # Manteniamo per calcolo punto debole, anche se non lo mostriamo
        })
    return pd.DataFrame(stats_data)