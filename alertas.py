import yfinance as yf
import pandas as pd

# ==========================================
# 1. EVALUADOR SWING TRADING (WYCKOFF + VSA)
# ==========================================

def evaluar_wyckoff_vsa_alertas(df, factor_volumen=1.3, ventana_rangos=12):
    """
    Procesa el DataFrame y devuelve la última vela junto con el diagnóstico
    sincronizado con la lógica de app.py.
    """
    if df is None or len(df) < 50:
        return None, "DATOS_INSUFICIENTES"

    df = df.copy()

    # Medias Móviles y Volumen Relativo
    df['Vol_SMA'] = df['Volume'].rolling(window=20).mean()
    df['Vol_Ratio'] = df['Volume'] / df['Vol_SMA']
    df['SMA20'] = df['Close'].rolling(window=20).mean()
    df['SMA50'] = df['Close'].rolling(window=50).mean()

    # Soportes y Resistencias Previas (excluyendo la vela actual)
    df['Min_Previo'] = df['Low'].shift(1).rolling(window=ventana_rangos).min()
    df['Max_Previo'] = df['High'].shift(1).rolling(window=ventana_rangos).max()

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

    # Giros de Histograma e Intención del Cierre
    df['MACD_Giro_Alcista'] = df['MACD_Hist'] > df['MACD_Hist'].shift(1)
    df['MACD_Giro_Bajista'] = df['MACD_Hist'] < df['MACD_Hist'].shift(1)
    df['Vela_Alcista'] = df['Close'] > df['Open']
    df['Vela_Bajista'] = df['Close'] < df['Open']

    # Tests de Volumen
    df['Test_Suelo'] = (df['Vol_Ratio'] >= factor_volumen) & (df['Low'] <= df['Min_Previo'])
    df['Test_Techo'] = (df['Vol_Ratio'] >= factor_volumen) & (df['High'] >= df['Max_Previo'])

    # Lógica de SUBIDA CONFIRMADA (🚀)
    spring_confirmado = df['Test_Suelo'] & df['Vela_Alcista'] & df['MACD_Giro_Alcista'] & (df['RSI'] < 50)
    absorcion_confirmada = (
        df['Test_Techo'] & 
        df['Vela_Alcista'] & 
        (df['Close'] >= df['SMA20']) & 
        (df['Close'] >= df['SMA50']) & 
        (df['MACD_Hist'] > 0) & 
        df['MACD_Giro_Alcista']
    )
    df['Señal_Subida'] = spring_confirmado | absorcion_confirmada

    # Lógica de CAÍDA CONFIRMADA (💩)
    upthrust_confirmado = df['Test_Techo'] & df['Vela_Bajista'] & df['MACD_Giro_Bajista'] & (df['RSI'] > 50)
    ruptura_confirmada = (
        df['Test_Suelo'] & 
        df['Vela_Bajista'] & 
        (df['Close'] <= df['SMA20']) & 
        (df['Close'] <= df['SMA50']) & 
        (df['MACD_Hist'] < 0) & 
        df['MACD_Giro_Bajista']
    )
    df['Señal_Bajada'] = upthrust_confirmado | ruptura_confirmada

    ultima_vela = df.iloc[-1]

    if ultima_vela['Señal_Subida']:
        tipo_patron = "SPRING (Suelo)" if spring_confirmado.iloc[-1] else "ABSORCIÓN (Breakout)"
        return ultima_vela, f"🚀 SUBIDA_PROBABLE ({tipo_patron})"
    elif ultima_vela['Señal_Bajada']:
        tipo_patron = "UPTHRUST (Techo)" if upthrust_confirmado.iloc[-1] else "FALLO DE SOPORTE"
        return ultima_vela, f"💩 CAÍDA_PROBABLE ({tipo_patron})"
    else:
        return ultima_vela, "NEUTRAL"

def generar_mensaje_swing_telegram(ticker, nombre, period="1y", interval="1d", factor_volumen=1.3):
    """
    Genera el mensaje formateado para Telegram en caso de señal Swing Trading.
    """
    try:
        df = yf.download(ticker, period=period, interval=interval, progress=False, auto_adjust=True)
        if isinstance(df.columns, pd.MultiIndex):
            df = df.xs(ticker, level=1, axis=1) if ticker in df.columns.levels[1] else df.droplevel(1, axis=1)
            
        ultima_vela, estado = evaluar_wyckoff_vsa_alertas(df, factor_volumen=factor_volumen)

        if "SUBIDA_PROBABLE" in estado:
            emoji = "🚀"
        elif "CAÍDA_PROBABLE" in estado:
            emoji = "💩"
        else:
            return None

        mensaje = (
            f"{emoji} *ALERTA WYCKOFF + VSA (SWING)*\n"
            f"*Activo:* {ticker} ({nombre})\n"
            f"*Diagnóstico:* {estado}\n\n"
            f"📊 *Datos Clave:*\n"
            f"• Precio: ${round(float(ultima_vela['Close']), 2)}\n"
            f"• Volumen Relativo: {round(float(ultima_vela['Vol_Ratio']), 2)}x\n"
            f"• RSI (14): {round(float(ultima_vela['RSI']), 1)}\n"
            f"───────────────────"
        )
        return mensaje
    except Exception:
        return None


# ==========================================
# 2. EVALUADOR DCA INTELIGENTE (LARGO PLAZO)
# ==========================================

def calcular_dca_inteligente_alertas(df, cuota_base=100.0):
    """
    Evalúa si un activo de largo plazo está en zona de descuento/oportunidad.
    """
    if df is None or len(df) < 50:
        return None

    df = df.copy()

    # RSI Semanal (14)
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI_Semanal'] = 100 - (100 / (1 + rs))

    # Media Móvil Anual y Drawdown %
    df['SMA50_Semanal'] = df['Close'].rolling(window=50).mean()
    df['Max_52W'] = df['High'].rolling(window=52).max()
    df['Drawdown_Pct'] = ((df['Close'] - df['Max_52W']) / df['Max_52W']) * 100

    u = df.iloc[-1]
    rsi = float(u['RSI_Semanal'])
    dd = float(u['Drawdown_Pct'])
    precio = float(u['Close'])
    sma50 = float(u['SMA50_Semanal'])

    multiplicador = 1.0
    explicacion = []

    # Ajuste por RSI
    if rsi < 35:
        multiplicador += 0.6
        explicacion.append("RSI en sobreventa extrema (<35)")
    elif rsi < 45:
        multiplicador += 0.3
        explicacion.append("RSI en sobreventa/descuento (<45)")
    elif rsi > 70:
        multiplicador -= 0.6
        explicacion.append("RSI eufórico (>70)")

    # Ajuste por caída desde máximos
    if dd <= -40:
        multiplicador += 0.5
        explicacion.append(f"Caída fuerte del {dd:.1f}%")
    elif dd <= -20:
        multiplicador += 0.25
        explicacion.append(f"Corrección del {dd:.1f}%")

    if precio < sma50:
        multiplicador += 0.2
        explicacion.append("Bajo la media móvil anual")

    multiplicador = max(0.0, round(multiplicador, 2))
    aportacion = round(cuota_base * multiplicador, 2)

    if multiplicador >= 1.3:
        zona = "🟢 OPORTUNIDAD DE COMPRA (Descuento)"
    elif multiplicador <= 0.4:
        zona = "🔴 MERCADO EUFÓRICO (Pausar/Reducir)"
    else:
        zona = "🟡 NEUTRAL"

    return {
        "Precio": round(precio, 2),
        "RSI": round(rsi, 1),
        "Drawdown": f"{dd:.1f}%",
        "Zona": zona,
        "Multiplicador": f"{multiplicador}x",
        "Aportacion": f"{aportacion} €",
        "Motivo": " | ".join(explicacion) if explicacion else "Normal"
    }

def generar_mensaje_dca_telegram(ticker, nombre, cuota_base=100.0):
    """
    Descarga datos semanales y genera el mensaje para Telegram si hay oportunidad DCA.
    """
    try:
        df = yf.download(ticker, period="3y", interval="1wk", progress=False, auto_adjust=True)
        if isinstance(df.columns, pd.MultiIndex):
            df = df.xs(ticker, level=1, axis=1) if ticker in df.columns.levels[1] else df.droplevel(1, axis=1)
            
        res = calcular_dca_inteligente_alertas(df, cuota_base)

        if res and ("OPORTUNIDAD" in res['Zona'] or "EUFÓRICO" in res['Zona']):
            mensaje = (
                f"💎 *ALERTA DCA INTELIGENTE*\n"
                f"*Activo:* {ticker} ({nombre})\n"
                f"*Estado:* {res['Zona']}\n\n"
                f"📊 *Datos Clave:*\n"
                f"• Precio: ${res['Precio']}\n"
                f"• RSI Semanal: {res['RSI']}\n"
                f"• Caída desde máximos: {res['Drawdown']}\n\n"
                f"🎯 *Sugerencia de Aportación:*\n"
                f"• *{res['Aportacion']}* (Multiplicador {res['Multiplicador']})\n"
                f"💡 *Motivo:* {res['Motivo']}\n"
                f"───────────────────"
            )
            return mensaje
        return None
    except Exception:
        return None
