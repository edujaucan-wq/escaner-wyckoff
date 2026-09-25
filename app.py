import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(page_title="Escáner Wyckoff + VSA + MACD Afinado", layout="wide")

# ==========================================
# 1. CATÁLOGO DE ACTIVOS
# ==========================================
CATALOGO_ACTIVOS = {
    "⛏️ Activos Escasos, Commodities y Cripto": {
        "GLD": "SPDR Gold Shares (Oro Físico)",
        "SLV": "iShares Silver Trust (Plata)",
        "BTC-USD": "Bitcoin / USD",
        "ETH-USD": "Ethereum / USD",
        "SOL-USD": "Solana / USD",
        "COPX": "Global X Copper Miners (Cobre)",
        "URA": "Global X Uranium ETF",
        "USO": "United States Oil Fund (Petróleo)"
    },
    "🌍 Índices Globales y Regiones": {
        "URTH": "iShares MSCI World",
        "QQQ": "Invesco QQQ (Nasdaq 100)",
        "SPY": "SPDR S&P 500 ETF",
        "IWM": "iShares Russell 2000",
        "EEM": "iShares MSCI Emerging Markets",
        "EWP": "iShares MSCI Spain ETF"
    },
    "🏭 Sectores y Temáticos": {
        "XLK": "Technology Select Sector",
        "XLF": "Financial Select Sector",
        "XLE": "Energy Select Sector",
        "SMH": "VanEck Semiconductor ETF",
        "BOTZ": "Global X Robotics & AI"
    }
}

# ==========================================
# 2. CONTROLES Y PARÁMETROS
# ==========================================
st.sidebar.header("⚙️ Parámetros del Escáner")

categoria_sel = st.sidebar.selectbox("Universo de Activos:", list(CATALOGO_ACTIVOS.keys()))
temporalidad = st.sidebar.radio("Temporalidad:", options=["Semanal", "Diario"], index=0)

intervalo_yf = "1wk" if temporalidad == "Semanal" else "1d"
periodo_yf = "3y" if temporalidad == "Semanal" else "1y"

factor_volumen = st.sidebar.slider("Factor Volumen Inusual", 1.1, 3.0, 1.5, 0.1)
ventana_rangos = st.sidebar.slider("Ventana Soportes/Resistencias", 4, 52, 12)

activos_dic = CATALOGO_ACTIVOS[categoria_sel]
tickers_lista = list(activos_dic.keys())

# ==========================================
# 3. CÁLCULOS Y PROCESAMIENTO
# ==========================================
@st.cache_data(ttl=300)
def descargar_datos(tickers, period, interval):
    return yf.download(tickers, period=period, interval=interval, group_by="ticker", progress=False, auto_adjust=True)

def procesar_datos(df, f_vol, v_rangos):
    if len(df) < 50:
        return df

    # Medias Móviles y Volumen
    df['Vol_SMA'] = df['Volume'].rolling(window=20).mean()
    df['Vol_Ratio'] = df['Volume'] / df['Vol_SMA']
    df['SMA20'] = df['Close'].rolling(window=20).mean()
    df['SMA50'] = df['Close'].rolling(window=50).mean()

    # Soportes y Resistencias Previas (excluyendo vela actual)
    df['Min_Previo'] = df['Low'].shift(1).rolling(window=v_rangos).min()
    df['Max_Previo'] = df['High'].shift(1).rolling(window=v_rangos).max()

    # MACD (12, 26, 9)
    ema12 = df['Close'].ewm(span=12, adjust=False).mean()
    ema26 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = ema12 - ema26
    df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    df['MACD_Hist'] = df['MACD'] - df['MACD_Signal']

    # RSI (14)
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))

    # Giros del Histograma
    df['MACD_Giro_Alcista'] = df['MACD_Hist'] > df['MACD_Hist'].shift(1)
    df['MACD_Giro_Bajista'] = df['MACD_Hist'] < df['MACD_Hist'].shift(1)

    # -------------------------------------------------------------
    # LÓGICA AFINADA WYCKOFF + VSA + CONFIRMACIÓN DE CIERRE
    # -------------------------------------------------------------
    df['Vela_Alcista'] = df['Close'] > df['Open']
    df['Vela_Bajista'] = df['Close'] < df['Open']

    # Tests con volumen
    df['Test_Suelo'] = (df['Vol_Ratio'] >= f_vol) & (df['Low'] <= df['Min_Previo'])
    df['Test_Techo'] = (df['Vol_Ratio'] >= f_vol) & (df['High'] >= df['Max_Previo'])

    # 🚀 SUBIDA CONFIRMADA:
    # 1. Spring VSA: Testea suelo pero CIERRA ALCISTA + Giro de MACD + RSI recuperando (<50)
    spring_confirmado = df['Test_Suelo'] & df['Vela_Alcista'] & df['MACD_Giro_Alcista'] & (df['RSI'] < 50)
    # 2. Absorción / Breakout: Rompe techo con volumen + Cierra alcista + Precio > SMA20 y SMA50 + MACD > 0
    absorcion_confirmada = df['Test_Techo'] & df['Vela_Alcista'] & (df['Close'] >= df['SMA20']) & (df['Close'] >= df['SMA50']) & (df['MACD_Hist'] > 0) & df['MACD_Giro_Alcista']

    df['Señal_Subida'] = spring_confirmado | absorcion_confirmada

    # 💩 CAÍDA CONFIRMADA:
    # 1. Upthrust VSA: Testea techo pero CIERRA BAJISTA + Giro bajista de MACD + RSI en zona alta (>50)
    upthrust_confirmado = df['Test_Techo'] & df['Vela_Bajista'] & df['MACD_Giro_Bajista'] & (df['RSI'] > 50)
    # 2. Ruptura Bajista: Rompe suelo con volumen + Cierra bajista + Precio < SMA20 y SMA50 + MACD < 0
    ruptura_confirmada = df['Test_Suelo'] & df['Vela_Bajista'] & (df['Close'] <= df['SMA20']) & (df['Close'] <= df['SMA50']) & (df['MACD_Hist'] < 0) & df['MACD_Giro_Bajista']

    df['Señal_Bajada'] = upthrust_confirmado | ruptura_confirmada

    return df

# ==========================================
# 4. TABLA RESUMEN
# ==========================================
st.title("📊 Detección Wyckoff + VSA Afinado")
st.write(f"Categoría: **{categoria_sel}** | Vela: **{temporalidad}**")

datos = descargar_datos(tickers_lista, periodo_yf, intervalo_yf)
resultados = []

for ticker in tickers_lista:
    try:
        df_a = datos.copy() if len(tickers_lista) == 1 else datos[ticker].dropna()
        df_a = procesar_datos(df_a, factor_volumen, ventana_rangos)

        if not df_a.empty and len(df_a) >= 50:
            u = df_a.iloc[-1]
            estado = "NEUTRAL"
            if u['Señal_Subida']:
                estado = "🚀 SUBIDA PROBABLE"
            elif u['Señal_Bajada']:
                estado = "💩 CAÍDA PROBABLE"

            resultados.append({
                "Ticker": ticker,
                "Nombre": activos_dic[ticker],
                "Precio Cierre": round(float(u['Close']), 2),
                "Volumen Relativo": f"{round(float(u['Vol_Ratio']), 2)}x",
                "RSI (14)": round(float(u['RSI']), 1),
                "Predicción": estado
            })
    except Exception:
        pass

st.dataframe(pd.DataFrame(resultados), use_container_width=True, hide_index=True)

# ==========================================
# 5. GRÁFICO INTERACTIVO CON SMA50 Y LÍNEAS MACD
# ==========================================
st.markdown("---")
activo_grafico = st.selectbox("Selecciona un activo para analizar:", options=tickers_lista, format_func=lambda x: f"{x} - {activos_dic[x]}")

if activo_grafico:
    df_g = datos.copy() if len(tickers_lista) == 1 else datos[activo_grafico].dropna()
    df_g = procesar_datos(df_g, factor_volumen, ventana_rangos)

    fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.5, 0.25, 0.25])

    # 1. FILA 1: Precio, SMA 20, SMA 50 y Marcadores
    fig.add_trace(go.Candlestick(x=df_g.index, open=df_g['Open'], high=df_g['High'], low=df_g['Low'], close=df_g['Close'], name="Velas"), row=1, col=1)
    fig.add_trace(go.Scatter(x=df_g.index, y=df_g['Close'], mode='lines', line=dict(color='#FFFF00', width=2), name="Cierre (Amarillo)"), row=1, col=1)
    fig.add_trace(go.Scatter(x=df_g.index, y=df_g['SMA20'], mode='lines', line=dict(color='#00E5FF', width=1.5), name="SMA 20 (Cian)"), row=1, col=1)
    fig.add_trace(go.Scatter(x=df_g.index, y=df_g['SMA50'], mode='lines', line=dict(color='#FF9100', width=2), name="SMA 50 (Naranja)"), row=1, col=1)

    subidas = df_g[df_g['Señal_Subida']]
    bajadas = df_g[df_g['Señal_Bajada']]

    if not subidas.empty:
        fig.add_trace(go.Scatter(x=subidas.index, y=subidas['Low']*0.98, mode='text', text=['🚀']*len(subidas), textfont=dict(size=22), textposition='bottom center', name="Alcista (🚀)"), row=1, col=1)

    if not bajadas.empty:
        fig.add_trace(go.Scatter(x=bajadas.index, y=bajadas['High']*1.02, mode='text', text=['💩']*len(bajadas), textfont=dict(size=22), textposition='top center', name="Bajista (💩)"), row=1, col=1)

    # 2. FILA 2: LÍNEAS MACD + SEÑAL + HISTOGRAMA
    fig.add_trace(go.Scatter(x=df_g.index, y=df_g['MACD'], mode='lines', line=dict(color='#00E5FF', width=1.5), name="Línea MACD"), row=2, col=1)
    fig.add_trace(go.Scatter(x=df_g.index, y=df_g['MACD_Signal'], mode='lines', line=dict(color='#FF9100', width=1.5), name="Línea Señal"), row=2, col=1)
    colores_hist = ['#00E676' if v >= 0 else '#FF1744' for v in df_g['MACD_Hist']]
    fig.add_trace(go.Bar(x=df_g.index, y=df_g['MACD_Hist'], marker_color=colores_hist, name="Hist. MACD"), row=2, col=1)

    # 3. FILA 3: RSI
    fig.add_trace(go.Scatter(x=df_g.index, y=df_g['RSI'], mode='lines', line=dict(color='#D000FF', width=1.5), name="RSI (14)"), row=3, col=1)
    fig.add_hline(y=70, line_dash="dash", line_color="red", row=3, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="green", row=3, col=1)

    fig.update_layout(template="plotly_dark", height=800, xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)
