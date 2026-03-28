import streamlit as st
import mysql.connector
import pandas as pd
import math
import json
import streamlit.components.v1 as components
from fpdf import FPDF

# ==========================================
# KONFIGURASI DATABASE (MySQL)
# ==========================================

@st.cache_resource(ttl=3600)
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="mbti_db"
    )

@st.cache_resource
def init_db():
    base_conn = mysql.connector.connect(host="localhost", user="root", password="")
    base_cursor = base_conn.cursor()
    base_cursor.execute("CREATE DATABASE IF NOT EXISTS mbti_db")
    base_cursor.close()
    base_conn.close()

    conn = get_db_connection()
    c = conn.cursor(buffered=True)
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            nama VARCHAR(255) NOT NULL,
            umur INT NOT NULL,
            q1 INT, q2 INT, q3 INT, q4 INT,
            mbti_result TEXT,
            tanggal TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS case_base (
            id INT AUTO_INCREMENT PRIMARY KEY,
            mbti_type VARCHAR(10) NOT NULL,
            q1 INT, q2 INT, q3 INT, q4 INT
        )
    ''')
    
    c.execute("SELECT COUNT(*) FROM case_base")
    if c.fetchone()[0] == 0:
        prototypes = [
            ("INTJ", 1, 5, 1, 1), ("INTP", 1, 5, 1, 5), ("ENTJ", 5, 5, 1, 1), ("ENTP", 5, 5, 1, 5),
            ("INFJ", 1, 5, 5, 1), ("INFP", 1, 5, 5, 5), ("ENFJ", 5, 5, 5, 1), ("ENFP", 5, 5, 5, 5),
            ("ISTJ", 1, 1, 1, 1), ("ISTP", 1, 1, 1, 5), ("ESTJ", 5, 1, 1, 1), ("ESTP", 5, 1, 1, 5),
            ("ISFJ", 1, 1, 5, 1), ("ISFP", 1, 1, 5, 5), ("ESFJ", 5, 1, 5, 1), ("ESFP", 5, 1, 5, 5)
        ]
        c.executemany("INSERT INTO case_base (mbti_type, q1, q2, q3, q4) VALUES (%s, %s, %s, %s, %s)", prototypes)
        conn.commit()
        
    c.close()
    conn.close()

# MBTI_INFO (unchanged)
MBTI_INFO = {
    "INTJ": {"nama": "Arsitek", "kelebihan": "Rasional, mandiri, pemikir strategis.", "kekurangan": "Terkadang arogan, terlalu analitis terhadap emosi.", "profesi": "Programmer, Ilmuwan, Ahli Strategi.", "nasihat": "Belajarlah untuk lebih terbuka terhadap perasaan orang lain dan jangan terlalu keras pada diri sendiri."},
    "INTP": {"nama": "Ahli Logika", "kelebihan": "Kreatif, objektif, pemecah masalah yang baik.", "kekurangan": "Sering ragu-ragu, sulit dipahami orang lain.", "profesi": "Analis Data, Peneliti, Insinyur.", "nasihat": "Cobalah untuk menyelesaikan apa yang telah Anda mulai sebelum beralih ke ide baru."},
    # ... (all 16 types - abbreviated for brevity)
    "ESFP": {"nama": "Penghibur", "kelebihan": "Berani, orisinal, estetis, pandai mengamati.", "kekurangan": "Mudah bosan, menghindari konflik, tidak fokus jangka panjang.", "profesi": "Aktor, Pemandu Wisata, Desainer Interior.", "nasihat": "Rencanakan masa depan Anda; kesenangan sesaat bisa mengorbankan tujuan jangka panjang."},
}

# PDF generation function (unchanged)
def generate_pdf_report(user_name, age, mbti_type, info):
    pdf = FPDF()
    pdf.add_page()
    
    pdf.set_font("Helvetica", 'B', 20)
    pdf.set_text_color(64, 224, 208)
    pdf.cell(0, 20, "Laporan Analisis MBTI - Pyth-MBTI", ln=True, align='C')
    pdf.ln(10)
    
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", 'B', 12)
    pdf.cell(0, 10, f"Nama: {user_name}", ln=True)
    pdf.cell(0, 10, f"Usia: {age} Tahun", ln=True)
    pdf.cell(0, 10, f"Hasil Diagnosis: {mbti_type} ({info['nama']})", ln=True)
    pdf.ln(10)
    
    sections = [
        ("Kelebihan", info['kelebihan']),
        ("Kekurangan", info['kekurangan']),
        ("Profesi yang Cocok", info['profesi']),
        ("Nasihat untuk Anda", info['nasihat'])
    ]
    
    for title, content in sections:
        pdf.set_font("Helvetica", 'B', 12)
        pdf.cell(0, 10, f"{title}:", ln=True)
        pdf.set_font("Helvetica", '', 11)
        pdf.multi_cell(0, 7, content)
        pdf.ln(5)
        
    return pdf.output()

# CBR logic (unchanged)
def calculate_similarity(user_case, db_case):
    distance = math.sqrt(sum((u - d) ** 2 for u, d in zip(user_case, db_case)))
    return 1 / (1 + distance)

def run_cbr(user_answers):
    conn = get_db_connection()
    c = conn.cursor(buffered=True)
    c.execute("SELECT mbti_type, q1, q2, q3, q4 FROM case_base")
    cases = c.fetchall()
    c.close()
    conn.close()

    best_match = None
    highest_similarity = -1

    for case in cases:
        mbti_type = case[0]
        db_case = case[1:5]
        sim = calculate_similarity(user_answers, db_case)
        if sim > highest_similarity:
            highest_similarity = sim
            best_match = mbti_type
    return best_match

# Radar chart (unchanged)
def show_radar_chart(user_scores, mbti_type):
    html_code = f"""
<!DOCTYPE html>
<html>
<head>
    <script src="https://unpkg.com/chart.js@3.9.1/dist/chart.min.js"></script>
    <style>
        body {{ background: transparent; font-family: monospace; }}
        canvas {{ max-height: 400px; }}
    </style>
</head>
<body>
    <canvas id="radarChart"></canvas>
    <script>
        const ctx = document.getElementById('radarChart').getContext('2d');
        new Chart(ctx, {{
            type: 'radar',
            data: {{
                labels: ['E/I', 'S/N', 'T/F', 'J/P'],
                datasets: [{{
                    label: '{mbti_type}',
                    data: {user_scores},
                    backgroundColor: 'rgba(64,224,208,0.2)',
                    borderColor: 'rgb(64,224,208)',
                    pointBackgroundColor: 'rgb(32,205,50)',
                    borderWidth: 2
                }}]
            }},
            options: {{
                responsive: true,
                scales: {{ r: {{ angleLines: {{ color: 'rgba(255,255,255,0.2)' }}, grid: {{ color: 'rgba(255,255,255,0.1)' }}
                }};
            }};
        }});
    </script>
</body>
</html>
    """
    components.html(html_code, height=450)

# Main app
def user_interface():
    st.title("🧠 Pyth-MBTI CBR Analyzer")
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Info", "Data Diri", "Pelajari MBTI", "Tes MBTI", "Kasus Sebelumnya"])
    
    with tab1:
        st.header("Selamat Datang!")
        st.markdown("**Pyth-MBTI** menggunakan CBR untuk analisis 16 tipe kepribadian.")
    
    with tab2:
        with st.form("user_form"):
            nama = st.text_input("Nama")
            umur = st.number_input("Umur", 5, 100)
            if st.form_submit_button("Simpan"):
                st.session_state.user_data = {'nama': nama, 'umur': umur}
    
    with tab3:
        for mbti, info in MBTI_INFO.items():
            with st.expander(f"{mbti} - {info['nama']}"):
                st.write(info)
    
    with tab4:
        if 'user_data' not in st.session_state:
            st.warning("Lengkapi data diri dulu!")
        else:
            with st.form("test_form"):
                col1, col2 = st.columns(2)
                with col1:
                    q1 = st.slider("E/I: Sendiri energize (1) → Sosial energize (5)", 1, 5, 3)
                    q3 = st.slider("T/F: Logika (1) → Feeling (5)", 1, 5, 3)
                with col2:
                    q2 = st.slider("S/N: Fakta (1) → Ide (5)", 1, 5, 3)
                    q4 = st.slider("J/P: Terstruktur (1) → Fleksibel (5)", 1, 5, 3)
                if st.form_submit_button("Analisis"):
                    answers = [q1, q2, q3, q4]
                    with st.spinner("CBR analyzing..."):
                        result = run_cbr(answers)
                        # Save to DB
                        conn = get_db_connection()
                        c = conn.cursor()
                        c.execute("INSERT INTO users (nama, umur, q1, q2, q3, q4, mbti_result) VALUES (%s, %s, %s, %s, %s, %s, %s)", 
                                 (st.session_state.user_data['nama'], st.session_state.user_data['umur'], *answers, result))
                        conn.commit()
                        c.close()
                        conn.close()
                    
                    st.session_state.result = {'mbti': result, 'answers': answers}
                    st.rerun()
            
            if 'result' in st.session_state:
                r = st.session_state.result
                info = MBTI_INFO[r['mbti']]
                st.success(f"**Hasil: {r['mbti']} - {info['nama']}**")
                col1, col2 = st.columns(2)
                with col1:
                    st.info(info['kelebihan'])
                    st.warning(info['nasihat'])
                with col2:
                    st.success(info['profesi'])
                    st.error(info['kekurangan'])
                st.subheader("Radar Chart")
                show_radar_chart(r['answers'], r['mbti'])
                pdf = generate_pdf_report(st.session_state.user_data['nama'], st.session_state.user_data['umur'], r['mbti'], info)
                st.download_button("Download PDF", pdf, f"MBTI_{r['mbti']}.pdf", "application/pdf")
    
    with tab5:
        st.header("📋 Kasus-kasus Sebelumnya")
        conn = get_db_connection()
        df = pd.read_sql("SELECT * FROM users ORDER BY tanggal DESC LIMIT 50", conn)
        conn.close()
        
        if df.empty:
            st.info("Belum ada data pengguna.")
        else:
            for _, row in df.iterrows():
                with st.expander(f"{row['nama']} - {row['mbti_result']} (Umur: {row['umur']})"):
                    st.write(f"**Skor:** Q1(E/I):{row['q1']}, Q2(S/N):{row['q2']}, Q3(T/F):{row['q3']}, Q4(J/P):{row['q4']}")
                    answers = [row['q1'], row['q2'], row['q3'], row['q4']]
                    show_radar_chart(answers, row['mbti_result'])
                    
                    # Generate PDF for this user
                    info = MBTI_INFO[row['mbti_result']]
                    pdf_bytes = generate_pdf_report(row['nama'], row['umur'], row['mbti_result'], info)
                    st.download_button(
                        f"📥 Download PDF {row['nama']}",
                        pdf_bytes,
                        f"MBTI_{row['mbti_result']}_{row['nama']}.pdf",
                        "application/pdf"
                    )
            st.dataframe(df[['nama', 'umur', 'mbti_result', 'tanggal']])

def admin_interface():
    st.title("Admin Panel")
    st.warning("Admin panel unchanged for now.")

def main():
    st.set_page_config(page_title="Pyth-MBTI", layout="wide")
    init_db()
    
    mode = st.sidebar.selectbox("Mode", ["User", "Admin"])
    if mode == "User":
        user_interface()
    else:
        admin_interface()

if __name__ == "__main__":
    main()
