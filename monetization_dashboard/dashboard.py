"""
Dashboard de Monetizacao - v3
Versao com filtros dinamicos e visao estrategica
"""
import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
import subprocess

# =============================================================================
# CONFIGURACAO
# =============================================================================
st.set_page_config(
    page_title="Monetization Dashboard",
    page_icon="💰",
    layout="wide"
)

SUPABASE_URL = "https://prvkmzstyedepvlbppyo.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBydmttenN0eWVkZXB2bGJwcHlvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDQxNDY3MTQsImV4cCI6MjA1OTcyMjcxNH0.T0aspHrF0tz1G6iVOBIO3zgvs1g5vvQcb25jhGriQGo"

headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}

# =============================================================================
# FUNCOES DE DADOS
# =============================================================================

@st.cache_data(ttl=300)
def load_channels():
    resp = requests.get(f"{SUPABASE_URL}/rest/v1/yt_channels", headers=headers)
    return pd.DataFrame(resp.json()) if resp.status_code == 200 else pd.DataFrame()

@st.cache_data(ttl=300)
def load_daily_metrics():
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/yt_daily_metrics",
        params={"order": "date.desc"},
        headers=headers
    )
    if resp.status_code == 200:
        df = pd.DataFrame(resp.json())
        if not df.empty:
            df['date'] = pd.to_datetime(df['date'])
        return df
    return pd.DataFrame()

# =============================================================================
# CARREGAR DADOS
# =============================================================================
channels_df = load_channels()
metrics_df = load_daily_metrics()

if metrics_df.empty:
    st.error("Nenhum dado encontrado. Rode a coleta primeiro.")
    st.stop()

# Mapear channel_id para nome
channel_names = dict(zip(channels_df['channel_id'], channels_df['channel_name']))

# =============================================================================
# SIDEBAR - FILTROS E ACOES
# =============================================================================
with st.sidebar:
    st.title("⚙️ Controles")

    # Acoes
    st.subheader("Acoes")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Coletar", use_container_width=True, help="Rodar coleta de dados"):
            with st.spinner("Coletando..."):
                result = subprocess.run(
                    ["python", "C:/Users/User-OEM/Desktop/content-factory/monetization_dashboard/coleta_diaria.py"],
                    capture_output=True, text=True
                )
                if result.returncode == 0:
                    st.success("OK!")
                    st.cache_data.clear()
                else:
                    st.error("Erro")
    with col2:
        if st.button("🔃 Atualizar", use_container_width=True, help="Recarregar dados"):
            st.cache_data.clear()
            st.rerun()

    st.divider()

    # Filtro de periodo
    st.subheader("📅 Periodo")

    periodo = st.radio(
        "Selecione o periodo:",
        ["Ultimos 7 dias", "Ultimos 14 dias", "Ultimos 30 dias", "Este mes", "Mes passado", "Todo periodo"],
        index=0,
        label_visibility="collapsed"
    )

    # Calcular datas baseado no periodo
    today = datetime.now().date()
    last_date_with_data = metrics_df['date'].max().date()

    if periodo == "Ultimos 7 dias":
        start_filter = last_date_with_data - timedelta(days=6)
        end_filter = last_date_with_data
    elif periodo == "Ultimos 14 dias":
        start_filter = last_date_with_data - timedelta(days=13)
        end_filter = last_date_with_data
    elif periodo == "Ultimos 30 dias":
        start_filter = last_date_with_data - timedelta(days=29)
        end_filter = last_date_with_data
    elif periodo == "Este mes":
        start_filter = today.replace(day=1)
        end_filter = last_date_with_data
    elif periodo == "Mes passado":
        first_this_month = today.replace(day=1)
        last_month_end = first_this_month - timedelta(days=1)
        start_filter = last_month_end.replace(day=1)
        end_filter = last_month_end
    else:  # Todo periodo
        start_filter = metrics_df['date'].min().date()
        end_filter = last_date_with_data

    st.caption(f"{start_filter.strftime('%d/%m/%Y')} - {end_filter.strftime('%d/%m/%Y')}")

    st.divider()

    # Filtro de canal
    st.subheader("📺 Canal")

    channel_options = ["Todos os canais"] + list(channels_df['channel_name'])
    selected_channel = st.selectbox(
        "Selecione o canal:",
        channel_options,
        index=0,
        label_visibility="collapsed"
    )

# =============================================================================
# FILTRAR DADOS
# =============================================================================

# Filtrar por periodo
filtered_df = metrics_df[
    (metrics_df['date'].dt.date >= start_filter) &
    (metrics_df['date'].dt.date <= end_filter)
].copy()

# Filtrar por canal se necessario
if selected_channel != "Todos os canais":
    selected_channel_id = channels_df[channels_df['channel_name'] == selected_channel]['channel_id'].values[0]
    filtered_df = filtered_df[filtered_df['channel_id'] == selected_channel_id]

# Verificar se tem dados
if filtered_df.empty:
    st.warning(f"Nenhum dado encontrado para o periodo selecionado.")
    st.stop()

# =============================================================================
# CALCULOS DO PERIODO
# =============================================================================

# Agregar por dia
daily_totals = filtered_df.groupby(filtered_df['date'].dt.date).agg({
    'revenue': 'sum',
    'views': 'sum'
}).reset_index()
daily_totals.columns = ['date', 'revenue', 'views']
daily_totals = daily_totals.sort_values('date')

# Apenas dias com receita
monetized_days = daily_totals[daily_totals['revenue'] > 0].copy()

if monetized_days.empty:
    st.warning("Nenhum dia com receita no periodo selecionado.")
    st.stop()

# Metricas do periodo
total_revenue_period = monetized_days['revenue'].sum()
total_days_period = len(monetized_days)
avg_per_day_period = total_revenue_period / total_days_period if total_days_period > 0 else 0

# Ultimo dia e anterior
latest = monetized_days.iloc[-1]
latest_date = latest['date']
latest_revenue = latest['revenue']

if len(monetized_days) >= 2:
    previous = monetized_days.iloc[-2]
    previous_date = previous['date']
    previous_revenue = previous['revenue']
    delta_pct = ((latest_revenue - previous_revenue) / previous_revenue * 100) if previous_revenue > 0 else 0
else:
    previous_date = None
    previous_revenue = 0
    delta_pct = 0

# Projecao mensal (baseada nos ultimos 7 dias COM DADOS, nao no periodo filtrado)
last_7_days_data = metrics_df[metrics_df['date'].dt.date > (last_date_with_data - timedelta(days=7))]
if selected_channel != "Todos os canais":
    last_7_days_data = last_7_days_data[last_7_days_data['channel_id'] == selected_channel_id]

last_7_revenue = last_7_days_data.groupby(last_7_days_data['date'].dt.date)['revenue'].sum()
last_7_revenue = last_7_revenue[last_7_revenue > 0]
avg_last_7 = last_7_revenue.mean() if len(last_7_revenue) > 0 else 0
monthly_projection = avg_last_7 * 30

# =============================================================================
# HEADER
# =============================================================================
st.title("💰 Dashboard de Monetizacao")

# Info do periodo e canal
subtitle = f"📅 {periodo}"
if selected_channel != "Todos os canais":
    subtitle += f" | 📺 {selected_channel}"
subtitle += f" | Ultimo dado: {last_date_with_data.strftime('%d/%m/%Y')}"
st.caption(subtitle)

# =============================================================================
# METRICAS PRINCIPAIS
# =============================================================================
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label=f"💵 Total no Periodo",
        value=f"${total_revenue_period:.2f}",
        delta=f"{total_days_period} dias com receita",
        help=f"Soma de receita de {start_filter.strftime('%d/%m')} a {end_filter.strftime('%d/%m')}"
    )

with col2:
    st.metric(
        label=f"📊 Media/Dia (Periodo)",
        value=f"${avg_per_day_period:.2f}",
        help="Media diaria no periodo selecionado"
    )

with col3:
    delta_str = f"{delta_pct:+.1f}% vs {previous_date.strftime('%d/%m')}" if previous_date else None
    st.metric(
        label=f"📅 Ultimo Dia ({latest_date.strftime('%d/%m')})",
        value=f"${latest_revenue:.2f}",
        delta=delta_str,
        help="Receita do ultimo dia com dados"
    )

with col4:
    st.metric(
        label="📈 Projecao Mensal",
        value=f"${monthly_projection:.2f}",
        delta=f"Media ${avg_last_7:.2f}/dia (ult. 7d)",
        help="Projecao baseada na media dos ultimos 7 dias"
    )

# =============================================================================
# GRAFICO PRINCIPAL - RECEITA DIARIA
# =============================================================================
st.divider()

tab1, tab2, tab3 = st.tabs(["📈 Receita Diaria", "📊 Crescimento", "🏆 Por Canal"])

with tab1:
    # Grafico de barras
    fig = px.bar(
        monetized_days,
        x='date',
        y='revenue',
        text='revenue',
        labels={'date': 'Data', 'revenue': 'Receita ($)'}
    )
    fig.update_traces(
        texttemplate='$%{text:.0f}',
        textposition='outside',
        marker_color='#00D26A'
    )
    fig.update_layout(
        hovermode='x unified',
        yaxis_title='Receita ($)',
        xaxis_title='',
        height=400
    )
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    # Calcular variacao
    monetized_days_calc = monetized_days.copy()
    monetized_days_calc['prev_revenue'] = monetized_days_calc['revenue'].shift(1)
    monetized_days_calc['growth'] = monetized_days_calc['revenue'] - monetized_days_calc['prev_revenue']
    monetized_days_calc['growth_pct'] = (monetized_days_calc['growth'] / monetized_days_calc['prev_revenue'] * 100)

    # Grafico de delta
    fig_growth = go.Figure()

    colors = ['#00D26A' if x >= 0 else '#FF4B4B' for x in monetized_days_calc['growth'].fillna(0)]

    fig_growth.add_trace(go.Bar(
        x=monetized_days_calc['date'],
        y=monetized_days_calc['growth'],
        marker_color=colors,
        text=[f"${x:+.0f}" if pd.notna(x) else "" for x in monetized_days_calc['growth']],
        textposition='outside'
    ))

    fig_growth.update_layout(
        title="Variacao Dia a Dia ($)",
        yaxis_title='Variacao ($)',
        xaxis_title='',
        height=400,
        showlegend=False
    )

    st.plotly_chart(fig_growth, use_container_width=True)

    # Tabela de crescimento
    growth_table = monetized_days_calc[['date', 'revenue', 'growth', 'growth_pct']].copy()
    growth_table = growth_table.sort_values('date', ascending=False)
    growth_table['date'] = growth_table['date'].apply(lambda x: x.strftime('%d/%m/%Y'))
    growth_table.columns = ['Data', 'Receita', 'Variacao ($)', 'Variacao (%)']
    growth_table['Receita'] = growth_table['Receita'].apply(lambda x: f"${x:.2f}")
    growth_table['Variacao ($)'] = growth_table['Variacao ($)'].apply(lambda x: f"${x:+.2f}" if pd.notna(x) else "-")
    growth_table['Variacao (%)'] = growth_table['Variacao (%)'].apply(lambda x: f"{x:+.1f}%" if pd.notna(x) else "-")

    st.dataframe(growth_table, hide_index=True, use_container_width=True)

with tab3:
    if selected_channel == "Todos os canais":
        # Calcular metricas por canal no periodo
        channel_stats = []
        for _, ch in channels_df.iterrows():
            channel_id = ch['channel_id']
            channel_name = ch['channel_name']

            # Filtrar metricas do canal no periodo
            channel_metrics = filtered_df[filtered_df['channel_id'] == channel_id]
            channel_revenue = channel_metrics['revenue'].sum()

            # Dias com receita no periodo
            days_with_revenue = len(channel_metrics[channel_metrics['revenue'] > 0])

            # Media por dia
            avg_day = channel_revenue / days_with_revenue if days_with_revenue > 0 else 0

            # Ultimo dia
            if not channel_metrics.empty:
                latest_ch = channel_metrics.sort_values('date', ascending=False)
                latest_ch_with_rev = latest_ch[latest_ch['revenue'] > 0]
                if not latest_ch_with_rev.empty:
                    latest_ch_revenue = latest_ch_with_rev.iloc[0]['revenue']
                else:
                    latest_ch_revenue = 0
            else:
                latest_ch_revenue = 0

            if channel_revenue > 0:
                channel_stats.append({
                    'Canal': channel_name,
                    'Total': channel_revenue,
                    'Media/Dia': avg_day,
                    'Dias': days_with_revenue,
                    'Ultimo Dia': latest_ch_revenue
                })

        if channel_stats:
            stats_df = pd.DataFrame(channel_stats)
            stats_df = stats_df.sort_values('Total', ascending=False)

            # Grafico de barras horizontal
            fig_channels = px.bar(
                stats_df.sort_values('Total', ascending=True),
                x='Total',
                y='Canal',
                orientation='h',
                text='Total',
                color='Total',
                color_continuous_scale='Greens'
            )
            fig_channels.update_traces(texttemplate='$%{text:.0f}', textposition='outside')
            fig_channels.update_layout(
                title=f"Receita por Canal ({periodo})",
                xaxis_title='Receita ($)',
                yaxis_title='',
                height=400,
                showlegend=False,
                coloraxis_showscale=False
            )
            st.plotly_chart(fig_channels, use_container_width=True)

            # Tabela
            stats_display = stats_df.copy()
            stats_display['Total'] = stats_display['Total'].apply(lambda x: f"${x:.2f}")
            stats_display['Media/Dia'] = stats_display['Media/Dia'].apply(lambda x: f"${x:.2f}")
            stats_display['Ultimo Dia'] = stats_display['Ultimo Dia'].apply(lambda x: f"${x:.2f}")

            st.dataframe(stats_display, hide_index=True, use_container_width=True)
        else:
            st.info("Nenhum canal com receita no periodo.")
    else:
        # Mostrar historico do canal selecionado
        st.subheader(f"Historico: {selected_channel}")

        # Grafico de linha do canal
        channel_daily = monetized_days.copy()

        fig_channel = px.line(
            channel_daily,
            x='date',
            y='revenue',
            markers=True
        )
        fig_channel.update_traces(line_color='#00D26A', marker_size=8)
        fig_channel.update_layout(
            title=f"Evolucao de Receita - {selected_channel}",
            yaxis_title='Receita ($)',
            xaxis_title='',
            height=400
        )
        st.plotly_chart(fig_channel, use_container_width=True)

# =============================================================================
# RESUMO GERAL (sempre visivel)
# =============================================================================
st.divider()

# Buscar totais gerais (todo periodo, todos canais)
all_revenue = metrics_df[metrics_df['revenue'] > 0]['revenue'].sum()
all_days = metrics_df[metrics_df['revenue'] > 0].groupby(metrics_df['date'].dt.date).size().count()
first_date = metrics_df[metrics_df['revenue'] > 0]['date'].min().date()

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("💰 Receita Total (Historico)", f"${all_revenue:.2f}")

with col2:
    st.metric("📅 Primeiro Dia Monetizado", first_date.strftime('%d/%m/%Y'))

with col3:
    st.metric("📺 Canais Ativos", f"{len(channels_df[channels_df['monetization_start_date'].notna()])}/{len(channels_df)}")

# =============================================================================
# FOOTER
# =============================================================================
st.divider()
st.caption(f"Atualizado em {datetime.now().strftime('%d/%m/%Y %H:%M')} | YouTube Analytics API")
