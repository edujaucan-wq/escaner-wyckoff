import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ==========================================
# CONFIGURACIÓN DE LA PÁGINA
# ==========================================
st.set_page_config(page_title="Escáner Wyckoff Multi-Tendencia", layout="wide")

# ==========================================
# 1. CATÁLOGO COMPLETO DE ACTIVOS
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
        "ACWI": "iShares MSCI ACWI ETF (Mundo Global Desarrollado + Emergentes)",
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
@st.cache_data(ttl=300)
def descargar_datos(tickers, period, interval):
    df = yf.download(tickers, period=period, interval=interval, group_by="ticker", progress=False, auto_adjust=True)
    try:
        df_hoy = yf.download(tickers, period="5d", interval=interval, group_by="ticker", progress=False, auto_adjust=True)
        df = df.combine_first(df_hoy)
    except Exception:
        pass
    return df

def procesar_df_wyckoff(df, p_vol, f_vol, v_rangos, p_tend):
    if len(df) < max(p_vol, p_tend, 50) + 4:
        return df
    
    # 1. Volumen y Medias Móviles
    df['Vol_SMA'] = df['Volume'].rolling(window=p_vol).mean()
    df['Vol_Ratio'] = df['Volume'] / df['Vol_SMA']
    df['Precio_SMA_Tend'] = df['Close'].rolling(window=p_tend).mean()
    df['SMA_Pendiente'] = df['Precio_SMA_Tend'] - df['Precio_SMA_Tend'].shift(4)
    df['SMA20'] = df['Close'].rolling(window=20).mean()
    df['SMA50'] = df['Close'].rolling(window=50).mean()
    
    # Referencias de Techo/Suelo previo (sin incluir la vela actual)
    df['Min_Previo'] = df['Low'].shift(1).rolling(window=v_rangos).min()
    df['Max_Previo'] = df['High'].shift(1).rolling(window=v_rangos).max()
    
    # 2. MACD (12, 26, 9)
    ema12 = df['Close'].ewm(span=12, adjust=False).mean()
    ema26 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = ema12 - ema26
    df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    df['MACD_Hist'] = df['MACD'] - df['MACD_Signal']
    
    df['MACD_Giro_Alcista'] = df['MACD_Hist'] > df['MACD_Hist'].shift(1)
    df['MACD_Giro_Bajista'] = df['MACD_Hist'] < df['MACD_Hist'].shift(1)
    
    # 3. Interacciones con Volumen en Soportes / Resistencias
    df['Test_Suelo'] = (df['Vol_Ratio'] >= f_vol) & (df['Low'] <= df['Min_Previo'])
    df['Test_Techo'] = (df['Vol_Ratio'] >= f_vol) & (df['High'] >= df['Max_Previo'])
    
    # --- SEÑALES DE IMPULSO ALCISTA CONFIRMADO (🚀 COHETE) ---
    # A) Spring Élite: Barrido de mínimos con giro alcista de MACD
    spring_e = df['Test_Suelo'] & df['MACD_Giro_Alcista']
    # B) Absorción de Resistencia: Ruptura con volumen + MACD en zona positiva subiendo + Precio > SMA20
    absorcion_alcista = df['Test_Techo'] & (df['MACD_Hist'] > 0) & df['MACD_Giro_Alcista'] & (df['Close'] >= df['SMA20'])
    
    df['Señal_Subida'] = spring_e | absorcion_alcista

    # --- SEÑALES DE IMPULSO BAJISTA CONFIRMADO (💩 CAÍDA) ---
    # A) Upthrust Élite: Testeo de techo con giro bajista de MACD
    upthrust_e = df['Test_Techo'] & df['MACD_Giro_Bajista']
    # B) Fallo de Spring / Ruptura de Soporte: Pérdida de suelo con volumen + MACD fuertemente negativo
    caida_libre = df['Test_Suelo'] & (df['MACD_Hist'] < 0) & df['MACD_Giro_Bajista']
    
    df['Señal_Bajada'] = upthrust_e | caida_libre

    def evaluar_tendencia(row):
        if row['Close'] >= row['Precio_SMA_Tend'] and row['SMA_Pendiente'] > 0:
            return "🟢 ALCISTA FUERTE"
        elif row['Close'] < row['Precio_SMA_Tend'] and row['SMA_Pendiente'] < 0:
            return "🔴 BAJISTA FUERTE"
        else:
            return "🟡 LATERAL / TRANSICIÓN"

    df['Tendencia'] = df.apply(evaluar_tendencia, axis=1)
    return df

# ==========================================
# 4. EJECUCIÓN PRINCIPAL Y TABLA
# ==========================================
st.title("📊 Escáner Wyckoff + MACD: Detección Institucional")
st.write(f"Categoría activa: **{categoria_sel}** | Temporalidad: **{temporalidad}** | Tendencia a **{periodo_tendencia} {sufijo_tiempo}**")

datos = descargar_datos(tickers_lista, periodo_yf, intervalo_yf)
resultados = []

for ticker in tickers_lista:
    try:
        df_activo = datos.copy() if len(tickers_lista) == 1 else datos[ticker].dropna()
        df_activo = procesar_df_wyckoff(df_activo, periodo_volumen, factor_volumen, ventana_rangos, periodo_tendencia)
        
        if not df_activo.empty and len(df_activo) >= periodo_tendencia:
            ultima = df_activo.iloc[-1]
            estado = "NEUTRAL"
            
            if ultima['Señal_Subida']:
                estado = "🚀 SUBIDA PROBABLE (Acumulación / Absorción)"
            elif ultima['Señal_Bajada']:
                estado = "💩 CAÍDA PROBABLE (Distribución / Pérdida Soporte)"
                
            resultados.append({
                "Ticker": ticker,
                "Nombre": activos_dic[ticker],
                "Precio Cierre": round(float(ultima['Close']), 2),
                "Tendencia Macro": ultima['Tendencia'],
                "Ratio Vol": f"{round(float(ultima['Vol_Ratio']), 2)}x",
                "Predicción Wyckoff + MACD": estado
            })
    except Exception:
        pass

df_res = pd.DataFrame(resultados)
st.dataframe(df_res, use_container_width=True, hide_index=True)

# ==========================================
# 5. VISUALIZADOR DE GRÁFICO CON MACD
# ==========================================
st.markdown("---")
st.subheader(f"📈 Gráfico ({temporalidad}) con Precio, SMA 20, SMA 50, MACD y Señales")

activo_grafico = st.selectbox(
    "Selecciona un activo para inspeccionar sus puntos:",
    options=tickers_lista,
    format_func=lambda x: f"{x} - {activos_dic[x]}"
)

if activo_grafico:
    df_g = datos.copy() if len(tickers_lista) == 1 else datos[activo_grafico].dropna()
    df_g = procesar_df_wyckoff(df_g, periodo_volumen, factor_volumen, ventana_rangos, periodo_tendencia)
    
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.7, 0.3])

    # 1. Velas Japonesas
    fig.add_trace(go.Candlestick(
        x=df_g.index, 
        open=df_g['Open'], 
        high=df_g['High'], 
        low=df_g['Low'], 
        close=df_g['Close'], 
        name="Velas"
    ), row=1, col=1)

    # 2. Línea de Precio de Cierre (Amarillo Neón)
    fig.add_trace(go.Scatter(
        x=df_g.index, 
        y=df_g['Close'], 
        mode='lines', 
        line=dict(color='#FFFF00', width=2.5), 
        name="Línea Precio Cierre"
    ), row=1, col=1)

    # 3. Media Móvil SMA 20 (Cian)
    fig.add_trace(go.Scatter(
        x=df_g.index, 
        y=df_g['SMA20'], 
        mode='lines', 
        line=dict(color='#00E5FF', width=1.5), 
        name="SMA 20 (Corto Plazo)"
    ), row=1, col=1)

    # 4. Media Móvil SMA 50 (Naranja)
    fig.add_trace(go.Scatter(
        x=df_g.index, 
        y=df_g['SMA50'], 
        mode='lines', 
        line=dict(color='#FF9100', width=2), 
        name="SMA 50 (Tendencia)"
    ), row=1, col=1)

    # Marcadores visuales simplificados
    subidas = df_g[df_g['Señal_Subida']]
    bajadas = df_g[df_g['Señal_Bajada']]

    # A) SUBIDA PROBABLE (🚀 Cohete debajo del mínimo de la vela)
    if not subidas.empty:
        fig.add_trace(go.Scatter(
            x=subidas.index, 
            y=subidas['Low']*0.98, 
            mode='text', 
            text=['🚀']*len(subidas), 
            textfont=dict(size=22),
            textposition='bottom center', 
            name="Impulso Alcista (🚀)"
        ), row=1, col=1)

    # B) CAÍDA PROBABLE (💩 Caca encima del máximo de la vela)
    if not bajadas.empty:
        fig.add_trace(go.Scatter(
            x=bajadas.index, 
            y=bajadas['High']*1.02, 
            mode='text', 
            text=['💩']*len(bajadas), 
            textfont=dict(size=22),
            textposition='top center', 
            name="Impulso Bajista (💩)"
        ), row=1, col=1)

    # Fila 2: Indicador MACD e Histograma
    fig.add_trace(go.Scatter(x=df_g.index, y=df_g['MACD'], mode='lines', line=dict(color='cyan', width=1.5), name="MACD"), row=2, col=1)
    fig.add_trace(go.Scatter(x=df_g.index, y=df_g['MACD_Signal'], mode='lines', line=dict(color='orange', width=1.5), name="Señal"), row=2, col=1)
    colores_hist = ['green' if val >= 0 else 'red' for val in df_g['MACD_Hist']]
    fig.add_trace(go.Bar(x=df_g.index, y=df_g['MACD_Hist'], marker_color=colores_hist, name="Histograma"), row=2, col=1)

    fig.update_layout(
        title=f"Wyckoff + MACD: {activo_grafico}", 
        template="plotly_dark", 
        height=700, 
        xaxis_rangeslider_visible=False,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig, use_container_width=True)
