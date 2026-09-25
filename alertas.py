import os
import requests
import yfinance as yf
import pandas as pd
from app import CATALOGO_ACTIVOS

# ==========================================
# CONFIGURACIÓN DE TELEGRAM Y PARÁMETROS
# ==========================================
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

FACTOR_VOLUMEN = 1.3  # Umbral de volumen inusual (1.3x la media)

def enviar_telegram(mensaje):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ Variables de Telegram no configuradas.")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": mensaje,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Error al enviar mensaje a Telegram: {e}")

# ==========================================
# EVALUACIÓN DE SEÑALES WYCKOFF + MACD
# ==========================================
def evaluar_wyckoff_macd(df, p_vol=20, f_vol=FACTOR_VOLUMEN, v_rangos=12):
    if len(df) < 35:
        return None
        
    # 1. Volumen y Rangos
    df['Vol_SMA'] = df['Volume'].rolling(window=p_vol).mean()
    df['Vol_Ratio'] = df['Volume'] / df['Vol_SMA']
    df['Min_Reciente'] = df['Close'].rolling(window=v_rangos).min()
    df['Max_Reciente'] = df['Close'].rolling(window=v_rangos).max()
    
    # 2. MACD (12, 26, 9)
    ema12 = df['Close'].ewm(span=12, adjust=False).mean()
    ema26 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = ema12 - ema26
    df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    df['MACD_Hist'] = df['MACD'] - df['MACD_Signal']
    
    # 3. Giros de MACD
    df['MACD_Giro_Alcista'] = df['MACD_Hist'] > df['MACD_Hist'].shift(1)
    df['MACD_Giro_Bajista'] = df['MACD_Hist'] < df['MACD_Hist'].shift(1)
    
    # 4. Detección de Señales
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
            f"⚠️ **ALERTA FALLO SPRING** ⚠️\n\n"
            f"📌 **Activo:** {ticker}\n"
            f"🟡 **Patrón:** Spring sin confirmación MACD\n"
            f"📊 **Volumen Inusual:** {round(ultima['Vol_Ratio'], 2)}x\n"
            f"🛑 **Atención:** El MACD sigue bajista con fuerza. Posible caída libre o venta real."
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
            f"🎁 **REGALO DEL MERCADO / REGALO DE TRULLAS** 🎁\n\n"
            f"📌 **Activo:** {ticker}\n"
            f"🚀 **Patrón:** Fallo de MACD en Resistencia (Absorción Institucional)\n"
            f"📊 **Volumen Inusual:** {round(ultima['Vol_Ratio'], 2)}x\n"
            f"🔥 **Lectura:** El MACD no confirma la distribución. Las manos fuertes están absorbiendo la oferta para romper al alza.\n"
            f"💰 **Precio:** ${round(ultima['Close'], 2)}"
        )
    return None

# ==========================================
# EJECUCIÓN PRINCIPAL (SCANNER AUTOMÁTICO)
# ==========================================
def ejecutar_escaneo():
    # Extraer todos los tickers configurados en CATALOGO_ACTIVOS de app.py
    todos_los_tickers = []
    for cat, dic in CATALOGO_ACTIVOS.items():
        todos_los_tickers.extend(list(dic.keys()))
    
    # Eliminar duplicados manteniendo orden
    tickers_lista = list(dict.fromkeys(todos_los_tickers))
    
    print(f"Buscando señales en {len(tickers_lista)} activos...")
    
    # Descarga de datos
    datos = yf.download(tickers_lista, period="6m", interval="1d", group_by="ticker", progress=False, auto_adjust=True)
    
    for ticker in tickers_lista:
        try:
            df_activo = datos.copy() if len(tickers_lista) == 1 else datos[ticker].dropna()
            df_eval = evaluar_wyckoff_macd(df_activo)
            
            if df_eval is not None and not df_eval.empty:
                ultima = df_eval.iloc[-1]
                msg = formatear_mensaje_telegram(ticker, ultima)
                if msg:
                    enviar_telegram(msg)
                    print(f"Alerta enviada para {ticker}")
        except Exception as e:
            print(f"Error procesando {ticker}: {e}")

if __name__ == "__main__":
    ejecutar_escaneo()
