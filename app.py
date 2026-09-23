import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# ==========================================
# CONFIGURACIÓN DE LA PÁGINA
# ==========================================
st.set_page_config(page_title="Escáner Wyckoff Multi-Tendencia", layout="wide")

# ==========================================
# 1. CATÁLOGO COMPLETO DE ACTIVOS (CON CRIPTO)
# ==========================================
CATALOGO_ACTIVOS = {
    "⛏️ Activos Escasos, Commodities y Cripto": {
        "GLD": "SPDR Gold Shares (Oro Físico)",
        "SLV": "iShares Silver Trust (Plata)",
        "BTC-USD": "Bitcoin / USD (Activo Escaso Digital)",
        "ETH-USD": "Ethereum / USD (Plataforma L1 / PoS)",
        "SOL-USD": "Solana / USD (Activo L1 Alt-Cap)",
        "COPX": "Global X Copper Miners (Cobre)",
        "URA": "Global X Uranium ETF (Uranio)",
        "LIT": "Global X Lithium & Battery Tech (Litio)",
        "REMX": "VanEck Rare Earth/Strategic Metals",
        "USO": "United States Oil Fund (Petróleo WTI)",
        "BNO": "United States Brent Oil Fund",
        "UNG": "United States Natural Gas Fund",
        "DBA": "Invesco DB Agriculture Fund",
        "CORN": "Teucrium Corn Fund (Maíz)",
        "WEAT": "Teucrium Wheat Fund (Trigo)",
        "SOYB": "Teucrium Soybean Fund (Soja)",
        "CPER": "United States Copper Index Fund",
        "PALL": "Abrdn Physical Palladium Shares",
        "PPLT": "Abrdn Physical Platinum Shares",
        "XME": "SPDR S&P Metals & Mining ETF",
        "XOP": "SPDR S&P Oil & Gas Exploration"
    },
    "🌍 Índices Globales y Regiones": {
        "URTH": "iShares MSCI World (Desarrollados Global)",
        "QQQ": "Invesco QQQ (Nasdaq 100 EE.UU.)",
        "SPY": "SPDR S&P 500 ETF Trust",
        "IWM": "iShares Russell 2000 (Small Caps EE.UU.)",
        "EEM": "iShares MSCI Emerging Markets",
        "VGK": "Vanguard FTSE Europe ETF",
        "EWJ": "iShares MSCI Japan ETF (Nikkei 225)",
        "FXI": "iShares China Large-Cap ETF",
        "INDA": "iShares MSCI India ETF",
        "EWZ": "iShares MSCI Brazil ETF",
        "EWP": "iShares MSCI Spain ETF (Ibex 35)",
        "EWG": "iShares MSCI Germany ETF (DAX)",
        "EWT": "iShares MSCI Taiwan ETF",
        "EWY": "iShares MSCI South Korea ETF",
        "TUR": "iShares MSCI Turkey ETF"
    },
    "🏭 Sectores Industriales y Macro": {
        "XLK": "Technology Select Sector (Tecnología)",
        "XLF": "Financial Select Sector (Bancos y Finanzas)",
        "XLV": "Health Care Select Sector (Salud y Farmacia)",
        "XLE": "Energy Select Sector (Energía Tradicional)",
        "XLY": "Consumer Discretionary (Consumo Cíclico)",
        "XLP": "Consumer Staples (Consumo Defensivo)",
        "XLI": "Industrial Select Sector (Industria)",
        "XLU": "Utilities Select Sector (Servicios Públicos)",
        "XLB": "Materials Select Sector (Materiales Básicos)",
        "XLRE": "Real Estate Select Sector (Inmobiliario)",
        "XLC": "Communication Services (Comunicaciones)",
        "SMH": "VanEck Semiconductor ETF",
        "SOXX": "iShares Semiconductor ETF",
        "KBE": "SPDR S&P Bank ETF",
        "XBI": "SPDR S&P Biotech ETF",
        "ITA": "iShares U.S. Aerospace & Defense"
    },
    "🏛️ Bonos y Renta Fija": {
        "TLT": "iShares 20+ Year Treasury Bond ETF",
        "DTLA.L": "iShares $ Treasury Bond 20+yr UCITS",
        "IEF": "iShares 7-10 Year Treasury Bond ETF",
        "SHY": "iShares 1-3 Year Treasury Bond ETF",
        "TIP": "iShares TIPS Bond ETF (Protegido Inflación)",
        "HYG": "iShares High Yield Corporate Bond",
        "AGG": "iShares Core U.S. Aggregate Bond"
    },
    "🚀 Temáticos y Megatrends": {
        "ARKK": "ARK Innovation ETF",
        "BOTZ": "Global X Robotics & AI",
        "AIQ": "Global X Artificial Intelligence & Tech",
        "CIBR": "First Trust NASDAQ Cybersecurity",
        "ICLN": "iShares Global Clean Energy ETF",
        "TAN": "Invesco Solar ETF",
        "PAVE": "Global X U.S. Infrastructure"
    },
    "👑 Megacaps": {
        "AAPL": "Apple Inc.",
        "MSFT": "Microsoft Corporation",
        "NVDA": "NVIDIA Corporation",
        "AMZN": "Amazon.com Inc.",
        "GOOGL": "Alphabet Inc.",
        "META": "Meta Platforms Inc.",
        "TSLA": "Tesla Inc.",
        "BRK-B": "Berkshire Hathaway Inc.",
        "AVGO": "Broadcom Inc.",
        "LLY": "Eli Lilly and Company"
    }
}

# ==========================================
# 2. BARRA LATERAL (CONTROLES E INPUTS)
# ==========================================
st.sidebar.header("⚙️ Configuración del Escáner")

categoria_sel = st.sidebar.selectbox(
    "Universo de Activos:",
    list(CATALOGO_ACTIVOS.keys())
)

st.sidebar.subheader("⏱️ Temporalidad")
temporalidad = st.sidebar.radio(
    "Selecciona la vela:",
    options=["Semanal", "Diario"],
    index=0
)

# Ajuste de sufijos y configuraciones según temporalidad
intervalo_yf = "1wk" if temporalidad == "Semanal" else "1d"
periodo_yf = "3y" if temporalidad == "Semanal" else "1y"
sufijo_tiempo = "semanas" if temporalidad == "Semanal" else "días"

st.sidebar.subheader("Filtro de Tendencia Macro")
periodo_tendencia = st.sidebar.radio(
    "Evaluación de Tendencia:",
    options=[20, 50],
    format_func=lambda x: f"Media Móvil {x} {sufijo_tiempo} ({'Medio Plazo' if x==20 else 'Largo Plazo'})",
    index=1
)

st.sidebar.subheader("Parámetros Wyckoff")
periodo_volumen = st.sidebar.slider(f"Media Móvil Volumen ({sufijo_tiempo.capitalize()})", min_value=5, max_value=50, value=20)
factor_volumen = st.sidebar.slider("Factor Volumen Inusual", min_value=1.1, max_value=3.0, value=1.5, step=0.1)
ventana_rangos = st.sidebar.slider("Ventana de Mínimos/Máximos", min_value=4, max_value=52, value=12)

activos_dic = CATALOGO_ACTIVOS[categoria_sel]
tickers_lista = list(activos_dic.keys())

# ==========================================
# 3. FUNCIONES DE DESCARGA Y CÁLCULO
# ==========================================
@st.cache_data(ttl=900)
def descargar_datos(tickers, period, interval):
    return yf.download(tickers, period=period, interval=interval, group_by="ticker", progress=False)

def procesar_df_wyckoff(df, p_vol, f_vol, v_rangos, p_tend):
    if len(df) < max(p_vol, p_tend) + 4:
        return df
    
    # Media de Volumen
    df['Vol_SMA'] = df['Volume'].rolling(window=p_vol).mean()
    df['Vol_Ratio'] = df['Volume'] / df['Vol_SMA']
    
    # Media Móvil de Tendencia Configurable (SMA20 o SMA50)
    df['Precio_SMA_Tend'] = df['Close'].rolling(window=p_tend).mean()
    df['SMA_Pendiente'] = df['Precio_SMA_Tend'] - df['Precio_SMA_Tend'].shift(4)
    
    # Media SMA20 auxiliar para el gráfico
    df['SMA20'] = df['Close'].rolling(window=20).mean()
    
    # Mínimos y Máximos móviles
    df['Min_Reciente'] = df['Close'].rolling(window=v_rangos).min()
    df['Max_Reciente'] = df['Close'].rolling(window=v_rangos).max()
    
    # Evaluación de Tendencia con Pendiente
    def evaluar_tendencia(row):
        if row['Close'] >= row['Precio_SMA_Tend'] and row['SMA_Pendiente'] > 0:
            return "🟢 ALCISTA FUERTE"
        elif row['Close'] < row['Precio_SMA_Tend'] and row['SMA_Pendiente'] < 0:
            return "🔴 BAJISTA FUERTE"
        else:
            return "🟡 LATERAL / TRANSICIÓN"

    df['Tendencia'] = df.apply(evaluar_tendencia, axis=1)
    df['Es_Spring'] = (df['Vol_Ratio'] >= f_vol) & (df['Close'] <= df['Min_Reciente'])
    df['Es_Upthrust'] = (df['Vol_Ratio'] >= f_vol) & (df['Close'] >= df['Max_Reciente'])
    
    return df

# ==========================================
# 4. EJECUCIÓN PRINCIPAL Y TABLA
# ==========================================
st.title("📊 Escáner Wyckoff: Análisis Multitendencia")
st.write(f"Categoría activa: **{categoria_sel}** | Temporalidad: **{temporalidad}** | Tendencia calculada a **{periodo_tendencia} {sufijo_tiempo}**")

datos = descargar_datos(tickers_lista, periodo_yf, intervalo_yf)
resultados = []

for ticker in tickers_lista:
    try:
        if len(tickers_lista) == 1:
            df_activo = datos.copy()
        else:
            df_activo = datos[ticker].dropna()
            
        df_activo = procesar_df_wyckoff(df_activo, periodo_volumen, factor_volumen, ventana_rangos, periodo_tendencia)
        
        if not df_activo.empty and len(df_activo) >= periodo_tendencia:
            ultima = df_activo.iloc[-1]
            
            estado = "NEUTRAL"
            if ultima['Es_Spring']:
                estado = "🟢 SPRING / ACUMULACIÓN"
            elif ultima['Es_Upthrust']:
                estado = "🔴 UPTHRUST / DISTRIBUCIÓN"
                
            resultados.append({
                "Ticker": ticker,
                "Nombre": activos_dic[ticker],
                "Precio Cierre": round(float(ultima['Close']), 2),
                "Tendencia Macro": ultima['Tendencia'],
                "Ratio Vol": f"{round(float(ultima['Vol_Ratio']), 2)}x",
                "Estado Wyckoff": estado
            })
    except Exception:
        pass

df_res = pd.DataFrame(resultados)
st.dataframe(df_res, use_container_width=True, hide_index=True)

# ==========================================
# 5. VISUALIZADOR DE GRÁFICO DETALLADO
# ==========================================
st.markdown("---")
st.subheader(f"📈 Gráfico ({temporalidad}) con Medias Móviles y Flechas Wyckoff")

activo_grafico = st.selectbox(
    "Selecciona un activo para inspeccionar sus puntos:",
    options=tickers_lista,
    format_func=lambda x: f"{x} - {activos_dic[x]}"
)

if activo_grafico:
    if len(tickers_lista) == 1:
        df_g = datos.copy()
    else:
        df_g = datos[activo_grafico].dropna()
        
    df_g = procesar_df_wyckoff(df_g, periodo_volumen, factor_volumen, ventana_rangos, periodo_tendencia)
    
    springs = df_g[df_g['Es_Spring']]
    upthrusts = df_g[df_g['Es_Upthrust']]
    
    fig = go.Figure()

    # Velas Japonesas
    fig.add_trace(go.Candlestick(
        x=df_g.index,
        open=df_g['Open'],
        high=df_g['High'],
        low=df_g['Low'],
        close=df_g['Close'],
        name="Precio"
    ))

    # Media Móvil 20 sem/días (Naranja)
    fig.add_trace(go.Scatter(
        x=df_g.index,
        y=df_g['SMA20'],
        mode='lines',
        line=dict(color='orange', width=1.5),
        name=f"SMA 20 {sufijo_tiempo} (Medio Plazo)"
    ))

    # Media Móvil de Tendencia seleccionada (Azul) si no es la de 20
    if periodo_tendencia != 20:
        fig.add_trace(go.Scatter(
            x=df_g.index,
            y=df_g['Precio_SMA_Tend'],
            mode='lines',
            line=dict(color='cyan', width=2),
            name=f"SMA {periodo_tendencia} {sufijo_tiempo} (Largo Plazo)"
        ))

    # Flechas Verdes (Springs)
    if not springs.empty:
        fig.add_trace(go.Scatter(
            x=springs.index,
            y=springs['Low'] * 0.98,
            mode='markers+text',
            marker=dict(symbol='triangle-up', size=14, color='lime'),
            text=['🟢 Spring'] * len(springs),
            textposition='bottom center',
            name="Spring (Acumulación)"
        ))

    # Flechas Rojas (Upthrusts)
    if not upthrusts.empty:
        fig.add_trace(go.Scatter(
            x=upthrusts.index,
            y=upthrusts['High'] * 1.02,
            mode='markers+text',
            marker=dict(symbol='triangle-down', size=14, color='red'),
            text=['🔴 Upthrust'] * len(upthrusts),
            textposition='top center',
            name="Upthrust (Distribución)"
        ))

    fig.update_layout(
        title=f"Análisis Técnico Wyckoff [{temporalidad}]: {activo_grafico} ({activos_dic[activo_grafico]})",
        yaxis_title="Precio ($ / €)",
        xaxis_rangeslider_visible=False,
        template="plotly_dark",
        height=550,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    st.plotly_chart(fig, use_container_width=True)
