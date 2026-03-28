import streamlit as st
import mysql.connector
import pandas as pd
import math
import json
import streamlit.components.v1 as components
from fpdf import FPDF
from datetime import datetime

# ==========================================
# KONFIGURASI DATABASE (MySQL)
# ==========================================

def get_db_connection():
    return mysql.connector.connect(
       host=st.secrets["db_host"],
        user=st.secrets["db_user"],
        password=st.secrets["db_password"],
        database=st.secrets["db_database"],
        port=3306,
        connection_timeout=10
    )
    
@st.cache_resource
def init_db():
    conn = get_db_connection()
    c = conn.cursor(buffered=True)
    
    # Create table for MBTI descriptions and advice
    c.execute("""
        CREATE TABLE IF NOT EXISTS mbti_info (
            mbti_type VARCHAR(10) PRIMARY KEY,
            nama VARCHAR(255),
            definisi TEXT,
            kelebihan TEXT,
            kekurangan TEXT,
            profesi TEXT,
            nasihat TEXT
        )
    """)
    
    c.execute("SELECT COUNT(*) FROM mbti_info")
    if c.fetchone()[0] == 0:
        for mbti, d in MBTI_INFO.items():
            c.execute("""
                INSERT INTO mbti_info (mbti_type, nama, definisi, kelebihan, kekurangan, profesi, nasihat)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (mbti, d['nama'], d.get('definisi', ''), d['kelebihan'], d.get('kekurangan', ''), d['profesi'], d['nasihat']))
        conn.commit()

    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            nama VARCHAR(255) NOT NULL,
            umur INT NOT NULL,
            q1 INT, q2 INT, q3 INT, q4 INT,
            mbti_result TEXT,
            tanggal TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    c.execute("""
        CREATE TABLE IF NOT EXISTS case_base (
            id INT AUTO_INCREMENT PRIMARY KEY,
            mbti_type VARCHAR(10) NOT NULL,
            q1 INT, q2 INT, q3 INT, q4 INT
        )
    """)
    
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
    return conn

def get_mbti_info_db():
    try:
        conn = get_db_connection()
        df = pd.read_sql("SELECT * FROM mbti_info", conn)
        conn.close()
        if not df.empty:
            return df.set_index('mbti_type').to_dict('index')
    except:
        pass
    return MBTI_INFO

# MBTI data (full)
MBTI_INFO = {
    "INTJ": {
        "nama": "Arsitek",
        "definisi": "INTJ (Introverted, Intuitive, Thinking, Judging) dikenal sebagai 'Arsitek' atau pemikir strategis yang paling mandiri di antara semua tipe kepribadian. Mereka memiliki pikiran yang sangat analitis dan selalu berorientasi pada tujuan jangka panjang. INTJ melihat dunia sebagai papan catur yang penuh dengan pola dan kemungkinan yang bisa dioptimalkan. Mereka sangat jarang puas dengan cara-cara konvensional dan selalu mencari metode yang lebih efisien dan inovatif. Dalam kehidupan sehari-hari, INTJ cenderung pendiam namun penuh dengan pemikiran mendalam yang kompleks.",
        "kelebihan": "INTJ memiliki kemampuan berpikir strategis yang luar biasa, mampu melihat gambaran besar sekaligus detail teknis secara bersamaan. Mereka sangat mandiri, tidak mudah terpengaruh opini orang lain, dan memiliki standar kualitas yang sangat tinggi terhadap diri sendiri maupun orang lain. Kemampuan analitis mereka memungkinkan mereka memecahkan masalah yang kompleks dengan cara yang sistematis dan efisien.",
        "kekurangan": "INTJ terkadang terkesan arogan dan tidak sabar terhadap orang yang dianggap kurang kompeten. Mereka sering kesulitan mengekspresikan emosi dan bisa tampak dingin atau tidak peduli secara sosial. Kecenderungan perfeksionisme mereka juga bisa membuat mereka sulit mendelegasikan tugas dan bekerja sama dalam tim.",
        "profesi": "Programmer, Ilmuwan, Ahli Strategi, Arsitek, Analis Sistem, Konsultan Manajemen, Peneliti.",
        "nasihat": "Belajarlah untuk lebih terbuka terhadap perasaan dan pendapat orang lain. Ingat bahwa kecerdasan emosional sama pentingnya dengan kecerdasan intelektual. Cobalah untuk lebih fleksibel dan menerima bahwa tidak semua hal harus sempurna sesuai rencanamu."
    },
    "INTP": {
        "nama": "Ahli Logika",
        "definisi": "INTP (Introverted, Intuitive, Thinking, Perceiving) dikenal sebagai 'Ahli Logika' yang selalu haus akan pengetahuan dan pemahaman mendalam. Mereka adalah pemikir orisinal yang senang mengeksplorasi ide-ide abstrak dan teori-teori kompleks. INTP memiliki kemampuan luar biasa untuk menganalisis sistem yang rumit dan menemukan inkonsistensi logis yang tidak terlihat orang lain. Mereka hidup di dunia ide dan konsep, sering kali lebih nyaman dengan pikiran mereka sendiri daripada interaksi sosial.",
        "kelebihan": "INTP sangat kreatif dalam pemecahan masalah dan mampu berpikir di luar kotak dengan cara yang unik. Mereka objektif, tidak bias, dan selalu mencari kebenaran berdasarkan logika dan bukti. Kemampuan mereka untuk menganalisis pola dan menemukan solusi inovatif membuat mereka sangat berharga dalam bidang riset dan pengembangan.",
        "kekurangan": "INTP sering ragu-ragu dan kesulitan mengambil keputusan karena selalu melihat semua sisi permasalahan. Mereka bisa tampak tidak praktis karena terlalu fokus pada teori dan mengabaikan implementasi. Dalam komunikasi, mereka sering kesulitan menyederhanakan ide-ide kompleks sehingga sulit dipahami orang lain.",
        "profesi": "Analis Data, Peneliti, Ilmuwan Komputer, Filsuf, Matematikawan, Pengembang Software, Ekonom.",
        "nasihat": "Latih dirimu untuk menyelesaikan apa yang sudah dimulai dan belajar menerima bahwa 'cukup baik' terkadang lebih baik daripada 'sempurna tapi tidak selesai'. Kembangkan kemampuan komunikasimu agar ide-ide brilliantmu bisa dipahami dan diwujudkan oleh orang lain."
    },
    "ENTJ": {
        "nama": "Komandan",
        "definisi": "ENTJ (Extraverted, Intuitive, Thinking, Judging) dikenal sebagai 'Komandan' yang lahir untuk memimpin. Mereka adalah individu yang karismatik, tegas, dan selalu berorientasi pada pencapaian tujuan. ENTJ memiliki kemampuan luar biasa untuk melihat inefisiensi dalam sistem dan langsung mengambil tindakan untuk memperbaikinya. Mereka adalah pemimpin alami yang menginspirasi orang lain melalui visi yang jelas dan keyakinan yang kuat. ENTJ sangat ambisius dan tidak pernah berhenti sampai tujuan mereka tercapai.",
        "kelebihan": "ENTJ adalah pemimpin yang efisien dan tegas, mampu mengorganisir orang dan sumber daya dengan sangat baik untuk mencapai tujuan bersama. Mereka memiliki visi jangka panjang yang jelas dan kemampuan strategis untuk mewujudkannya. Kepercayaan diri dan ketegasan mereka membuat orang lain merasa aman dan terarah di bawah kepemimpinan mereka.",
        "kekurangan": "ENTJ bisa sangat keras kepala dan tidak toleran terhadap ketidakefisienan atau inkompetensI. Mereka terkadang terlalu dominan dan tidak cukup mempertimbangkan perasaan anggota tim mereka. Ambisi yang tinggi juga bisa membuat mereka menjadi workaholics yang mengabaikan kehidupan pribadi dan kesehatan.",
        "profesi": "CEO, Direktur, Manajer Senior, Pengacara, Konsultan Strategi, Entrepreneur, Pemimpin Militer.",
        "nasihat": "Tambahkan empati dalam gaya kepemimpinanmu. Ingat bahwa tim yang bahagia dan dihargai akan memberikan hasil jauh lebih baik daripada tim yang hanya didorong oleh tekanan. Luangkan waktu untuk mendengarkan dan memahami perspektif orang lain sebelum mengambil keputusan."
    },
    "ENTP": {
        "nama": "Pendebat",
        "definisi": "ENTP (Extraverted, Intuitive, Thinking, Perceiving) dikenal sebagai 'Pendebat' yang cerdas dan selalu penuh dengan ide-ide segar. Mereka adalah individu yang sangat inovatif, suka tantangan intelektual, dan tidak takut mempertanyakan status quo. ENTP senang berdebat bukan karena ingin menang, tetapi karena mereka percaya bahwa melalui pertukaran ide yang tajam, kebenaran terbaik akan muncul. Mereka adalah pemikir cepat yang mampu melihat berbagai kemungkinan sekaligus.",
        "kelebihan": "ENTP sangat karismatik dan pandai berkomunikasi, mampu meyakinkan orang lain dengan argumen yang kuat dan logis. Kreativitas dan kemampuan berinovasi mereka membantu mereka menemukan solusi yang tidak terpikirkan orang lain. Mereka juga sangat adaptif dan cepat belajar dalam berbagai situasi baru.",
        "kekurangan": "ENTP cenderung cepat bosan dengan rutinitas dan bisa meninggalkan proyek di tengah jalan ketika sudah tidak lagi terasa menantang. Kecenderungan untuk selalu berdebat bisa membuat orang lain merasa tidak nyaman atau tidak dihargai. Mereka juga sering kesulitan fokus dan menindaklanjuti rencana secara konsisten.",
        "profesi": "Entrepreneur, Pengacara, Konsultan Inovasi, Ilmuwan, Jurnalis, Pengembang Produk, Komedian.",
        "nasihat": "Bangun ide-idemu hingga menjadi kenyataan, jangan hanya berhenti pada tahap perdebatan dan perencanaan. Belajarlah untuk lebih sensitif terhadap perasaan orang lain saat berdebat, dan latih konsistensi dalam menyelesaikan komitmen yang sudah kamu buat."
    },
    "INFJ": {
        "nama": "Advokat",
        "definisi": "INFJ (Introverted, Intuitive, Feeling, Judging) adalah tipe kepribadian paling langka di dunia, dikenal sebagai 'Advokat' yang hidup dengan misi untuk membuat perbedaan positif bagi dunia. Mereka memiliki intuisi yang sangat kuat dan kemampuan luar biasa untuk memahami motivasi dan emosi orang lain. INFJ adalah pemimpi yang sekaligus praktis, memiliki visi idealis namun juga kemampuan untuk mewujudkannya secara nyata. Mereka sangat berprinsip dan tidak akan berkompromi dengan nilai-nilai inti mereka.",
        "kelebihan": "INFJ memiliki empati yang sangat dalam dan kemampuan untuk benar-benar memahami penderitaan serta kebutuhan orang lain. Mereka sangat berkomitmen terhadap tujuan mulia dan mampu menginspirasi orang lain melalui keaslian dan ketulusan mereka. Kombinasi intuisi kuat dan pemikiran terstruktur membuat mereka unggul dalam pekerjaan yang membutuhkan pemahaman manusia mendalam.",
        "kekurangan": "INFJ sangat rentan terhadap burnout karena mereka cenderung memberikan segalanya untuk orang lain tanpa cukup memperhatikan kebutuhan diri sendiri. Mereka bisa sangat perfeksionis dan terlalu kritis terhadap diri sendiri. Sensitivitas tinggi mereka juga membuat mereka mudah terpengaruh oleh energi negatif dari lingkungan sekitar.",
        "profesi": "Psikolog, Konselor, Penulis, Aktivis Sosial, Dokter, Pemimpin Spiritual, Pendidik.",
        "nasihat": "Jaga dirimu sendiri sama seperti kamu menjaga orang lain. Pelajari cara menetapkan batasan yang sehat agar kamu bisa terus memberikan yang terbaik tanpa mengorbankan kesehatan mentalmu sendiri. Ingat bahwa kamu tidak bisa menuangkan dari cangkir yang kosong."
    },
    "INFP": {
        "nama": "Mediator",
        "definisi": "INFP (Introverted, Intuitive, Feeling, Perceiving) dikenal sebagai 'Mediator' yang hidup dengan panduan nilai-nilai dan perasaan yang sangat dalam. Mereka adalah individu yang sangat empatik, kreatif, dan selalu mencari makna yang lebih dalam dalam setiap pengalaman hidup. INFP memiliki dunia batin yang sangat kaya dan kompleks, sering kali mengungkapkannya melalui seni, tulisan, atau musik. Mereka sangat peduli dengan keaslian diri dan tidak suka kepura-puraan dalam bentuk apapun.",
        "kelebihan": "INFP memiliki empati yang luar biasa dan kemampuan untuk benar-benar merasakan apa yang dirasakan orang lain. Kreativitas dan kepekaan mereka menghasilkan karya-karya yang menyentuh hati dan bermakna. Mereka juga sangat setia dan tulus dalam hubungan, selalu memberikan dukungan emosional yang mendalam kepada orang-orang yang mereka cintai.",
        "kekurangan": "INFP sering terlalu idealis sehingga mudah kecewa ketika kenyataan tidak sesuai dengan harapan mereka. Mereka cenderung menghindari konflik dan kesulitan membuat keputusan yang tegas. Kecenderungan untuk terlalu banyak berefleksi juga bisa membuat mereka terjebak dalam pikiran sendiri dan menjadi tidak produktif.",
        "profesi": "Penulis, Seniman, Konselor, Psikolog, Musisi, Desainer, Pekerja Sosial, Pendidik.",
        "nasihat": "Terima kenyataan bahwa dunia tidak selalu bisa sesuai dengan idealismemu, dan itu tidak apa-apa. Belajarlah untuk mengambil tindakan nyata meskipun situasinya tidak sempurna. Keseimbangan antara idealisme dan pragmatisme akan membantumu mewujudkan nilai-nilaimu dengan lebih efektif."
    },
    "ENFJ": {
        "nama": "Protagonis",
        "definisi": "ENFJ (Extraverted, Intuitive, Feeling, Judging) dikenal sebagai 'Protagonis' yang lahir sebagai pemimpin yang menginspirasi dan peduli. Mereka adalah individu yang karismatik, hangat, dan memiliki kemampuan luar biasa untuk memotivasi serta memberdayakan orang lain. ENFJ secara alami menarik orang-orang ke sekitar mereka dan memiliki bakat untuk melihat potensi terbaik dalam setiap orang. Mereka sangat berorientasi pada hubungan dan selalu berusaha menciptakan harmoni dalam lingkungan sosial mereka.",
        "kelebihan": "ENFJ adalah komunikator yang sangat baik dan mampu membangun koneksi yang bermakna dengan siapapun. Kemampuan mereka untuk memahami emosi dan motivasi orang lain membuat mereka menjadi pemimpin yang sangat efektif dan dicintai. Mereka juga sangat berkomitmen dan dapat diandalkan dalam membantu orang lain mencapai potensi terbaik mereka.",
        "kekurangan": "ENFJ sering mengorbankan kebutuhan dan keinginan pribadi mereka demi kepentingan orang lain, yang bisa menyebabkan kelelahan emosional. Mereka terkadang terlalu sensitif terhadap kritik dan sangat khawatir tentang pendapat orang lain. Keinginan kuat untuk menjaga harmoni juga bisa membuat mereka menghindari konflik yang sebenarnya perlu diselesaikan.",
        "profesi": "Guru, Konselor, Pemimpin Organisasi, Diplomat, Pelatih Kehidupan, Manajer SDM, Politisi.",
        "nasihat": "Ingatlah bahwa menjaga dirimu sendiri bukanlah hal yang egois, melainkan prasyarat untuk bisa terus membantu orang lain secara efektif. Belajarlah untuk mengatakan tidak ketika perlu, dan jangan biarkan kebutuhan orang lain selalu mengesampingkan kebutuhanmu sendiri."
    },
    "ENFP": {
        "nama": "Juru Kampanye",
        "definisi": "ENFP (Extraverted, Intuitive, Feeling, Perceiving) dikenal sebagai 'Juru Kampanye' yang penuh semangat, kreativitas, dan cinta terhadap kehidupan. Mereka adalah jiwa bebas yang melihat hidup sebagai petualangan penuh kemungkinan. ENFP memiliki kemampuan luar biasa untuk terhubung dengan orang lain dan membawa energi positif ke mana pun mereka pergi. Mereka sangat antusias, imajinatif, dan selalu mencari cara-cara baru untuk mengekspresikan diri dan membantu orang lain.",
        "kelebihan": "ENFP memiliki antusiasme yang menular dan kemampuan untuk menginspirasi orang lain dengan visi dan semangat mereka. Kreativitas dan imajinasi mereka yang tinggi membantu mereka menemukan solusi-solusi inovatif dan tidak konvensional. Empati dan kemampuan komunikasi mereka yang kuat membuat mereka sangat efektif dalam membangun hubungan yang bermakna.",
        "kekurangan": "ENFP sering kesulitan fokus pada satu hal dalam jangka waktu lama karena selalu tertarik pada ide dan peluang baru. Mereka cenderung menunda-nunda pekerjaan yang tidak mereka sukai dan bisa menjadi tidak konsisten dalam menindaklanjuti komitmen. Sensitivitas emosional yang tinggi juga bisa membuat mereka mudah terpengaruh oleh suasana hati.",
        "profesi": "Pemasar, Konselor, Jurnalis, Aktor, Pengusaha Sosial, Desainer Kreatif, Pelatih.",
        "nasihat": "Disiplin diri adalah kunci untuk mewujudkan potensi luar biasamu. Coba buat sistem dan rutinitas yang membantu kamu tetap fokus dan menyelesaikan apa yang sudah kamu mulai. Energi dan kreativitasmu adalah hadiah besar, pastikan disalurkan dengan terarah."
    },
    "ISTJ": {
        "nama": "Logistik",
        "definisi": "ISTJ (Introverted, Sensing, Thinking, Judging) dikenal sebagai 'Logistik' yang merupakan tulang punggung masyarakat dan organisasi. Mereka adalah individu yang sangat bertanggung jawab, dapat diandalkan, dan memiliki integritas yang tinggi. ISTJ percaya pada kejujuran, dedikasi, dan kerja keras sebagai fondasi kehidupan yang baik. Mereka adalah penjaga tradisi dan prosedur yang telah terbukti bekerja dengan baik, dan sangat menghargai stabilitas serta kepastian dalam kehidupan mereka.",
        "kelebihan": "ISTJ sangat dapat diandalkan dan konsisten dalam memenuhi komitmen dan tanggung jawab mereka. Perhatian mereka terhadap detail dan kemampuan organisasi yang sangat baik membuat mereka unggul dalam pekerjaan yang membutuhkan ketelitian dan akurasi tinggi. Mereka juga sangat logis dan faktual dalam pengambilan keputusan, jauh dari pengaruh emosi sesaat.",
        "kekurangan": "ISTJ bisa sangat kaku dan sulit beradaptasi dengan perubahan yang tiba-tiba atau metode-metode baru yang belum teruji. Mereka cenderung terlalu fokus pada prosedur dan aturan sehingga kadang melewatkan fleksibilitas yang diperlukan. Dalam hubungan interpersonal, mereka sering kesulitan mengekspresikan emosi dan terkesan dingin atau tidak peduli.",
        "profesi": "Akuntan, Auditor, Manajer Proyek, Pegawai Negeri, Hakim, Dokter, Insinyur, Militer.",
        "nasihat": "Coba sesekali keluar dari zona nyamanmu dan variasikan rutinitas yang sudah ada. Perubahan tidak selalu berarti kekacauan, dan terkadang cara-cara baru bisa membawa hasil yang lebih baik. Belajarlah juga untuk lebih mengekspresikan apresiasi dan afeksi kepada orang-orang di sekitarmu."
    },
    "ISTP": {
        "nama": "Pengrajin",
        "definisi": "ISTP (Introverted, Sensing, Thinking, Perceiving) dikenal sebagai 'Pengrajin' atau 'Virtuoso' yang memiliki kemampuan luar biasa untuk memahami dan memanipulasi sistem mekanis dan teknis. Mereka adalah pemecah masalah pragmatis yang bekerja paling baik ketika menghadapi tantangan langsung dan nyata. ISTP memiliki rasa ingin tahu yang besar tentang cara kerja sesuatu dan senang membongkar-pasang objek untuk memahaminya lebih dalam. Mereka sangat mandiri dan menghargai kebebasan dalam cara mereka bekerja.",
        "kelebihan": "ISTP sangat terampil secara teknis dan mampu belajar keterampilan baru dengan sangat cepat melalui pengalaman langsung. Mereka sangat tenang dalam situasi krisis dan mampu mengambil tindakan cepat dan tepat ketika dibutuhkan. Kemampuan analitis dan pragmatisme mereka membuat mereka sangat efektif dalam memecahkan masalah teknis yang kompleks.",
        "kekurangan": "ISTP cenderung mengambil risiko yang tidak perlu dan bisa bertindak impulsif tanpa mempertimbangkan konsekuensi jangka panjang. Mereka sering kesulitan dengan komitmen jangka panjang dan bisa tampak tidak dapat diandalkan dalam hubungan interpersonal. Kurangnya perhatian terhadap aturan dan prosedur juga bisa membawa mereka ke dalam masalah.",
        "profesi": "Mekanik, Insinyur, Pilot, Atlet, Ahli Forensik, Programmer, Teknisi, Pemadam Kebakaran.",
        "nasihat": "Belajarlah untuk berpikir lebih jauh ke depan dan mempertimbangkan dampak jangka panjang dari tindakanmu. Kembangkan kemampuan interpersonalmu agar kamu bisa bekerja lebih efektif dalam tim dan membangun hubungan yang lebih bermakna dengan orang lain."
    },
    "ESTJ": {
        "nama": "Eksekutif",
        "definisi": "ESTJ (Extraverted, Sensing, Thinking, Judging) dikenal sebagai 'Eksekutif' yang merupakan pilar masyarakat dan organisasi. Mereka adalah individu yang sangat terorganisir, tegas, dan berkomitmen untuk memastikan bahwa segala sesuatu berjalan dengan benar dan efisien. ESTJ percaya pada nilai-nilai tradisional, aturan yang jelas, dan hierarki yang terstruktur. Mereka adalah administrator yang sangat baik dan mampu mengkoordinasikan orang dan sumber daya dengan sangat efektif untuk mencapai tujuan.",
        "kelebihan": "ESTJ sangat efisien dalam mengorganisir orang, sumber daya, dan proses untuk mencapai tujuan yang ditetapkan. Kejujuran dan ketegasan mereka membuat mereka dapat dipercaya dan dihormati sebagai pemimpin. Komitmen mereka terhadap tradisi dan nilai-nilai yang telah terbukti memberikan stabilitas dan keandalan bagi organisasi.",
        "kekurangan": "ESTJ bisa sangat kaku dan tidak fleksibel ketika menghadapi situasi yang membutuhkan pendekatan yang lebih inovatif atau non-konvensional. Mereka sering kesulitan mengekspresikan emosi dan bisa tampak tidak peka terhadap perasaan orang lain. Kecenderungan untuk mendominasi percakapan dan mengontrol situasi juga bisa membuat orang lain merasa tidak didengar.",
        "profesi": "Manajer, Direktur, Pengacara, Hakim, Perwira Militer, Kepala Sekolah, Akuntan Senior.",
        "nasihat": "Luangkan waktu untuk benar-benar mendengarkan perspektif orang lain, terutama mereka yang berbeda cara pandangnya denganmu. Fleksibilitas dan keterbukaan terhadap ide-ide baru tidak akan melemahkan otoritasmu, justru akan memperkuat kemampuan kepemimpinanmu."
    },
    "ESTP": {
        "nama": "Pengusaha",
        "definisi": "ESTP (Extraverted, Sensing, Thinking, Perceiving) dikenal sebagai 'Pengusaha' yang hidup untuk momen ini dan selalu mencari aksi serta pengalaman baru. Mereka adalah individu yang energetik, pragmatis, dan sangat perceptif terhadap lingkungan sekitar mereka. ESTP memiliki kemampuan luar biasa untuk membaca situasi dan orang dengan sangat cepat, dan langsung mengambil tindakan yang diperlukan. Mereka adalah pemecah masalah yang berorientasi pada tindakan dan tidak suka teori tanpa praktik.",
        "kelebihan": "ESTP sangat karismatik dan mampu mempengaruhi orang lain dengan keberanian dan energi yang mereka pancarkan. Kemampuan mereka untuk beradaptasi dengan cepat dan berpikir di bawah tekanan membuat mereka sangat efektif dalam situasi krisis. Kepraktisan dan orientasi hasil mereka memastikan bahwa mereka selalu berfokus pada apa yang benar-benar penting.",
        "kekurangan": "ESTP cenderung sangat impulsif dan membuat keputusan tanpa mempertimbangkan konsekuensi jangka panjang secara matang. Kecenderungan untuk mencari sensasi dan kegembiraan bisa membawa mereka ke situasi berisiko. Mereka juga sering tidak sabar dengan teori, perencanaan jangka panjang, dan diskusi abstrak.",
        "profesi": "Atlet Profesional, Pengusaha, Pemasar, Paramedik, Detektif, Broker Saham, Pilot.",
        "nasihat": "Belajarlah untuk lebih sabar dan luangkan waktu untuk merencanakan langkah ke depan sebelum bertindak. Impulsivitasmu adalah kekuatan dalam situasi tertentu, namun memahami kapan harus menahan diri akan membuatmu jauh lebih efektif dan sukses dalam jangka panjang."
    },
    "ISFJ": {
        "nama": "Pembela",
        "definisi": "ISFJ (Introverted, Sensing, Feeling, Judging) dikenal sebagai 'Pembela' yang merupakan salah satu tipe kepribadian paling murah hati dan peduli. Mereka adalah individu yang hangat, sabar, dan selalu siap memberikan dukungan kepada orang-orang yang mereka cintai. ISFJ memiliki ingatan yang luar biasa terhadap detail-detail personal tentang orang lain dan menggunakan pengetahuan ini untuk memberikan perhatian yang sangat personal dan bermakna. Mereka adalah penjaga tradisi dan nilai-nilai keluarga yang teguh.",
        "kelebihan": "ISFJ sangat dapat diandalkan, perhatian, dan selalu hadir ketika dibutuhkan oleh orang-orang yang mereka cintai. Perhatian mereka terhadap detail dan kemampuan praktis mereka membuat mereka sangat efektif dalam pekerjaan yang membutuhkan ketelitian dan kepedulian terhadap orang lain. Loyalitas dan komitmen mereka tidak tertandingi.",
        "kekurangan": "ISFJ cenderung pemalu dan kesulitan mengekspresikan kebutuhan dan perasaan mereka sendiri kepada orang lain. Mereka sering menekan perasaan negatif dan menumpuk resentment daripada menghadapi konflik secara langsung. Kecenderungan untuk terlalu fokus pada masa lalu juga bisa membuat mereka sulit beradaptasi dengan perubahan.",
        "profesi": "Perawat, Dokter Umum, Guru, Konselor, Asisten Administrasi, Pustakawan, Pekerja Sosial.",
        "nasihat": "Belajarlah untuk mengkomunikasikan kebutuhan dan perasaanmu sendiri dengan lebih terbuka. Ingat bahwa meminta bantuan dan menetapkan batasan bukanlah tanda kelemahan, melainkan tanda kematangan emosional. Kamu berhak untuk diperlakukan dengan kebaikan yang sama seperti yang kamu berikan kepada orang lain."
    },
    "ISFP": {
        "nama": "Petualang",
        "definisi": "ISFP (Introverted, Sensing, Feeling, Perceiving) dikenal sebagai 'Petualang' atau 'Seniman' yang hidup dengan penuh rasa ingin tahu dan keterbukaan terhadap pengalaman baru. Mereka adalah individu yang sangat sensitif, artistik, dan memiliki hubungan yang mendalam dengan lingkungan sekitar mereka. ISFP mengekspresikan diri melalui tindakan dan kreasi daripada kata-kata, dan sering mengejutkan orang lain dengan bakat-bakat tersembunyi yang mereka miliki. Mereka hidup di momen sekarang dan sangat menghargai kebebasan dan keaslian.",
        "kelebihan": "ISFP memiliki sensitivitas estetis yang luar biasa dan kemampuan kreatif yang memungkinkan mereka menciptakan karya-karya yang indah dan bermakna. Empati dan ketulusan mereka membuat mereka sangat mudah didekati dan dipercaya oleh orang lain. Fleksibilitas dan keterbukaan mereka terhadap pengalaman baru membuat mereka sangat adaptif.",
        "kekurangan": "ISFP sangat mudah stres ketika menghadapi konflik atau tekanan dan cenderung menarik diri dari situasi yang tidak nyaman. Mereka sering kesulitan merencanakan masa depan dan bisa tampak tidak ambisius atau kurang terorganisir. Sensitivitas tinggi mereka juga membuat mereka sangat rentan terhadap kritik.",
        "profesi": "Seniman, Musisi, Desainer Grafis, Fotografer, Chef, Terapis Fisik, Dokter Hewan.",
        "nasihat": "Jangan takut untuk membiarkan orang lain melihat dan menghargai bakat serta kreativitasmu yang luar biasa. Belajarlah untuk menghadapi kritik sebagai alat untuk berkembang, bukan sebagai serangan pribadi. Membangun struktur dan rutinitas sederhana akan membantumu mewujudkan potensi kreatifmu secara lebih konsisten."
    },
    "ESFJ": {
        "nama": "Konsul",
        "definisi": "ESFJ (Extraverted, Sensing, Feeling, Judging) dikenal sebagai 'Konsul' yang merupakan tipe kepribadian yang paling berorientasi pada komunitas dan hubungan sosial. Mereka adalah individu yang hangat, sosial, dan mendedikasikan diri mereka untuk menciptakan harmoni dan kesejahteraan dalam komunitas mereka. ESFJ sangat peduli dengan perasaan orang lain dan selalu berusaha memastikan bahwa semua orang merasa diterima, dihargai, dan bahagia. Mereka adalah pilar sosial yang menjaga tradisi dan nilai-nilai komunal.",
        "kelebihan": "ESFJ sangat baik dalam membangun dan memelihara hubungan yang bermakna dengan berbagai macam orang. Kepedulian dan perhatian mereka yang tulus membuat orang lain merasa dihargai dan didukung. Kemampuan organisasi dan praktis mereka juga sangat membantu dalam menciptakan lingkungan yang terstruktur dan harmonis.",
        "kekurangan": "ESFJ sangat membutuhkan validasi dan pengakuan dari orang lain, yang bisa membuat mereka rentan terhadap manipulasi. Mereka sering terlalu khawatir tentang apa yang orang lain pikirkan dan bisa mengorbankan kebutuhan pribadi demi persetujuan sosial. Kesulitan mereka dalam menerima kritik juga bisa menjadi hambatan dalam pertumbuhan pribadi.",
        "profesi": "Guru, Perawat, Manajer SDM, Event Planner, Konselor Sekolah, Apoteker, Asisten Sosial.",
        "nasihat": "Belajarlah untuk menghargai dan memvalidasi dirimu sendiri tanpa selalu membutuhkan konfirmasi dari orang lain. Nilai dan harga dirimu tidak seharusnya bergantung sepenuhnya pada pendapat orang lain. Kepercayaan diri yang sejati datang dari dalam, bukan dari luar."
    },
    "ESFP": {
        "nama": "Penghibur",
        "definisi": "ESFP (Extraverted, Sensing, Feeling, Perceiving) dikenal sebagai 'Penghibur' yang merupakan jiwa pesta yang sesungguhnya. Mereka adalah individu yang spontan, energetik, dan selalu membawa kegembiraan serta hiburan ke mana pun mereka pergi. ESFP hidup sepenuhnya di momen sekarang dan memiliki kemampuan luar biasa untuk membuat orang lain merasa senang dan diterima. Mereka sangat orisinal dan tidak takut untuk tampil beda dan menjadi pusat perhatian.",
        "kelebihan": "ESFP sangat pandai membuat orang lain merasa nyaman, bahagia, dan diterima dalam kelompok sosial. Spontanitas dan kreativitas mereka menghasilkan pengalaman-pengalaman yang tak terlupakan bagi orang-orang di sekitar mereka. Kemampuan praktis mereka juga membuat mereka sangat efektif dalam situasi yang membutuhkan tindakan cepat dan kreatif.",
        "kekurangan": "ESFP sering kesulitan fokus pada tujuan jangka panjang dan bisa terganggu oleh kesenangan dan stimulasi jangka pendek. Menghindari konflik dan situasi yang tidak menyenangkan bisa membuat mereka tidak mengatasi masalah penting secara langsung. Impulsivitas mereka juga bisa membawa konsekuensi keuangan dan relasional yang tidak menyenangkan.",
        "profesi": "Aktor, Penyanyi, Event Organizer, Pemasar, Pelatih Olahraga, Terapis, Tour Guide.",
        "nasihat": "Mulailah memikirkan dan merencanakan masa depanmu dengan lebih serius tanpa kehilangan keceriaan dan spontanitasmu yang berharga. Belajarlah untuk menghadapi situasi yang tidak nyaman secara langsung, karena menghindarinya hanya akan membuatnya semakin besar dan sulit diselesaikan."
    },
}


def generate_pdf_report(user_name, age, mbti_type, info, answers=None):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=20)

    # ── Halaman 1: Cover ──────────────────────────────────────────
    pdf.add_page()

    # Header bar
    pdf.set_fill_color(15, 52, 96)
    pdf.rect(0, 0, 210, 40, 'F')
    pdf.set_font("Helvetica", 'B', 22)
    pdf.set_text_color(64, 224, 208)
    pdf.set_y(12)
    pdf.cell(0, 10, "LAPORAN ANALISIS KEPRIBADIAN MBTI", ln=True, align='C')
    pdf.set_font("Helvetica", '', 11)
    pdf.set_text_color(200, 220, 240)
    pdf.cell(0, 8, "Pyth-MBTI Psychology Detector  |  Powered by Case-Based Reasoning", ln=True, align='C')

    pdf.ln(12)

    # Kotak info user
    pdf.set_fill_color(240, 245, 255)
    pdf.set_draw_color(15, 52, 96)
    pdf.set_line_width(0.5)
    pdf.rect(15, pdf.get_y(), 180, 50, 'FD')
    pdf.set_y(pdf.get_y() + 6)
    pdf.set_font("Helvetica", 'B', 13)
    pdf.set_text_color(15, 52, 96)
    pdf.cell(10)  # Memberikan margin ke kanan
    pdf.cell(65, 10, "DATA SUBJEK", ln=True)
    pdf.set_font("Helvetica", '', 12)
    pdf.set_text_color(40, 40, 40)
    pdf.cell(10)
    pdf.cell(50, 7, "Nama Lengkap", ln=False)
    pdf.cell(5, 7, ":", ln=False)
    pdf.cell(0, 7, f" {user_name}", ln=True)
    pdf.cell(10)
    pdf.cell(50, 7, "Usia", ln=False)
    pdf.cell(5, 7, ":", ln=False)
    pdf.cell(0, 7, f" {age} tahun", ln=True)
    pdf.cell(10)
    pdf.cell(50, 7, "Tanggal Tes", ln=False)
    pdf.cell(5, 7, ":", ln=False)
    pdf.cell(0, 7, f" {datetime.now().strftime('%d %B %Y, %H:%M WIB')}", ln=True)

    pdf.ln(12)

    # Kotak hasil MBTI besar
    pdf.set_fill_color(15, 52, 96)
    pdf.set_draw_color(64, 224, 208)
    pdf.set_line_width(1)
    pdf.rect(15, pdf.get_y(), 180, 55, 'FD')
    pdf.set_y(pdf.get_y() + 6)
    pdf.set_font("Helvetica", 'B', 11)
    pdf.set_text_color(64, 224, 208)
    pdf.cell(0, 7, "HASIL TIPE KEPRIBADIAN", ln=True, align='C')
    pdf.set_font("Helvetica", 'B', 36)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 16, mbti_type, ln=True, align='C')
    pdf.set_font("Helvetica", 'B', 16)
    pdf.set_text_color(64, 224, 208)
    pdf.cell(0, 10, f"\"{info['nama']}\"", ln=True, align='C')
    pdf.ln(2)
    pdf.set_font("Helvetica", '', 10)
    pdf.set_text_color(180, 210, 240)
    pdf.cell(0, 7, "Dianalisis menggunakan metode Case-Based Reasoning (CBR)", ln=True, align='C')

    pdf.ln(10)

    # Skor dimensi jika tersedia
    if answers:
        pdf.set_text_color(40, 40, 40)
        pdf.set_font("Helvetica", 'B', 12)
        pdf.set_fill_color(230, 240, 255)
        pdf.set_draw_color(15, 52, 96)
        pdf.rect(15, pdf.get_y(), 180, 8, 'FD')
        pdf.cell(10)  # Memberikan margin ke kanan agar sejajar
        pdf.cell(0, 8, "SKOR DIMENSI KEPRIBADIAN", ln=True)
        pdf.ln(2)
        dims = [("E/I (Ekstraversi - Introversi)", answers[0]),
                ("S/N (Sensing - Intuition)", answers[1]),
                ("T/F (Thinking - Feeling)", answers[2]),
                ("J/P (Judging - Perceiving)", answers[3])]
        for label, val in dims:
            bar_w = int((val / 5) * 120)
            pdf.set_font("Helvetica", '', 10)
            pdf.set_text_color(40, 40, 40)
            pdf.cell(10)
            pdf.cell(80, 6, label, ln=False)
            pdf.set_fill_color(64, 224, 208)
            pdf.set_draw_color(200, 200, 200)
            pdf.rect(pdf.get_x(), pdf.get_y() + 1, bar_w, 4, 'FD')
            pdf.set_x(pdf.get_x() + 122)
            pdf.set_text_color(15, 52, 96)
            pdf.set_font("Helvetica", 'B', 10)
            pdf.cell(15, 6, f"{val}/5", ln=True)
        pdf.ln(6)

    # ── Halaman 2: Laporan Detail ─────────────────────────────────
    pdf.add_page()

    def section_header(title):
        pdf.set_fill_color(15, 52, 96)
        pdf.set_text_color(64, 224, 208)
        pdf.set_font("Helvetica", 'B', 12)
        pdf.rect(15, pdf.get_y(), 180, 9, 'F')
        pdf.cell(10)  # Konsistensi margin 10 unit untuk semua judul bagian
        pdf.cell(0, 9, title, ln=True)
        pdf.set_text_color(40, 40, 40)
        pdf.ln(2)

    def body_text(text):
        pdf.set_font("Helvetica", '', 11)
        pdf.set_text_color(50, 50, 50)
        pdf.set_x(15)
        pdf.multi_cell(180, 6, text)
        pdf.ln(4)

    # Header halaman 2
    pdf.set_fill_color(15, 52, 96)
    pdf.rect(0, 0, 210, 18, 'F')
    pdf.set_font("Helvetica", 'B', 13)
    pdf.set_text_color(64, 224, 208)
    pdf.set_y(5)
    pdf.cell(0, 8, f"LAPORAN DETAIL  |  {mbti_type} - {info['nama']}  |  {user_name}", ln=True, align='C')
    pdf.ln(6)

    section_header("1. DEFINISI DAN GAMBARAN UMUM")
    body_text(info.get('definisi', '-'))

    section_header("2. KELEBIHAN DAN KEKUATAN")
    body_text(info.get('kelebihan', '-'))

    section_header("3. KELEMAHAN DAN AREA PENGEMBANGAN")
    body_text(info.get('kekurangan', '-'))

    section_header("4. REKOMENDASI KARIR DAN PROFESI")
    body_text(f"Berdasarkan analisis tipe kepribadian {mbti_type}, berikut adalah bidang karir yang paling sesuai: {info.get('profesi', '-')}")

    section_header("5. NASIHAT DAN REKOMENDASI PENGEMBANGAN DIRI")
    body_text(info.get('nasihat', '-'))

    section_header("6. KESIMPULAN")
    body_text(
        f"Berdasarkan hasil analisis menggunakan metode Case-Based Reasoning (CBR), {user_name} "
        f"(usia {age} tahun) teridentifikasi memiliki tipe kepribadian {mbti_type} - {info['nama']}. "
        f"Tipe kepribadian ini mencerminkan pola pikir, perasaan, dan perilaku yang khas yang dapat "
        f"dijadikan sebagai panduan dalam pengembangan diri, pemilihan karir, dan pengelolaan hubungan "
        f"interpersonal. Laporan ini bersifat panduan dan diharapkan dapat membantu {user_name} "
        f"untuk lebih memahami diri sendiri dan memaksimalkan potensi yang dimiliki."
    )

    # Footer
    pdf.set_y(-20)
    pdf.set_fill_color(15, 52, 96)
    pdf.rect(0, pdf.get_y(), 210, 20, 'F')
    pdf.set_font("Helvetica", 'I', 9)
    pdf.set_text_color(150, 180, 220)
    pdf.cell(0, 10, f"Pyth-MBTI Psychology Detector  |  Laporan dibuat otomatis  |  {datetime.now().strftime('%d/%m/%Y')}", ln=True, align='C')

    return bytes(pdf.output(dest="S").encode("latin-1"))
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

def show_radar_chart(user_scores, mbti_type):
    components.html(f"""
    <!DOCTYPE html>
    <html>
    <head>
        <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
    </head>
    <body style="background-color: transparent; margin: 0; padding: 0; overflow: hidden;">
        <div style="width: 100%; height: 420px; display: flex; justify-content: center; align-items: center;">
            <canvas id="chart"></canvas>
        </div>
        <script>
            const ctx = document.getElementById('chart').getContext('2d');
            new Chart(ctx, {{
                type: 'radar',
                data: {{
                    labels: ['Energi (E/I)', 'Informasi (S/N)', 'Keputusan (T/F)', 'Gaya Hidup (J/P)'],
                    datasets: [{{
                        label: 'Skor Karakteristik {mbti_type}',
                        data: {user_scores},
                        backgroundColor: 'rgba(64, 224, 208, 0.3)',
                        borderColor: '#40E0D0',
                        borderWidth: 3,
                        pointBackgroundColor: '#ffffff',
                        pointBorderColor: '#40E0D0',
                        pointRadius: 5
                    }}]
                }},
                options: {{
                    responsive: true,
                    scales: {{
                        r: {{
                            angleLines: {{ color: 'rgba(255, 255, 255, 0.2)' }},
                            grid: {{ color: 'rgba(255, 255, 255, 0.1)' }},
                            pointLabels: {{ color: '#e6edf3', font: {{ size: 14, weight: 'bold' }} }},
                            ticks: {{ display: false, stepSize: 1 }},
                            suggestedMin: 1,
                            suggestedMax: 5
                        }}
                    }},
                    plugins: {{
                        legend: {{ labels: {{ color: '#e6edf3', font: {{ size: 14 }} }} }}
                    }}
                }}
            }});
        </script>
    </body>
    </html>
    """, height=450)

def main():
    st.set_page_config(page_title="Pyth-MBTI Psychology Detector | Selamat datang di platform MBTI Psychology Detector berbasis sistem CBR ", layout="wide", page_icon="Desain tanpa judul (1).png")
    init_db()

    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800&family=Poppins:wght@400;500;600;700&display=swap');

    /* ── Dark theme background & teks utama ── */
    html, body, .stApp, [class*="css"] {
        font-family: 'Nunito', sans-serif !important;
        font-size: 17px !important;
        line-height: 1.7 !important;
        background-color: #0d1117 !important;
        color: #e6edf3 !important;
    }

    /* ── Main content area ── */
    .main .block-container {
        background-color: #0d1117 !important;
        padding: 2rem 5rem !important;
        max-width: 1300px !important;
        margin-left: auto !important;
        margin-right: auto !important;
    }
    @media (max-width: 992px) {
        .main .block-container { padding: 2rem 1.5rem !important; }
    }

    /* ── Headings ── */
    h1 { font-family: 'Poppins', sans-serif !important; font-size: 2.4rem !important; font-weight: 700 !important; color: #40E0D0 !important; margin-bottom: 0.4em !important; }
    h2 { font-family: 'Poppins', sans-serif !important; font-size: 1.9rem !important; font-weight: 600 !important; color: #7ee8e0 !important; }
    h3 { font-family: 'Poppins', sans-serif !important; font-size: 1.5rem !important; font-weight: 600 !important; color: #e6edf3 !important; }
    h4 { font-size: 1.2rem !important; font-weight: 700 !important; color: #e6edf3 !important; }

    /* ── Semua teks biasa ── */
    p, li, span, div {
        color: #e6edf3 !important;
    }

    /* ── Sidebar ── */
    [data-testid="stSidebar"] {
        background: #0d1117 !important;
        padding: 1rem 0.5rem !important;
        min-width: 240px !important;
        border-right: 1px solid #30363d !important;
    }

    /* Styling Sidebar Toggle Button (Arrow) */
    [data-testid="stSidebarCollapseButton"] {
        color: #40E0D0 !important;
        background-color: #161b22 !important;
        border-radius: 50% !important;
        padding: 4px !important;
        margin: 5px !important;
        border: 1px solid #30363d !important;
        transition: all 0.3s ease !important;
    }
    [data-testid="stSidebarCollapseButton"]:hover {
        background-color: #40E0D0 !important;
        color: #0d1117 !important;
        transform: scale(1.1);
    }

    /* Styling Navigasi Radio di Sidebar */
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label {
        background-color: #161b22 !important;
        border: 1px solid #30363d !important;
        padding: 12px 20px !important;
        border-radius: 10px !important;
        margin-bottom: 12px !important;
        transition: all 0.3s ease !important;
        width: 100% !important;
    }
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label:hover {
        border-color: #40E0D0 !important;
        background-color: rgba(64, 224, 208, 0.05) !important;
        transform: translateX(5px);
    }
    /* Highlight saat dipilih (Streamlit menggunakan div internal untuk selection) */
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] [data-testid="stWidgetLabel"] {
        color: #e6edf3 !important;
        font-weight: 600 !important;
    }

    /* ── Tabs ── */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px !important;
        background-color: #161b22 !important;
        border-radius: 12px !important;
        padding: 6px !important;
    }
    .stTabs [data-baseweb="tab"] {
        font-size: 16px !important;
        font-weight: 600 !important;
        padding: 10px 22px !important;
        border-radius: 8px !important;
        font-family: 'Nunito', sans-serif !important;
        color: #8b949e !important;
        background: transparent !important;
    }
    .stTabs [aria-selected="true"] {
        background: #40E0D0 !important;
        color: #0d1117 !important;
    }

    /* ── Tombol ── */
    .stButton > button, .stDownloadButton > button, .stFormSubmitButton > button {
        font-family: 'Nunito', sans-serif !important;
        font-size: 16px !important;
        font-weight: 700 !important;
        padding: 0.6rem 1.6rem !important;
        border-radius: 12px !important;
        transition: all 0.2s ease !important;
        background: linear-gradient(135deg, #40E0D0, #0f3460) !important;
        color: #ffffff !important;
        border: none !important;
    }
    .stButton > button:hover, .stDownloadButton > button:hover, .stFormSubmitButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(64,224,208,0.35) !important;
        opacity: 0.92 !important;
    }

    /* ── Input, number, selectbox ── */
    .stTextInput input, .stNumberInput input {
        font-size: 16px !important;
        padding: 10px 14px !important;
        border-radius: 10px !important;
        font-family: 'Nunito', sans-serif !important;
        background-color: #161b22 !important;
        color: #e6edf3 !important;
        border: 1px solid #30363d !important;
    }
    .stTextInput input:focus, .stNumberInput input:focus {
        border-color: #40E0D0 !important;
        box-shadow: 0 0 0 2px rgba(64,224,208,0.2) !important;
    }
    .stSelectbox > div > div {
        background-color: #161b22 !important;
        color: #e6edf3 !important;
        border: 1px solid #30363d !important;
        border-radius: 10px !important;
        font-size: 16px !important;
    }

    /* ── Slider ── */
    .stSlider { padding-top: 10px !important; padding-bottom: 18px !important; }
    .stSlider label { font-size: 16px !important; font-weight: 600 !important; color: #e6edf3 !important; }
    .stSlider [data-baseweb="slider"] [role="slider"] {
        background: #40E0D0 !important;
        border: 3px solid #ffffff !important;
        width: 20px !important;
        height: 20px !important;
    }
    .stSlider [data-baseweb="slider"] div[data-testid="stSliderTrack"] > div:first-child {
        background: #30363d !important;
    }
    .stSlider [data-baseweb="slider"] div[data-testid="stSliderTrack"] > div:nth-child(2) {
        background: #40E0D0 !important;
    }

    /* ── Expander ── */
    .streamlit-expanderHeader {
        font-size: 17px !important;
        font-weight: 700 !important;
        padding: 14px 18px !important;
        border-radius: 10px !important;
        font-family: 'Nunito', sans-serif !important;
        background-color: #161b22 !important;
        color: #e6edf3 !important;
        border: 1px solid #30363d !important;
    }
    .streamlit-expanderContent {
        padding: 16px 20px !important;
        font-size: 16px !important;
        line-height: 1.8 !important;
        background-color: #0d1117 !important;
        color: #e6edf3 !important;
        border: 1px solid #30363d !important;
        border-top: none !important;
    }

    /* ── Alert boxes ── */
    .stAlert { font-size: 16px !important; padding: 14px 20px !important; border-radius: 12px !important; }
    [data-testid="stNotification"] { background-color: #161b22 !important; color: #e6edf3 !important; }

    /* ── Form container ── */
    [data-testid="stForm"] {
        padding: 24px 28px !important;
        border-radius: 16px !important;
        background: #161b22 !important;
        border: 1px solid #30363d !important;
        margin-bottom: 1.5rem !important;
    }

    /* ── Label ── */
    label, .stRadio label, .stCheckbox label {
        font-size: 16px !important;
        font-weight: 600 !important;
        font-family: 'Nunito', sans-serif !important;
        color: #e6edf3 !important;
    }

    /* ── Markdown ── */
    .stMarkdown p, .stMarkdown li, .stMarkdown span {
        font-size: 16px !important;
        line-height: 1.8 !important;
        color: #e6edf3 !important;
    }

    /* ── Dataframe ── */
    .dataframe, [data-testid="stDataFrame"] {
        font-size: 15px !important;
        background-color: #161b22 !important;
        color: #e6edf3 !important;
    }

    /* ── Spacing ── */
    .element-container { margin-bottom: 0.8rem !important; }
    </style>
    """, unsafe_allow_html=True)

    # ── SIDEBAR ──────────────────────────────────────────────────────
    st.sidebar.markdown("""
    <div style="text-align:center; padding: 10px 0 20px 0;">
        <div style="font-size: 3rem;">🧠</div>
        <div style="font-size: 1.4rem; font-weight: 800; color: #40E0D0; letter-spacing: 1px;">Pyth-MBTI</div>
        <div style="font-size: 0.85rem; color: #8b949e; margin-top: 4px;">Psychology Detector</div>
    </div>
    """, unsafe_allow_html=True)
    st.sidebar.markdown("---")

    st.sidebar.markdown("<div style='color:#8b949e; font-size:13px; font-weight:700; letter-spacing:2px; margin-bottom:8px;'>NAVIGASI</div>", unsafe_allow_html=True)
    mode = st.sidebar.radio("", ["👤 User", "🔧 Admin"])
    mode = "User" if "User" in mode else "Admin"

    st.sidebar.markdown("---")
    st.sidebar.markdown("""
    <div style="font-size:13px; color:#8b949e; line-height:1.8; padding: 0 4px;">
        <b style="color:#40E0D0;">v1.0.0</b><br>
        Dibuat dengan ❤️ menggunakan<br>
        <b>CBR (Case-Based Reasoning)</b><br>
        & <b>Streamlit</b>
    </div>
    """, unsafe_allow_html=True)

    mbti_info = get_mbti_info_db()

    if mode == "User":
        st.markdown("""
        <div style="display:flex; align-items:center; gap:16px; margin-bottom:0.2em;">
            <span style="font-size:3rem;">🧠</span>
            <div>
                <div style="font-size:2.2rem; font-weight:800; color:#40E0D0; font-family:'Poppins',sans-serif; line-height:1.1; text-align:center;">Pyth-MBTI</div>
                <div style="font-size:1.1rem; color:#8b949e; font-weight:600; text-align:center;">Psychology Detector — Powered by CBR</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("---")

        tab1, tab2, tab3, tab4, tab5 = st.tabs(["ℹ️ Info", "👤 Data Diri", "📚 Learn MBTI", "🧪 Take Test", "📊 Past Cases"])
        
        with tab1:
            st.markdown("""
            <div style="background:linear-gradient(135deg,#161b22,#0f3460); border-radius:18px; padding:32px 36px; border:1px solid #30363d; margin-bottom:24px;">
                <h2 style="color:#40E0D0; margin-bottom:8px;">Selamat Datang di Pyth-MBTI 👋</h2>
                <p style="color:#c9d1d9; font-size:17px; line-height:1.9;">
                    <b style="color:#40E0D0;">Pyth-MBTI Psychology Detector</b> adalah aplikasi analisis kepribadian berbasis
                    <b>Case-Based Reasoning (CBR)</b> yang membantu kamu mengetahui tipe kepribadian MBTI-mu secara cepat dan akurat.
                </p>
                <br>
            </div>
            """, unsafe_allow_html=True)

            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown("""
                <div style="background:#161b22; border-radius:14px; padding:8px; border:1px solid #30363d; text-align:center; height:180px;">
                    <div style="font-size:2.2rem; margin-bottom:10px;">🧪</div>
                    <div style="font-weight:800; font-size:16px; color:#40E0D0; margin-bottom:8px;">Tes Kepribadian</div>
                    <div style="color:#8b949e; font-size:14px; line-height:1.6;">4 pertanyaan slider untuk menentukan tipe MBTI-mu <br> </div>
                    <br>
                </div>
                """, unsafe_allow_html=True)
            with col2:
                st.markdown("""
                <div style="background:#161b22; border-radius:14px; padding:8px; border:1px solid #30363d; text-align:center; height:180px;">
                    <div style="font-size:2.2rem; margin-bottom:10px;">📡</div>
                    <div style="font-weight:800; font-size:16px; color:#40E0D0; margin-bottom:8px;">Algoritma CBR</div>
                    <div style="color:#8b949e; font-size:14px; line-height:1.6;">Mencocokkan jawabanmu dengan 16 prototype MBTI <br> </div>
                    <br>
                </div>
                """, unsafe_allow_html=True)
            with col3:
                st.markdown("""
                <div style="background:#161b22; border-radius:14px; padding:8px; border:1px solid #30363d; text-align:center; height:180px;">
                    <div style="font-size:2.2rem; margin-bottom:10px;">📥</div>
                    <div style="font-weight:800; font-size:16px; color:#40E0D0; margin-bottom:8px;">Download PDF</div>
                    <div style="color:#8b949e; font-size:14px; line-height:1.6;">Simpan hasil analisis kepribadianmu sebagai laporan <br> </div>
                <br>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            col4, col5, col6 = st.columns(3)
            with col4:
                st.markdown("""
                <div style="background:#161b22; border-radius:14px; padding:8px; border:1px solid #30363d; text-align:center; height:180px;">
                    <div style="font-size:2.2rem; margin-bottom:10px;">📊</div>
                    <div style="font-weight:800; font-size:16px; color:#40E0D0; margin-bottom:8px;">Radar Chart</div>
                    <div style="color:#8b949e; font-size:14px; line-height:1.6;">Visualisasi hasil dalam bentuk grafik radar interaktif <br></div>
                <br>
                </div>
                """, unsafe_allow_html=True)
            with col5:
                st.markdown("""
                <div style="background:#161b22; border-radius:14px; padding:8px; border:1px solid #30363d; text-align:center; height:180px;">
                    <div style="font-size:2.2rem; margin-bottom:10px;">📚</div>
                    <div style="font-weight:800; font-size:16px; color:#40E0D0; margin-bottom:8px;">16 Tipe MBTI</div>
                    <div style="color:#8b949e; font-size:14px; line-height:1.6;">Pelajari semua tipe kepribadian beserta kelebihan & profesinya<br></div>
                <br>
                </div>
                """, unsafe_allow_html=True)
            with col6:
                st.markdown("""
                <div style="background:#161b22; border-radius:14px; padding:8px; border:1px solid #30363d; text-align:center; height:180px;">
                    <div style="font-size:2.2rem; margin-bottom:10px;">🕓</div>
                    <div style="font-weight:800; font-size:16px; color:#40E0D0; margin-bottom:8px;">Riwayat Kasus</div>
                    <div style="color:#8b949e; font-size:14px; line-height:1.6;">Lihat kembali semua hasil tes yang pernah dilakukan <br> </div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("""
            <div style="background:#0f3460; border-radius:14px; padding:20px 28px; border:1px solid #40E0D033;">
                <b style="color:#40E0D0; font-size:16px;">🚀 Cara Mulai:</b>
                <span style="color:#c9d1d9; font-size:15px; margin-left:10px;">
                    Isi Data Diri → Ambil Tes → Lihat Hasil & Radar Chart → Download PDF Laporan
                </span><br>
            </div>
            """, unsafe_allow_html=True)
        
        with tab2:
            if 'user_data' not in st.session_state:
                with st.form("profile"):
                    nama = st.text_input("Nama Lengkap")
                    umur = st.number_input("Umur", 5, 100)
                    if st.form_submit_button("Save"):
                        st.session_state.user_data = {'nama': nama, 'umur': umur}
                        st.success("Profile saved!")
                        st.rerun()
            else:
                st.success("Profile ready!")
                st.write(st.session_state.user_data)
        
        with tab3:
            for mbti, info in MBTI_INFO.items():
                with st.expander(mbti):
                    st.markdown(f"**{info['nama']}**")
                    st.markdown(f"*Kelebihan:* {info['kelebihan']}")
                    st.markdown(f"*Profesi:* {info['profesi']}")
        
        with tab4:
            if 'user_data' not in st.session_state:
                st.warning("Complete profile first!")
            else:
                with st.form("test"):
                    col1, col2 = st.columns(2)
                    with col1:
                        q1 = st.slider("1. Fokus Energi: Bagaimana Anda mengisi ulang energi? (1: Menghabiskan waktu sendiri/Introversi → 5: Berinteraksi dengan orang lain/Ekstraversi)", 1, 5, 3)
                        q3 = st.slider("3. Pengambilan Keputusan: Apa yang lebih Anda utamakan? (1: Logika objektif dan kebenaran faktual → 5: Perasaan, empati, dan nilai kemanusiaan)", 1, 5, 3)
                    with col2:
                        q2 = st.slider("2. Cara Memproses Informasi: Mana yang lebih menarik bagi Anda? (1: Fakta nyata dan detail praktis → 5: Ide abstrak, imajinasi, dan kemungkinan masa depan)", 1, 5, 3)
                        q4 = st.slider("4. Gaya Hidup: Bagaimana Anda mengatur keseharian? (1: Terencana, terstruktur, dan tepat waktu → 5: Spontan, fleksibel, dan menyukai kebebasan)", 1, 5, 3)
                    if st.form_submit_button("Analyze"):
                        answers = [q1, q2, q3, q4]
                        result = run_cbr(answers)
                        
                        # Save
                        conn = get_db_connection()
                        c = conn.cursor()
                        c.execute("INSERT INTO users (nama, umur, q1, q2, q3, q4, mbti_result) VALUES (%s,%s,%s,%s,%s,%s,%s)",
                                (st.session_state.user_data['nama'], st.session_state.user_data['umur'], *answers, result))
                        conn.commit()
                        c.close()
                        
                        st.session_state.result = {'mbti': result, 'answers': answers}
                        st.rerun()
                
                if 'result' in st.session_state:
                    r = st.session_state.result
                    info = mbti_info[r['mbti']]
                    
                    # --- HEADER HASIL (HERO SECTION) ---
                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, #161b22 0%, #0f3460 100%); padding: 40px; border-radius: 20px; border: 2px solid #40E0D0; text-align: center; margin-top: 20px; margin-bottom: 30px; max-width: 1100px; margin-left: auto; margin-right: auto;">
                        <p style="color: #40E0D0; font-size: 1.2rem; font-weight: 700; text-transform: uppercase; margin-bottom: 5px; letter-spacing: 2px;">Tipe Kepribadian Anda Adalah</p>
                        <h1 style="margin:0; font-size: 5rem; color: #ffffff; line-height: 1;">{r['mbti']}</h1>
                        <h2 style="margin:0; color: #40E0D0; font-size: 2rem; font-weight: 500;">{info['nama']}</h2>
                    </div>
                    """, unsafe_allow_html=True)

                    # --- GRID INFORMASI ---
                    c1, c2 = st.columns(2)
                    with c1:
                        st.markdown("### 🌟 Kelebihan Utama")
                        st.info(info['kelebihan'])
                        
                        st.markdown("### 💼 Profesi yang Disarankan")
                        st.success(info['profesi'])

                    with c2:
                        st.markdown("### ⚠️ Area Pengembangan")
                        st.warning(info['kekurangan'])
                        
                        st.markdown("### 💡 Nasihat Untukmu")
                        st.info(info['nasihat'])

                    st.markdown("---")
                    
                    # --- VISUALISASI GRAFIK ---
                    col_left, col_right = st.columns([1, 1.2])
                    with col_left:
                        st.subheader("📊 Grafik Radar Karakter")
                        st.write("Grafik ini menunjukkan kecenderungan skor Anda pada 4 dimensi utama MBTI berdasarkan algoritma CBR.")
                        pdf_bytes = generate_pdf_report(st.session_state.user_data['nama'], st.session_state.user_data['umur'], r['mbti'], info, r['answers'])
                        st.download_button("📥 Download Laporan Lengkap (PDF)", pdf_bytes, f"Hasil_MBTI_{st.session_state.user_data['nama']}.pdf", "application/pdf", use_container_width=True)
                    
                    with col_right:
                        show_radar_chart(r['answers'], r['mbti'])

        
        with tab5:
            st.header("📊 Previous Cases with Radar Charts")
            conn = get_db_connection()
            df = pd.read_sql("SELECT * FROM users ORDER BY tanggal DESC LIMIT 20", conn)
            conn.close()
            
            if df.empty:
                st.info("No data yet.")
            else:
                for idx, row in df.iterrows():
                    with st.expander(f"Case #{row['id']}: {row['nama']} ({row['mbti_result']}, Age {row['umur']})"):
                        st.json({'q1(E/I)': row['q1'], 'q2(S/N)': row['q2'], 'q3(T/F)': row['q3'], 'q4(J/P)': row['q4']})
                        
                        # Show radar chart
                        show_radar_chart([row['q1'], row['q2'], row['q3'], row['q4']], row['mbti_result'])
                        
                        # PDF download for this case
                        info = mbti_info[row['mbti_result']]
                        pdf_bytes = generate_pdf_report(row['nama'], row['umur'], row['mbti_result'], info, [row['q1'], row['q2'], row['q3'], row['q4']])
                        st.download_button(
                            label=f"📥 Download {row['nama']}'s Report",
                            data=pdf_bytes,
                            file_name=f"MBTI_{row['mbti_result']}_{row['nama']}.pdf",
                            mime="application/pdf",
                            key=f"dl_hist_{row['id']}"
                        )
                st.dataframe(df[['nama', 'mbti_result', 'tanggal']])
    
    elif mode == "Admin":
        # ── LOGIN ADMIN ───────────────────────────────────────────────
        ADMIN_USERNAME = "Edward_James"
        ADMIN_PASSWORD = "mentawai01"

        if 'admin_logged_in' not in st.session_state:
            st.session_state.admin_logged_in = False

        if not st.session_state.admin_logged_in:
            st.title("🔐 Admin Login")
            st.markdown("Masukkan kredensial untuk mengakses panel admin.")
            with st.form("admin_login"):
                username = st.text_input("👤 Username")
                password = st.text_input("🔑 Password", type="password")
                if st.form_submit_button("🚀 Masuk"):
                    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
                        st.session_state.admin_logged_in = True
                        st.success("Login berhasil! Selamat datang, Admin.")
                        st.rerun()
                    else:
                        st.error("❌ Username atau password salah!")
            st.stop()

        # ── Tombol Logout di Sidebar ──────────────────────────────────
        st.title("🔧 Admin Panel")
        if st.sidebar.button("🚪 Logout Admin"):
            st.session_state.admin_logged_in = False
            st.rerun()

        admin_tab1, admin_tab2, admin_tab3, admin_tab4 = st.tabs([
            "📋 Data User", "🗑️ Hapus Data", "✏️ Edit Case Base", "📊 Grafik & Statistik"
        ])

        # ── TAB 1: Lihat semua data user ──────────────────────────────
        with admin_tab1:
            st.subheader("Semua Data User")
            conn = get_db_connection()
            df_users = pd.read_sql("SELECT * FROM users ORDER BY tanggal DESC", conn)
            conn.close()

            if df_users.empty:
                st.info("Belum ada data user.")
            else:
                st.dataframe(df_users, use_container_width=True)

                # Export CSV
                csv_data = df_users.to_csv(index=False).encode("utf-8")
                st.download_button("📥 Export CSV", csv_data, "data_users.csv", "text/csv")

                # Export Excel
                import io
                excel_buffer = io.BytesIO()
                with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
                    df_users.to_excel(writer, index=False, sheet_name="Users")
                excel_data = excel_buffer.getvalue()
                st.download_button("📥 Export Excel", excel_data, "data_users.xlsx",
                                   "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

        # ── TAB 2: Hapus data user ────────────────────────────────────
        with admin_tab2:
            st.subheader("Hapus Data User")
            conn = get_db_connection()
            df_del = pd.read_sql("SELECT id, nama, mbti_result, tanggal FROM users ORDER BY tanggal DESC", conn)
            conn.close()

            if df_del.empty:
                st.info("Tidak ada data untuk dihapus.")
            else:
                st.dataframe(df_del, use_container_width=True)

                col_a, col_b = st.columns(2)
                with col_a:
                    del_id = st.number_input("Hapus berdasarkan ID", min_value=1, step=1)
                    if st.button("🗑️ Hapus ID ini"):
                        conn = get_db_connection()
                        c = conn.cursor()
                        c.execute("DELETE FROM users WHERE id = %s", (int(del_id),))
                        conn.commit()
                        c.close()
                        st.success(f"Data ID {del_id} berhasil dihapus!")
                        st.rerun()
                with col_b:
                    if st.button("⚠️ Hapus SEMUA Data User", type="primary"):
                        conn = get_db_connection()
                        c = conn.cursor()
                        c.execute("DELETE FROM users")
                        conn.commit()
                        c.close()
                        st.success("Semua data user berhasil dihapus!")
                        st.rerun()

        # ── TAB 3: Edit Case Base ─────────────────────────────────────
        with admin_tab3:
            st.subheader("📝 Edit Penjelasan & Profesi MBTI")
            st.info("Gunakan panel ini untuk memperbarui konten narasi, definisi, dan rekomendasi profesi untuk setiap tipe MBTI.")

            st.markdown("---")
            edit_mbti = st.selectbox("Pilih Tipe MBTI untuk Diedit", list(mbti_info.keys()))
            data = mbti_info[edit_mbti]

            with st.form("edit_mbti_content_form"):
                new_nama = st.text_input("Nama / Alias (Contoh: Arsitek)", data['nama'])
                new_definisi = st.text_area("Definisi Lengkap", data.get('definisi', ''), height=200)
                new_kelebihan = st.text_area("Kelebihan Utama", data['kelebihan'], height=120)
                new_kekurangan = st.text_area("Kekurangan / Area Pengembangan", data.get('kekurangan', ''), height=120)
                new_profesi = st.text_area("Daftar Profesi Disarankan", data['profesi'], height=100)
                new_nasihat = st.text_area("Nasihat Pengembangan Diri", data['nasihat'], height=120)

                if st.form_submit_button("💾 Simpan Perubahan"):
                    conn = get_db_connection()
                    c = conn.cursor()
                    c.execute("""
                        UPDATE mbti_info 
                        SET nama=%s, definisi=%s, kelebihan=%s, kekurangan=%s, profesi=%s, nasihat=%s 
                        WHERE mbti_type=%s
                    """, (new_nama, new_definisi, new_kelebihan, new_kekurangan, new_profesi, new_nasihat, edit_mbti))
                    conn.commit()
                    c.close()
                    conn.close()
                    st.success(f"Konten {edit_mbti} ({new_nama}) berhasil diperbarui!")
                    st.rerun()

        # ── TAB 4: Grafik & Statistik ─────────────────────────────────
        with admin_tab4:
            st.subheader("📊 Statistik Distribusi MBTI")
            conn = get_db_connection()
            df_stat = pd.read_sql("SELECT mbti_result FROM users", conn)
            conn.close()

            if df_stat.empty:
                st.info("Belum ada data untuk ditampilkan.")
            else:
                count_df = df_stat['mbti_result'].value_counts().reset_index()
                count_df.columns = ['MBTI', 'Jumlah']

                # Pastikan semua 16 tipe muncul meski 0
                all_types = list(mbti_info.keys())
                count_df = count_df.set_index('MBTI').reindex(all_types, fill_value=0).reset_index()
                count_df.columns = ['MBTI', 'Jumlah']

                labels = count_df['MBTI'].tolist()
                values = count_df['Jumlah'].tolist()

                # 1. Bar Chart (Histogram)
                st.markdown("#### 📊 Bar Chart — Jumlah per Tipe MBTI")
                components.html(f"""
<!DOCTYPE html><html><body style="background:transparent">
<canvas id="bar" width="800" height="350"></canvas>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script>
new Chart(document.getElementById('bar'), {{
  type: 'bar',
  data: {{
    labels: {labels},
    datasets: [{{
      label: 'Jumlah',
      data: {values},
      backgroundColor: [
        '#FF6384','#36A2EB','#FFCE56','#4BC0C0','#9966FF','#FF9F40',
        '#FF6384','#36A2EB','#FFCE56','#4BC0C0','#9966FF','#FF9F40',
        '#C9CBCF','#7BC8A4','#F4A261','#E76F51'
      ]
    }}]
  }},
  options: {{
    responsive: false,
    plugins: {{ legend: {{ display: false }} }},
    scales: {{ y: {{ beginAtZero: true, ticks: {{ stepSize: 1 }} }} }}
  }}
}});
</script></body></html>
                """, height=380)

                # 2. Pie Chart
                st.markdown("#### 🥧 Pie Chart — Proporsi MBTI")
                components.html(f"""
<!DOCTYPE html><html><body style="background:transparent">
<canvas id="pie" width="500" height="400"></canvas>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script>
new Chart(document.getElementById('pie'), {{
  type: 'pie',
  data: {{
    labels: {labels},
    datasets: [{{
      data: {values},
      backgroundColor: [
        '#FF6384','#36A2EB','#FFCE56','#4BC0C0','#9966FF','#FF9F40',
        '#FF6384','#36A2EB','#FFCE56','#4BC0C0','#9966FF','#FF9F40',
        '#C9CBCF','#7BC8A4','#F4A261','#E76F51'
      ]
    }}]
  }},
  options: {{ responsive: false }}
}});
</script></body></html>
                """, height=430)

                # 3. Radar / Polygon Chart
                st.markdown("#### 🕸️ Radar Chart — Distribusi 16 Tipe MBTI")
                components.html(f"""
<!DOCTYPE html><html><body style="background:transparent">
<canvas id="radar" width="500" height="500"></canvas>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script>
new Chart(document.getElementById('radar'), {{
  type: 'radar',
  data: {{
    labels: {labels},
    datasets: [{{
      label: 'Jumlah Kepribadian',
      data: {values},
      backgroundColor: 'rgba(64,224,208,0.2)',
      borderColor: '#40E0D0',
      pointBackgroundColor: '#40E0D0'
    }}]
  }},
  options: {{
    responsive: false,
    scales: {{ r: {{ beginAtZero: true, ticks: {{ stepSize: 1 }} }} }}
  }}
}});
</script></body></html>
                """, height=530)

                # 4. Tabel Ringkasan
                st.markdown("#### 📋 Tabel Ringkasan")
                st.dataframe(count_df.sort_values("Jumlah", ascending=False), use_container_width=True)

if __name__ == "__main__":
    main()
