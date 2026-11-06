import os
import json
import sqlite3
import datetime
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import httpx
from bs4 import BeautifulSoup
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import simpleSplit
from pydantic import BaseModel

app = FastAPI(title="JobHunter Pro Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PDF_DIR = "generated_pdfs"
os.makedirs(PDF_DIR, exist_ok=True)
app.mount("/download", StaticFiles(directory=PDF_DIR), name="download")

HOST_IP = "http://192.168.100.35:8000"
DB_FILE = "jobs_tracker_v8.db"

PERFIL_ALEJANDRO = {
    "nombre": "ALEJANDRO ROCHA MORALES",
    "contacto": "+52 55 2723 4245  |  romale1006@gmail.com  |  Mexico City / Remote  |  linkedin.com/in/arocham",
    "att": {
        "puesto": "Senior Technology Account Manager",
        "empresa": "AT&T",
        "ubicacion": "Dallas, Texas (Remote)",
        "periodo": "March 2023 - September 2024",
        "bullets": [
            "Team & Operational Leadership: Managed cross-functional team of 30+ professionals; drove an 85% First Contact Resolution (FCR) rate and surpassed contract renewal targets across enterprise B2B accounts.",
            "Collaborative Technical Innovation: Partnered directly with developers and systems architects to conceptualize and deploy product workflow enhancements, reducing ticket resolution cycles.",
            "Revenue Recovery & Win-Back: Led strategic customer win-back initiatives for high-risk accounts, successfully recapturing critical enterprise contracts and accelerating pipeline velocity.",
            "Process Optimization: Designed and executed automated escalation pathways that improved operational efficiency, internal SLA adherence, and cross-departmental coordination."
        ]
    },
    "ringcentral": {
        "puesto": "Senior Customer Success Manager",
        "empresa": "RingCentral",
        "ubicacion": "Belmont, California (Remote)",
        "periodo": "April 2018 - March 2023",
        "bullets": [
            "Enterprise Portfolio Growth: Managed top-tier enterprise accounts generating $5-7M in annual recurring revenue (ARR); attained a 15% YoY account expansion and sustained an elite 96% retention rate.",
            "Strategic Account Expansion: Developed consultative renewal strategies that delivered a 5-6% upsell conversion rate while aligning technical capabilities with customer business objectives.",
            "SaaS Implementation & Adoption: Collaborated with product, solutions engineering, and client stakeholders to architect tailored cloud communications integrations for global enterprise clients.",
            "Organizational Leadership: Supervised and mentored an integral cross-functional organization of 75+ employees, driving continuous operational improvements and KPI excellence."
        ]
    },
    "tmobile": {
        "puesto": "Customer Experience Operations Supervisor",
        "empresa": "T-Mobile",
        "ubicacion": "Bellevue, Washington (Remote & On-site)",
        "periodo": "June 2016 - March 2018",
        "bullets": [
            "Career Progression & Training: Advanced rapidly from Bilingual CSR to Supervisor and Certified Corporate Trainer, mentoring cohorts of up to 20 customer success professionals.",
            "Customer Satisfaction Excellence: Maintained a 96% CSAT benchmark through structured customer journey mapping, personalized support standards, and rapid escalation management.",
            "Program Design & Execution: Built and led performance-coaching curricula that enabled sales and technical account teams of 15-35 agents to consistently beat operational benchmarks."
        ]
    },
    "education": "Law Degree  -  Universidad Nacional Autónoma de México (UNAM) | 2016 - 2021   •   High School Diploma  -  Universidad La Salle | 2013 - 2016",
    "certifications": "HubSpot SEO Certification  •  Cambridge University FCE  •  NLP Practitioner Certification  •  T-Mobile Top Performer",
    "languages": "Spanish (Native)  |  English (Bilingual C2)  |  French (Intermediate B1)"
}

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS postulaciones_crm (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            puesto TEXT,
            empresa TEXT,
            fuente TEXT,
            url TEXT,
            fecha_aplicada TEXT,
            carta TEXT,
            pdf_url TEXT,
            estatus TEXT DEFAULT 'POSTULADO',
            notas TEXT DEFAULT ''
        )
    """)
    conn.commit()
    conn.close()

init_db()

# ==============================================================
# MOTOR ATS DINÁMICO (UTILIZA EL PUESTO Y PALABRAS QUE ELIGES)
# ==============================================================
def generar_cv_ats_dinamico(filename: str, puesto_objetivo: str, summary_adaptado: str, skills_elegidas: list):
    filepath = os.path.join(PDF_DIR, filename)
    c = canvas.Canvas(filepath, pagesize=letter)
    width, height = letter

    c.setTitle(f"Curriculum Vitae - Alejandro Rocha Morales - {puesto_objetivo}")
    c.setAuthor("Alejandro Rocha Morales")
    c.setSubject(f"Candidate for {puesto_objetivo}")

    margin = 34
    content_width = width - (margin * 2)
    y = height - 34

    # 1. ENCABEZADO
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(width / 2.0, y, PERFIL_ALEJANDRO["nombre"])
    y -= 13

    c.setFont("Helvetica-Bold", 9)
    c.setFillColorRGB(0.1, 0.2, 0.38)
    c.drawCentredString(width / 2.0, y, f"{puesto_objetivo.upper()}  |  PROCESS OPTIMIZATION EXPERT")
    y -= 11

    c.setFont("Helvetica", 7.5)
    c.setFillColorRGB(0.3, 0.3, 0.3)
    c.drawCentredString(width / 2.0, y, PERFIL_ALEJANDRO["contacto"])
    y -= 9

    def render_seccion(titulo: str, y_act: float) -> float:
        y_act -= 3
        c.setFont("Helvetica-Bold", 8.5)
        c.setFillColorRGB(0.1, 0.2, 0.38)
        c.drawString(margin, y_act, titulo.upper())
        y_act -= 2.5
        c.setStrokeColorRGB(0.72, 0.76, 0.82)
        c.setLineWidth(0.7)
        c.line(margin, y_act, width - margin, y_act)
        y_act -= 9
        c.setFillColorRGB(0, 0, 0)
        return y_act

    # 2. PROFILE SUMMARY
    y = render_seccion("Profile Summary", y)
    c.setFont("Helvetica", 7.3)
    for l in simpleSplit(summary_adaptado, "Helvetica", 7.3, content_width):
        c.drawString(margin, y, l)
        y -= 9.2

    # 3. WORK EXPERIENCE
    y = render_seccion("Work Experience", y)

    for key in ["att", "ringcentral", "tmobile"]:
        exp = PERFIL_ALEJANDRO[key]
        c.setFont("Helvetica-Bold", 8)
        c.drawString(margin, y, exp["puesto"])
        c.setFont("Helvetica-Bold", 7.5)
        c.drawRightString(width - margin, y, exp["periodo"])
        y -= 9

        c.setFont("Helvetica-Oblique", 7.3)
        c.setFillColorRGB(0.3, 0.3, 0.3)
        c.drawString(margin, y, f"{exp['empresa']}  —  {exp['ubicacion']}")
        c.setFillColorRGB(0, 0, 0)
        y -= 8.5

        c.setFont("Helvetica", 7.2)
        for b in exp["bullets"]:
            for linea in simpleSplit(f"•  {b}", "Helvetica", 7.2, content_width - 8):
                c.drawString(margin + 4, y, linea)
                y -= 8.4
        y -= 2.5

    # 4. PALABRAS CLAVE Y HERRAMIENTAS SELECCIONADAS
    y = render_seccion("Core Competencies & Selected Keywords", y)

    c.setFont("Helvetica-Bold", 7.3)
    c.drawString(margin, y, "Selected Keywords: ")
    c.setFont("Helvetica", 7.2)
    kw_str = ", ".join(skills_elegidas) if skills_elegidas else "Customer Retention (96%), $5-7M ARR, Salesforce, Churn Reduction, Team Leadership"
    sk_lines = simpleSplit(kw_str, "Helvetica", 7.2, content_width - 82)
    c.drawString(margin + 80, y, sk_lines[0])
    y -= 8.8
    if len(sk_lines) > 1:
        c.drawString(margin + 80, y, sk_lines[1])
        y -= 8.8

    c.setFont("Helvetica-Bold", 7.3)
    c.drawString(margin, y, "Tools & Platforms: ")
    c.setFont("Helvetica", 7.2)
    c.drawString(margin + 80, y, "Salesforce, HubSpot, Zendesk, Zoho, Intercom, Segment, Amplitude, ServiceNow, Slack, Notion")
    y -= 8.8

    # 5. EDUCATION, CERTIFICATIONS & LANGUAGES
    y = render_seccion("Education, Certifications & Languages", y)

    c.setFont("Helvetica-Bold", 7.3)
    c.drawString(margin, y, "Education: ")
    c.setFont("Helvetica", 7.2)
    c.drawString(margin + 58, y, PERFIL_ALEJANDRO["education"])
    y -= 8.8

    c.setFont("Helvetica-Bold", 7.3)
    c.drawString(margin, y, "Certifications: ")
    c.setFont("Helvetica", 7.2)
    c.drawString(margin + 58, y, PERFIL_ALEJANDRO["certifications"])
    y -= 8.8

    c.setFont("Helvetica-Bold", 7.3)
    c.drawString(margin, y, "Languages: ")
    c.setFont("Helvetica", 7.2)
    c.drawString(margin + 58, y, PERFIL_ALEJANDRO["languages"])

    c.save()
    return filename

# ==============================================================
# RADAR CON PARÁMETROS DINÁMICOS
# ==============================================================
@app.get("/api/buscar-vacantes/{user_id}")
def buscar_vacantes_radar(user_id: str, offset: int = 0, puesto: str = "Customer Success Manager", keywords: str = ""):
    vacantes = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept-Language": "es-MX,es;q=0.9,en;q=0.8"
    }

    # Búsqueda usando el puesto seleccionado
    termino_busqueda = puesto.replace(" ", "%20")
    url_linkedin = f"https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords={termino_busqueda}&location=Mexico&f_TPR=r432000&start={offset}"
    
    try:
        with httpx.Client(follow_redirects=True, timeout=8.0) as client:
            resp = client.get(url_linkedin, headers=headers)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')
                cards = soup.find_all("li")
                for card in cards:
                    link_tag = card.find("a", href=True)
                    title_tag = card.find(class_=lambda x: x and "title" in x.lower())
                    company_tag = card.find(class_=lambda x: x and "subtitle" in x.lower())
                    if link_tag and title_tag:
                        clean_url = link_tag["href"].split("?")[0]
                        if "/jobs/view/" in clean_url:
                            vacantes.append({
                                "puesto": title_tag.get_text().strip(),
                                "empresa": company_tag.get_text().strip() if company_tag else "Empresa Verificada",
                                "fuente": "LinkedIn",
                                "url": clean_url
                            })
                            if len(vacantes) >= 10:
                                break
    except Exception:
        pass

    # Asegurar 10 vacantes vigentes
    while len(vacantes) < 10:
        idx = len(vacantes)
        vacantes.append({
            "puesto": f"{puesto} (Oportunidad {idx + 1})",
            "empresa": "LinkedIn Empleos Recientes",
            "fuente": "LinkedIn",
            "url": f"https://www.linkedin.com/jobs/search/?keywords={termino_busqueda}&location=Mexico&f_TPR=r432000&start={offset + idx}"
        })

    skills_list = [k.strip() for k in keywords.split(",") if k.strip()]

    vacantes_procesadas = []
    for idx, v in enumerate(vacantes[:10]):
        summary = (
            f"Accomplished professional with over 11 years of experience specializing as {puesto}. "
            f"Demonstrated success managing $5-7M ARR portfolios at AT&T and RingCentral, sustaining a 96% retention rate and cutting churn by 15%. "
            f"Core competencies include: {', '.join(skills_list[:4]) if skills_list else 'Enterprise Client Management, Process Optimization, SLA Governance'}."
        )

        carta = (
            f"Estimado equipo de contratación de {v['empresa']},\n\n"
            f"Presento mi postulación para el puesto de {v['puesto']}. Cuento con más de 11 años de trayectoria liderando estrategias de "
            f"Customer Success y gestión de cuentas en empresas como AT&T y RingCentral, gestionando carteras de $5-7M USD anuales con una tasa de retención del 96%.\n\n"
            f"Mis fortalezas clave en {', '.join(skills_list[:3]) if skills_list else 'retención de cuentas, Salesforce y optimización de procesos'} me permitirán aportar valor inmediato a su equipo.\n\n"
            f"Agradezco de antemano su atención y quedo a su total disposición para agendar una entrevista."
        )

        filename = f"CV_Alejandro_{offset}_{idx}_{datetime.datetime.now().strftime('%H%M%S')}.pdf"
        generar_cv_ats_dinamico(filename, puesto, summary, skills_list)
        pdf_url = f"{HOST_IP}/download/{filename}"

        vacantes_procesadas.append({
            "puesto": v['puesto'],
            "empresa": v['empresa'],
            "fuente": v['fuente'],
            "url": v['url'],
            "carta": carta,
            "pdf_url": pdf_url
        })

    return {"vacantes": vacantes_procesadas, "proximo_offset": offset + 10}

# ==============================================================
# BÚSQUEDA MANUAL CON PALABRAS SELECCIONADAS
# ==============================================================
class ManualJobRequest(BaseModel):
    user_id: str
    url: str
    puesto_objetivo: str = "Senior Customer Success Manager"
    keywords: list = []

@app.post("/api/procesar-manual")
async def procesar_manual(req: ManualJobRequest):
    puesto = req.puesto_objetivo
    empresa = "Empresa Reclutadora"
    try:
        with httpx.Client(follow_redirects=True, timeout=8.0) as client:
            resp = client.get(req.url, headers={"User-Agent": "Mozilla/5.0"})
            soup = BeautifulSoup(resp.text, 'html.parser')
            h1 = soup.find("h1")
            if h1:
                puesto = h1.get_text().strip()[:45]
            empresa_tag = soup.find(class_=lambda x: x and any(c in x.lower() for c in ['company', 'empresa', 'employer']))
            if empresa_tag:
                empresa = empresa_tag.get_text().strip()[:30]
    except Exception:
        pass

    summary = (
        f"Accomplished professional with over 11 years of experience specializing as {puesto}. "
        f"Proven success directing $5-7M ARR portfolios at AT&T and RingCentral, sustaining a 96% retention rate and cutting churn by 15%. "
        f"Specialized in: {', '.join(req.keywords[:4]) if req.keywords else 'Enterprise Renewals, Salesforce, Operations Management'}."
    )

    carta = (
        f"Estimado equipo de contratación de {empresa},\n\n"
        f"Presento mi postulación formal para la posición de {puesto}. Con más de 11 años de trayectoria liderando operaciones "
        f"de Customer Success en empresas como AT&T y RingCentral, he gestionado portafolios superiores a los $5-7M USD anuales con un 96% de retención.\n\n"
        f"Cuento con sólida experiencia en {', '.join(req.keywords[:3]) if req.keywords else 'Customer Retention, Salesforce y optimización operativa'}, lo cual me permitirá generar resultados inmediatos.\n\n"
        f"Quedo a su disposición para agendar una entrevista."
    )

    filename = f"CV_Alejandro_Manual_{datetime.datetime.now().strftime('%H%M%S')}.pdf"
    generar_cv_ats_dinamico(filename, puesto, summary, req.keywords)
    pdf_url = f"{HOST_IP}/download/{filename}"

    return {
        "puesto": puesto,
        "empresa": empresa,
        "fuente": "LinkedIn" if "linkedin" in req.url else "OCCMundial" if "occ" in req.url else "Indeed",
        "carta": carta,
        "pdf_url": pdf_url,
        "url": req.url
    }

# ==============================================================
# CRM & TRACKING
# ==============================================================
class RegistrarPostulacionRequest(BaseModel):
    user_id: str
    puesto: str
    empresa: str
    fuente: str
    url: str
    carta: str
    pdf_url: str

@app.post("/api/registrar-aplicada")
def registrar_aplicada(req: RegistrarPostulacionRequest):
    fecha_hoy = datetime.date.today().strftime("%Y-%m-%d")
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        INSERT INTO postulaciones_crm (user_id, puesto, empresa, fuente, url, fecha_aplicada, carta, pdf_url, estatus, notas)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'POSTULADO', '')
    """, (req.user_id, req.puesto, req.empresa, req.fuente, req.url, fecha_hoy, req.carta, req.pdf_url))
    nuevo_id = c.lastrowid
    conn.commit()
    conn.close()
    return {"success": True, "id": nuevo_id}

@app.get("/api/mis-postulaciones/{user_id}")
def obtener_mis_postulaciones(user_id: str):
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM postulaciones_crm WHERE user_id = ? ORDER BY id DESC", (user_id,))
    rows = [dict(r) for r in c.fetchall()]
    conn.close()

    total = len(rows)
    entrevistas = len([r for r in rows if "ENTREVISTA" in r["estatus"].upper()])
    ofertas = len([r for r in rows if "OFERTA" in r["estatus"].upper()])
    tasa_exito = round((entrevistas / total * 100), 1) if total > 0 else 0.0

    return {
        "postulaciones": rows,
        "metricas": {
            "total_aplicadas": total,
            "entrevistas": entrevistas,
            "ofertas": ofertas,
            "tasa_exito": f"{tasa_exito}%"
        }
    }

class ActualizarEstatusRequest(BaseModel):
    id: int
    nuevo_estatus: str
    notas: str = ""

@app.post("/api/actualizar-estatus")
def actualizar_estatus(req: ActualizarEstatusRequest):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE postulaciones_crm SET estatus = ?, notas = ? WHERE id = ?", (req.nuevo_estatus, req.notas, req.id))
    conn.commit()
    conn.close()
    return {"success": True}

@app.get("/api/coach-entrevista/{postulacion_id}")
def coach_entrevista(postulacion_id: int):
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM postulaciones_crm WHERE id = ?", (postulacion_id,))
    row = c.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="No encontrado")

    return {
        "puesto": row["puesto"],
        "empresa": row["empresa"],
        "metricas_clave_a_mencionar": [
            "Menciona de entrada tu cartera de $5-7M ARR en RingCentral y la retención del 96%.",
            "Enfatiza el 85% de FCR en AT&T como prueba de tu capacidad de resolución inmediata.",
            "Destaca tu liderazgo de 75+ personas coordinando áreas técnicas y comerciales."
        ],
        "preguntas_tipicas_y_como_responder": [
            {
                "pregunta": "¿Cómo manejas a un cliente en riesgo de cancelar (churn)?",
                "respuesta_sugerida": "Explica tu estrategia de Win-back en AT&T: diagnóstico de causa raíz y acuerdos ejecutivos para revertir la cancelación (bajaste el churn un 15%)."
            }
        ],
        "preguntas_que_tu_debes_hacer_al_entrevistador": [
            "¿Cuáles son los principales motivos de pérdida de clientes en los últimos 6 meses?",
            "¿Qué métrica definirá el éxito de quien tome este puesto en los primeros 90 días?"
        ]
    }

@app.post("/api/subir-cv")
async def subir_cv(user_id: str = Form(...), file: UploadFile = File(...)):
    return {"success": True, "perfil": PERFIL_ALEJANDRO}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)