
import streamlit as st
import pandas as pd
import numpy as np
import requests
import plotly.express as px
from pathlib import Path
import unicodedata
import re
from datetime import datetime

# ============================================================
# CONTROLE DE ORDENS DE SERVIÇO — STREAMLIT + PLOTLY
# Mantém as regras e informações do painel HTML original.
# ============================================================

st.set_page_config(
    page_title="Controle de Ordens de Serviço — 2026",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -----------------------------
# Configuração
# -----------------------------
SUPABASE_URL = "https://kfjjngcncrqcezyyumvi.supabase.co"
SUPABASE_KEY = "sb_publishable_tHdykHZugn2CzR3ago9bKg__KsZafC6"
SUPABASE_TABLE = "ordens_servico"

RUAS_SUPABASE_URL = "https://ypykiczrahhjepwojaim.supabase.co"
RUAS_SUPABASE_KEY = "sb_publishable_7cjD1eDSihnnTR70q-3Ytg_diHgiKMy"
RUAS_SUPABASE_TABLE = "ruas"

PAGE_SIZE = 1000

BAIRROS_EXCLUIDOS = {
    "OUROFINOPAULISTA", "ITRAPOA", "SOMMA",
    "CASAVERMELHA", "POUSOALEGRE", "KM4"
}

MONTH_NAMES = [
    "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
]

ODS_MAP = {
    "ODS 12": "Consumo e produção responsáveis",
    "ODS 11": "Cidades e comunidades sustentáveis",
    "ODS 6": "Água potável e saneamento",
    "ODS 15": "Vida terrestre",
}

# -----------------------------
# Visual
# -----------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@500;600;700;800;900&display=swap');

html, body, [class*="css"], button, input, textarea, select,
[data-testid="stMarkdownContainer"], [data-testid="stMetricLabel"],
[data-testid="stMetricValue"] {
    font-family: 'Montserrat', Arial, Helvetica, sans-serif !important;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
    text-rendering: geometricPrecision;
}

[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] li,
[data-testid="stMarkdownContainer"] span,
[data-testid="stMarkdownContainer"] label {
    font-weight: 600;
}

[data-testid="stMetricLabel"] p {
    font-weight: 800 !important;
    font-size: .78rem !important;
}

[data-testid="stMetricValue"] {
    font-weight: 900 !important;
    font-size: 1.65rem !important;
    line-height: 1.15 !important;
}

[data-testid="stSelectbox"] label,
[data-testid="stTextInput"] label,
[data-testid="stMultiSelect"] label {
    font-weight: 800 !important;
}

[data-testid="stSelectbox"] div[data-baseweb="select"] > div,
[data-testid="stTextInput"] input {
    font-weight: 700 !important;
}

body { font-weight: 500; }

[data-testid="stAppViewContainer"] {
    background: #f4f6f8;
}

[data-testid="stHeader"] {
    background: rgba(0,0,0,0);
}

.block-container {
    padding-top: 1rem;
    padding-bottom: 3rem;
    max-width: 1800px;
}

.hero {
    background: #ffffff;
    border: 1px solid #e2e8ee;
    border-radius: 18px;
    padding: 10px 16px 4px 16px;
    box-shadow: 0 8px 30px rgba(20,40,60,.08);
    margin-bottom: 14px;
}

.hero img {
    width: 100%;
    max-height: 220px;
    object-fit: contain;
    border-radius: 12px;
}

.title-box {
    background: linear-gradient(135deg, #0b3766, #124f91);
    color: white;
    border-radius: 16px;
    padding: 18px 22px;
    margin-bottom: 14px;
    box-shadow: 0 8px 24px rgba(8,49,91,.18);
}

.title-box h1 {
    margin: 0;
    font-size: 1.55rem;
    font-weight: 900;
    letter-spacing: .2px;
}

.title-box p {
    margin: 5px 0 0;
    opacity: .96;
    font-size: .84rem;
    font-weight: 600;
}

.section {
    font-size: 1.08rem;
    font-weight: 900;
    color: #123b63;
    margin: 18px 0 9px;
}

div[data-testid="stMetric"] {
    background: #ffffff;
    border: 1px solid #e0e7ee;
    border-radius: 14px;
    padding: 12px 14px;
    box-shadow: 0 4px 15px rgba(20,40,60,.05);
}

div[data-testid="stMetricLabel"] {
    font-weight: 800;
}

div[data-testid="stMetricValue"] {
    color: #123b63;
}

.card {
    background: #ffffff;
    border: 1px solid #e0e7ee;
    border-radius: 14px;
    padding: 16px;
    box-shadow: 0 4px 16px rgba(20,40,60,.05);
}

.info-card {
    background: linear-gradient(180deg,#ffffff,#f8fafc);
    border: 1px solid #e0e7ee;
    border-radius: 14px;
    padding: 14px;
    min-height: 112px;
    box-shadow: 0 4px 16px rgba(20,40,60,.05);
}

.info-card .label {
    font-size: .72rem;
    font-weight: 800;
    color: #6b7785;
    text-transform: uppercase;
}

.info-card .value {
    font-size: 1.45rem;
    font-weight: 800;
    color: #123b63;
    margin-top: 5px;
}

.info-card .desc {
    font-size: .68rem;
    color: #778391;
    margin-top: 3px;
}

.warning-box {
    background: #fff9ec;
    border: 1px solid #ecd89d;
    border-left: 5px solid #d19a27;
    border-radius: 12px;
    padding: 13px 16px;
}

.success-box {
    background: #eff9f2;
    border: 1px solid #cce7d4;
    border-left: 5px solid #25834a;
    border-radius: 12px;
    padding: 13px 16px;
}

.small-muted {
    color: #6d7884;
    font-size: .75rem;
}

[data-testid="stDataFrame"] {
    border-radius: 12px;
}

.sidebar-title {
    color: #123b63;
    font-weight: 800;
    font-size: 1rem;
}

button[kind="primary"] {
    background: #124f91;
}
</style>
""", unsafe_allow_html=True)

# -----------------------------
# Cabeçalho com a imagem enviada
# -----------------------------
img = Path(__file__).with_name("ChatGPT Image 7 de ago. de 2026, 10_25_44.png")
if img.exists():
    st.markdown('<div class="hero">', unsafe_allow_html=True)
    st.image(str(img), use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("""
<div class="title-box">
  <h1>CONTROLE DE ORDENS DE SERVIÇO — 2026</h1>
  <p>Gestão operacional • análise mensal • serviços • bairros • ODS • vias numeradas e cálculo físico</p>
</div>
""", unsafe_allow_html=True)

# -----------------------------
# Funções equivalentes ao HTML
# -----------------------------
def clean(v):
    if v is None:
        return ""
    if pd.isna(v):
        return ""
    return str(v).strip()

def normalize(s):
    s = clean(s)
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = re.sub(r"[^A-Za-z0-9 ]", " ", s.upper())
    return re.sub(r"\s+", " ", s).strip()

def similarity_key(value):
    n = normalize(value)
    n = re.sub(r"[-–—_]+", " ", n)
    n = re.sub(r"[/\\]+", " ", n)
    n = re.sub(r"[^A-Z0-9 ]", " ", n)
    return re.sub(r"\s+", " ", n).strip()

def num(v):
    if v is None or clean(v) == "":
        return 0.0
    if isinstance(v, (int, float, np.number)):
        return float(v) if np.isfinite(v) else 0.0
    s = clean(v).replace(".", "").replace(",", ".")
    try:
        return float(s)
    except Exception:
        return 0.0

def numeric_os(v):
    try:
        if clean(v) == "":
            return None
        return int(float(clean(v).replace(",", ".")))
    except Exception:
        return None

def get_field(row, names, fallback_index=None):
    for n in names:
        if n in row:
            return row.get(n, "")
    if fallback_index is not None:
        keys = list(row.keys())
        if fallback_index < len(keys):
            return row.get(keys[fallback_index], "")
    return ""

def parse_date(v):
    if v is None or clean(v) == "":
        return pd.NaT
    if isinstance(v, (datetime, pd.Timestamp)):
        return pd.Timestamp(v)
    if isinstance(v, (int, float, np.number)):
        try:
            return pd.Timestamp("1899-12-30") + pd.to_timedelta(float(v), unit="D")
        except Exception:
            return pd.NaT
    s = clean(v)
    d = pd.to_datetime(s, dayfirst=True, errors="coerce")
    return d

def get_date_value(r):
    return get_field(
        r,
        ["data_solicitacao", "data solicitacao", "Data Solicitação",
         "DATA SOLICITAÇÃO", "Data_Solicitacao", "Data", "DATA"],
        2
    )

def month_of(r):
    d = parse_date(get_date_value(r))
    if pd.isna(d):
        return None
    return int(d.year == 2026 and d.month) if d.year == 2026 else None

def date_text(r):
    d = parse_date(get_date_value(r))
    if pd.isna(d):
        return clean(get_date_value(r))
    return d.strftime("%d/%m/%Y")

def service_canonical(value):
    raw = clean(value)
    n = similarity_key(raw)
    if not n:
        return "Não informado"

    m = re.match(r"^(\d+)\s*(.*)$", n)
    if m:
        code = int(m.group(1))
        labels = {
            1:"1 - Capinação",
            2:"2 - Cata Bagulho",
            3:"3 - Varrição",
            4:"4 - Poda",
            5:"5 - Recolha de Capinação",
            6:"6 - Drenagem",
            7:"7 - Desassoreamento",
            8:"8 - Limpeza de Boca de Lobo/Caixa de Leão",
            9:"9 - Troca de Tampa/Reparo de Gradil",
            10:"10 - Tapa Buraco",
            11:"11 - Manutenção/Reparo em Vias",
            12:"12 - Nivelamento",
            13:"13 - Remoção de Árvores",
            14:"14 - Construção",
            15:"15 - Manutenção/Limpeza de Mobiliário Urbano",
        }
        if code in labels:
            return labels[code]
        return f"{code} - {m.group(2).replace('  ',' ').strip()}"

    aliases = [
        ("CATA BAGULHO","2 - Cata Bagulho"),
        ("CAPINACAO","1 - Capinação"),
        ("VARRICAO","3 - Varrição"),
        ("NIVELAMENTO","12 - Nivelamento"),
        ("DRENAGEM","6 - Drenagem"),
        ("DESASSOREAMENTO","7 - Desassoreamento"),
        ("LIMPEZA DE BOCA DE LOBO","8 - Limpeza de Boca de Lobo/Caixa de Leão"),
        ("LIMPEZA DE BOCA DE LEAO","8 - Limpeza de Boca de Lobo/Caixa de Leão"),
        ("TROCA DE TAMPA","9 - Troca de Tampa/Reparo de Gradil"),
        ("MANUTENCAO REPARO EM VIAS","11 - Manutenção/Reparo em Vias"),
        ("MANUTENCAO REPARO DE VIAS","11 - Manutenção/Reparo em Vias"),
        ("MANUTENCAO LIMPEZA DE MOBILIARIO URBANO","15 - Manutenção/Limpeza de Mobiliário Urbano"),
    ]
    for needle, label in aliases:
        if needle in n:
            return label
    return raw

def bairro_canonical(value):
    n = similarity_key(value).replace(" ", "")
    if not n:
        return "Não informado"
    aliases = {
        "OUROFINOPAULISTA":"Ouro Fino Paulista",
        "OUROFINO":"Ouro Fino Paulista",
        "ITRAPOA":"Itrapoá",
        "ITAPOA":"Itrapoá",
        "SOMMA":"Somma",
        "CASAVERMELHA":"Casa Vermelha",
        "POUSOALEGRE":"Pouso Alegre",
        "KM4":"KM4",
        "KM04":"KM4",
        "KM0004":"KM4",
    }
    return aliases.get(n, clean(value) or "Não informado")

def bairro_key(value):
    n = re.sub(r"[^A-Z0-9]+", " ", normalize(value)).strip()
    compact = n.replace(" ", "")
    aliases = {
        "OUROFINOPAULISTA":"OUROFINOPAULISTA",
        "OUROFINO":"OUROFINOPAULISTA",
        "ITRAPOA":"ITRAPOA",
        "ITAPOA":"ITRAPOA",
        "SOMMA":"SOMMA",
        "CASAVERMELHA":"CASAVERMELHA",
        "POUSOALEGRE":"POUSOALEGRE",
        "KM4":"KM4",
        "KM04":"KM4",
        "KM0004":"KM4",
    }
    return aliases.get(compact, compact)

def is_excluded_neighborhood(bairro):
    return bairro_key(bairro) in BAIRROS_EXCLUIDOS

def count_by(values, mode="exact"):
    s = pd.Series([clean(v) or "Não informado" for v in values], dtype="object")
    if s.empty:
        return pd.DataFrame(columns=["Item", "Quantidade"])
    if mode == "tipo":
        s = s.map(service_canonical)
    elif mode == "bairro":
        s = s.map(bairro_canonical)
    out = s.value_counts().reset_index()
    out.columns = ["Item", "Quantidade"]
    return out

def find_missing(values):
    nums = sorted(set(n for n in [numeric_os(x) for x in values] if n is not None))
    if len(nums) < 2:
        return []
    out = []
    for prev, cur in zip(nums[:-1], nums[1:]):
        gap = cur - prev
        if gap > 1 and gap <= 2:
            out.extend(range(prev + 1, cur))
    return out

def service_rule(s):
    x = normalize(s)
    if "CAPINACAO" in x:
        return ("Comprimento × 2", 2, "METROS", "cap")
    if "VARRICAO" in x:
        return ("Comprimento × 2", 2, "METROS", "varr")
    if "NIVELAMENTO" in x:
        return ("Comprimento × 80%", .8, "METROS", "nivel")
    if "11 - MANUTENCAO REPARO EM VIAS" in x or "MANUTENCAO REPARO EM VIAS" in x:
        return ("Comprimento × 80%", .8, "METROS", "manut")
    if "2 - CATA BAGULHO" in x or "CATA BAGULHO" in x:
        return ("1 OS × 3,5 toneladas", 3.5, "TONELADAS", "cata")
    return None

def full_name(v):
    return normalize(" ".join(
        str(x) for x in [v.get("COMPLEMENTO DO NOME"), v.get("NOME")]
        if clean(x)
    ))

def compact_name(s):
    return normalize(s).replace(" ", "")

def length_of(v):
    e = num(v.get("METRAGEM ESCADARIA/VIELA"))
    if e > 0:
        return e
    return (
        num(v.get("TERRA")) +
        num(v.get("BLOQUETE")) +
        num(v.get("PARALELEPÍPEDO", v.get("PARALELEPIPEDO"))) +
        num(v.get("ASFALTO"))
    )

def strip_type(a):
    return re.sub(
        r"^(RUA|AVENIDA|AV|TRAVESSA|TV|ESTRADA|RODOVIA|ROD|PRACA|PRAÇA|"
        r"VIELA|ESCADARIA|ALAMEDA|AL|BECO|SERVIDAO|CAMINHO)\s+",
        "",
        normalize(a)
    ).strip()

def build_indexes(vias):
    exact, compact = {}, {}
    for v in vias:
        f = full_name(v)
        c = compact_name(f)
        if f and f not in exact:
            exact[f] = v
        if c and c not in compact:
            compact[c] = v
    return exact, compact

def find_via(addr, by_exact, by_compact):
    a = normalize(addr)
    if not a:
        return None, "Endereço vazio"
    s = strip_type(a)
    v = by_exact.get(s) or by_compact.get(compact_name(s))
    if v is not None:
        return v, ""

    best = None
    best_len = 0
    for key, val in by_exact.items():
        if len(key) > best_len and f" {s} ".find(f" {key} ") >= 0:
            best = val
            best_len = len(key)
    if best is not None:
        return best, ""

    toks = [x for x in s.split() if len(x) >= 3]
    if len(toks) >= 2:
        hits = []
        for key, val in by_exact.items():
            score = sum(t in key for t in toks)
            if score >= min(3, len(toks)):
                hits.append((score, len(key), val))
        if hits:
            hits.sort(key=lambda x: (x[0], x[1]), reverse=True)
            if len(hits) == 1 or hits[0][0] > hits[1][0]:
                return hits[0][2], ""
    return None, "Via não encontrada"

def process_rows(data, vias):
    by_exact, by_compact = build_indexes(vias)
    out = []

    for i, r in enumerate(data):
        os_num = get_field(r, ["OS","O.S.","Nº OS","Nº O.S.","Numero OS","Número OS","os"], 0)
        addr = get_field(r, ["Endereco","Endereço","ENDEREÇO","Endereço da OS","endereco","endereço"], 5)
        svc = get_field(r, ["Tipo","TIPO","Tipo de Serviço","TIPO DE SERVIÇO","tipo"], 9)
        rule = service_rule(svc)

        base = {
            "linha": i + 2,
            "OS": os_num,
            "Endereço da OS": addr,
            "Serviço": svc,
            "Data": date_text(r),
            "Número da rua": "—",
            "Via encontrada": "—",
            "Bairro": "",
            "Vila": "",
            "Comprimento m": None,
            "Fórmula": "—",
            "Resultado": None,
            "Unidade": "",
            "Status": "",
            "Problema": "",
            "kind": "",
            "_raw": r,
        }

        if not rule:
            base["Status"] = "Fora das regras"
            base["Problema"] = "Serviço sem regra de cálculo"
            out.append(base)
            continue

        formula, factor, unit, kind = rule
        base["Fórmula"] = formula
        base["Unidade"] = unit
        base["kind"] = kind

        if kind == "cata":
            base["Resultado"] = 3.5
            base["Status"] = "Calculado"
            out.append(base)
            continue

        found, reason = find_via(addr, by_exact, by_compact)
        if found is None:
            base["Status"] = reason
            base["Problema"] = reason
            out.append(base)
            continue

        v = found
        m = num(v.get("TERRA")) if kind == "nivel" else length_of(v)
        number = clean(v.get("NÚMERO DA RUA", v.get("NUMERO DA RUA", "")))

        base["Número da rua"] = number or "—"
        base["Via encontrada"] = " ".join(
            str(x) for x in [v.get("COMPLEMENTO DO NOME"), v.get("NOME")]
            if clean(x)
        )
        base["Bairro"] = clean(v.get("BAIRRO"))
        base["Vila"] = clean(v.get("VILA"))

        if not (m > 0):
            base["Status"] = "Comprimento inválido"
            base["Problema"] = "Via localizada, mas sem comprimento válido"
            out.append(base)
            continue

        base["Comprimento m"] = m
        base["Resultado"] = m * factor
        base["Status"] = "Calculado"
        out.append(base)

    return pd.DataFrame(out)

def classify_ods(tipo):
    n = normalize(tipo)
    n = re.sub(r"\s*[-–—]\s*", "-", n)
    n = re.sub(r"\s*/\s*", "/", n)
    n = re.sub(r"\s+", " ", n).strip()

    m = re.match(r"^(\d+)\s*-?\s*(.*)$", n)
    codigo = int(m.group(1)) if m else None
    nome = m.group(2) if m else n

    if codigo == 2 or nome.startswith("CATA BAGULHO"):
        return "ODS 12"
    if (
        codigo in [6,7,8,9] or
        nome.startswith("DRENAGEM") or
        nome.startswith("DESASSOREAMENTO") or
        nome.startswith("LIMPEZA DE BOCA DE LOBO") or
        nome.startswith("LIMPEZA DE BOCA DE LEAO") or
        nome.startswith("TROCA DE TAMPA")
    ):
        return "ODS 6"
    if codigo == 12 or nome.startswith("NIVELAMENTO"):
        return "ODS 11"
    if (
        codigo in [11,15] or
        nome.startswith("MANUTENCAO/REPARO EM VIAS") or
        nome.startswith("MANUTENCAO/REPARO DE VIAS") or
        nome.startswith("MANUTENCAO/LIMPEZA DE MOBILIARIO URBANO")
    ):
        return "ODS 15"
    return None

# -----------------------------
# Supabase
# -----------------------------
@st.cache_data(ttl=120, show_spinner=False)
def fetch_all_supabase(base_url, key, table, order_by="id"):
    all_rows = []
    offset = 0

    while True:
        url = (
            f"{base_url}/rest/v1/{table}"
            f"?select=*&order={order_by}.asc"
            f"&limit={PAGE_SIZE}&offset={offset}"
        )
        response = requests.get(
            url,
            headers={
                "apikey": key,
                "Authorization": f"Bearer {key}",
                "Accept": "application/json",
            },
            timeout=60,
        )
        if not response.ok:
            try:
                detail = response.json()
                detail = detail.get("message") or detail.get("error_description") or detail.get("hint") or str(detail)
            except Exception:
                detail = response.text
            raise RuntimeError(f"Supabase HTTP {response.status_code}: {detail}")

        page = response.json() if response.text else []
        if not isinstance(page, list):
            raise RuntimeError(f"A tabela {table} não retornou uma lista.")

        all_rows.extend(page)

        if len(page) < PAGE_SIZE:
            break
        offset += PAGE_SIZE

    return all_rows

def load_data(force=False):
    if force:
        st.cache_data.clear()

    os_all = fetch_all_supabase(SUPABASE_URL, SUPABASE_KEY, SUPABASE_TABLE, "os")
    vias = fetch_all_supabase(RUAS_SUPABASE_URL, RUAS_SUPABASE_KEY, RUAS_SUPABASE_TABLE, "id")

    rows2026 = []
    for r in os_all:
        d = parse_date(get_date_value(r))
        if not pd.isna(d) and d.year == 2026:
            rows2026.append(r)

    processed = process_rows(rows2026, vias)
    if not processed.empty:
        processed["bairro_raw"] = processed["_raw"].apply(lambda r: get_field(r, ["bairro","Bairro","BAIRRO"], 7))

    return os_all, vias, processed

# -----------------------------
# Sidebar
# -----------------------------
with st.sidebar:
    st.markdown('<div class="sidebar-title">PAINEL DE CONTROLE</div>', unsafe_allow_html=True)
    period_label = st.selectbox(
        "Período de análise",
        ["TOTAL DO ANO — 2026"] + [f"{m.upper()} — 2026" for m in MONTH_NAMES],
        index=0,
    )

    refresh = st.button("↻ Atualizar dados", use_container_width=True, type="primary")

    st.divider()
    st.markdown("**Filtros do detalhamento**")
    search_text = st.text_input("Pesquisar", placeholder="OS, rua, bairro, vila ou serviço...")
    only_problems = st.checkbox("Somente problemas")
    status_filter = st.multiselect(
        "Status",
        ["Calculado", "Via não encontrada", "Comprimento inválido", "Fora das regras", "Endereço vazio"],
    )

# -----------------------------
# Carregamento
# -----------------------------
try:
    with st.spinner("Consultando ordens de serviço e banco de ruas..."):
        os_all, vias, all_rows = load_data(refresh)

    st.markdown(
        f'<div class="success-box">● Supabase conectado • '
        f'<b>{len(os_all):,}</b> OS • <b>{len(vias):,}</b> ruas • '
        f'<b>{len(all_rows):,}</b> OS de 2026</div>'.replace(",", "."),
        unsafe_allow_html=True,
    )
except Exception as e:
    st.error(f"Erro ao carregar o Supabase: {e}")
    st.stop()

# -----------------------------
# Período
# -----------------------------
if period_label.startswith("TOTAL"):
    period_num = "total"
    rows = all_rows.copy()
    period_title = "TOTAL DO ANO — 2026"
    period_sub = "Consolidação anual de todas as OS válidas."
else:
    period_num = MONTH_NAMES.index(period_label.split(" —")[0].title()) + 1
    rows = all_rows[all_rows["_raw"].apply(lambda r: month_of(r) == period_num)].copy()
    period_title = period_label
    period_sub = f"Somente OS com data_solicitacao em {MONTH_NAMES[period_num-1]}."

valid = rows[rows["OS"].apply(numeric_os).notna()].copy()
total = len(valid)

st.markdown(f'<div class="section"><b>{period_title}</b><br><span class="small-muted">{period_sub}</span></div>', unsafe_allow_html=True)

# -----------------------------
# KPIs
# -----------------------------
k1,k2,k3,k4,k5,k6 = st.columns(6)

def has_service(s, needle):
    return needle in normalize(s)

q_nivel = int(valid["Serviço"].map(lambda x: has_service(x, "NIVELAMENTO")).sum())
q_varr = int(valid["Serviço"].map(lambda x: has_service(x, "VARRICAO")).sum())
q_cap = int(valid["Serviço"].map(lambda x: has_service(x, "CAPINACAO")).sum())
q_cata = int(valid["Serviço"].map(lambda x: has_service(x, "CATA BAGULHO")).sum())

missing = find_missing(valid["OS"].tolist())

k1.metric("OS válidas", f"{total:,}".replace(",", "."))
k2.metric("Números faltantes", f"{len(missing):,}".replace(",", "."))
k3.metric("Nivelamento", f"{q_nivel:,}".replace(",", "."))
k4.metric("Varrição", f"{q_varr:,}".replace(",", "."))
k5.metric("Capinação", f"{q_cap:,}".replace(",", "."))
k6.metric("Cata-Bagulho", f"{q_cata:,}".replace(",", "."))

# -----------------------------
# Cálculos físicos
# -----------------------------
st.markdown('<div class="section">Resultados físicos calculados</div>', unsafe_allow_html=True)
calc_cols = st.columns(5)

def sum_kind(kind):
    x = rows[(rows["kind"] == kind) & (rows["Status"] == "Calculado")]["Resultado"]
    return float(x.fillna(0).sum()) if not x.empty else 0.0

nivel = sum_kind("nivel")
cap = sum_kind("cap")
varr = sum_kind("varr")
manut = sum_kind("manut")
cata = sum_kind("cata")

for col, label, value, unit, desc in [
    (calc_cols[0], "Nivelamento", nivel, "m", "comprimento da via × 80%"),
    (calc_cols[1], "Capinação", cap, "m", "comprimento da via × 2"),
    (calc_cols[2], "Varrição", varr, "m", "comprimento da via × 2"),
    (calc_cols[3], "11 — Manutenção/Reparo em Vias", manut, "m", "comprimento da via × 80%"),
    (calc_cols[4], "2 — Cata-Bagulho", cata, "t", "1 OS × 3,5 toneladas"),
]:
    col.markdown(
        f'<div class="info-card"><div class="label">{label}</div>'
        f'<div class="value">{value:,.1f} {unit}</div>'
        f'<div class="desc">{desc}</div></div>'.replace(",", "X").replace(".", ",").replace("X", "."),
        unsafe_allow_html=True,
    )

# -----------------------------
# Regras
# -----------------------------
st.markdown('<div class="section">Regras de cálculo</div>', unsafe_allow_html=True)
rule_cols = st.columns(5)
rules = [
    ("Capinação", "comprimento da via × 2"),
    ("Varrição", "comprimento da via × 2"),
    ("Nivelamento", "comprimento da via × 80%"),
    ("11 - Manutenção/Reparo Em Vias", "comprimento da via × 80%"),
    ("2 - Cata Bagulho", "1 OS × 3,5 toneladas"),
]
for c, (a,b) in zip(rule_cols, rules):
    c.markdown(f'<div class="card"><b>{a}</b><br><span class="small-muted">{b}</span></div>', unsafe_allow_html=True)

# -----------------------------
# Sequenciais faltantes
# -----------------------------
st.markdown('<div class="section">Números sequenciais faltantes</div>', unsafe_allow_html=True)
if missing:
    st.markdown(
        f'<div class="warning-box"><b>{len(missing)}</b> números faltantes: '
        + " ".join(f'<code>{n}</code>' for n in missing)
        + "</div>",
        unsafe_allow_html=True,
    )
else:
    st.markdown('<div class="success-box">Nenhum número faltante na sequência encontrada.</div>', unsafe_allow_html=True)

# -----------------------------
# Gráficos
# -----------------------------
def donut(df, title):
    if df.empty:
        st.info("Nenhum dado para este gráfico.")
        return
    fig = px.pie(
        df,
        names="Item",
        values="Quantidade",
        hole=0.52,
        title=title,
    )
    fig.update_traces(
        textposition="inside",
        textinfo="percent",
        hovertemplate="<b>%{label}</b><br>%{value} OS<br>%{percent}<extra></extra>",
    )
    fig.update_layout(
        margin=dict(l=10,r=10,t=55,b=10),
        legend=dict(orientation="h", y=-0.08),
        height=390,
        font=dict(family="Montserrat"),
    )
    st.plotly_chart(fig, use_container_width=True, config={"displaylogo": False})

st.markdown('<div class="section">Análise geral — total de todas as OS válidas</div>', unsafe_allow_html=True)
g1,g2 = st.columns(2)

with g1:
    donut(count_by(valid["_raw"].apply(lambda r: get_field(r, ["Origem","ORIGEM","origem"], 8))), "Origem dos serviços")
with g2:
    donut(count_by(valid["Serviço"], "tipo"), "Tipo de serviço")

g3,g4 = st.columns(2)
with g3:
    donut(count_by(valid["_raw"].apply(lambda r: get_field(r, ["bairro","Bairro","BAIRRO"], 7)), "bairro"), "Serviços por bairro")
with g4:
    ods_counts = valid["Serviço"].map(classify_ods).dropna().value_counts().reset_index()
    ods_counts.columns = ["Item","Quantidade"]
    donut(ods_counts, "Serviços por ODS")

# -----------------------------
# Análise específica da Secretaria
# -----------------------------
filtered = valid[
    ~valid["_raw"].apply(lambda r: is_excluded_neighborhood(get_field(r, ["bairro","Bairro","BAIRRO"], 7))) &
    ~valid["Bairro"].apply(is_excluded_neighborhood)
].copy()

st.markdown('<div class="section">Análise específica — serviços da secretaria</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="warning-box"><b>Filtro aplicado:</b> não contabilizados '
    '<b>Ouro Fino Paulista, Itrapoá, Somma, Casa Vermelha, Pouso Alegre e KM4</b>. '
    'Maiúsculas/minúsculas, acentos, hífens e espaços são normalizados; o filtro verifica '
    'o bairro da OS e também o bairro da via.</div>',
    unsafe_allow_html=True,
)

st.metric("OS consideradas", len(filtered))

f1,f2 = st.columns(2)
with f1:
    donut(count_by(filtered["Serviço"], "tipo"), "Tipo de serviço — área atendida")
with f2:
    donut(count_by(filtered["_raw"].apply(lambda r: get_field(r, ["bairro","Bairro","BAIRRO"], 7)), "bairro"), "Serviços por bairro — área atendida")

fods = filtered["Serviço"].map(classify_ods).dropna().value_counts().reset_index()
fods.columns = ["ODS","Quantidade"]
if not fods.empty:
    fods["Objetivo"] = fods["ODS"].map(ODS_MAP)
    fods["%"] = (fods["Quantidade"] / len(filtered) * 100).round(1)
    st.plotly_chart(
        px.pie(fods, names="ODS", values="Quantidade", hole=.52,
               title="Serviços por ODS — área atendida").update_layout(
                   height=390, margin=dict(l=10,r=10,t=55,b=10), font=dict(family="Montserrat")
               ),
        use_container_width=True,
        config={"displaylogo": False},
    )

# ODS table — área atendida
ods_table = []
for ods, q in fods[["ODS","Quantidade"]].itertuples(index=False):
    serv = filtered[filtered["Serviço"].map(classify_ods) == ods]["Serviço"].map(service_canonical).value_counts()
    ods_table.append({
        "ODS": ods,
        "Objetivo": ODS_MAP.get(ods, ""),
        "Quantidade": int(q),
        "%": f"{(q/len(filtered)*100):.1f}%" if len(filtered) else "0.0%",
        "Serviços": " • ".join(f"{k} ({v})" for k,v in serv.items())
    })
if ods_table:
    st.dataframe(pd.DataFrame(ods_table), use_container_width=True, hide_index=True)

# -----------------------------
# ODS total
# -----------------------------
st.markdown('<div class="section">Classificação das OS por ODS — total da planilha</div>', unsafe_allow_html=True)
ods_total = []
for ods, q in valid["Serviço"].map(classify_ods).dropna().value_counts().items():
    serv = valid[valid["Serviço"].map(classify_ods) == ods]["Serviço"].map(service_canonical).value_counts()
    ods_total.append({
        "ODS": ods,
        "Objetivo": ODS_MAP.get(ods, ""),
        "Quantidade": int(q),
        "Serviços": " • ".join(f"{k} ({v})" for k,v in serv.items())
    })
if ods_total:
    st.dataframe(pd.DataFrame(ods_total), use_container_width=True, hide_index=True)
else:
    st.info("Nenhum serviço classificado.")

# -----------------------------
# Comparativo
# -----------------------------
st.markdown('<div class="section">Comparativo da análise específica</div>', unsafe_allow_html=True)
c1,c2,c3,c4 = st.columns(4)
c1.metric("Total de OS válidas", total)
c2.metric("OS dos bairros excluídos", total-len(filtered))
c3.metric("OS na análise da Secretaria", len(filtered))
c4.metric("Percentual considerado", f"{(len(filtered)/total*100 if total else 0):.1f}%")

# -----------------------------
# Resumo detalhado
# -----------------------------
st.markdown('<div class="section">Resumo detalhado — análise geral</div>', unsafe_allow_html=True)
summary_rows = []
groups = [
    ("Origem", valid["_raw"].apply(lambda r: get_field(r, ["Origem","ORIGEM","origem"], 8))),
    ("Tipo de serviço", valid["Serviço"]),
    ("Bairro", valid["_raw"].apply(lambda r: get_field(r, ["bairro","Bairro","BAIRRO"], 7))),
    ("Classificação das OS", valid["Serviço"].map(lambda x: classify_ods(x) or "Não classificada")),
]
for cat, vals in groups:
    cb = count_by(vals)
    denom = cb["Quantidade"].sum()
    for _, rr in cb.iterrows():
        summary_rows.append({
            "Categoria": cat,
            "Item": rr["Item"],
            "Quantidade": int(rr["Quantidade"]),
            "%": f"{(rr['Quantidade']/denom*100 if denom else 0):.1f}%"
        })
st.dataframe(pd.DataFrame(summary_rows), use_container_width=True, hide_index=True, height=430)

# -----------------------------
# Detalhamento
# -----------------------------
st.markdown('<div class="section">Detalhamento dos cálculos de vias numeradas</div>', unsafe_allow_html=True)

detail = rows.copy()

if search_text:
    q = normalize(search_text)
    cols = ["OS","Endereço da OS","Serviço","Número da rua","Via encontrada","Bairro","Vila"]
    mask = detail[cols].fillna("").astype(str).apply(
        lambda row: q in normalize(" ".join(row.tolist())), axis=1
    )
    detail = detail[mask]

if status_filter:
    detail = detail[detail["Status"].isin(status_filter)]

if only_problems:
    detail = detail[detail["Status"] != "Calculado"]

display_cols = [
    "OS","Data","Endereço da OS","Serviço","Número da rua","Via encontrada",
    "Bairro","Vila","Comprimento m","Fórmula","Resultado","Unidade","Status","Problema"
]

detail_show = detail[display_cols].copy()
if not detail_show.empty:
    detail_show["Comprimento m"] = detail_show["Comprimento m"].round(2)
    detail_show["Resultado"] = detail_show["Resultado"].round(2)

st.dataframe(
    detail_show,
    use_container_width=True,
    hide_index=True,
    height=620,
    column_config={
        "OS": st.column_config.TextColumn("OS"),
        "Resultado": st.column_config.NumberColumn("Resultado", format="%.2f"),
        "Comprimento m": st.column_config.NumberColumn("Comprimento m", format="%.2f"),
    }
)

st.caption(f"Exibindo {len(detail_show):,} registros no detalhamento.".replace(",", "."))
