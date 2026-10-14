import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

st.set_page_config(page_title="Afficionado | Product & Demand Intelligence", page_icon="☕", layout="wide", initial_sidebar_state="expanded")
DATA_PATH = Path(__file__).parent / "data" / "Afficionado Coffee Roasters.xlsx"

# Theme palette. Dark mode is the default and can be switched in the sidebar.
PALETTES = {
    "Dark": {"bg":"#0B0F14", "panel":"#111820", "panel2":"#171F29", "text":"#F3F6FA", "muted":"#9AA9B8", "line":"#273442", "accent":"#78C7FF", "accent2":"#E5A45D", "coffee":"#9C6B45", "grid":"#283542", "sidebar":"#151922", "plot":"#111820", "paper":"#111820", "font":"#EAF0F6"},
    "Light": {"bg":"#F4F6F8", "panel":"#FFFFFF", "panel2":"#F8FAFC", "text":"#202A35", "muted":"#667789", "line":"#DCE4EC", "accent":"#1677B8", "accent2":"#B9783D", "coffee":"#6F4E37", "grid":"#E2E8F0", "sidebar":"#E9EDF2", "plot":"#FFFFFF", "paper":"#FFFFFF", "font":"#263442"}
}

@st.cache_data
def load_workbook_transactions():
    return pd.read_excel(DATA_PATH, sheet_name="Transactions")

@st.cache_data
def load_sample():
    return pd.read_csv(Path(__file__).parent / "data" / "sample_coffee_sales.csv")

def prepare(df):
    df=df.copy(); df.columns=[str(c).strip() for c in df.columns]
    for c in ["transaction_qty", "unit_price"]:
        if c not in df.columns: raise ValueError(f"Required column missing: {c}")
        df[c]=pd.to_numeric(df[c], errors="coerce")
    df=df.dropna(subset=["transaction_qty","unit_price"])
    df=df[(df.transaction_qty>=0)&(df.unit_price>=0)].copy()
    defaults={"store_id":"Store 1","store_location":"Unknown location","product_category":"Uncategorized","product_type":"Unknown product type","product_detail":"Unknown product","transaction_id":None}
    for c,v in defaults.items():
        if c not in df.columns: df[c]=v if v is not None else np.arange(1,len(df)+1)
        df[c]=df[c].fillna("Unknown").astype(str)
    df["revenue"]=df.transaction_qty*df.unit_price
    if "transaction_time" in df.columns:
        def hour_of(v):
            if pd.isna(v): return np.nan
            if hasattr(v,"hour"): return int(v.hour)
            try: return int(str(v).strip().split(":")[0])
            except Exception: return np.nan
        df["hour"]=df.transaction_time.map(hour_of)
    else: df["hour"]=np.nan
    df=df.dropna(subset=["hour"]); df["hour"]=df.hour.astype(int)
    return df

def style_fig(fig, p, height=None, legend=True):
    fig.update_layout(template="plotly_dark" if p is PALETTES["Dark"] else "plotly_white",
        paper_bgcolor=p["paper"], plot_bgcolor=p["plot"], font=dict(color=p["font"], family="Inter, Arial, sans-serif", size=12),
        title_font=dict(size=16, color=p["text"]), margin=dict(l=18,r=18,t=58,b=18),
        legend=dict(bgcolor="rgba(0,0,0,0)", orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1) if legend else dict(visible=False),
        hoverlabel=dict(bgcolor=p["panel2"], font_color=p["text"], bordercolor=p["line"]))
    fig.update_xaxes(gridcolor=p["grid"], zerolinecolor=p["grid"], linecolor=p["line"])
    fig.update_yaxes(gridcolor=p["grid"], zerolinecolor=p["grid"], linecolor=p["line"])
    if height: fig.update_layout(height=height)
    return fig

def money(v): return f"${v:,.0f}" if False else f"${v:,.2f}"

with st.sidebar:
    st.markdown("<div style='font-size:28px;font-weight:800;letter-spacing:-1px'>☕ AFFICIONADO</div><div style='font-size:11px;letter-spacing:2px;opacity:.7;margin-bottom:20px'>COFFEE INTELLIGENCE</div>", unsafe_allow_html=True)
    theme_name=st.radio("Appearance", ["Dark","Light"], horizontal=True, index=0, help="Switch the dashboard theme.")
    uploaded=st.file_uploader("Upload transaction workbook / CSV", type=["xlsx","csv"])
    st.caption("Default source: Transactions sheet from the provided workbook.")
    st.markdown("---")
    metric_label=st.radio("Analyze by", ["Revenue", "Quantity"], horizontal=True)

p=PALETTES[theme_name]
css=f'''<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
:root{{--bg:{p['bg']};--panel:{p['panel']};--panel2:{p['panel2']};--text:{p['text']};--muted:{p['muted']};--line:{p['line']};--accent:{p['accent']};}}
.stApp{{background:radial-gradient(ellipse at 80% -15%, {p['accent']}18 0%, transparent 34%),{p['bg']};color:{p['text']};font-family:Inter,Arial,sans-serif;}}
[data-testid="stHeader"]{{background:transparent;}}
[data-testid="stSidebar"]{{background:{p['sidebar']};border-right:1px solid {p['line']};}}
[data-testid="stSidebar"] *{{color:{p['text']} !important;}}
.block-container{{max-width:1600px;padding-top:1.4rem;padding-bottom:2.5rem;}}
h1,h2,h3,p,label{{color:{p['text']};}}
.hero{{background:linear-gradient(115deg,{p['panel']} 0%,{p['panel2']} 65%,{p['coffee']} 160%);border:1px solid {p['line']};border-radius:24px;padding:30px 34px;margin-bottom:20px;position:relative;overflow:hidden;box-shadow:0 18px 50px #0002;}}
.hero:after{{content:'☕';position:absolute;right:5%;top:-30px;font-size:155px;opacity:.08;transform:rotate(-15deg);}}
.kicker{{font-size:10px;text-transform:uppercase;letter-spacing:2.5px;color:{p['accent']};font-weight:800;margin-bottom:12px;}}
.hero h1{{font-size:clamp(28px,3vw,42px);line-height:1.1;letter-spacing:-1.5px;margin:0 0 10px 0;color:{p['text']};font-weight:800;}}
.hero p{{color:{p['muted']};font-size:14px;max-width:850px;line-height:1.65;margin:0;}}
.badges{{display:flex;gap:8px;flex-wrap:wrap;margin-top:18px;}}
.badge{{border:1px solid {p['line']};background:{p['panel2']};border-radius:100px;padding:6px 10px;font-size:11px;color:{p['text']};}}
.section-eyebrow{{font-size:10px;letter-spacing:2px;text-transform:uppercase;color:{p['accent']};font-weight:800;margin:20px 0 8px 2px;}}
[data-testid="stMetric"]{{background:linear-gradient(145deg,{p['panel']},{p['panel2']});border:1px solid {p['line']};padding:18px 19px;border-radius:18px;box-shadow:0 8px 26px #0001;min-height:112px;}}
[data-testid="stMetricLabel"]{{color:{p['muted']} !important;font-size:10px !important;font-weight:800;letter-spacing:1.1px;}}
[data-testid="stMetricValue"]{{color:{p['text']} !important;font-weight:800;font-size:clamp(22px,2vw,30px) !important;}}
.stTabs [data-baseweb="tab-list"]{{gap:6px;background:{p['panel']};border:1px solid {p['line']};padding:6px;border-radius:15px;}}
.stTabs [data-baseweb="tab"]{{border-radius:10px;padding:10px 15px;font-weight:700;color:{p['muted']};}}
.stTabs [aria-selected="true"]{{background:{p['panel2']} !important;color:{p['accent']} !important;}}
[data-testid="stPlotlyChart"]{{background:{p['panel']};border:1px solid {p['line']};border-radius:17px;padding:7px;box-shadow:0 8px 26px #0001;}}
[data-testid="stDataFrame"]{{border:1px solid {p['line']};border-radius:14px;overflow:hidden;}}
.insight{{background:linear-gradient(135deg,{p['panel']},{p['panel2']});border:1px solid {p['line']};border-radius:16px;padding:15px 17px;min-height:100px;}}
.insight-label{{font-size:10px;text-transform:uppercase;letter-spacing:1.2px;color:{p['muted']};font-weight:800;margin-bottom:7px;}}
.insight-value{{font-size:20px;font-weight:800;color:{p['accent']};margin-bottom:4px;}}
.insight-note{{font-size:11px;line-height:1.45;color:{p['muted']};}}
.stButton button,.stDownloadButton button{{border-radius:10px;font-weight:700;border:1px solid {p['line']};}}
hr{{border-color:{p['line']};}}
[data-testid="stCaptionContainer"]{{color:{p['muted']};}}
@media(max-width:700px){{.hero{{padding:22px;}}.hero:after{{font-size:70px;right:10px;}}}}
</style>'''
st.markdown(css, unsafe_allow_html=True)

try:
    if uploaded:
        raw=pd.read_excel(uploaded, sheet_name="Transactions") if uploaded.name.lower().endswith(".xlsx") else pd.read_csv(uploaded)
    else: raw=load_workbook_transactions()
    df=prepare(raw)
except Exception as e:
    st.error(f"Could not load dataset: {e}"); st.stop()

stores=sorted(df.store_id.unique().tolist())
locations=sorted(df.store_location.unique().tolist())
categories=sorted(df.product_category.unique().tolist())
product_types=sorted(df.product_type.unique().tolist())
with st.sidebar:
    st.markdown("### Dashboard filters")
    selected_locations=st.multiselect("Store location", locations, default=locations)
    selected_categories=st.multiselect("Product category", categories, default=categories)
    selected_types=st.multiselect("Product type", product_types, default=product_types)
    st.caption(f"{len(df):,} cleaned source rows available")

filtered=df[df.store_location.isin(selected_locations)&df.product_category.isin(selected_categories)&df.product_type.isin(selected_types)].copy()
measure="revenue" if metric_label=="Revenue" else "transaction_qty"
measure_title="Revenue ($)" if metric_label=="Revenue" else "Units sold"
total_rev=filtered.revenue.sum(); total_qty=filtered.transaction_qty.sum(); n_tx=len(filtered)
peak_hour=int(filtered.groupby("hour").transaction_qty.sum().idxmax()) if not filtered.empty else 0
avg_ticket=total_rev/n_tx if n_tx else 0

st.markdown(f'''<div class="hero"><div class="kicker">Retail analytics / product optimization / revenue intelligence</div><h1>Afficionado Coffee Roasters</h1><p>A premium command center for understanding what sells, where revenue comes from, and when customers create the biggest demand spikes. Built around your supplied transaction workbook.</p><div class="badges"><span class="badge">◈ Product mix</span><span class="badge">↗ Revenue contribution</span><span class="badge">◷ Peak-hour analytics</span><span class="badge">◎ Store comparison</span><span class="badge">◐ {theme_name} mode</span></div></div><div class="section-eyebrow">Executive snapshot</div>''',unsafe_allow_html=True)

m1,m2,m3,m4,m5=st.columns(5)
m1.metric("TOTAL REVENUE",f"${total_rev:,.0f}")
m2.metric("UNITS SOLD",f"{total_qty:,.0f}")
m3.metric("TRANSACTIONS",f"{n_tx:,}")
m4.metric("PEAK HOUR",f"{peak_hour:02d}:00–{peak_hour+1:02d}:00")
m5.metric("AVG. REVENUE / ROW",f"${avg_ticket:,.2f}")

bycat=filtered.groupby("product_category",as_index=False).agg(revenue=("revenue","sum"),quantity=("transaction_qty","sum"),transactions=("transaction_id","count"))
bycat=bycat.sort_values(measure,ascending=False)
byproduct=filtered.groupby(["product_category","product_type"],as_index=False).agg(revenue=("revenue","sum"),quantity=("transaction_qty","sum"),transactions=("transaction_id","count"))
byproduct=byproduct.sort_values(measure,ascending=False)
by_store=filtered.groupby(["store_id","store_location"],as_index=False).agg(revenue=("revenue","sum"),quantity=("transaction_qty","sum"),transactions=("transaction_id","count"))
product_col="product_detail" if "product_detail" in filtered.columns else "product_type"
prod=filtered.groupby(product_col,as_index=False).agg(revenue=("revenue","sum"),quantity=("transaction_qty","sum"),transactions=("transaction_id","count"))
prod=prod.sort_values(measure,ascending=False)
topcat=str(bycat.iloc[0].product_category) if not bycat.empty else "—"
topprod=str(prod.iloc[0][product_col]) if not prod.empty else "—"
topstore=str(by_store.sort_values("revenue",ascending=False).iloc[0].store_location) if not by_store.empty else "—"
i1,i2,i3=st.columns(3)
i1.markdown(f'<div class="insight"><div class="insight-label">Leading category</div><div class="insight-value">{topcat}</div><div class="insight-note">Top category by {metric_label.lower()} in the current filter selection.</div></div>',unsafe_allow_html=True)
i2.markdown(f'<div class="insight"><div class="insight-label">Top product</div><div class="insight-value">{topprod}</div><div class="insight-note">Highest-contributing individual product detail.</div></div>',unsafe_allow_html=True)
i3.markdown(f'<div class="insight"><div class="insight-label">Leading location</div><div class="insight-value">{topstore}</div><div class="insight-note">Highest revenue location within the current filters.</div></div>',unsafe_allow_html=True)

overview, products_tab, pareto_tab, peaks_tab, stores_tab, data_tab = st.tabs(["◈ Executive Overview","▦ Product Optimization","∿ Pareto Contribution","◷ Peak Demand","⌖ Store Performance","▤ Data & Insights"])

with overview:
    st.markdown("### Revenue contribution at a glance")
    st.caption("The visuals below are interactive: hover for exact values, zoom, or use the legend to focus on a category.")
    a,b=st.columns([0.92,1.35])
    with a:
        fig=px.pie(bycat,names="product_category",values=measure,hole=.62,title=f"{metric_label} share by category",color_discrete_sequence=["#78C7FF","#1479C9","#FF8B8B","#F04444","#67D9A0","#2EB7A8","#F2C15B","#F28E2B","#8A62D6"])
        fig.update_traces(textposition="outside",textinfo="label+percent",pull=[.035]+[0]*max(0,len(bycat)-1),marker=dict(line=dict(color=p['panel'],width=2)))
        style_fig(fig,p,410,False); st.plotly_chart(fig,use_container_width=True)
    with b:
        fig=px.treemap(byproduct,path=["product_category","product_type"],values=measure,color="product_category",title=f"Category → product type | {metric_label}",color_discrete_sequence=["#78C7FF","#1679C4","#FF8F8F","#E33E42","#5ED49A","#2CA99A","#E8BB4B","#F08B24","#7656CA"])
        fig.update_traces(root_color=p['panel'],marker=dict(line=dict(color=p['panel'],width=2)),textfont=dict(size=12))
        style_fig(fig,p,410,False); st.plotly_chart(fig,use_container_width=True)
    left,right=st.columns(2)
    with left:
        f=px.bar(by_store.sort_values(measure),x=measure,y="store_location",orientation="h",title=f"Store contribution · {metric_label}",color=measure,color_continuous_scale=[p['accent'],p['accent2']],text_auto=".2s")
        f.update_layout(coloraxis_showscale=False,xaxis_title=measure_title,yaxis_title="")
        style_fig(f,p,360,False);st.plotly_chart(f,use_container_width=True)
    with right:
        hourly=filtered.groupby("hour",as_index=False).agg(quantity=("transaction_qty","sum"),revenue=("revenue","sum"))
        hourly=pd.DataFrame({"hour":range(24)}).merge(hourly,on="hour",how="left").fillna(0)
        f=px.area(hourly,x="hour",y=measure,title=f"Observed hourly profile · {metric_label}",markers=True,color_discrete_sequence=[p['accent']])
        accent_hex=p['accent'].lstrip('#')
        accent_rgba=f"rgba({int(accent_hex[0:2],16)},{int(accent_hex[2:4],16)},{int(accent_hex[4:6],16)},0.18)"
        f.update_traces(line=dict(width=3),fillcolor=accent_rgba,marker=dict(size=5))
        f.update_layout(xaxis=dict(title="Hour of day",dtick=2),yaxis_title=measure_title)
        style_fig(f,p,360,False);st.plotly_chart(f,use_container_width=True)

with products_tab:
    st.markdown("### Product optimization matrix")
    st.caption("Bubble size reflects revenue contribution; placement compares popularity with revenue.")
    if not prod.empty:
        scatter=filtered.groupby([product_col,"product_category"],as_index=False).agg(revenue=("revenue","sum"),quantity=("transaction_qty","sum"),transactions=("transaction_id","count"))
        f=px.scatter(scatter,x="quantity",y="revenue",size="revenue",color="product_category",hover_name=product_col, size_max=48,opacity=.78,title="Product popularity vs revenue",color_discrete_sequence=["#78C7FF","#1479C9","#FF8B8B","#E33E42","#67D9A0","#2EB7A8","#F2C15B","#F28E2B","#8A62D6"])
        f.add_vline(x=scatter.quantity.median(),line_dash="dot",line_color=p['muted'],opacity=.8)
        f.add_hline(y=scatter.revenue.median(),line_dash="dot",line_color=p['muted'],opacity=.8)
        f.update_layout(xaxis_title="Units sold (popularity)",yaxis_title="Revenue ($)")
        style_fig(f,p,500,True);st.plotly_chart(f,use_container_width=True)
        st.markdown("**How to read the quadrants**")
        q1,q2,q3,q4=st.columns(4)
        q1.markdown(f'<div class="insight"><div class="insight-label">High popularity / high revenue</div><div class="insight-note">Core menu drivers: protect availability and promote.</div></div>',unsafe_allow_html=True)
        q2.markdown(f'<div class="insight"><div class="insight-label">Low popularity / high revenue</div><div class="insight-note">Premium niche items: test placement and targeted marketing.</div></div>',unsafe_allow_html=True)
        q3.markdown(f'<div class="insight"><div class="insight-label">High popularity / low revenue</div><div class="insight-note">Review price, cost, and upsell opportunities.</div></div>',unsafe_allow_html=True)
        q4.markdown(f'<div class="insight"><div class="insight-label">Low popularity / low revenue</div><div class="insight-note">Consider limited stock, repositioning, or menu review.</div></div>',unsafe_allow_html=True)
        st.dataframe(scatter.sort_values("revenue",ascending=False).rename(columns={product_col:"Product","product_category":"Category","revenue":"Revenue ($)","quantity":"Units sold","transactions":"Transaction rows"}),use_container_width=True,hide_index=True)

with pareto_tab:
    st.markdown("### Pareto analysis — cumulative revenue contribution")
    st.caption("Ranks products from highest to lowest revenue and shows the cumulative percentage of revenue.")
    if not prod.empty:
        pareto=prod.sort_values("revenue",ascending=False).copy(); total=pareto.revenue.sum()
        pareto["cumulative_pct"]=pareto.revenue.cumsum()/total*100 if total else 0
        pareto["rank"]=np.arange(1,len(pareto)+1)
        f=go.Figure()
        f.add_trace(go.Bar(x=pareto[product_col],y=pareto.revenue,name="Revenue",marker_color=p['accent'],hovertemplate="%{x}<br>Revenue: $%{y:,.2f}<extra></extra>"))
        f.add_trace(go.Scatter(x=pareto[product_col],y=pareto.cumulative_pct,name="Cumulative %",yaxis="y2",mode="lines+markers",line=dict(color="#EF4444",width=3),marker=dict(size=5),hovertemplate="%{x}<br>Cumulative: %{y:.1f}%<extra></extra>"))
        f.add_hline(y=80,line_dash="dot",line_color=p['muted'],annotation_text="80% revenue threshold",annotation_position="top left")
        f.update_layout(title="Products ranked by revenue",xaxis_title="Products (ranked by revenue)",yaxis=dict(title="Revenue ($)"),yaxis2=dict(title="Cumulative %",overlaying="y",side="right",range=[0,105],ticksuffix="%"),showlegend=True)
        style_fig(f,p,500,True);st.plotly_chart(f,use_container_width=True)
        count80=int((pareto.cumulative_pct<80).sum()+1) if total else 0
        share=count80/len(pareto)*100 if len(pareto) else 0
        st.markdown(f'<div class="insight"><div class="insight-value">{count80} of {len(pareto)} products ({share:.1f}%)</div><div class="insight-note">Products required to reach approximately 80% of observed revenue. Use this to prioritize availability and menu review.</div></div>',unsafe_allow_html=True)
        st.dataframe(pareto[["rank",product_col,"revenue","quantity","cumulative_pct"]].rename(columns={"rank":"Rank",product_col:"Product","revenue":"Revenue ($)","quantity":"Units sold","cumulative_pct":"Cumulative revenue %"}).round(2),use_container_width=True,hide_index=True)

with peaks_tab:
    st.markdown("### Peak demand intelligence")
    hourly=filtered.groupby("hour",as_index=False).agg(quantity=("transaction_qty","sum"),revenue=("revenue","sum"),transactions=("transaction_id","count"))
    hourly=pd.DataFrame({"hour":range(24)}).merge(hourly,on="hour",how="left").fillna(0)
    hourly["time_window"]=hourly.hour.map(lambda h:f"{h:02d}:00–{h+1:02d}:00")
    f=px.bar(hourly,x="time_window",y=measure,title=f"Total {metric_label.lower()} by hour",color=measure,color_continuous_scale=[p['accent'],p['accent2']],text_auto=".2s")
    f.update_layout(coloraxis_showscale=False,xaxis_title="Hour of day",yaxis_title=measure_title)
    style_fig(f,p,430,False);st.plotly_chart(f,use_container_width=True)
    t=hourly.sort_values("quantity",ascending=False).head(8)
    st.markdown("**Busiest trading hours**")
    st.dataframe(t[["time_window","quantity","revenue","transactions"]].rename(columns={"time_window":"Time window","quantity":"Units sold","revenue":"Revenue ($)","transactions":"Transaction rows"}),use_container_width=True,hide_index=True)
    st.info("The workbook contains time-of-day but no calendar transaction date. This analysis ranks total observed activity by hour; it cannot infer weekday patterns or forecast tomorrow's demand.")

with stores_tab:
    st.markdown("### Store performance")
    a,b=st.columns(2)
    with a:
        f=px.bar(by_store.sort_values("revenue"),x="revenue",y="store_location",orientation="h",color="revenue",color_continuous_scale=[p['accent'],p['accent2']],text_auto=".2s",title="Revenue by location")
        f.update_layout(coloraxis_showscale=False,xaxis_title="Revenue ($)",yaxis_title="")
        style_fig(f,p,450,False);st.plotly_chart(f,use_container_width=True)
    with b:
        f=px.scatter(by_store,x="quantity",y="revenue",size="transactions",color="store_location",hover_name="store_location",title="Store volume vs revenue",size_max=50)
        f.update_layout(xaxis_title="Units sold",yaxis_title="Revenue ($)")
        style_fig(f,p,450,True);st.plotly_chart(f,use_container_width=True)
    st.dataframe(by_store.sort_values("revenue",ascending=False).rename(columns={"store_id":"Store ID","store_location":"Location","revenue":"Revenue ($)","quantity":"Units sold","transactions":"Transaction rows"}),use_container_width=True,hide_index=True)

with data_tab:
    st.markdown("### Data quality & export")
    x1,x2,x3=st.columns(3);x1.metric("Rows after cleaning",f"{len(df):,}");x2.metric("Store locations",f"{df.store_location.nunique()}");x3.metric("Product categories",f"{df.product_category.nunique()}")
    missing=raw.isna().sum().rename("missing_values").reset_index().rename(columns={"index":"column"})
    st.markdown("**Missing values in source workbook**");st.dataframe(missing,use_container_width=True,hide_index=True)
    st.markdown("**Filtered transaction preview**");st.dataframe(filtered.head(150),use_container_width=True,hide_index=True)
    st.download_button("↓ Download filtered transactions CSV",filtered.to_csv(index=False).encode("utf-8"),"afficionado_filtered_transactions.csv","text/csv",type="primary")
    st.download_button("↓ Download product summary CSV",prod.to_csv(index=False).encode("utf-8"),"afficionado_product_summary.csv","text/csv")
    st.markdown("**Forecasting readiness**")
    st.warning("The supplied Transactions sheet has year and transaction_time, but no true calendar date. Daily/weekly forecasting requires a transaction_date or transaction_datetime column. No synthetic dates are invented by this dashboard.")

st.markdown(f'<div style="text-align:center;color:{p["muted"]};font-size:10px;letter-spacing:1.4px;padding:24px 0 8px">AFFICIONADO COFFEE ROASTERS · PRODUCT OPTIMIZATION & REVENUE INTELLIGENCE · {theme_name.upper()} THEME</div>',unsafe_allow_html=True)
