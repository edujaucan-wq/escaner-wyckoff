import os
import requests
import yfinance as yf
import pandas as pd

# CONFIGURACIÓN (Usa las variables de entorno para seguridad)
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

ACTIVOS = [
    "GLD", "SLV", "BTC-USD", "ETH-USD", "COPX", "URA", "USO", 
    "QQQ", "SPY", "IWM", "EEM", "XLK", "XLF", "XLE", "SMH", 
    "TLT", "AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "TSLA"
]

def enviar_telegram(mensaje):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("Faltan credenciales de Telegram.")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": mensaje, "parse_mode": "Markdown"}
    requests.post(url, data=payload)

def comprobar_alertas():
    print("Iniciando análisis de alertas Wyckoff...")
    datos = yf.download(ACTIVOS, period="1y", interval="1d", group_by="ticker", progress=False)
    
    alertas = []
    
    for ticker in ACTIVOS:
        try:
            df = datos[ticker].dropna().copy() if len(ACTIVOS) > 1 else datos.dropna().copy()
            if len(df) < 50:
                continue
            
            # Cálculo de variables
            df['Vol_SMA'] = df['Volume'].rolling(window=20).mean()
            df['Vol_Ratio'] = df['Volume'] / df['Vol_SMA']
            df['Min_Reciente'] = df['Close'].rolling(window=12).min()
            df['Max_Reciente'] = df['Close'].rolling(window=12).max()
            
            ultima = df.iloc[-1]
            
            # Detección
            es_spring = (ultima['Vol_Ratio'] >= 1.5) and (ultima['Close'] <= ultima['Min_Reciente'])
            es_upthrust = (ultima['Vol_Ratio'] >= 1.5) and (ultima['Close'] >= ultima['Max_Reciente'])
            
            if es_spring:
                alertas.append(f"🟢 **SPRING (Acumulación)** detectado en **{ticker}** | Precio: ${round(ultima['Close'], 2)} | Vol Ratio: {round(ultima['Vol_Ratio'], 2)}x")
            elif es_upthrust:
                alertas.append(f"🔴 **UPTHRUST (Distribución)** detectado en **{ticker}** | Precio: ${round(ultima['Close'], 2)} | Vol Ratio: {round(ultima['Vol_Ratio'], 2)}x")
        except Exception as e:
            continue

    if alertas:
        mensaje_final = "🚨 **ALERTAS WYCKOFF DETECTADAS** 🚨\n\n" + "\n\n".join(alertas)
        enviar_telegram(mensaje_final)
        print("Alertas enviadas a Telegram.")
    else:
        print("No se encontraron alertas en este pase.")

if __name__ == "__main__":
    comprobar_alertas()