import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(page_title="Escáner Wyckoff + VSA + MACD Afinado", layout="wide")

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
# 2. FUNCIONES DE DESCARGA Y CÁLCULO
# ==========================================
@st.cache_data(ttl=300)
def descargar_datos(tickers, period, interval):
    return yf.download(tickers, period=period, interval=interval, group_by="ticker", progress=False, auto_adjust=True)

def procesar_wyckoff_vsa(df, f_vol, v_rangos):
    if len(df) < 50:
        return df

    df['Vol_SMA'] = df['Volume'].rolling(window=20).mean()
    df['Vol_Ratio'] = df['Volume'] / df['Vol_SMA']
    df['SMA20'] = df['Close'].rolling(window=20).mean()
    df['SMA50'] = df['Close'].rolling(window=50).mean()

    df['Min_Previo'] = df['Low'].shift(1).rolling(window=v_rangos).min()
    df['Max_Previo'] = df['High'].shift(1).rolling(window=v_rangos).max()

    ema12 = df['Close'].ewm(span=12, adjust=False).mean()
    ema26 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = ema12 - ema26
    df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    df['MACD_Hist'] = df['MACD'] - df['MACD_Signal']

    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))

    df['MACD_Giro_Alcista'] = df['MACD_Hist'] > df['MACD_Hist'].shift(1)
    df['MACD_Giro_Bajista'] = df['MACD_Hist'] < df['MACD_Hist'].shift(1)
    df['Vela_Alcista'] = df['Close'] > df['Open']
    df['Vela_Bajista'] = df['Close'] < df['Open']

    df['Test_Suelo'] = (df['Vol_Ratio'] >= f_vol) & (df['Low'] <= df['Min_Previo'])
    df['Test_Techo'] = (df['Vol_Ratio'] >= f_vol) & (df['High'] >= df['Max_Previo'])

    spring_c = df['Test_Suelo'] & df['Vela_Alcista'] & df['MACD_Giro_Alcista'] & (df['RSI'] < 50)
    absorcion_c = df['Test_Techo'] & df['Vela_Alcista'] & (df['Close'] >= df['SMA20']) & (df['Close'] >= df['SMA50']) & (df['MACD_Hist'] > 0) & df['MACD_Giro_Alcista']
    df['Señal_Subida'] = spring_c | absorcion_c

    upthrust_c = df['Test_Techo'] & df['Vela_Bajista'] & df['MACD_Giro_Bajista'] & (df['RSI'] > 50)
    ruptura_c = df['Test_Suelo'] & df['Vela_Bajista'] & (df['Close'] <= df['SMA20']) & (df['Close'] <= df['SMA50']) & (df['MACD_Hist'] < 0) & df['MACD_Giro_Bajista']
    df['Señal_Bajada'] = upthrust_c | ruptura_c

    return df

def calcular_dca_inteligente(df, cuota_base=100.0):
    if len(df) < 50:
        return None

    # RSI (14)
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI_Semanal'] = 100 - (100 / (1 + rs))

    # Media Móvil de Largo Plazo (SMA 50 semanas ~ 1 año)
    df['SMA50_Semanal'] = df['Close'].rolling(window=50).mean()

    # Máximo de 52 semanas y Drawdown %
    df['Max_52W'] = df['High'].rolling(window=52).max()
    df['Drawdown_Pct'] = ((df['Close'] - df['Max_52W']) / df['Max_52W']) * 100

    u = df.iloc[-1]
    rsi = u['RSI_Semanal']
    dd = u['Drawdown_Pct']
    precio = u['Close']
    sma50 = u['SMA50_Semanal']

    # Lógica de Ponderación DCA
    multiplicador = 1.0
    zona = "🟡 NEUTRAL / APORTACIÓN NORMAL"
    explicacion = []

    # Evaluador RSI
    if rSI < 35:
        multiplicador += 0.6
        explicacion.append("RSI en sobreventa extrema (<35)")
    elif rSI < 45:
        multiplicador += 0.3
        explicacion.append("RSI en zona de descuento (<45)")
    elif rSI > 70:
        multiplicador -= 0.6
        explicacion.append("RSI en sobrecompra eufórica (>70)")
    elif rSI > 60:
        multiplicador -= 0.3
        explicacion.append("RSI en zona alta (>60)")

    # Evaluador Drawdown
    if dd <= -40:
        multiplicador += 0.5
        explicacion.append(f"Caída fuerte del {dd:.1f}% desde máximos")
    elif dd <= -20:
        multiplicador += 0.25
        explicacion.append(f"Corrección del {dd:.1f}% desde máximos")

    # Evaluador SMA 50
    if precio < sma50:
        multiplicador += 0.2
        explicacion.append("Cotizando por debajo de la media móvil anual")

    multiplicador = max(0.0, round(multiplicador, 2))
    aportacion_sugerida = round(cuota_base * multiplicador, 2)

    if multiplicador >= 1.5:
        zona = "🟢 OPORTUNIDAD FUERTE (Comprar más)"
    elif multiplicador >= 1.1:
        zona = "🟩 ZONA DE DESCUENTO (Ligera sobre-aportación)"
    elif multiplicador <= 0.4:
        zona = "🔴 ZONA EUFÓRICA (Pausar o reducir aportación)"
    elif multiplicador < 1.0:
        zona = "🟠 SOBREVALORADO LIGERO (Reducir aportación)"

    return {
        "Precio": round(precio, 2),
        "RSI Semanal": round(rsi, 1),
        "Drawdown %": f"{dd:.1f}%",
        "Zona DCA": zona,
        "Multiplicador": f"{multiplicador}x",
        "Aportación Sugerida": f"{aportacion_sugerida} €",
        "Razones": " | ".join(explicacion) if explicacion else "Sin desviaciones relevantes"
    }

# ==========================================
# 3. INTERFAZ Y PESTAÑAS
# ==========================================
tab1, tab2 = st.tabs(["🎯 Swing Trading (Wyckoff + VSA)", "💎 DCA Inteligente (Largo Plazo)"])

# -------------------------------------------------------------------
# PESTAÑA 1: SWING TRADING (WYCKOFF + VSA)
# -------------------------------------------------------------------
with tab1:
    st.sidebar.header("⚙️ Configuración Swing Trading")
    categoria_sel = st.sidebar.selectbox("Universo de Activos:", list(CATALOGO_ACTIVOS.keys()), key="cat_swing")
    temporalidad = st.sidebar.radio("Temporalidad:", options=["Semanal", "Diario"], index=0, key="temp_swing")

    intervalo_yf = "1wk" if temporalidad == "Semanal" else "1d"
    periodo_yf = "3y" if temporalidad == "Semanal" else "1y"

    factor_volumen = st.sidebar.slider("Factor Volumen Inusual", 1.1, 3.0, 1.3, 0.1, key="vol_swing")
    ventana_rangos = st.sidebar.slider("Ventana Soportes/Resistencias", 4, 52, 12, key="win_swing")

    activos_dic = CATALOGO_ACTIVOS[categoria_sel]
    tickers_lista = list(activos_dic.keys())

    st.title("📊 Escáner Swing Trading: Wyckoff + VSA")
    datos_swing = descargar_datos(tickers_lista, periodo_yf, intervalo_yf)
    resultados_swing = []

    for ticker in tickers_lista:
        try:
            df_a = datos_swing.copy() if len(tickers_lista) == 1 else datos_swing[ticker].dropna()
            df_a = procesar_wyckoff_vsa(df_a, factor_volumen, ventana_rangos)

            if not df_a.empty and len(df_a) >= 50:
                u = df_a.iloc[-1]
                estado = "NEUTRAL"
                if u['Señal_Subida']:
                    estado = "🚀 SUBIDA PROBABLE"
                elif u['Señal_Bajada']:
                    estado = "💩 CAÍDA PROBABLE"

                resultados_swing.append({
                    "Ticker": ticker,
                    "Nombre": activos_dic[ticker],
                    "Precio Cierre": round(float(u['Close']), 2),
                    "Volumen Relativo": f"{round(float(u['Vol_Ratio']), 2)}x",
                    "RSI (14)": round(float(u['RSI']), 1),
                    "Predicción": estado
                })
        except Exception:
            pass

    st.dataframe(pd.DataFrame(resultados_swing), use_container_width=True, hide_index=True)

    # Gráfico Swing Trading
    st.markdown("---")
    activo_grafico = st.selectbox("Selecciona activo para gráfico:", options=tickers_lista, format_func=lambda x: f"{x} - {activos_dic[x]}", key="sel_swing")

    if activo_grafico:
        df_g = datos_swing.copy() if len(tickers_lista) == 1 else datos_swing[activo_grafico].dropna()
        df_g = procesar_wyckoff_vsa(df_g, factor_volumen, ventana_rangos)

        fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.5, 0.25, 0.25])
        fig.add_trace(go.Candlestick(x=df_g.index, open=df_g['Open'], high=df_g['High'], low=df_g['Low'], close=df_g['Close'], name="Velas"), row=1, col=1)
        fig.add_trace(go.Scatter(x=df_g.index, y=df_g['Close'], mode='lines', line=dict(color='#FFFF00', width=2), name="Cierre (Amarillo)"), row=1, col=1)
        fig.add_trace(go.Scatter(x=df_g.index, y=df_g['SMA20'], mode='lines', line=dict(color='#00E5FF', width=1.5), name="SMA 20"), row=1, col=1)
        fig.add_trace(go.Scatter(x=df_g.index, y=df_g['SMA50'], mode='lines', line=dict(color='#FF9100', width=2), name="SMA 50"), row=1, col=1)

        subidas = df_g[df_g['Señal_Subida']]
        bajadas = df_g[df_g['Señal_Bajada']]

        if not subidas.empty:
            fig.add_trace(go.Scatter(x=subidas.index, y=subidas['Low']*0.98, mode='text', text=['🚀']*len(subidas), textfont=dict(size=22), textposition='bottom center', name="Alcista"), row=1, col=1)

        if not bajadas.empty:
            fig.add_trace(go.Scatter(x=bajadas.index, y=bajadas['High']*1.02, mode='text', text=['💩']*len(bajadas), textfont=dict(size=22), textposition='top center', name="Bajista"), row=1, col=1)

        fig.add_trace(go.Scatter(x=df_g.index, y=df_g['MACD'], mode='lines', line=dict(color='#00E5FF', width=1.5), name="MACD"), row=2, col=1)
        fig.add_trace(go.Scatter(x=df_g.index, y=df_g['MACD_Signal'], mode='lines', line=dict(color='#FF9100', width=1.5), name="Señal"), row=2, col=1)
        colores_hist = ['#00E676' if v >= 0 else '#FF1744' for v in df_g['MACD_Hist']]
        fig.add_trace(go.Bar(x=df_g.index, y=df_g['MACD_Hist'], marker_color=colores_hist, name="Hist. MACD"), row=2, col=1)

        fig.add_trace(go.Scatter(x=df_g.index, y=df_g['RSI'], mode='lines', line=dict(color='#D000FF', width=1.5), name="RSI"), row=3, col=1)
        fig.add_hline(y=70, line_dash="dash", line_color="red", row=3, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="green", row=3, col=1)

        fig.update_layout(template="plotly_dark", height=800, xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True)

# -------------------------------------------------------------------
# PESTAÑA 2: DCA INTELIGENTE (LARGO PLAZO)
# -------------------------------------------------------------------
with tab2:
    st.title("💎 Calculadora DCA Inteligente / Value Averaging")
    st.write("Ajusta la aportación periódica según la valoración y el nivel de descuento histórico del activo.")

    col1, col2 = st.columns([1, 2])
    with col1:
        cuota_usuario = st.number_input("Aportación Base Periódica (€ / $):", min_value=10.0, max_value=10000.0, value=100.0, step=10.0)
        cat_dca = st.selectbox("Categoría a Evaluar:", list(CATALOGO_ACTIVOS.keys()), key="cat_dca")

    activos_dca_dic = CATALOGO_ACTIVOS[cat_dca]
    tickers_dca = list(activos_dca_dic.keys())

    datos_dca = descargar_datos(tickers_dca, period="3y", interval="1wk")
    resultados_dca = []

    for tk in tickers_dca:
        try:
            df_tk = datos_dca.copy() if len(tickers_dca) == 1 else datos_dca[tk].dropna()
            res_dca = calcular_dca_inteligente(df_tk, cuota_usuario)
            if res_dca:
                res_dca["Ticker"] = tk
                res_dca["Nombre"] = activos_dca_dic[tk]
                resultados_dca.append(res_dca)
        except Exception:
            pass

    df_dca_res = pd.DataFrame(resultados_dca)
    columnas_orden = ["Ticker", "Nombre", "Precio", "RSI Semanal", "Drawdown %", "Zona DCA", "Multiplicador", "Aportación Sugerida", "Razones"]
    st.dataframe(df_dca_res[columnas_orden], use_container_width=True, hide_index=True)

    st.markdown("---")
    st.subheader("💡 Guía de Zonas DCA")
    st.markdown("""
    * **🟢 OPORTUNIDAD FUERTE (Multiplicador 1.5x - 2.0x):** El activo sufre caídas intensas o RSI semanal en sobreventa extrema. Momento ideal para aportar más del presupuesto mensual.
    * **🟩 ZONA DE DESCUENTO (Multiplicador 1.1x - 1.4x):** Ligero descuento respecto a su valor promedio. Aportación ligeramente superior a la base.
    * **🟡 NEUTRAL (Multiplicador 1.0x):** Aportación base normal.
    * **🔴 ZONA EUFÓRICA (Multiplicador 0.0x - 0.4x):** Mercado muy eufórico / sobrecomprado. Se recomienda guardar la liquidez en liquidez/remunerada para compras futuras.
    """)
