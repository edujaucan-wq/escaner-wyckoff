import yfinance as yf
import pandas as pd

# UMBRAL DE VOLUMEN INUSUAL CONFIGURABLE
FACTOR_VOLUMEN = 1.3  # Ajustado a 1.3x la media de volumen

def evaluar_wyckoff_macd(df, p_vol=20, f_vol=FACTOR_VOLUMEN, v_rangos=12):
    if len(df) < 35:
        return None
        
    # 1. Volumen y Rangos
    df['Vol_SMA'] = df['Volume'].rolling(window=p_vol).mean()
    df['Vol_Ratio'] = df['Volume'] / df['Vol_SMA']
    df['Min_Reciente'] = df['Close'].rolling(window=v_rangos).min()
    df['Max_Reciente'] = df['Close'].rolling(window=v_rangos).max()
    
    # 2. MACD
    ema12 = df['Close'].ewm(span=12, adjust=False).mean()
    ema26 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = ema12 - ema26
    df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    df['MACD_Hist'] = df['MACD'] - df['MACD_Signal']
    
    # 3. Giros
    df['MACD_Giro_Alcista'] = df['MACD_Hist'] > df['MACD_Hist'].shift(1)
    df['MACD_Giro_Bajista'] = df['MACD_Hist'] < df['MACD_Hist'].shift(1)
    
    # 4. Señales
    df['Es_Spring'] = (df['Vol_Ratio'] >= f_vol) & (df['Close'] <= df['Min_Reciente'])
    df['Es_Upthrust'] = (df['Vol_Ratio'] >= f_vol) & (df['Close'] >= df['Max_Reciente'])
    
    df['Spring_Elite'] = df['Es_Spring'] & df['MACD_Giro_Alcista']
    df['Spring_Fallo'] = df['Es_Spring'] & (~df['MACD_Giro_Alcista'])
    
    df['Upthrust_Elite'] = df['Es_Upthrust'] & df['MACD_Giro_Bajista']
    df['Upthrust_Fallo'] = df['Es_Upthrust'] & (~df['MACD_Giro_Bajista'])
    
    return df

def formatear_mensaje_telegram(ticker, ultima):
    if ultima['Spring_Elite']:
        return (
            f"🚀 **ALERTA ÉLITE WYCKOFF + MACD** 🚀\n\n"
            f"📌 **Activo:** {ticker}\n"
            f"🟢 **Patrón:** Spring / Acumulación Institucional\n"
            f"📊 **Volumen Inusual:** {round(ultima['Vol_Ratio'], 2)}x\n"
            f"💡 **MACD:** Giro Alcista Confirmado (Absorción de Oferta)\n"
            f"💰 **Precio:** ${round(ultima['Close'], 2)}"
        )
    elif ultima['Spring_Fallo']:
        return (
            f"⚠️ **ALERTA TRAMPA / FALLO MACD** ⚠️\n\n"
            f"📌 **Activo:** {ticker}\n"
            f"🟡 **Patrón:** Spring con Fallo de MACD\n"
            f"📊 **Volumen Inusual:** {round(ultima['Vol_Ratio'], 2)}x\n"
            f"🛑 **Atención:** El histograma MACD no acompaña. Posible trampa bajista o venta masiva."
        )
    elif ultima['Upthrust_Elite']:
        return (
            f"🔴 **ALERTA ÉLITE WYCKOFF + MACD** 🔴\n\n"
            f"📌 **Activo:** {ticker}\n"
            f"🔴 **Patrón:** Upthrust / Distribución Institucional\n"
            f"📊 **Volumen Inusual:** {round(ultima['Vol_Ratio'], 2)}x\n"
            f"💡 **MACD:** Giro Bajista Confirmado (Falta de Demanda)\n"
            f"💰 **Precio:** ${round(ultima['Close'], 2)}"
        )
    elif ultima['Upthrust_Fallo']:
        return (
            f"⚠️ **ALERTA TRAMPA / FALLO MACD** ⚠️\n\n"
            f"📌 **Activo:** {ticker}\n"
            f"🟡 **Patrón:** Upthrust con Fallo de MACD\n"
            f"📊 **Volumen Inusual:** {round(ultima['Vol_Ratio'], 2)}x\n"
            f"🛑 **Atención:** El MACD sigue con fuerza alcista. Posible absorción compradora."
        )
    return None
