# -*- coding: utf-8 -*-
import re
import unicodedata
from datetime import datetime
from typing import Any

import numpy as np
import pandas as pd
import plotly.express as px
import requests
import streamlit as st

st.set_page_config(
    page_title="Controle de Ordens de Serviço — 2026",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# As chaves publishable/anon são destinadas ao uso no cliente. Podem ser
# substituídas em Streamlit Cloud > Settings > Secrets.
DEFAULT_OS_URL = "https://kfjjngcncrqcezyyumvi.supabase.co"
DEFAULT_OS_KEY = "sb_publishable_tHdykHZugn2CzR3ago9bKg__KsZafC6"
DEFAULT_RUAS_URL = "https://ypykiczrahhjepwojaim.supabase.co"
DEFAULT_RUAS_KEY = "sb_publishable_7cjD1eDSihnnTR70q-3Ytg_diHgiKMy"
OS_TABLE = "ordens_servico"
RUAS_TABLE = "ruas"
PAGE_SIZE = 1000

AREA_BAIRROS = [
    "Ouro Fino Paulista", "Itrapoá", "KM4",
    "Casa Vermelha", "Pouso Alegre", "Somma",
]
MESES = [
    "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro",
]
ODS_NOMES = {
    "ODS 12": "Consumo e produção responsáveis",
    "ODS 11": "Cidades e comunidades sustentáveis",
    "ODS 6": "Água potável e saneamento",
    "ODS 15": "Vida terrestre",
}
SERVICOS = {
    1: "1 - Capinação",
    2: "2 - Cata Bagulho",
    3: "3 - Poda de Árvore",
    4: "4 - Poda",
    5: "5 - Recolha de Capinação",
    6: "6 - Drenagem",
    7: "7 - Desassoreamento",
    8: "8 - Limpeza de Boca de Lobo/Caixa de Leão",
    9: "9 - Troca de Tampa/Reparo de Gradil",
    10: "10 - Tapa Buraco",
    11: "11 - Manutenção/Reparo em Vias",
    12: "12 - Nivelamento",
    13: "13 - Remoção de Árvores",
    14: "14 - Construção",
    15: "15 - Manutenção/Limpeza de Mobiliário Urbano",
    22: "22 - Varrição",  # compatibilidade com cadastros antigos

}
PALETA = ["#21633f", "#b7791f", "#3977a8", "#8a5aa6", "#d16b48",
          "#6b8e23", "#7b8794", "#c04c64", "#3d8b8b", "#9b7653"]

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700;800;900&display=swap');
html, body, [class*="css"] {font-family: 'Montserrat', sans-serif;}
.stApp {background:#eef3f0;}
header[data-testid="stHeader"] {background:rgba(238,243,240,.9);}
.block-container {padding-top:1.3rem; max-width:1800px;}
.hero {background:linear-gradient(135deg,#102b1e,#21633f); color:white;
       padding:22px 26px; border-radius:15px; margin-bottom:18px;}
.hero h1 {font-size:25px; margin:0; font-weight:900;}
.hero p {font-size:12px; margin:6px 0 0; opacity:.85;}
.section {color:#173d2b;font-size:18px;font-weight:900;margin:22px 0 10px;}
.kpi {background:white;border:1px solid #d8e3dc;border-radius:13px;
      padding:15px 16px;min-height:112px;box-shadow:0 3px 12px #0f2d1d0a;}
.kpi-label {font-size:10px;color:#68786f;font-weight:900;text-transform:uppercase;}
.kpi-value {font-size:27px;color:#173d2b;font-weight:900;margin-top:7px;}
.kpi-desc {font-size:10px;color:#68786f;margin-top:2px;}
.metric-card {background:white;border:1px solid #d8e3dc;border-radius:12px;
              padding:15px;min-height:95px;}
.metric-card small {font-size:10px;color:#68786f;font-weight:900;text-transform:uppercase;}
.metric-card strong {display:block;color:#173d2b;font-size:24px;margin-top:6px;}
.area-banner {background:#f0f7f2;border:1px solid #d5e4da;border-left:5px solid #21633f;
              border-radius:12px;padding:13px 16px;margin:8px 0 12px;}
div[data-testid="stMetric"] {background:white;border:1px solid #d8e3dc;
  border-radius:12px;padding:12px 14px;box-shadow:0 3px 12px #0f2d1d0a;}
div[data-testid="stMetricLabel"] p {font-size:10px;font-weight:800;text-transform:uppercase;}
div[data-testid="stMetricValue"] {color:#173d2b;}
</style>
""", unsafe_allow_html=True)

def secret_or_default(section: str, key: str, default: str) -> str:
    try:
        return str(st.secrets[section][key]).strip()
    except Exception:
        try:
            return str(st.secrets[key]).strip()
        except Exception:
            return default

def cfg():
    return {
        "os_url": secret_or_default("supabase", "os_url", DEFAULT_OS_URL).rstrip("/"),
        "os_key": secret_or_default("supabase", "os_key", DEFAULT_OS_KEY),
        "ruas_url": secret_or_default("supabase", "ruas_url", DEFAULT_RUAS_URL).rstrip("/"),
        "ruas_key": secret_or_default("supabase", "ruas_key", DEFAULT_RUAS_KEY),
    }

def clean(v: Any) -> str:
    return "" if v is None else str(v).strip()

def normalize(v: Any) -> str:
    s = unicodedata.normalize("NFD", clean(v))
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", re.sub(r"[^A-Z0-9 ]", " ", s.upper())).strip()

def num(v: Any) -> float:
    if v is None or (isinstance(v, str) and not v.strip()):
        return 0.0
    if isinstance(v, (int, float, np.number)):
        return float(v) if np.isfinite(v) else 0.0
    s = str(v).strip().replace("\u00a0", " ")
    # Aceita tanto 1.234,56 (padrão brasileiro) quanto 1234.56.
    if "," in s:
        s = s.replace(".", "").replace(",", ".")
    try:
        result = float(s)
        return result if np.isfinite(result) else 0.0
    except (TypeError, ValueError):
        return 0.0

def fmt(v: Any, decimals: int = 0) -> str:
    try:
        return f"{float(v):,.{decimals}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "0"

def get_field(row: dict, names: list[str], fallback=None):
    for name in names:
        if name in row:
            return row[name]
    if fallback is not None:
        keys = list(row.keys())
        if len(keys) > fallback:
            return row[keys[fallback]]
    return ""

def parse_date(v: Any):
    """Interpreta datas ISO, brasileiras e seriais do Excel sem inverter dia/mês."""
    if v is None or (isinstance(v, str) and not v.strip()):
        return pd.NaT
    if isinstance(v, (datetime, pd.Timestamp)):
        return pd.Timestamp(v)
    if isinstance(v, (int, float, np.number)) and not pd.isna(v):
        try:
            return pd.Timestamp("1899-12-30") + pd.to_timedelta(float(v), unit="D")
        except Exception:
            return pd.NaT
    value = str(v).strip()
    if re.match(r"^\d{4}-\d{2}-\d{2}", value):
        return pd.to_datetime(value[:10], format="%Y-%m-%d", errors="coerce")
    match = re.match(r"^(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})", value)
    if match:
        day, month, year = map(int, match.groups())
        if year < 100:
            year += 2000
        try:
            return pd.Timestamp(year=year, month=month, day=day)
        except ValueError:
            return pd.NaT
    return pd.to_datetime(value, errors="coerce")

def date_of(row):
    return get_field(row, [
        "data_solicitacao", "data solicitacao", "Data Solicitação",
        "DATA SOLICITAÇÃO", "Data_Solicitacao", "Data", "DATA"
    ], 2)

def service_canonical(value: Any) -> str:
    raw = clean(value)
    n = normalize(raw)
    if not n:
        return "Não informado"
    m = re.match(r"^(\d+)\s*(.*)$", n)
    if m:
        code = int(m.group(1))
        return SERVICOS.get(code, f"{code} - {m.group(2).strip()}")
    aliases = [
        ("CATA BAGULHO", SERVICOS[2]), ("CAPINACAO", SERVICOS[1]),
        ("VARRICAO", SERVICOS[22]), ("PODA DE ARVORE", SERVICOS[3]),
        ("PODA", SERVICOS[3]), ("NIVELAMENTO", SERVICOS[12]),
        ("DRENAGEM", SERVICOS[6]), ("DESASSOREAMENTO", SERVICOS[7]),
        ("LIMPEZA DE BOCA DE LOBO", SERVICOS[8]),
        ("LIMPEZA DE BOCA DE LEAO", SERVICOS[8]),
        ("TROCA DE TAMPA", SERVICOS[9]),
        ("MANUTENCAO REPARO EM VIAS", SERVICOS[11]),
        ("MANUTENCAO REPARO DE VIAS", SERVICOS[11]),
        ("MANUTENCAO LIMPEZA DE MOBILIARIO URBANO", SERVICOS[15]),
    ]
    for needle, label in aliases:
        if needle in n:
            return label
    return raw

def bairro_canonical(value: Any) -> str:
    n = normalize(value).replace(" ", "")
    aliases = {
        "OUROFINOPAULISTA": "Ouro Fino Paulista", "OUROFINO": "Ouro Fino Paulista",
        "ITRAPOA": "Itrapoá", "ITAPOA": "Itrapoá", "SOMMA": "Somma",
        "CASAVERMELHA": "Casa Vermelha", "POUSOALEGRE": "Pouso Alegre",
        "KM4": "KM4", "KM04": "KM4", "KM0004": "KM4",
    }
    return aliases.get(n, clean(value) or "Não informado")

def bairro_key(value: Any) -> str:
    return normalize(value).replace(" ", "")

def is_area(value: Any) -> bool:
    return bairro_key(bairro_canonical(value)) in {bairro_key(x) for x in AREA_BAIRROS}

def classify_ods(tipo: Any):
    n = normalize(tipo)
    m = re.match(r"^(\d+)\s*-?\s*(.*)$", n)
    code = int(m.group(1)) if m else None
    name = m.group(2) if m else n
    if code == 2 or name.startswith("CATA BAGULHO"):
        return "ODS 12"
    if code in (6, 7, 8, 9) or name.startswith((
        "DRENAGEM", "DESASSOREAMENTO", "LIMPEZA DE BOCA DE LOBO",
        "LIMPEZA DE BOCA DE LEAO", "TROCA DE TAMPA"
    )):
        return "ODS 6"
    if code == 12 or name.startswith("NIVELAMENTO"):
        return "ODS 11"
    if code in (11, 15) or name.startswith((
        "MANUTENCAO/REPARO EM VIAS", "MANUTENCAO/REPARO DE VIAS",
        "MANUTENCAO/LIMPEZA DE MOBILIARIO URBANO"
    )):
        return "ODS 15"
    return None

def numeric_os(v):
    try:
        if v is None or str(v).strip() == "":
            return None
        return int(float(str(v).replace(",", ".")))
    except Exception:
        return None

def find_missing(values):
    nums = sorted(set(n for n in (numeric_os(v) for v in values) if n is not None))
    missing = []
    for prev, cur in zip(nums, nums[1:]):
        gap = cur - prev
        # Mantém a regra do HTML: identifica lacunas curtas de até 2 posições.
        if 1 < gap <= 2:
            missing.extend(range(prev + 1, cur))
    return missing

def street_full(v):
    return normalize(" ".join(filter(None, [
        clean(v.get("COMPLEMENTO DO NOME")), clean(v.get("NOME"))
    ])))

def strip_type(value):
    return re.sub(
        r"^(RUA|AVENIDA|AV|TRAVESSA|TV|ESTRADA|RODOVIA|ROD|PRACA|VIELA|ESCADARIA|ALAMEDA|BECO|CAMINHO)\s+",
        "", normalize(value)
    ).strip()

def street_length(v):
    stair = num(v.get("METRAGEM ESCADARIA/VIELA"))
    if stair > 0:
        return stair
    return (
        num(v.get("TERRA")) + num(v.get("BLOQUETE")) +
        num(v.get("PARALELEPÍPEDO", v.get("PARALELEPIPEDO"))) +
        num(v.get("ASFALTO"))
    )

def service_rule(service):
    s = normalize(service)
    if "CAPINACAO" in s:
        return ("Comprimento × 2", 2.0, "METROS", "cap")
    if "VARRICAO" in s:
        return ("Comprimento × 2", 2.0, "METROS", "varr")
    if "NIVELAMENTO" in s:
        return ("Comprimento × 80%", .8, "METROS", "nivel")
    if "MANUTENCAO REPARO EM VIAS" in s:
        return ("Comprimento × 80%", .8, "METROS", "manut")
    if "CATA BAGULHO" in s:
        return ("1 OS × 3,5 toneladas", 3.5, "TONELADAS", "cata")
    return None

def fetch_all(base_url: str, key: str, table: str, order: str):
    headers = {
        "apikey": key, "Authorization": f"Bearer {key}",
        "Accept": "application/json",
    }
    output, offset = [], 0
    while True:
        url = f"{base_url}/rest/v1/{table}"
        response = requests.get(
            url, headers=headers,
            params={"select": "*", "order": f"{order}.asc",
                    "limit": PAGE_SIZE, "offset": offset},
            timeout=45,
        )
        if not response.ok:
            raise RuntimeError(f"Supabase {table}: HTTP {response.status_code} — {response.text[:600]}")
        page = response.json()
        if not isinstance(page, list):
            raise RuntimeError(f"A tabela {table} não retornou uma lista.")
        output.extend(page)
        if len(page) < PAGE_SIZE:
            break
        offset += PAGE_SIZE
    return output

@st.cache_data(ttl=300, show_spinner=False)
def load_data():
    c = cfg()
    os_rows = fetch_all(c["os_url"], c["os_key"], OS_TABLE, "os")
    streets = fetch_all(c["ruas_url"], c["ruas_key"], RUAS_TABLE, "id")
    exact, compact = {}, {}
    for street in streets:
        full = street_full(street)
        if full and full not in exact:
            exact[full] = street
        if full:
            compact[full.replace(" ", "")] = street

    dated = []
    for row in os_rows:
        d = parse_date(date_of(row))
        if pd.notna(d) and d.year == 2026:
            dated.append((row, d))

    processed = []
    for row, d in dated:
        os_num = get_field(row, ["OS", "O.S.", "Nº OS", "Nº O.S.", "Numero OS", "Número OS", "os"], 0)
        address = get_field(row, ["Endereco", "Endereço", "ENDEREÇO", "Endereço da OS", "endereco", "endereço"], 5)
        service = get_field(row, ["Tipo", "TIPO", "Tipo de Serviço", "TIPO DE SERVIÇO", "tipo"], 9)
        raw_bairro = get_field(row, ["bairro", "Bairro", "BAIRRO"], 7)
        raw_origem = get_field(row, ["Origem", "ORIGEM", "origem"], 8)
        rule = service_rule(service)
        item = {
            "OS": os_num, "Data": d, "Endereço": clean(address),
            "Serviço": service_canonical(service), "Tipo original": clean(service),
            "Bairro": bairro_canonical(raw_bairro), "Bairro original": clean(raw_bairro),
            "Origem": clean(raw_origem) or "Não informado",
            "Número da rua": "—", "Via encontrada": "—", "Vila": "",
            "Comprimento m": None, "Fórmula": "—", "Resultado": None,
            "Unidade": "", "Status": "Fora das regras",
            "Problema": "Serviço sem regra de cálculo" if not rule else "",
            "kind": "", "ODS": classify_ods(service), "raw": row,
        }
        if not rule:
            processed.append(item)
            continue
        formula, factor, unit, kind = rule
        item.update({"Fórmula": formula, "Unidade": unit, "kind": kind})
        if kind == "cata":
            item.update({"Resultado": 3.5, "Status": "Calculado", "Problema": ""})
            processed.append(item)
            continue

        addr = strip_type(address)
        street = exact.get(addr) or compact.get(addr.replace(" ", ""))
        if street is None and addr:
            # Correspondência parcial controlada, como no HTML.
            candidates = [(k, v) for k, v in exact.items() if f" {k} " in f" {addr} "]
            if candidates:
                street = max(candidates, key=lambda x: len(x[0]))[1]
        if street is None:
            item.update({"Status": "Via não encontrada", "Problema": "Via não encontrada"})
            processed.append(item)
            continue

        length = num(street.get("TERRA")) if kind == "nivel" else street_length(street)
        item["Número da rua"] = clean(street.get("NÚMERO DA RUA", street.get("NUMERO DA RUA"))) or "—"
        item["Via encontrada"] = " ".join(filter(None, [
            clean(street.get("COMPLEMENTO DO NOME")), clean(street.get("NOME"))
        ]))
        item["Bairro"] = bairro_canonical(raw_bairro or street.get("BAIRRO"))
        item["Vila"] = clean(street.get("VILA"))
        if length <= 0:
            item.update({"Status": "Comprimento inválido",
                         "Problema": "Via localizada, mas sem comprimento válido"})
        else:
            item.update({
                "Comprimento m": length, "Resultado": length * factor,
                "Status": "Calculado", "Problema": "",
            })
        processed.append(item)
    return processed, len(os_rows), len(streets)

def count_entries(series, canonical=False):
    values = []
    for value in series:
        values.append(service_canonical(value) if canonical else (clean(value) or "Não informado"))
    counts = pd.Series(values, dtype="object").value_counts()
    return counts

def doughnut(title, series, canonical=False, height=340):
    counts = count_entries(series, canonical)
    if counts.empty:
        st.info("Não há dados para este gráfico.")
        return
    df = counts.rename_axis("Categoria").reset_index(name="OS")
    fig = px.pie(df, names="Categoria", values="OS", hole=.48,
                 color_discrete_sequence=PALETA)
    fig.update_traces(textposition="inside", textinfo="percent",
                      hovertemplate="%{label}<br>%{value} OS (%{percent})<extra></extra>")
    fig.update_layout(
        title={"text": title, "x": 0.02, "xanchor": "left"},
        height=height, margin=dict(l=10, r=10, t=48, b=10),
        legend=dict(orientation="h", yanchor="top", y=-.08, x=0),
        font=dict(family="Montserrat, sans-serif", size=11),
    )
    st.plotly_chart(fig, use_container_width=True)

def area_charts(rows: pd.DataFrame, area: bool):
    if rows.empty:
        st.info("Nenhuma OS nesta área para o período selecionado.")
        return
    c1, c2 = st.columns(2)
    with c1:
        counts = rows["Bairro"].value_counts()
        if area:
            counts = pd.Series({b: int(counts.get(b, 0)) for b in AREA_BAIRROS})
        df = counts.rename_axis("Bairro").reset_index(name="OS")
        fig = px.pie(df, names="Bairro", values="OS", hole=.45,
                     color_discrete_sequence=PALETA)
        fig.update_layout(title="1. Distribuição dos serviços por bairro", height=350,
                          margin=dict(l=8,r=8,t=48,b=8), legend=dict(orientation="h",y=-.1))
        fig.update_traces(textinfo="percent")
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        doughnut("2. Tipos de serviço", rows["Tipo original"], canonical=True)
    c3, c4 = st.columns(2)
    with c3:
        doughnut("3. Origem dos serviços", rows["Origem"])
    with c4:
        ods = rows["ODS"].dropna().value_counts()
        if ods.empty:
            st.info("Nenhum serviço classificado por ODS nesta área.")
        else:
            df = ods.rename_axis("ODS").reset_index(name="OS")
            fig = px.pie(df, names="ODS", values="OS", hole=.45,
                         color_discrete_sequence=PALETA)
            fig.update_layout(title="4. Serviços por ODS", height=350,
                              margin=dict(l=8,r=8,t=48,b=8), legend=dict(orientation="h",y=-.1))
            fig.update_traces(textinfo="percent")
            st.plotly_chart(fig, use_container_width=True)

def show_table(df: pd.DataFrame, title: str):
    st.markdown(f'<div class="section">{title}</div>', unsafe_allow_html=True)
    if df.empty:
        st.info("Nenhum registro para exibir.")
        return
    st.dataframe(df, use_container_width=True, hide_index=True, height=380)

# Imagem de cabeçalho opcional: basta colocar o arquivo ao lado de app.py.
from pathlib import Path
header_image = Path(__file__).with_name("ChatGPT Image 7 de ago. de 2026, 10_25_44.png")
if header_image.exists():
    st.image(str(header_image), use_container_width=True)

st.markdown("""
<div class="hero">
  <h1>CONTROLE DE ORDENS DE SERVIÇO — 2026</h1>
  <p>Gestão operacional • análise mensal • serviços • bairros • ODS • vias numeradas e cálculo físico</p>
</div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.header("Controle da análise")
    periodo = st.selectbox("Período de análise", ["TOTAL DO ANO — 2026"] + [f"{m.upper()} — 2026" for m in MESES])
    if st.button("↻ Atualizar dados do Supabase", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    st.caption("Os dados são consultados diretamente nas duas tabelas Supabase.")
    st.divider()
    st.caption("Área de Ouro Fino")
    st.write(", ".join(AREA_BAIRROS))

try:
    with st.spinner("Carregando ordens de serviço e cadastro de ruas do Supabase..."):
        records, total_db, total_streets = load_data()
except Exception as exc:
    st.error(f"Não foi possível carregar os dados: {exc}")
    st.info("Confira se as chaves publishable têm permissão SELECT nas tabelas ordens_servico e ruas.")
    st.stop()

df = pd.DataFrame(records)
if not df.empty:
    # Auditoria baseada nos registros brutos, antes de qualquer cálculo de ruas.
    raw_september = df[df["Data"].dt.month == 9].copy()
    raw_valid_september = raw_september[raw_september["OS"].apply(numeric_os).notna()]
    with st.expander("🔎 Auditoria da contagem — origem dos números", expanded=True):
        a1, a2, a3, a4, a5 = st.columns(5)
        a1.metric("Registros recebidos", fmt(total_db))
        a2.metric("Registros em 2026", fmt(len(df)))
        a3.metric("Setembro/2026", fmt(len(raw_september)))
        a4.metric("OS válidas em setembro", fmt(len(raw_valid_september)))
        a5.metric("Sem OS numérica", fmt(len(raw_september) - len(raw_valid_september)))
        st.caption("A auditoria considera a data de solicitação em 2026 e separa registros brutos de OS com número válido. O cálculo de ruas não altera essa contagem.")
        if not raw_september.empty:
            audit = raw_september[["OS", "Data", "Serviço", "Bairro", "Origem"]].copy()
            audit["Data"] = audit["Data"].dt.strftime("%d/%m/%Y")
            audit["Válida"] = audit["OS"].apply(numeric_os).notna()
            st.dataframe(audit, use_container_width=True, hide_index=True)
if df.empty:
    st.warning("Não foram encontradas ordens de serviço com data em 2026.")
    st.stop()

if periodo == "TOTAL DO ANO — 2026":
    selected = df.copy()
    periodo_titulo = "TOTAL DO ANO — 2026"
else:
    mes = MESES.index(periodo.split(" — ")[0].title()) + 1
    selected = df[df["Data"].dt.month == mes].copy()
    periodo_titulo = periodo

valid = selected[selected["OS"].apply(numeric_os).notna()].copy()
total = len(valid)
missing = find_missing(valid["OS"].tolist())

st.caption(
    f"**{periodo_titulo}** · {fmt(total)} OS válidas · "
    f"{fmt(total_db)} registros na tabela · {fmt(total_streets)} ruas cadastradas"
)

st.markdown('<div class="section">Indicadores do período</div>', unsafe_allow_html=True)
kpis = [
    ("OS válidas", total, "Total do período"),
    ("Números faltantes", len(missing), "Na sequência de OS"),
    ("Nivelamento", int(valid["Tipo original"].map(lambda x: "NIVELAMENTO" in normalize(x)).sum()), "Quantidade de OS"),
    ("Varrição (serviço 22)", int(valid["Tipo original"].map(lambda x: "VARRICAO" in normalize(x)).sum()), "Quantidade de OS"),
    ("Capinação", int(valid["Tipo original"].map(lambda x: "CAPINACAO" in normalize(x)).sum()), "Quantidade de OS"),
    ("Cata-Bagulho", int(valid["Tipo original"].map(lambda x: "CATA BAGULHO" in normalize(x)).sum()), "Quantidade de OS"),
]
cols = st.columns(6)
for col, (label, value, desc) in zip(cols, kpis):
    with col:
        st.markdown(
            f'<div class="kpi"><div class="kpi-label">{label}</div>'
            f'<div class="kpi-value">{fmt(value)}</div><div class="kpi-desc">{desc}</div></div>',
            unsafe_allow_html=True
        )

st.markdown('<div class="section">Resultados físicos calculados</div>', unsafe_allow_html=True)
calc_labels = [
    ("Nivelamento", "nivel", "Comprimento da via × 80%"),
    ("Capinação", "cap", "Comprimento da via × 2"),
    ("Varrição", "varr", "Comprimento da via × 2"),
    ("11 — Manutenção/Reparo em Vias", "manut", "Comprimento da via × 80%"),
    ("2 — Cata-Bagulho", "cata", "1 OS × 3,5 toneladas"),
]
calc_cols = st.columns(5)
for col, (label, kind, desc) in zip(calc_cols, calc_labels):
    value = valid[(valid["kind"] == kind) & (valid["Status"] == "Calculado")]["Resultado"].fillna(0).sum()
    unit = " t" if kind == "cata" else " m"
    decimals = 1 if kind == "cata" else 0
    with col:
        st.markdown(
            f'<div class="metric-card"><small>{label}</small>'
            f'<strong>{fmt(value, decimals)}{unit}</strong><span style="font-size:10px;color:#68786f">{desc}</span></div>',
            unsafe_allow_html=True
        )

with st.expander("Regras de cálculo utilizadas", expanded=False):
    rcols = st.columns(5)
    rules = [
        ("Capinação", "Comprimento da via × 2"),
        ("Varrição", "Comprimento da via × 2"),
        ("Nivelamento", "Comprimento da via × 80%"),
        ("11 — Manutenção/Reparo em Vias", "Comprimento da via × 80%"),
        ("2 — Cata-Bagulho", "1 OS × 3,5 toneladas"),
    ]
    for col, (name, formula) in zip(rcols, rules):
        with col:
            st.markdown(f"**{name}**  \n{formula}")

st.markdown('<div class="section">Números sequenciais faltantes</div>', unsafe_allow_html=True)
if missing:
    st.warning(f"{len(missing)} número(s) faltante(s): " + ", ".join(map(str, missing)))
else:
    st.success("Nenhum número faltante na sequência encontrada.")

area_mask = valid["Bairro"].apply(is_area)
area_df = valid[area_mask].copy()
outside_df = valid[~area_mask].copy()
rate = (len(area_df) / total * 100) if total else 0

st.markdown('<div class="section">Área de atuação — Secretaria de Desenvolvimento Regional de Ouro Fino</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="area-banner"><b>Bairros incluídos nesta análise</b><br>'
    'Ouro Fino Paulista, Itrapoá, KM4, Casa Vermelha, Pouso Alegre e Somma. '
    'Os gráficos consideram somente as OS desses bairros.</div>',
    unsafe_allow_html=True
)
st.metric("OS da área", fmt(len(area_df)))
area_charts(area_df, True)

st.markdown('<div class="section">Fora da área de atuação — demais bairros</div>', unsafe_allow_html=True)
st.metric("OS fora da área", fmt(len(outside_df)))
area_charts(outside_df, False)

st.markdown('<div class="section">Comparativo das duas áreas</div>', unsafe_allow_html=True)
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total de OS válidas", fmt(total))
c2.metric("OS nos seis bairros", fmt(len(area_df)))
c3.metric("OS nos demais bairros", fmt(len(outside_df)))
c4.metric("Percentual da área de atuação", f"{rate:.1f}%".replace(".", ","))

st.markdown('<div class="section">Classificação das OS por ODS — total do período</div>', unsafe_allow_html=True)
ods_df = valid[valid["ODS"].notna()].groupby("ODS").agg(
    Quantidade=("OS", "count"),
    Serviços=("Serviço", lambda s: ", ".join(
        f"{name} ({count})" for name, count in s.value_counts().items()
    ))
).reset_index()
if not ods_df.empty:
    ods_df["Objetivo"] = ods_df["ODS"].map(ODS_NOMES)
    ods_df["ODS_num"] = ods_df["ODS"].str.extract(r"(\d+)").astype(int)
    ods_df = ods_df.sort_values("Quantidade", ascending=False)
    st.dataframe(ods_df[["ODS", "Objetivo", "Quantidade", "Serviços"]],
                 use_container_width=True, hide_index=True)
else:
    st.info("Nenhuma OS classificada nas ODS 6, 11, 12 ou 15.")

st.markdown('<div class="section">Resumo detalhado — análise geral</div>', unsafe_allow_html=True)
summary_parts = []
for category, column in [("Origem", "Origem"), ("Tipo de serviço", "Tipo original"),
                         ("Bairro", "Bairro original"), ("Classificação das OS", "ODS")]:
    values = valid[column].fillna("Não informado").replace("", "Não informado")
    counts = values.value_counts()
    denom = counts.sum()
    for item, quantity in counts.items():
        summary_parts.append({
            "Categoria": category, "Item": item, "Quantidade": int(quantity),
            "%": f"{(quantity / denom * 100):.1f}%".replace(".", ",")
        })
summary_df = pd.DataFrame(summary_parts)
show_table(summary_df, "Distribuição por categoria")

st.markdown('<div class="section">Detalhamento dos cálculos de vias numeradas</div>', unsafe_allow_html=True)
f1, f2, f3, f4 = st.columns([2, 1, 1, 1])
with f1:
    search = st.text_input("Pesquisar OS, rua, bairro, vila ou serviço")
with f2:
    services = ["Todos os serviços"] + sorted(selected["Serviço"].dropna().unique().tolist())
    service_filter = st.selectbox("Serviço", services)
with f3:
    statuses = ["Todos os status"] + sorted(selected["Status"].dropna().unique().tolist())
    status_filter = st.selectbox("Status", statuses)
with f4:
    only_problems = st.checkbox("Somente problemas")

detail = selected.copy()
if search.strip():
    term = normalize(search)
    cols_search = ["OS", "Endereço", "Serviço", "Número da rua", "Via encontrada", "Bairro", "Vila"]
    mask = detail[cols_search].fillna("").astype(str).apply(
        lambda row: term in normalize(" ".join(row)), axis=1
    )
    detail = detail[mask]
if service_filter != "Todos os serviços":
    detail = detail[detail["Serviço"] == service_filter]
if status_filter != "Todos os status":
    detail = detail[detail["Status"] == status_filter]
if only_problems:
    detail = detail[detail["Status"] != "Calculado"]

display_cols = [
    "OS", "Data", "Endereço", "Serviço", "Número da rua", "Via encontrada",
    "Bairro", "Vila", "Comprimento m", "Fórmula", "Resultado", "Unidade",
    "Status", "Problema",
]
detail_view = detail[display_cols].copy()
detail_view["Data"] = detail_view["Data"].dt.strftime("%d/%m/%Y")
for col in ["Comprimento m", "Resultado"]:
    detail_view[col] = detail_view[col].apply(lambda x: "—" if pd.isna(x) else fmt(x, 2))
st.caption(f"{fmt(len(detail_view))} registro(s) encontrado(s) com os filtros atuais.")
st.dataframe(detail_view, use_container_width=True, hide_index=True, height=550)

csv = detail_view.to_csv(index=False, sep=";", encoding="utf-8-sig")
st.download_button(
    "⬇ Baixar detalhamento filtrado (CSV)",
    data=csv,
    file_name="detalhamento_ordens_servico_2026.csv",
    mime="text/csv",
)

with st.expander("Diagnóstico da conexão e integridade dos dados"):
    st.write({
        "Registros totais na tabela ordens_servico": total_db,
        "Ruas carregadas": total_streets,
        "OS de 2026 carregadas": len(df),
        "OS válidas no período": total,
        "OS na área de Ouro Fino": len(area_df),
        "OS nos demais bairros": len(outside_df),
    })
