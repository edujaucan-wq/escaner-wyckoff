import yfinance as yf
import pandas as pd
import numpy as np

# ==========================================
# PARÁMETROS CONFIGURABLES DE ALERTA
# ==========================================
FACTOR_VOLUMEN = 1.5   # Volumen anormal: 150% sobre su media
VENTANA_RANGOS = 12    # Barras para definir techos y suelos previos
PERIODO_VOL = 20       # Media móvil de volumen

def calcular_indicadores(df):
    """Calcula Medias, MACD, RSI y ATR para el análisis de divergencias y volatilidad."""
    if len(df) < 50:
        return df

    # 1. Medias Móviles y Volumen Relativo
    df['Vol_SMA'] = df['Volume'].rolling(window=PERIODO_VOL).mean()
    df['Vol_Ratio'] = df['Volume'] / df['Vol_SMA']
    df['SMA20'] = df['Close'].rolling(window=20).mean()
    df['SMA50'] = df['Close'].rolling(window=50).mean()

    # 2. Rangos Previos (Soportes y Resistencias excluyendo la vela actual)
    df['Min_Previo'] = df['Low'].shift(1).rolling(window=VENTANA_RANGOS).min()
    df['Max_Previo'] = df['High'].shift(1).rolling(window=VENTANA_RANGOS).max()

    # 3. MACD (12, 26, 9)
    ema12 = df['Close'].ewm(span=12, adjust=False).mean()
    ema26 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = ema12 - ema26
    df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    df['MACD_Hist'] = df['MACD'] - df['MACD_Signal']

    # 4. RSI (14)
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))

    # 5. Giros del Histograma del MACD
    df['MACD_Giro_Alcista'] = df['MACD_Hist'] > df['MACD_Hist'].shift(1)
    df['MACD_Giro_Bajista'] = df['MACD_Hist'] < df['MACD_Hist'].shift(1)

    return df

def evaluar_wyckoff_vsa(df):
    """
    Evalúa la presencia de patrones Wyckoff + VSA + Divergencias de Indicador.
    Devuelve la última vela analizada con su diagnóstico de alerta.
    """
    df = calcular_indicadores(df)
    if len(df) < 50:
        return None

    # Testeo de Soportes y Resistencias con volumen inusual
    df['Test_Suelo'] = (df['Vol_Ratio'] >= FACTOR_VOLUMEN) & (df['Low'] <= df['Min_Previo'])
    df['Test_Techo'] = (df['Vol_Ratio'] >= FACTOR_VOLUMEN) & (df['High'] >= df['Max_Previo'])

    # --- CONDICIONES ALCISTAS (🚀 SUBIDA PROBABLE) ---
    # A) Spring / Acumulación: Barrido de soporte + Giro alcista MACD + RSI recuperando de sobreventa (<45)
    spring = df['Test_Suelo'] & df['MACD_Giro_Alcista'] & (df['RSI'] < 50)
    # B) Absorción en Resistencias: Ruptura/Test de techo con volumen + MACD fuertemente positivo (>0) + Precio > SMA20
    absorcion = df['Test_Techo'] & (df['MACD_Hist'] > 0) & df['MACD_Giro_Alcista'] & (df['Close'] >= df['SMA20'])

    df['Alerta_Subida'] = spring | absorcion

    # --- CONDICIONES BAJISTAS (💩 CAÍDA PROBABLE) ---
    # A) Upthrust / Distribución: Testeo de techo con volumen + Giro bajista MACD + RSI en zona alta (>55)
    upthrust = df['Test_Techo'] & df['MACD_Giro_Bajista'] & (df['RSI'] > 50)
    # B) Pérdida de Soporte / Fallo Spring: Caída rompiendo suelo con volumen + MACD negativo (<0) y cayendo
    ruptura_bajista = df['Test_Suelo'] & (df['MACD_Hist'] < 0) & df['MACD_Giro_Bajista']

    df['Alerta_Bajada'] = upthrust | ruptura_bajista

    return df.iloc[-1]

def generar_mensaje_telegram(ticker, nombre, ultima_vela):
    """Genera el texto de la notificación para Telegram si hay alerta activa."""
    if ultima_vela['Alerta_Subida']:
        emoji = "🚀"
        tipo = "SUBIDA PROBABLE (Acumulación / Absorción)"
        detalles = f"• Volumen Relativo: {ultima_vela['Vol_Ratio']:.2f}x\n• RSI: {ultima_vela['RSI']:.1f}\n• Precio: ${ultima_vela['Close']:.2f}"
    elif ultima_vela['Alerta_Bajada']:
        emoji = "💩"
        tipo = "CAÍDA PROBABLE (Distribución / Pérdida Soporte)"
        detalles = f"• Volumen Relativo: {ultima_vela['Vol_Ratio']:.2f}x\n• RSI: {ultima_vela['RSI']:.1f}\n• Precio: ${ultima_vela['Close']:.2f}"
    else:
        return None

    mensaje = (
        f"{emoji} *ALERTA WYCKOFF + VSA*\n"
        f"*Activo:* {ticker} ({nombre})\n"
        f"*Diagnóstico:* {tipo}\n\n"
        f"*Datos Clave:*\n{detalles}\n"
        f"───────────────────"
    )
    return mensaje
