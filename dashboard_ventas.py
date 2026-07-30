
import io
from datetime import datetime

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "axes.edgecolor": "#D7DEE6",
    "axes.linewidth": 0.6,
    "text.color": "#1B2C42",
    "axes.labelcolor": "#1B2C42",
    "xtick.color": "#5B7089",
    "ytick.color": "#5B7089",
    "figure.facecolor": "white",
    "axes.facecolor": "white",
})
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage,
)

# --------------------------------------------------------------------------
# Configuración de página y paleta (estética tipo Power BI: navy + teal/rosa)
# --------------------------------------------------------------------------
st.set_page_config(page_title="Panel de Ventas", layout="wide", page_icon="📊")

BG = "#0A1B30"
CARD = "#0F2744"
CARD2 = "#122E4E"
BORDER = "#1E3A5C"
TEXT = "#EFF4F9"
MUTED = "#8496AF"
PRIMARY = "#2EC4B6"   # teal
ACCENT = "#FF5DA2"    # rosa/magenta
POS = "#3DDC97"
NEG = "#FF6B6B"

CEPA_COLORS = {
    "MALBEC": "#2EC4B6", "CHARDONNAY": "#FFB84D", "PINOT NOIR": "#FF5DA2",
    "PINOT-PINOT": "#A78BFA", "CABERNET SAUVIGNON": "#4C9AFF",
    "SAUVIGNON BLANC": "#9AE6B4", "SYRAH": "#FF7A59", "BONARDA": "#6366F1",
    "TORRONTES": "#D4E157",
}
DEFAULT_CEPA_COLOR = "#7E93AD"

CAT_PALETTE = [PRIMARY, ACCENT, "#FFB84D", "#A78BFA", "#4C9AFF", "#9AE6B4", "#FF7A59", "#6366F1"]

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@600;700&family=Inter:wght@400;500;600;700&family=IBM+Plex+Mono:wght@500;600&display=swap');
.stApp {{ background-color: {BG}; color: {TEXT}; font-family: 'Inter', sans-serif; }}
section[data-testid="stSidebar"] {{ background-color: {CARD}; border-right: 1px solid {BORDER}; }}
h1, h2, h3 {{ font-family: 'Poppins', sans-serif !important; color: {TEXT} !important; }}
.eyebrow {{ font-size: 11px; letter-spacing: .12em; color: {PRIMARY}; font-weight: 700; }}
.kpi-card {{ background: linear-gradient(155deg, {CARD2}, {CARD}); border: 1px solid {BORDER};
             border-radius: 16px; padding: 16px 18px; position: relative; overflow: hidden; }}
.kpi-card::before {{ content: ""; position: absolute; top: 0; left: 0; width: 4px; height: 100%;
                      background: {PRIMARY}; }}
.kpi-icon {{ font-size: 18px; margin-bottom: 6px; }}
.kpi-label {{ font-size: 11.5px; color: {MUTED}; margin-bottom: 4px; }}
.kpi-value {{ font-family: 'IBM Plex Mono', monospace; font-size: 22px; font-weight: 600; color: {TEXT}; }}
.kpi-sub {{ font-size: 11px; margin-top: 4px; font-weight: 600; }}
div[data-testid="stDataFrame"] {{ border: 1px solid {BORDER}; border-radius: 10px; }}
.section-title {{ font-family: 'Poppins', sans-serif; font-size: 17px; font-weight: 700; margin: 6px 0 10px 0; }}
.note-box {{ background: {CARD2}; border: 1px dashed {BORDER}; border-radius: 10px; padding: 14px 16px;
             color: {MUTED}; font-size: 12.5px; }}
button[data-baseweb="tab"] {{ font-family: 'Inter', sans-serif !important; font-weight: 600; }}
</style>
""", unsafe_allow_html=True)

EXPECTED_COLS = [
    "fecha_facturacion", "n_comp", "nombre_ven", "razon_soci", "localidad",
    "nom_zona", "nomprovin", "nomrubro", "cepa", "proveedor", "CANAL",
    "des_articu", "cantidad", "precio_net", "importe_ne", "costo_tota",
    "markup", "porc_utili", "bonif_fac",
]

OPTIONAL_COLS = {
    "cond_venta": "Condición de venta", "nomrech": "Motivo de rechazo",
    "nom_depos": "Depósito", "cantccargo": "Cantidad con cargo",
    "cantscargo": "Cantidad sin cargo", "nomlinea": "Línea de producto",
    "cod_vended": "Código de vendedor",
}

SAMPLE_DATA = [
    dict(fecha_facturacion="01/07/2026", n_comp="0012-00000178", nombre_ven="MODICA", razon_soci="LUPI GUILLERMO ROBERTO", localidad="SAN CARLOS DE BARILOCHE", nom_zona="PATAGONIA RN + NQN", nomprovin="RIO NEGRO", nomrubro="AS BRAVAS", cepa="MALBEC", proveedor=190, CANAL="TRADICIONAL", des_articu="CZ ENEMIGO AS BRAVAS MALBEC 6X750CC", cantidad=-1, precio_net=-327272.73, importe_ne=-327272.73, costo_tota=-256843.6363, markup=0.0, porc_utili=-27.42, bonif_fac=-327272.72),
    dict(fecha_facturacion="02/07/2026", n_comp="0020-00000099", nombre_ven="MODICA", razon_soci="BESARES LEONARDO ALBERTO", localidad="SAN CARLOS DE BARILOCHE", nom_zona="PATAGONIA RN + NQN", nomprovin="RIO NEGRO", nomrubro="CATENA ZAPATA", cepa="CHARDONNAY", proveedor=190, CANAL="TRADICIONAL", des_articu="CZ VINOS DE PARCELA WHITE BONES CHARDONNAY 750", cantidad=1, precio_net=248181.82, importe_ne=248181.82, costo_tota=149825.4545, markup=0.6565, porc_utili=65.65, bonif_fac=133636.36),
    dict(fecha_facturacion="02/07/2026", n_comp="0020-00000099", nombre_ven="MODICA", razon_soci="BESARES LEONARDO ALBERTO", localidad="SAN CARLOS DE BARILOCHE", nom_zona="PATAGONIA RN + NQN", nomprovin="RIO NEGRO", nomrubro="CATENA ZAPATA", cepa="CHARDONNAY", proveedor=190, CANAL="TRADICIONAL", des_articu="CZ VINOS DE PARCELA WHITE STONES CHARDONNAY 750", cantidad=1, precio_net=195000.0, importe_ne=195000.0, costo_tota=117720.0, markup=0.6565, porc_utili=65.65, bonif_fac=105000.0),
    dict(fecha_facturacion="02/07/2026", n_comp="0020-00000099", nombre_ven="MODICA", razon_soci="BESARES LEONARDO ALBERTO", localidad="SAN CARLOS DE BARILOCHE", nom_zona="PATAGONIA RN + NQN", nomprovin="RIO NEGRO", nomrubro="CATENA ZAPATA", cepa="MALBEC", proveedor=190, CANAL="TRADICIONAL", des_articu="CZ VINOS DE PARCELA MUNDUS BACILUS MALBEC 750", cantidad=1, precio_net=602727.28, importe_ne=602727.28, costo_tota=363861.8182, markup=0.6565, porc_utili=65.65, bonif_fac=324545.45),
    dict(fecha_facturacion="02/07/2026", n_comp="0020-00000099", nombre_ven="MODICA", razon_soci="BESARES LEONARDO ALBERTO", localidad="SAN CARLOS DE BARILOCHE", nom_zona="PATAGONIA RN + NQN", nomprovin="RIO NEGRO", nomrubro="CATENA ZAPATA", cepa="MALBEC", proveedor=190, CANAL="TRADICIONAL", des_articu="CZ VINOS DE PARCELA RIVER MALBEC 750CC 2022", cantidad=1, precio_net=283636.37, importe_ne=283636.37, costo_tota=171229.0909, markup=0.6565, porc_utili=65.65, bonif_fac=152727.27),
    dict(fecha_facturacion="02/07/2026", n_comp="0020-00000099", nombre_ven="MODICA", razon_soci="BESARES LEONARDO ALBERTO", localidad="SAN CARLOS DE BARILOCHE", nom_zona="PATAGONIA RN + NQN", nomprovin="RIO NEGRO", nomrubro="CATENA ZAPATA", cepa="MALBEC", proveedor=190, CANAL="TRADICIONAL", des_articu="CZ VINOS DE PARCELA FORTUNATERRAE MALBEC 750CC", cantidad=1, precio_net=230454.54, importe_ne=230454.54, costo_tota=139123.6363, markup=0.6565, porc_utili=65.65, bonif_fac=124090.91),
    dict(fecha_facturacion="02/07/2026", n_comp="0008-00011287", nombre_ven="VILLEGAS", razon_soci="MDQ JUSTEM SA", localidad="MAR DEL PLATA", nom_zona="BS AS + PAMPA + CABA", nomprovin="BS AS", nomrubro="BODEGAS MANOS NEGRAS", cepa="PINOT NOIR", proveedor=2513, CANAL="TRADICIONAL", des_articu="MANOS NEGRAS PINOT NOIR 750CC 2025", cantidad=3, precio_net=49537.19, importe_ne=148611.57, costo_tota=96322.314, markup=0.5429, porc_utili=54.29, bonif_fac=126595.04),
    dict(fecha_facturacion="02/07/2026", n_comp="0008-00011287", nombre_ven="VILLEGAS", razon_soci="MDQ JUSTEM SA", localidad="MAR DEL PLATA", nom_zona="BS AS + PAMPA + CABA", nomprovin="BS AS", nomrubro="BODEGAS MANOS NEGRAS", cepa="MALBEC", proveedor=2513, CANAL="TRADICIONAL", des_articu="MANOS NEGRAS MALBEC 750CC 2025", cantidad=4, precio_net=42842.975, importe_ne=171371.9, costo_tota=111074.3804, markup=0.5429, porc_utili=54.29, bonif_fac=145983.47),
    dict(fecha_facturacion="02/07/2026", n_comp="0008-00011287", nombre_ven="VILLEGAS", razon_soci="MDQ JUSTEM SA", localidad="MAR DEL PLATA", nom_zona="BS AS + PAMPA + CABA", nomprovin="BS AS", nomrubro="BODEGAS MANOS NEGRAS", cepa="MALBEC", proveedor=2513, CANAL="TRADICIONAL", des_articu="MANOS NEGRAS MALBEC 750CC 2025 (Devolución)", cantidad=1, precio_net=0.0, importe_ne=0.0, costo_tota=27768.5951, markup=-1.0, porc_utili=-100.0, bonif_fac=79338.84),
    dict(fecha_facturacion="02/07/2026", n_comp="0012-00001687", nombre_ven="MODICA", razon_soci="ZORREGUIETA MARTIN", localidad="SAN CARLOS DE BARILOCHE", nom_zona="PATAGONIA RN + NQN", nomprovin="RIO NEGRO", nomrubro="CATENA ZAPATA", cepa="PINOT-PINOT", proveedor=190, CANAL="TRADICIONAL", des_articu="CZ DV CATENA PINOT-PINOT 750CC 2024", cantidad=5, precio_net=57235.536, importe_ne=286177.68, costo_tota=249546.9, markup=0.1468, porc_utili=14.68, bonif_fac=349772.73),
]

DIMENSIONS = {
    "Vendedor": "nombre_ven", "Cliente": "razon_soci", "Provincia": "nomprovin",
    "Zona": "nom_zona", "Rubro / Bodega": "nomrubro", "Canal": "CANAL",
    "Producto": "des_articu",
}

PROVINCE_COORDS = {
    "BS AS": (-36.6, -60.0), "BUENOS AIRES": (-36.6, -60.0), "CABA": (-34.6, -58.4),
    "CIUDAD DE BUENOS AIRES": (-34.6, -58.4), "RIO NEGRO": (-40.8, -63.0),
    "NEUQUEN": (-38.9, -68.0), "MENDOZA": (-34.9, -68.8), "CORDOBA": (-31.4, -64.2),
    "SANTA FE": (-31.6, -60.7), "SALTA": (-24.8, -65.4), "JUJUY": (-23.6, -65.3),
    "TUCUMAN": (-26.8, -65.2), "ENTRE RIOS": (-32.0, -59.5), "CHUBUT": (-43.3, -68.0),
    "SANTA CRUZ": (-49.3, -69.0), "TIERRA DEL FUEGO": (-54.8, -68.3),
    "CORRIENTES": (-27.5, -58.0), "MISIONES": (-26.9, -54.6), "FORMOSA": (-25.2, -59.7),
    "CHACO": (-26.8, -60.4), "LA PAMPA": (-36.6, -64.3), "SAN LUIS": (-33.3, -66.3),
    "SAN JUAN": (-31.5, -68.5), "LA RIOJA": (-29.4, -66.8), "CATAMARCA": (-28.5, -65.8),
    "SANTIAGO DEL ESTERO": (-27.8, -64.3),
}


def cepa_color(name: str) -> str:
    return CEPA_COLORS.get(str(name).upper(), DEFAULT_CEPA_COLOR)


def fmt_money(n: float) -> str:
    return "$" + f"{n:,.0f}".replace(",", ".")


def fmt_pct(n: float) -> str:
    return f"{n:.1f}%"


def has_col(df: pd.DataFrame, col: str) -> bool:
    return col in df.columns and df[col].astype(str).str.strip().replace("nan", "").ne("").any()


def note(msg: str):
    st.markdown(f'<div class="note-box">ℹ️ {msg}</div>', unsafe_allow_html=True)


@st.cache_data
def load_sample() -> pd.DataFrame:
    return pd.DataFrame(SAMPLE_DATA)


def load_uploaded(file) -> pd.DataFrame:
    if file.name.lower().endswith(".csv"):
        return pd.read_csv(file)
    return pd.read_excel(file)


def prepare(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    numeric_cols = ["cantidad", "precio_net", "importe_ne", "costo_tota",
                     "markup", "porc_utili", "bonif_fac", "cantccargo", "cantscargo"]
    for c in numeric_cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)
    if "fecha_facturacion" in df.columns:
        df["fecha_dt"] = pd.to_datetime(df["fecha_facturacion"], format="%d/%m/%Y", errors="coerce")
    else:
        df["fecha_dt"] = pd.NaT
    for c in EXPECTED_COLS:
        if c not in df.columns:
            df[c] = ""
    return df


st.sidebar.markdown('<div class="eyebrow">FUENTE DE DATOS</div>', unsafe_allow_html=True)
uploaded = st.sidebar.file_uploader("Cargar Excel multidimensional / CSV", type=["xlsx", "xls", "csv"])

if uploaded is not None:
    try:
        raw = load_uploaded(uploaded)
        source_label = uploaded.name
    except Exception as e:
        st.sidebar.error(f"No se pudo leer el archivo: {e}")
        raw = load_sample()
        source_label = "Datos de muestra"
else:
    raw = load_sample()
    source_label = "Datos de muestra"

df = prepare(raw)

missing = [c for c in EXPECTED_COLS if c not in raw.columns]
if missing and uploaded is not None:
    st.sidebar.warning(f"Faltan columnas esperadas: {', '.join(missing)}")

extra_present = [c for c in OPTIONAL_COLS if has_col(df, c)]
if uploaded is not None and extra_present:
    st.sidebar.success(f"Columnas adicionales detectadas: {', '.join(extra_present)}")

st.sidebar.markdown('<div class="eyebrow" style="margin-top:18px;">FILTROS</div>', unsafe_allow_html=True)

def multiselect_filter(label, col):
    opts = sorted([o for o in df[col].dropna().unique() if o != ""])
    return st.sidebar.multiselect(label, opts)

f_vend = multiselect_filter("Vendedor", "nombre_ven")
f_cepa = multiselect_filter("Cepa", "cepa")
f_canal = multiselect_filter("Canal", "CANAL")
f_prov = multiselect_filter("Provincia", "nomprovin")
search = st.sidebar.text_input("Buscar (cliente, producto, comprobante)")

mask = pd.Series(True, index=df.index)
if f_vend: mask &= df["nombre_ven"].isin(f_vend)
if f_cepa: mask &= df["cepa"].isin(f_cepa)
if f_canal: mask &= df["CANAL"].isin(f_canal)
if f_prov: mask &= df["nomprovin"].isin(f_prov)
if search:
    s = search.lower()
    mask &= (
        df["razon_soci"].astype(str).str.lower().str.contains(s)
        | df["des_articu"].astype(str).str.lower().str.contains(s)
        | df["nombre_ven"].astype(str).str.lower().str.contains(s)
        | df["n_comp"].astype(str).str.lower().str.contains(s)
    )
fdf = df[mask]

st.markdown('<div class="eyebrow">📊 ANÁLISIS MULTIDIMENSIONAL DE VENTAS</div>', unsafe_allow_html=True)
st.markdown("# Panel de Ventas")
st.caption(f"Fuente: {source_label} · {len(fdf)} de {len(df)} registros · {fdf['n_comp'].nunique()} comprobantes")

revenue = fdf["importe_ne"].sum()
cost = fdf["costo_tota"].sum()
qty = fdf["cantidad"].sum()
invoices = fdf["n_comp"].nunique()
margin = revenue - cost
margin_pct = (margin / revenue * 100) if revenue != 0 else 0
avg_ticket = (revenue / invoices) if invoices > 0 else 0
bonif_total = fdf["bonif_fac"].sum()

prof_color = POS if margin_pct >= 0 else NEG
arrow = "▲" if margin_pct >= 0 else "▼"
st.markdown(f"""
<div style="background:linear-gradient(135deg, {CARD2}, {CARD});
            border:1px solid {BORDER}; border-radius:18px; padding:22px 26px;
            margin-bottom:18px; display:flex; align-items:center; gap:28px; flex-wrap:wrap;">
    <div>
        <div class="eyebrow" style="margin-bottom:6px;">RENTABILIDAD</div>
        <div style="font-family:'Poppins',sans-serif; font-size:46px; font-weight:700;
                    color:{prof_color}; line-height:1;">{arrow} {fmt_pct(margin_pct)}</div>
        <div style="color:{MUTED}; font-size:12.5px; margin-top:6px;">
            Margen bruto de {fmt_money(margin)} sobre {fmt_money(revenue)} facturados
        </div>
    </div>
</div>
""", unsafe_allow_html=True)


def kpi_row(defs):
    cols = st.columns(len(defs))
    for col, (icon, label, value, sub, sub_color) in zip(cols, defs):
        sub_html = f'<div class="kpi-sub" style="color:{sub_color}">{sub}</div>' if sub else ""
        col.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-icon">{icon}</div>
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value}</div>
            {sub_html}
        </div>""", unsafe_allow_html=True)


kpi_row([
    ("💹", "Margen bruto", fmt_money(margin), fmt_pct(margin_pct) + " de rentabilidad", prof_color),
    ("💰", "Facturado", fmt_money(revenue), None, MUTED),
    ("📦", "Costo total", fmt_money(cost), None, MUTED),
    ("🧮", "Unidades vendidas", f"{qty:,.0f}".replace(",", "."), None, MUTED),
    ("🧾", "Comprobantes", f"{invoices:,}".replace(",", "."), None, MUTED),
    ("🎯", "Ticket promedio", fmt_money(avg_ticket), None, MUTED),
])

st.markdown("<br>", unsafe_allow_html=True)

by_date = (
    fdf.dropna(subset=["fecha_dt"])
    .groupby("fecha_dt")
    .agg(revenue=("importe_ne", "sum"), qty=("cantidad", "sum"))
    .reset_index()
    .sort_values("fecha_dt")
)
cepa_agg = fdf.groupby("cepa", dropna=False)["importe_ne"].sum().reset_index()
cepa_agg = cepa_agg[cepa_agg["cepa"] != ""].sort_values("importe_ne", ascending=False)

tab_comercial, tab_rentabilidad, tab_logistica, tab_ranking = st.tabs(
    ["📊 Comercial", "💹 Rentabilidad", "🚚 Logística", "🏆 Ranking y Fuerza de Ventas"]
)

with tab_comercial:
    ca, cb = st.columns([1, 1])
    with ca:
        st.markdown('<div class="section-title">Participación por canal</div>', unsafe_allow_html=True)
        canal_agg = fdf.groupby("CANAL", dropna=False)["importe_ne"].sum().reset_index()
        canal_agg = canal_agg[canal_agg["CANAL"] != ""]
        if canal_agg.empty:
            note("No hay datos de canal en el archivo actual.")
        else:
            figc = go.Figure(go.Pie(
                labels=canal_agg["CANAL"], values=canal_agg["importe_ne"], hole=0.6,
                marker=dict(colors=CAT_PALETTE, line=dict(color=CARD, width=3)),
                textinfo="percent", textfont=dict(color=TEXT, size=12, family="Inter"),
            ))
            figc.update_layout(plot_bgcolor=CARD, paper_bgcolor=CARD, font=dict(color=TEXT, family="Inter"),
                                height=260, margin=dict(l=0, r=0, t=10, b=10),
                                legend=dict(orientation="h", y=-0.1, font=dict(size=10)))
            st.plotly_chart(figc, use_container_width=True)
        if has_col(fdf, "cond_venta"):
            cond_agg = fdf.groupby("cond_venta")["importe_ne"].sum().reset_index()
            figcv = go.Figure(go.Pie(labels=cond_agg["cond_venta"], values=cond_agg["importe_ne"], hole=0.6,
                                      marker=dict(colors=CAT_PALETTE), textinfo="percent"))
            figcv.update_layout(plot_bgcolor=CARD, paper_bgcolor=CARD, font=dict(color=TEXT, family="Inter"),
                                 height=220, margin=dict(l=0, r=0, t=10, b=10),
                                 title=dict(text="Por condición de venta", font=dict(size=12)))
            st.plotly_chart(figcv, use_container_width=True)

    with cb:
        st.markdown('<div class="section-title">Evolución temporal</div>', unsafe_allow_html=True)
        if len(by_date) >= 2 and by_date["revenue"].iloc[-2] != 0:
            day_change = (by_date["revenue"].iloc[-1] - by_date["revenue"].iloc[-2]) / abs(by_date["revenue"].iloc[-2]) * 100
            dc_color = POS if day_change >= 0 else NEG
            dc_arrow = "▲" if day_change >= 0 else "▼"
            st.markdown(f'<span style="color:{dc_color}; font-weight:600;">{dc_arrow} {abs(day_change):.1f}% vs. período anterior</span>', unsafe_allow_html=True)

        fig3 = go.Figure()
        fig3.add_trace(go.Scatter(
            x=by_date["fecha_dt"], y=by_date["revenue"], mode="lines+markers+text",
            line=dict(color=PRIMARY, width=3, shape="spline", smoothing=0.4),
            marker=dict(size=9, color=PRIMARY, line=dict(color=CARD, width=2)),
            fill="tozeroy", fillcolor="rgba(46,196,182,0.15)",
            text=[fmt_money(v) for v in by_date["revenue"]], textposition="top center",
            textfont=dict(size=11, color=TEXT, family="Inter"),
            hovertemplate="<b>%{x|%d/%m/%Y}</b><br>Facturado: %{y:,.0f}<extra></extra>",
        ))
        fig3.update_layout(
            plot_bgcolor=CARD, paper_bgcolor=CARD, font=dict(color=TEXT, family="Inter"), height=300,
            margin=dict(l=0, r=10, t=30, b=10), showlegend=False,
            xaxis=dict(showgrid=False, tickfont=dict(size=11)),
            yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)", tickprefix="$", tickfont=dict(size=11)),
            hoverlabel=dict(bgcolor=CARD, font_family="Inter", bordercolor=PRIMARY),
        )
        st.plotly_chart(fig3, use_container_width=True)

with tab_rentabilidad:
    r1, r2, r3 = st.columns(3)
    r1.markdown(f"""<div class="kpi-card"><div class="kpi-icon">💸</div>
        <div class="kpi-label">Bonificaciones otorgadas</div>
        <div class="kpi-value">{fmt_money(bonif_total)}</div></div>""", unsafe_allow_html=True)
    r2.markdown(f"""<div class="kpi-card"><div class="kpi-icon">✅</div>
        <div class="kpi-label">Utilidad neta real</div>
        <div class="kpi-value" style="color:{prof_color}">{fmt_money(margin)}</div></div>""", unsafe_allow_html=True)
    prods_neg = fdf[fdf["porc_utili"] < 0]["des_articu"].nunique()
    r3.markdown(f"""<div class="kpi-card"><div class="kpi-icon">⚠️</div>
        <div class="kpi-label">Productos con margen negativo</div>
        <div class="kpi-value" style="color:{NEG}">{prods_neg}</div></div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    rc1, rc2 = st.columns([1, 1])
    with rc1:
        st.markdown('<div class="section-title">Margen vs. bonificación por producto</div>', unsafe_allow_html=True)
        prod = fdf.groupby("des_articu", dropna=False).agg(
            importe_ne=("importe_ne", "sum"), bonif=("bonif_fac", "sum"),
            margin_pct=("porc_utili", "mean"), cepa=("cepa", "first"),
        ).reset_index()
        prod = prod[prod["des_articu"] != ""]
        prod["bonif_pct"] = (prod["bonif"] / prod["importe_ne"].replace(0, 1) * 100).clip(-100, 200)
        if prod.empty:
            note("No hay productos para graficar con los filtros actuales.")
        else:
            figs = px.scatter(
                prod, x="bonif_pct", y="margin_pct", size=prod["importe_ne"].abs(),
                color="cepa", color_discrete_map=CEPA_COLORS,
                hover_name="des_articu", labels={"bonif_pct": "% Bonificación", "margin_pct": "% Margen"},
            )
            figs.update_traces(marker=dict(line=dict(width=1, color=CARD), opacity=0.85))
            figs.update_layout(
                plot_bgcolor=CARD, paper_bgcolor=CARD, font=dict(color=TEXT, family="Inter"), height=340,
                margin=dict(l=10, r=10, t=10, b=10), legend=dict(font=dict(size=9)),
                xaxis=dict(gridcolor="rgba(255,255,255,0.05)", zeroline=True, zerolinecolor=BORDER),
                yaxis=dict(gridcolor="rgba(255,255,255,0.05)", zeroline=True, zerolinecolor=BORDER),
            )
            st.plotly_chart(figs, use_container_width=True)

    with rc2:
        st.markdown('<div class="section-title">Costo vs. facturado por rubro</div>', unsafe_allow_html=True)
        rubro_col = "nomlinea" if has_col(fdf, "nomlinea") else "nomrubro"
        rubro = fdf.groupby(rubro_col, dropna=False).agg(
            costo=("costo_tota", "sum"), facturado=("importe_ne", "sum")
        ).reset_index()
        rubro = rubro[rubro[rubro_col] != ""].sort_values("facturado", ascending=False).head(8)
        if rubro.empty:
            note("No hay datos de rubro/línea para graficar.")
        else:
            figr = go.Figure()
            figr.add_trace(go.Bar(x=rubro[rubro_col], y=rubro["facturado"], name="Facturado", marker_color=PRIMARY))
            figr.add_trace(go.Bar(x=rubro[rubro_col], y=rubro["costo"], name="Costo", marker_color=ACCENT))
            figr.update_layout(
                barmode="group", plot_bgcolor=CARD, paper_bgcolor=CARD,
                font=dict(color=TEXT, family="Inter"), height=340,
                margin=dict(l=0, r=10, t=10, b=60), legend=dict(orientation="h", y=1.1, font=dict(size=10)),
                xaxis=dict(tickangle=-30, tickfont=dict(size=9), gridcolor="rgba(0,0,0,0)"),
                yaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
            )
            st.plotly_chart(figr, use_container_width=True)

with tab_logistica:
    lc1, lc2 = st.columns([1, 1])
    with lc1:
        st.markdown('<div class="section-title">Motivos de rechazo</div>', unsafe_allow_html=True)
        if has_col(fdf, "nomrech"):
            rech = fdf[fdf["nomrech"] != ""]["nomrech"].value_counts().reset_index()
            rech.columns = ["motivo", "casos"]
            figrech = go.Figure(go.Bar(x=rech["casos"], y=rech["motivo"], orientation="h",
                                        marker_color=ACCENT))
            figrech.update_layout(plot_bgcolor=CARD, paper_bgcolor=CARD, font=dict(color=TEXT, family="Inter"),
                                   height=260, margin=dict(l=0, r=10, t=10, b=10),
                                   yaxis=dict(autorange="reversed"))
            st.plotly_chart(figrech, use_container_width=True)
        else:
            note("El archivo actual no incluye la columna 'nomrech' (motivos de rechazo). "
                 "Subí un export que la incluya para habilitar este gráfico.")

        st.markdown('<div class="section-title">Eficiencia de depósitos</div>', unsafe_allow_html=True)
        if has_col(fdf, "nom_depos") and (has_col(fdf, "cantccargo") or has_col(fdf, "cantscargo")):
            dep = fdf.groupby("nom_depos").agg(
                con_cargo=("cantccargo", "sum"), sin_cargo=("cantscargo", "sum")
            ).reset_index()
            st.dataframe(dep, use_container_width=True, height=180)
        else:
            note("Faltan las columnas 'nom_depos' / 'cantccargo' / 'cantscargo' para este análisis.")

    with lc2:
        st.markdown('<div class="section-title">Seguimiento geográfico</div>', unsafe_allow_html=True)
        geo = fdf.groupby("nomprovin", dropna=False)["importe_ne"].sum().reset_index()
        geo = geo[geo["nomprovin"] != ""]
        geo["lat"] = geo["nomprovin"].str.upper().str.strip().map(lambda p: PROVINCE_COORDS.get(p, (None, None))[0])
        geo["lon"] = geo["nomprovin"].str.upper().str.strip().map(lambda p: PROVINCE_COORDS.get(p, (None, None))[1])
        geo_ok = geo.dropna(subset=["lat", "lon"])
        if geo_ok.empty:
            note("No se pudieron ubicar las provincias en el mapa (nombres no reconocidos).")
        else:
            figmap = go.Figure(go.Scattergeo(
                lat=geo_ok["lat"], lon=geo_ok["lon"], text=geo_ok["nomprovin"],
                marker=dict(size=(geo_ok["importe_ne"].abs() / geo_ok["importe_ne"].abs().max() * 40 + 8),
                            color=PRIMARY, opacity=0.75, line=dict(width=1, color=CARD)),
                hovertemplate="<b>%{text}</b><br>Facturado: %{customdata:,.0f}<extra></extra>",
                customdata=geo_ok["importe_ne"],
            ))
            figmap.update_geos(scope="south america", showland=True, landcolor=CARD2,
                                showcountries=True, countrycolor=BORDER, bgcolor=CARD,
                                center=dict(lat=-38, lon=-64), projection_scale=3.2)
            figmap.update_layout(paper_bgcolor=CARD, height=340, margin=dict(l=0, r=0, t=10, b=10))
            st.plotly_chart(figmap, use_container_width=True)
        if geo.shape[0] > geo_ok.shape[0]:
            faltantes = geo[geo["lat"].isna()]["nomprovin"].tolist()
            note(f"Sin coordenadas para: {', '.join(faltantes)}.")

with tab_ranking:
    st.markdown('<div class="section-title">Ranking por dimensión</div>', unsafe_allow_html=True)
    dim_label = st.selectbox("Dimensión", list(DIMENSIONS.keys()), label_visibility="collapsed")
    dim_col = DIMENSIONS[dim_label]
    rank = (
        fdf.groupby(dim_col, dropna=False)
        .agg(revenue=("importe_ne", "sum"), cost=("costo_tota", "sum"),
             qty=("cantidad", "sum"), count=("n_comp", "count"))
        .reset_index()
        .rename(columns={dim_col: "name"})
    )
    total_rev = rank["revenue"].sum() or 1
    rank["pct"] = rank["revenue"] / total_rev * 100
    rank["margin_pct"] = (rank["revenue"] - rank["cost"]) / rank["revenue"].replace(0, 1) * 100
    rank = rank.sort_values("revenue", ascending=False).head(8)

    n = len(rank)
    def blend(t):
        a = tuple(int(PRIMARY[i:i+2], 16) for i in (1, 3, 5))
        b = tuple(int(ACCENT[i:i+2], 16) for i in (1, 3, 5))
        rgb = [round(a[i] + (b[i] - a[i]) * t) for i in range(3)]
        return f"rgb({rgb[0]},{rgb[1]},{rgb[2]})"
    bar_colors = [blend(i / max(n - 1, 1)) for i in range(n)]

    fig = go.Figure(go.Bar(
        x=rank["revenue"], y=rank["name"], orientation="h",
        marker=dict(color=bar_colors, line=dict(width=0)),
        text=[f"<b>{fmt_pct(p)}</b>" for p in rank["pct"]], textposition="outside",
        textfont=dict(size=13, family="Inter", color=TEXT),
        customdata=rank[["pct", "margin_pct", "qty"]],
        hovertemplate="<b>%{y}</b><br>Facturado: %{x:,.0f}<br>Participación: %{customdata[0]:.1f}%<br>Margen: %{customdata[1]:.1f}%<br>Unidades: %{customdata[2]:,.0f}<extra></extra>",
    ))
    fig.update_layout(
        plot_bgcolor=CARD, paper_bgcolor=CARD, font=dict(color=TEXT, family="Inter"),
        height=320, bargap=0.35,
        margin=dict(l=0, r=50, t=10, b=10),
        yaxis=dict(autorange="reversed", showgrid=False, tickfont=dict(size=12)),
        xaxis=dict(showticklabels=False, showgrid=False, zeroline=False),
        hoverlabel=dict(bgcolor=CARD, font_family="Inter", bordercolor=PRIMARY),
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="section-title">Matriz de clientes (drill-down: cliente → rubro → producto)</div>', unsafe_allow_html=True)
    tree = fdf[(fdf["razon_soci"] != "") & (fdf["nomrubro"] != "") & (fdf["des_articu"] != "")]
    if tree.empty:
        note("No hay suficientes datos para armar la matriz de clientes con los filtros actuales.")
    else:
        treed = tree.groupby(["razon_soci", "nomrubro", "des_articu"], dropna=False).agg(
            importe_ne=("importe_ne", "sum"), porc_utili=("porc_utili", "mean")
        ).reset_index()
        treed = treed[treed["importe_ne"] > 0]
        figt = px.treemap(
            treed, path=["razon_soci", "nomrubro", "des_articu"], values="importe_ne",
            color="porc_utili", color_continuous_scale=[NEG, "#3A4A63", PRIMARY],
            color_continuous_midpoint=0,
        )
        figt.update_layout(paper_bgcolor=CARD, font=dict(color=TEXT, family="Inter"), height=420,
                            margin=dict(l=0, r=0, t=10, b=10),
                            coloraxis_colorbar=dict(title="Margen %", tickfont=dict(size=9)))
        figt.update_traces(textfont=dict(size=11))
        st.plotly_chart(figt, use_container_width=True)

st.markdown('<div class="section-title">Lectura rápida</div>', unsafe_allow_html=True)


def leader(col):
    g = fdf.groupby(col, dropna=False)["importe_ne"].sum()
    g = g[g.index != ""]
    if g.empty or g.sum() == 0:
        return "Sin datos", 0.0
    top = g.idxmax()
    return str(top), g.max() / g.sum() * 100


q1, q2, q3, q4 = st.columns(4)
for col_widget, (title, dim) in zip(
    [q1, q2, q3, q4],
    [("Vendedor líder", "nombre_ven"), ("Cepa líder", "cepa"),
     ("Canal principal", "CANAL"), ("Provincia principal", "nomprovin")],
):
    name, pct = leader(dim)
    col_widget.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">{title}</div>
        <div class="kpi-value" style="font-size:16px;">{name}</div>
        <div class="kpi-sub" style="color:{PRIMARY};">{pct:.1f}% del facturado filtrado</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

st.markdown('<div class="section-title">Detalle de transacciones</div>', unsafe_allow_html=True)
table_cols = ["fecha_facturacion", "nombre_ven", "razon_soci", "des_articu",
              "cepa", "cantidad", "importe_ne", "porc_utili"]
table_view = fdf[table_cols].rename(columns={
    "fecha_facturacion": "Fecha", "nombre_ven": "Vendedor", "razon_soci": "Cliente",
    "des_articu": "Producto", "cepa": "Cepa", "cantidad": "Cant.",
    "importe_ne": "Facturado", "porc_utili": "Margen %",
})
st.dataframe(
    table_view.style.format({"Facturado": "${:,.0f}", "Margen %": "{:.1f}%"}),
    use_container_width=True, height=340,
)


def _fig_to_png_bytes(fig) -> bytes:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=160, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf.read()


def _blend_hex(c1, c2, t):
    a = tuple(int(c1[i:i+2], 16) for i in (1, 3, 5))
    b = tuple(int(c2[i:i+2], 16) for i in (1, 3, 5))
    r = [round(a[i] + (b[i] - a[i]) * t) for i in range(3)]
    return "#%02x%02x%02x" % tuple(r)


def _ranking_chart_png(rank_df: pd.DataFrame) -> bytes:
    fig, ax = plt.subplots(figsize=(7, 3.2))
    names = rank_df["name"].astype(str).tolist()[::-1]
    values = rank_df["revenue"].tolist()[::-1]
    pcts = rank_df["pct"].tolist()[::-1]
    n = len(values)
    bar_colors = [_blend_hex(PRIMARY, ACCENT, i / max(n - 1, 1)) for i in range(n)][::-1]
    bars = ax.barh(names, values, color=bar_colors, height=0.62, zorder=3)
    ax.xaxis.grid(True, color="#E4EAF0", linewidth=0.8, zorder=0)
    ax.set_axisbelow(True)
    for b, v, p in zip(bars, values, pcts):
        ax.text(b.get_width() + max(values) * 0.015, b.get_y() + b.get_height() / 2,
                f"{p:.1f}%", va="center", fontsize=9, fontweight="bold", color="#0F2744",
                bbox=dict(boxstyle="round,pad=0.25", facecolor="#EAF7F5", edgecolor="none"))
    ax.set_xticks([])
    ax.spines[["top", "right", "bottom"]].set_visible(False)
    ax.tick_params(axis="y", labelsize=9.5, length=0)
    fig.tight_layout()
    return _fig_to_png_bytes(fig)


def _cepa_chart_png(cepa_df: pd.DataFrame) -> bytes:
    fig, ax = plt.subplots(figsize=(4.4, 4.4))
    colors_ = [cepa_color(c) for c in cepa_df["cepa"]]
    total = cepa_df["importe_ne"].sum()
    wedges, _, autotexts = ax.pie(
        cepa_df["importe_ne"], colors=colors_, autopct="%1.1f%%",
        pctdistance=0.82, startangle=90, counterclock=False,
        wedgeprops=dict(width=0.38, edgecolor="white", linewidth=2),
        textprops=dict(fontsize=9, color="white", fontweight="bold"),
    )
    ax.text(0, 0.06, "$" + f"{total:,.0f}".replace(",", "."), ha="center", va="center",
            fontsize=13, fontweight="bold", color="#0F2744")
    ax.text(0, -0.12, "total", ha="center", va="center", fontsize=8, color="#5B7089")
    ax.legend(wedges, cepa_df["cepa"], loc="center left", bbox_to_anchor=(1.02, 0.5),
               fontsize=8.5, frameon=False)
    fig.tight_layout()
    return _fig_to_png_bytes(fig)


def _timeline_chart_png(by_date_df: pd.DataFrame) -> bytes:
    fig, ax = plt.subplots(figsize=(7, 2.8))
    x = range(len(by_date_df))
    y = by_date_df["revenue"].tolist()
    labels = by_date_df["fecha_dt"].dt.strftime("%d/%m").tolist()
    ax.fill_between(x, y, color=PRIMARY, alpha=0.18, zorder=2)
    ax.plot(x, y, color=PRIMARY, marker="o", markersize=7, linewidth=2.5,
            markerfacecolor=PRIMARY, markeredgecolor="white", zorder=3)
    top = max(y) if y else 1
    for i, v in enumerate(y):
        ax.text(i, v + top * 0.06, "$" + f"{v:,.0f}".replace(",", "."),
                 ha="center", fontsize=8.5, fontweight="bold", color="#0F2744",
                 bbox=dict(boxstyle="round,pad=0.22", facecolor="#EAF7F5", edgecolor="none"))
    ax.set_xticks(list(x))
    ax.set_xticklabels(labels)
    ax.yaxis.grid(True, color="#E4EAF0", linewidth=0.8, zorder=0)
    ax.set_axisbelow(True)
    ax.set_yticks([])
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.tick_params(labelsize=9.5, length=0)
    ax.margins(y=0.25)
    fig.tight_layout()
    return _fig_to_png_bytes(fig)


def generate_pdf_report(fdf, kpis, rank_df, cepa_df, by_date_df, dim_label, source_label, filtros_txt) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=1.5 * cm, bottomMargin=1.5 * cm,
                             leftMargin=1.5 * cm, rightMargin=1.5 * cm)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("TitleTeal", parent=styles["Title"], textColor=colors.HexColor("#0F2744"))
    h2 = ParagraphStyle("H2Teal", parent=styles["Heading2"], textColor=colors.HexColor("#159A8E"),
                          spaceBefore=14, spaceAfter=6)
    small = ParagraphStyle("Small", parent=styles["Normal"], fontSize=8.5, textColor=colors.HexColor("#5B7089"))

    story = [
        Paragraph("Panel de Ventas — Reporte", title_style),
        Paragraph(f"Generado el {datetime.now().strftime('%d/%m/%Y %H:%M')} · Fuente: {source_label}", small),
        Paragraph(f"Filtros aplicados: {filtros_txt}", small),
        Spacer(1, 12),
    ]

    kpi_rows = [
        ["Rentabilidad (margen %)", fmt_pct(kpis["margin_pct"])],
        ["Margen bruto", fmt_money(kpis["margin"])],
        ["Facturado", fmt_money(kpis["revenue"])],
        ["Costo total", fmt_money(kpis["cost"])],
        ["Unidades vendidas", f"{kpis['qty']:,.0f}".replace(",", ".")],
        ["Comprobantes", f"{kpis['invoices']:,}".replace(",", ".")],
        ["Ticket promedio", fmt_money(kpis["avg_ticket"])],
    ]
    kpi_table = Table(kpi_rows, colWidths=[7 * cm, 7 * cm])
    kpi_table.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#5B7089")),
        ("FONTNAME", (1, 0), (1, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 13),
        ("TEXTCOLOR", (1, 0), (1, 0), colors.HexColor("#159A8E")),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LINEBELOW", (0, 0), (-1, -2), 0.5, colors.HexColor("#DCE6EE")),
        ("LINEBELOW", (0, 0), (-1, 0), 0.8, colors.HexColor("#159A8E")),
    ]))
    story += [Paragraph("Resumen ejecutivo", h2), kpi_table, Spacer(1, 10)]

    if not rank_df.empty:
        story.append(Paragraph(f"Ranking por {dim_label.lower()}", h2))
        story.append(RLImage(io.BytesIO(_ranking_chart_png(rank_df)), width=17 * cm, height=17 * cm * 3.2 / 7))
        rank_table_data = [["#", dim_label, "Facturado", "% part.", "Margen %"]] + [
            [str(i + 1), str(r["name"])[:40], fmt_money(r["revenue"]), fmt_pct(r["pct"]), fmt_pct(r["margin_pct"])]
            for i, r in rank_df.reset_index(drop=True).iterrows()
        ]
        t = Table(rank_table_data, colWidths=[1 * cm, 7 * cm, 4 * cm, 2.5 * cm, 2.5 * cm])
        t.setStyle(TableStyle([
            ("FONTSIZE", (0, 0), (-1, -1), 8.5),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#159A8E")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("ALIGN", (2, 0), (-1, -1), "RIGHT"),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#DCE6EE")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F3F8FA")]),
        ]))
        story += [Spacer(1, 6), t, Spacer(1, 10)]

    if not cepa_df.empty:
        story.append(Paragraph("Participación por cepa", h2))
        story.append(RLImage(io.BytesIO(_cepa_chart_png(cepa_df)), width=10 * cm, height=10 * cm))
        story.append(Spacer(1, 10))

    if not by_date_df.empty:
        story.append(Paragraph("Evolución temporal", h2))
        story.append(RLImage(io.BytesIO(_timeline_chart_png(by_date_df)), width=17 * cm, height=17 * cm * 2.8 / 7))
        story.append(Spacer(1, 10))

    top_tx = fdf.sort_values("importe_ne", ascending=False).head(15)
    if not top_tx.empty:
        story.append(Paragraph("Top 15 transacciones por monto", h2))
        tx_data = [["Fecha", "Vendedor", "Cliente", "Producto", "Cant.", "Facturado", "Margen %"]] + [
            [r["fecha_facturacion"], r["nombre_ven"], str(r["razon_soci"])[:22], str(r["des_articu"])[:28],
             f"{r['cantidad']:.0f}", fmt_money(r["importe_ne"]), fmt_pct(r["porc_utili"])]
            for _, r in top_tx.iterrows()
        ]
        t2 = Table(tx_data, colWidths=[1.8 * cm, 2.3 * cm, 3.5 * cm, 5.5 * cm, 1.3 * cm, 2.6 * cm, 2 * cm])
        t2.setStyle(TableStyle([
            ("FONTSIZE", (0, 0), (-1, -1), 7.5),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0F2744")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("ALIGN", (4, 0), (-1, -1), "RIGHT"),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#DCE6EE")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F3F8FA")]),
        ]))
        story += [Spacer(1, 6), t2]

    doc.build(story)
    buf.seek(0)
    return buf.read()


kpis_dict = dict(revenue=revenue, cost=cost, margin=margin, margin_pct=margin_pct,
                  qty=qty, invoices=invoices, avg_ticket=avg_ticket)
filtros_aplicados = ", ".join([p for p in [
    f"Vendedor: {', '.join(f_vend)}" if f_vend else None,
    f"Cepa: {', '.join(f_cepa)}" if f_cepa else None,
    f"Canal: {', '.join(f_canal)}" if f_canal else None,
    f"Provincia: {', '.join(f_prov)}" if f_prov else None,
] if p]) or "Ninguno (vista completa)"

col_dl1, col_dl2 = st.columns(2)
with col_dl1:
    csv_bytes = fdf[EXPECTED_COLS].to_csv(index=False).encode("utf-8")
    st.download_button("⬇ Descargar vista filtrada (CSV)", data=csv_bytes,
                        file_name="ventas_filtrado.csv", mime="text/csv", use_container_width=True)
with col_dl2:
    if st.button("📄 Generar reporte PDF", use_container_width=True):
        st.session_state["pdf_bytes"] = generate_pdf_report(
            fdf, kpis_dict, rank, cepa_agg, by_date, dim_label, source_label, filtros_aplicados
        )
    if "pdf_bytes" in st.session_state:
        st.download_button("⬇ Descargar PDF generado", data=st.session_state["pdf_bytes"],
                            file_name=f"reporte_ventas_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                            mime="application/pdf", use_container_width=True)

st.caption(f"Panel construido a partir de la plantilla de ventas cargada · {len(EXPECTED_COLS)} campos base + columnas opcionales detectadas automáticamente")
