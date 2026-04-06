import streamlit as st
import pandas as pd
import yfinance as yf # type: ignore
import numpy as np
import requests

# --- KONFIGURASI TELEGRAM ---
TOKEN = "8608017703:AAH6fxUlgxup-ejAQS1JsEeMIEwaqikocmg"
CHAT_ID = "7472978130"

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={CHAT_ID}&text={message}"
    try:
        requests.get(url)
    except:
        pass

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Charis Quant Scanner", layout="wide")
st.title("🚀 Indo-Stock Physics Scanner")
st.subheader("Analisis Z-Score & Volume Momentum (Bursa Efek Indonesia)")

# Daftar Saham Pilihan (LQ45 & Bluechip)
tickers = [
    'BBCA.JK', 'BBRI.JK', 'BMRI.JK', 'BBNI.JK', 'TLKM.JK', 
    'ASII.JK', 'GOTO.JK', 'ADRO.JK', 'UNTR.JK', 'AMRT.JK', 
    'PGAS.JK', 'ANTM.JK', 'INCO.JK', 'BRIS.JK', 'ICBP.JK'
]

@st.cache_data(ttl=3600) # Update data setiap jam
def get_stock_data(ticker_list):
    df_close = yf.download(ticker_list, period="60d")['Close']
    df_vol = yf.download(ticker_list, period="60d")['Volume']
    return df_close, df_vol

try:
    close_data, vol_data = get_stock_data(tickers)
    
    # Perhitungan Statistik (Window 20 Hari)
    window = 20
    ma = close_data.rolling(window=window).mean()
    std = close_data.rolling(window=window).std()
    z_score = (close_data - ma) / std
    
    vol_ma = vol_data.rolling(window=window).mean()
    vol_ratio = vol_data / vol_ma

    # Ambil Data Terbaru
    res_list = []
    for ticker in tickers:
        z = z_score[ticker].iloc[-1]
        vr = vol_ratio[ticker].iloc[-1]
        price = close_data[ticker].iloc[-1]
        
        # Logika Strategi
        if z < -2 and vr > 1.5:
            status = "🔥 STRONG BUY (Accumulation)"
            # Kirim Notifikasi jika terdeteksi Strong Buy
            send_telegram(f"📢 SINYAL POSITIF!\nSaham: {ticker}\nHarga: Rp{price}\nZ-Score: {round(z,2)}\nVol Ratio: {round(vr,2)}x\nIndikasi: Akumulasi Besar!")
        elif z < -2:
            status = "Buy (Oversold)"
        elif z > 2 and vr > 1.5:
            status = "⚠️ STRONG SELL (Distribution)"
        elif z > 2:
            status = "Sell (Overbought)"
        else:
            status = "Neutral"
            
        res_list.append({
            'Ticker': ticker.replace('.JK', ''),
            'Price': price,
            'Z-Score': round(z, 2),
            'Vol Ratio': round(vr, 2),
            'Recommendation': status
        })

    # Tampilkan Tabel
    df_final = pd.DataFrame(res_list)
    
    # Styling Tabel
    def color_rec(val):
        color = 'white'
        if 'STRONG BUY' in val: color = '#2ecc71'
        elif 'STRONG SELL' in val: color = '#e74c3c'
        elif 'Buy' in val: color = '#d4efdf'
        elif 'Sell' in val: color = '#fadbd8'
        return f'background-color: {color}; color: black'

    st.dataframe(df_final.style.applymap(color_rec, subset=['Recommendation']), use_container_width=True)
    
    st.success("Scanner aktif. Jika muncul sinyal 'Strong Buy', notifikasi akan masuk ke Telegram Anda secara otomatis.")

except Exception as e:
    st.error(f"Koneksi data terputus: {e}")