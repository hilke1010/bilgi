import streamlit as st
import json
import random
import time
import pandas as pd
import sqlite3
from datetime import datetime

# --- SAYFA AYARLARI ---
st.set_page_config(
    page_title="Otogaz Bilgi Yarışması",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- CSS TASARIMI (MOBİL UYUMLU) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Roboto', sans-serif;
    }

    /* ARKA PLAN */
    .stApp {
        background: linear-gradient(135deg, #001f3f 0%, #003366 40%, #1a9f5b 100%);
        background-attachment: fixed;
        color: white;
        padding-bottom: 70px; /* Footer için alt boşluk */
    }

    /* HEADER */
    .main-header {
        text-align: center;
        padding: 20px;
        background: rgba(0,0,0,0.2);
        border-radius: 15px;
        margin-bottom: 30px;
        border: 1px solid rgba(255,255,255,0.1);
    }
    .main-header h1 {
        font-size: 3rem;
        font-weight: 800;
        margin: 0;
        color: #ffffff;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
    }

    /* KARTLAR */
    .info-card {
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        border-radius: 15px;
        padding: 25px;
        border: 1px solid rgba(255,255,255,0.2);
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        color: white;
        margin-bottom: 20px;
    }
    .info-card h3 {
        border-bottom: 2px solid #28a745;
        padding-bottom: 10px;
        margin-bottom: 15px;
        font-size: 1.3rem;
    }

    /* INPUT */
    .stTextInput input {
        background-color: rgba(255, 255, 255, 0.95) !important;
        color: #001f3f !important;
        font-weight: bold;
        border-radius: 10px !important;
    }

    /* BUTONLAR */
    .stButton button {
        background: linear-gradient(to right, #004d40, #1a9f5b);
        color: white;
        border: none;
        font-weight: bold;
        padding: 12px 24px;
        border-radius: 50px;
        width: 100%;
        font-size: 1.1rem;
        transition: transform 0.2s;
    }
    .stButton button:hover {
        transform: scale(1.02);
        box-shadow: 0 0 15px rgba(40, 167, 69, 0.6);
    }

    /* SORU ALANI */
    .question-box {
        background: white;
        color: #001f3f;
        padding: 30px;
        border-radius: 15px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        border-left: 8px solid #28a745;
        margin-bottom: 20px;
    }
    
    /* RADYO BUTONLARI */
    .stRadio label {
        color: #001f3f !important;
        background-color: rgba(255,255,255,0.9);
        padding: 12px;
        border-radius: 8px;
        margin-bottom: 8px;
        display: block;
        cursor: pointer;
    }

    /* FOOTER */
    .department-footer {
        position: fixed;
        bottom: 0;
        left: 0;
        width: 100%;
        background: rgba(0, 31, 63, 0.95);
        color: #a3cfbb;
        text-align: center;
        padding: 15px;
        font-size: 0.9rem;
        font-weight: 500;
        letter-spacing: 1px;
        border-top: 1px solid rgba(255,255,255,0.1);
        z-index: 9999;
    }

    /* MOBİL UYUMLULUK */
    @media only screen and (max-width: 600px) {
        .main-header { padding: 15px; margin-bottom: 15px; }
        .main-header h1 { font-size: 1.8rem !important; }
        .info-card { padding: 15px; margin-bottom: 15px; }
        .info-card h3 { font-size: 1.1rem; }
        .question-box { padding: 20px; }
        .question-box h2 { font-size: 1.2rem; }
        .question-box p { font-size: 1rem !important; }
        .department-footer { font-size: 0.7rem; padding: 10px; letter-spacing: 0px;}
        .stButton button { padding: 15px 20px; font-size: 1rem; }
    }
</style>
""", unsafe_allow_html=True)

# --- VERİTABANI ---
def init_db():
    conn = sqlite3.connect('otogaz_quiz.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS scores 
                 (username TEXT, score INTEGER, time_taken REAL, date_added TIMESTAMP)''')
    conn.commit()
    conn.close()

def save_score(user, score, time_t):
    conn = sqlite3.connect('otogaz_quiz.db')
    c = conn.cursor()
    c.execute('INSERT INTO scores VALUES (?, ?, ?, ?)', (user, score, time_t, datetime.now()))
    conn.commit()
    conn.close()

# --- GÜNCELLEME: LIMIT 1000 YAPILDI ---
def get_top_scores():
    conn = sqlite3.connect('otogaz_quiz.db')
    # Buradaki LIMIT 5 ibaresini LIMIT 1000 yaptık
    df = pd.read_sql("SELECT username, score, time_taken FROM scores ORDER BY score DESC, time_taken ASC LIMIT 1000", conn)
    conn.close()
    return df

@st.cache_data
def load_qs():
    try:
        with open('sorular_yeni.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            unique_questions = {}
            for q in data:
                unique_questions[q['question']] = q
            return list(unique_questions.values())
    except:
        return []

def format_time(s):
    m, s = divmod(int(s), 60)
    return f"{m:02d}:{s:02d}"

if 'page' not in st.session_state: st.session_state.page = 'home'
if 'quiz_set' not in st.session_state: st.session_state.quiz_set = []
if 'idx' not in st.session_state: st.session_state.idx = 0
if 'score' not in st.session_state: st.session_state.score = 0
if 'answers' not in st.session_state: st.session_state.answers = {}
if 'user' not in st.session_state: st.session_state.user = ""
if 'start' not in st.session_state: st.session_state.start = 0

init_db()

# --- SAYFALAR ---

# 1. ANA SAYFA
if st.session_state.page == 'home':
    
    st.markdown("""
    <div class="main-header">
        <h1>LPG Bilgi Yarışması</h1>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        st.markdown("""
        <div class="info-card">
            <h3>📋 Sınav Hakkında</h3>
            <p>🎲 Rastgele <strong>15 Soru</strong>.</p>
            <p>⏱️ Süre <strong>5 Dakika</strong>.</p>
            <p>⚖️ Kolay, Orta, Zor karışık.</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="info-card" style="text-align:center;">
            <h3>🚀 Başlangıç</h3>
            <p>Başlamak için rumuz giriniz.</p>
            <br>
        """, unsafe_allow_html=True)
        
        name = st.text_input("Rumuz", placeholder="Örn: BattalGazi")
        st.write("")
        if st.button("SINAVI BAŞLAT", use_container_width=True):
            if len(name) > 2:
                st.session_state.user = name
                all_q = load_qs()
                if all_q:
                    sample_size = min(15, len(all_q))
                    st.session_state.quiz_set = random.sample(all_q, sample_size)
                    st.session_state.idx = 0
                    st.session_state.score = 0
                    st.session_state.answers = {}
                    st.session_state.start = time.time()
                    st.session_state.page = 'quiz'
                    st.rerun()
                else:
                    st.error("Soru havuzu boş. Lütfen 'soru_olustur.py' dosyasını çalıştırıp soruları üretin.")
            else:
                st.warning("Lütfen geçerli bir rumuz giriniz.")
        st.markdown("</div>", unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div class="info-card">
            <h3>🏆 Lider Tablosu (Top 1000)</h3>
        """, unsafe_allow_html=True)
        
        df = get_top_scores()
        if not df.empty:
            # Tablo yüksekliğini biraz artırdık ki listede kaydırma kolay olsun
            st.dataframe(
                df, 
                column_config={"username": "Rumuz", "score": "Puan", "time_taken": "Süre"},
                hide_index=True, 
                use_container_width=True,
                height=400 
            )
        else:
            st.info("Henüz kayıt yok.")
        st.markdown("</div>", unsafe_allow_html=True)

# 2. QUIZ SAYFASI
elif st.session_state.page == 'quiz':
    elapsed = time.time() - st.session_state.start
    remaining = 300 - elapsed
    if remaining <= 0:
        st.session_state.page = 'result'
        st.rerun()

    c1, c2, c3 = st.columns([2, 2, 2])
    with c1:
        st.markdown(f"**👤 {st.session_state.user}**")
    with c2:
        total_q = len(st.session_state.quiz_set)
        prog = (st.session_state.idx + 1) / total_q if total_q > 0 else 0
        st.progress(prog)
    with c3:
        st.markdown(f"<div style='text-align:right; font-weight:bold;'>⏳ {format_time(remaining)}</div>", unsafe_allow_html=True)

    q = st.session_state.quiz_set[st.session_state.idx]
    
    st.markdown(f"""
    <div class="question-box">
        <h2 style='margin-top:0;'>Soru {st.session_state.idx + 1}</h2>
        <p style='font-size:20px;'>{q['question']}</p>
    </div>
    """, unsafe_allow_html=True)

    choice = st.radio("Cevabınız:", q['options'], key=f"q_{st.session_state.idx}", index=None)
    
    st.write("")
    col_btn1, col_btn2 = st.columns([3, 2])
    with col_btn2:
        is_last = st.session_state.idx < len(st.session_state.quiz_set) - 1
        btn_txt = "Sonraki ➡️" if is_last else "Bitir 🏁"
        
        if st.button(btn_txt, use_container_width=True):
            if choice:
                st.session_state.answers[st.session_state.idx] = choice
                if choice == q['answer']:
                    st.session_state.score += 1
                
                if is_last:
                    st.session_state.idx += 1
                    st.rerun()
                else:
                    st.session_state.page = 'result'
                    st.rerun()
            else:
                st.warning("Lütfen işaretleyiniz.")

# 3. SONUÇ SAYFASI
elif st.session_state.page == 'result':
    final_t = time.time() - st.session_state.start
    if final_t > 300: final_t = 300
    
    if 'saved' not in st.session_state:
        save_score(st.session_state.user, st.session_state.score, round(final_t, 2))
        st.session_state.saved = True
    
    total_questions = len(st.session_state.quiz_set)
    
    st.balloons()
    
    st.markdown("""
    <div class="main-header">
        <h1>Sonuçlar ✔️</h1>
    </div>
    """, unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"""<div class="info-card" style='text-align:center;'>
            <h3>Doğru</h3><h2 style='color:#28a745;'>{st.session_state.score}/{total_questions}</h2></div>""", unsafe_allow_html=True)
    with c2:
        puan = int((st.session_state.score / total_questions) * 100) if total_questions > 0 else 0
        st.markdown(f"""<div class="info-card" style='text-align:center;'>
            <h3>Puan</h3><h2 style='color:#ffc107;'>{puan}</h2></div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""<div class="info-card" style='text-align:center;'>
            <h3>Süre</h3><h2 style='color:#17a2b8;'>{format_time(final_t)}</h2></div>""", unsafe_allow_html=True)

    st.write("")
    st.markdown("### 📄 Cevap Anahtarı")
    
    for i, q in enumerate(st.session_state.quiz_set):
        u_ans = st.session_state.answers.get(i, "Boş")
        correct_ans = q['answer']
        is_corr = (u_ans == correct_ans)
        
        if is_corr:
            border_color = "#28a745"
            icon = "✅"
            feedback = f"<span style='color:#28a745; font-weight:bold;'>{u_ans}</span>"
        else:
            border_color = "#dc3545"
            icon = "❌"
            feedback = f"<span style='color:#dc3545; text-decoration:line-through;'>{u_ans}</span> <br> 👉 <span style='color:#28a745; font-weight:bold;'>{correct_ans}</span>"

        st.markdown(f"""
        <div style="background-color: white; padding: 15px; border-radius: 10px; border-left: 6px solid {border_color}; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 10px; color: #333;">
            <div style="font-size: 1rem; font-weight: bold; color: #001f3f; margin-bottom: 5px;">{i+1}. {q['question']}</div>
            <div style="font-size: 0.95rem;">{icon} {feedback}</div>
        </div>
        """, unsafe_allow_html=True)

    if st.button("Ana Sayfa", use_container_width=True):
        for k in list(st.session_state.keys()): del st.session_state[k]
        st.rerun()

st.markdown("""
<div class="department-footer">
    Otogaz ve Dökmegaz Yatırım Analizi ve Satış Destek Müdürlüğü
</div>
""", unsafe_allow_html=True)
