# app.py
# -----------------------------------------------------------------------------
# El Compás del Inversor - v25.0 (Versión Web Final Profesional)
# -----------------------------------------------------------------------------
#
# Para ejecutar esta aplicación:
# 1. Guarda este código como 'app.py'.
# 2. Abre una terminal y ejecuta: pip install streamlit yfinance matplotlib numpy pandas
# 3. En la misma terminal, navega a la carpeta donde guardaste el archivo y ejecuta:
#    streamlit run app.py
#
# -----------------------------------------------------------------------------

import streamlit as st
import yfinance as yf
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# --- CONFIGURACIÓN DE LA PÁGINA WEB Y ESTILOS ---
st.set_page_config(page_title="El Compás del Inversor", page_icon="🧭", layout="wide")

# Estilos CSS para un look profesional (negro y dorado)
st.markdown("""
<style>
    .stApp {
        background-color: #0E1117;
        color: #FAFAFA;
    }
    h1, h2, h3 {
        color: #D4AF37; /* Color dorado */
    }
    .st-emotion-cache-1r6slb0 {
        border: 1px solid #D4AF37 !important;
        border-radius: 10px;
        padding: 15px !important;
    }
    .stButton>button {
        background-color: #D4AF37;
        color: #0E1117;
        border-radius: 8px;
        border: 1px solid #D4AF37;
        font-weight: bold;
    }
    /* CORRECCIÓN: Hacer que el valor de la métrica sea legible */
    [data-testid="stMetricValue"] {
        color: #FAFAFA;
    }
</style>
""", unsafe_allow_html=True)


# --- BLOQUE 1: OBTENCIÓN DE DATOS (VERSIÓN ROBUSTA) ---
@st.cache_data(ttl=900)
def obtener_datos_completos(ticker):
    stock = yf.Ticker(ticker)
    info = stock.info
    if not info or info.get('longName') is None: return None
    
    roe = info.get('returnOnEquity')
    op_margin = info.get('operatingMargins')
    payout = info.get('payoutRatio')
    div_yield = 0
    dividend_rate = info.get('dividendRate')
    precio = info.get('currentPrice')
    
    if dividend_rate and precio and precio > 0:
        div_yield = (dividend_rate / precio)
        
    if payout is not None and (payout > 1.5 or payout < 0):
        trailing_eps = info.get('trailingEps')
        if trailing_eps and dividend_rate and trailing_eps > 0:
            payout = dividend_rate / trailing_eps
        else:
            payout = None
            
    return {
        "nombre": info.get('longName', 'N/A'), "sector": info.get('sector', 'N/A'),
        "pais": info.get('country', 'N/A'),
        "industria": info.get('industry', 'N/A'), "descripcion": info.get('longBusinessSummary', 'No disponible.'),
        "roe": roe * 100 if roe is not None else 0, "margen_operativo": op_margin * 100 if op_margin is not None else 0,
        "margen_beneficio": info.get('profitMargins', 0) * 100, "deuda_patrimonio": info.get('debtToEquity'),
        "ratio_corriente": info.get('currentRatio'), "per": info.get('trailingPE'),
        "per_adelantado": info.get('forwardPE'), "precio_ventas": info.get('priceToSalesTrailing12Months'),
        "precio_valor_contable": info.get('priceToBook'), "yield_dividendo": div_yield * 100 if div_yield is not None else 0,
        "payout_ratio": payout * 100 if payout is not None else 0,
        "recomendacion_analistas": info.get('recommendationKey', 'N/A'),
        "precio_objetivo": info.get('targetMeanPrice', 'N/A'),
    }

# --- BLOQUE 2: LÓGICA DE PUNTUACIÓN Y ANÁLISIS ---
@st.cache_data(ttl=3600)
def obtener_datos_historicos(ticker):
    try:
        stock = yf.Ticker(ticker)
        financials = stock.financials.T.sort_index(ascending=True).tail(4)
        balance_sheet = stock.balance_sheet.T.sort_index(ascending=True).tail(4)
        dividends = stock.dividends.resample('YE').sum().tail(5)
        hist_precios = stock.history(period="5y")['Close']
        
        if financials.empty: return None, None, None
        
        financials['Operating Margin'] = financials.get('Operating Income', 0) / financials.get('Total Revenue', 1)
        financials['Total Debt'] = balance_sheet.get('Total Debt', 0)
        financials['EPS'] = financials['Net Income'] / stock.info.get('sharesOutstanding', 1)
        
        return financials, dividends, hist_precios
    except Exception:
        return None, None, None

def analizar_banderas_rojas(datos, financials):
    banderas = []
    if datos['payout_ratio'] > 100:
        banderas.append("🔴 **Payout Peligroso:** El ratio de reparto de dividendos es superior al 100%.")
    if financials is not None and not financials.empty:
        if 'Operating Margin' in financials.columns and len(financials) >= 3:
            if pd.notna(financials['Operating Margin']).all() and (financials['Operating Margin'].diff().iloc[-2:] < 0).all():
                banderas.append("🔴 **Márgenes Decrecientes:** Los márgenes de beneficio llevan 3 años seguidos bajando.")
        if 'Total Debt' in financials.columns and len(financials) >= 3:
            if pd.notna(financials['Total Debt']).all() and financials['Total Debt'].iloc[-3] > 0 and financials['Total Debt'].iloc[-1] > financials['Total Debt'].iloc[-3] * 1.5:
                banderas.append("🔴 **Deuda Creciente:** La deuda total ha aumentado significativamente.")
    return banderas

def calcular_puntuaciones_y_justificaciones(datos):
    puntuaciones = {}
    justificaciones = {}
    sector = datos['sector']
    pais = datos['pais']
    benchmarks = {
        'Technology': {'roe_excelente': 25, 'roe_bueno': 18, 'margen_excelente': 25, 'margen_bueno': 18, 'per_barato': 25, 'per_justo': 35},
        'Financial Services': {'roe_excelente': 12, 'roe_bueno': 10, 'per_barato': 12, 'per_justo': 18},
        'Default': {'roe_excelente': 15, 'roe_bueno': 12, 'margen_excelente': 15, 'margen_bueno': 10, 'per_barato': 20, 'per_justo': 25}
    }
    sector_bench = benchmarks.get(sector, benchmarks['Default'])
    paises_seguros = ['United States', 'Canada', 'Germany', 'Switzerland', 'Netherlands', 'United Kingdom', 'France', 'Denmark', 'Sweden', 'Norway', 'Finland', 'Australia', 'New Zealand', 'Japan', 'Ireland']
    paises_precaucion = ['Spain', 'Italy', 'South Korea', 'Taiwan', 'India']
    paises_alto_riesgo = ['China', 'Brazil', 'Russia', 'Argentina', 'Turkey', 'Mexico']
    
    nota_geo, justificacion_geo, penalizador_geo = 10, "Opera en una jurisdicción estable y predecible.", 0
    if pais in paises_precaucion:
        nota_geo, justificacion_geo, penalizador_geo = 6, "PRECAUCIÓN: Jurisdicción con cierta volatilidad.", 1.5
    elif pais in paises_alto_riesgo:
        nota_geo, justificacion_geo, penalizador_geo = 2, "ALTO RIESGO: Jurisdicción con alta inestabilidad.", 3.0
    elif pais not in paises_seguros:
        nota_geo, justificacion_geo, penalizador_geo = 5, "PRECAUCIÓN: Jurisdicción no clasificada.", 2.0
    puntuaciones['geopolitico'], justificaciones['geopolitico'], puntuaciones['penalizador_geo'] = nota_geo, justificacion_geo, penalizador_geo

    nota_calidad = 0
    if datos['roe'] > sector_bench.get('roe_excelente', 15): nota_calidad += 5
    elif datos['roe'] > sector_bench.get('roe_bueno', 12): nota_calidad += 4
    if datos['margen_operativo'] > sector_bench.get('margen_excelente', 15): nota_calidad += 5
    elif datos['margen_operativo'] > sector_bench.get('margen_bueno', 10): nota_calidad += 4
    puntuaciones['calidad'] = nota_calidad
    if nota_calidad >= 8: justificaciones['calidad'] = "Rentabilidad y márgenes de élite para su sector."
    else: justificaciones['calidad'] = "Negocio de buena calidad con márgenes sólidos."

    nota_salud = 0
    deuda_ratio = datos['deuda_patrimonio']
    if sector in ['Financial Services', 'Real Estate', 'Utilities']:
        nota_salud = 8
        justificaciones['salud'] = "Sector intensivo en capital."
    elif isinstance(deuda_ratio, (int, float)):
        if deuda_ratio < 40: nota_salud = 10
        elif deuda_ratio < 80: nota_salud = 8
        else: nota_salud = 5
        if nota_salud >= 8: justificaciones['salud'] = "Balance muy sólido y conservador."
        else: justificaciones['salud'] = "Nivel de deuda manejable."
    else:
        nota_salud = 5
        justificaciones['salud'] = "Datos de deuda no disponibles."
    puntuaciones['salud'] = nota_salud
    
    # NUEVA PUNTUACIÓN DE MOAT
    puntuaciones['moat'] = round((nota_calidad * 0.7) + (nota_salud * 0.3))
    if puntuaciones['moat'] >= 8: justificaciones['moat'] = "Moat Ancho: Negocio dominante y muy defendido."
    elif puntuaciones['moat'] >= 5: justificaciones['moat'] = "Moat Estrecho: Ciertas ventajas competitivas."
    else: justificaciones['moat'] = "Sin Moat Claro: Negocio vulnerable a la competencia."

    nota_valoracion = 0
    per = datos['per']
    if isinstance(per, (int, float)):
        if per < sector_bench['per_barato']: nota_valoracion = 10
        elif per < sector_bench['per_justo']: nota_valoracion = 7
        else: nota_valoracion = 4
    puntuaciones['valoracion'] = nota_valoracion
    if nota_valoracion >= 7: justificaciones['valoracion'] = "Valoración atractiva para su sector."
    elif nota_valoracion >= 4: justificaciones['valoracion'] = "Precio justo por un negocio de calidad."
    else: justificaciones['valoracion'] = "Valoración exigente."

    nota_dividendos = 0
    if datos['yield_dividendo'] > 3.5: nota_dividendos += 5
    elif datos['yield_dividendo'] > 2: nota_dividendos += 3
    if 0 < datos['payout_ratio'] < 60: nota_dividendos += 5
    elif 0 < datos['payout_ratio'] < 80: nota_dividendos += 3
    puntuaciones['dividendos'] = nota_dividendos
    if nota_dividendos >= 8: justificaciones['dividendos'] = "Dividendo excelente, alto y muy seguro."
    elif nota_dividendos >= 5: justificaciones['dividendos'] = "Dividendo sólido y sostenible."
    else: justificaciones['dividendos'] = "Dividendo bajo o no prioritario."
    
    return puntuaciones, justificaciones

# --- BLOQUE 3: GRÁFICOS Y PRESENTACIÓN ---
@st.cache_data(ttl=3600)
def crear_graficos_profesionales(ticker, financials, dividends, hist_precios):
    try:
        if financials is None or financials.empty: return None
        años = [d.year for d in financials.index]
        fig, axs = plt.subplots(2, 2, figsize=(15, 10))
        plt.style.use('dark_background')
        fig.patch.set_facecolor('#0E1117')
        
        for ax in axs.flat:
            ax.tick_params(colors='white')
            ax.spines['bottom'].set_color('white')
            ax.spines['top'].set_color('white') 
            ax.spines['right'].set_color('white')
            ax.spines['left'].set_color('white')
            ax.yaxis.label.set_color('white')
            ax.xaxis.label.set_color('white')
            ax.title.set_color('white')

        # Gráfico 1: Crecimiento
        axs[0, 0].bar(años, financials['Total Revenue'] / 1e9, label='Ingresos', color='#87CEEB')
        axs[0, 0].bar(años, financials['Net Income'] / 1e9, label='Beneficio Neto', color='#D4AF37', width=0.5)
        axs[0, 0].set_title('1. Crecimiento del Negocio (B)')
        axs[0, 0].legend()

        # Gráfico 2: Rentabilidad
        ax2_twin = axs[0, 1].twinx()
        axs[0, 1].plot(años, financials['ROE'] * 100, label='ROE (%)', color='purple', marker='o')
        ax2_twin.plot(años, financials['Operating Margin'] * 100, label='Margen Op. (%)', color='#D4AF37', marker='s')
        axs[0, 1].set_title('2. Rentabilidad y Eficiencia')
        fig.legend(loc='upper center', bbox_to_anchor=(0.7, 0.9))

        # Gráfico 3: Valoración Histórica (PER)
        hist_per = hist_precios.resample('YE').last() / financials['EPS']
        media_per = hist_per.mean()
        axs[1, 0].plot(hist_per.index.year, hist_per, label='PER Histórico', color='cyan', marker='o')
        axs[1, 0].axhline(y=media_per, color='yellow', linestyle='--', label=f'Media 5 Años ({media_per:.1f}x)')
        axs[1, 0].set_title('3. Valoración Histórica (PER)')
        axs[1, 0].legend()

        # Gráfico 4: Dividendos
        axs[1, 1].bar(dividends.index.year, dividends, label='Dividendo por Acción', color='orange')
        axs[1, 1].set_title('4. Retorno al Accionista')
        
        plt.tight_layout(rect=[0, 0.03, 1, 0.95])
        return fig
    except Exception:
        return None

# --- ESTRUCTURA DE LA APLICACIÓN WEB ---
st.title('El Compás del Inversor 🧭')
st.caption("Tu copiloto para la inversión a largo plazo. Creado con un inversor exigente.")

ticker_input = st.text_input("Introduce el Ticker de la Acción a Analizar (ej. JNJ, MSFT, BABA)", "AAPL").upper()

if st.button('Analizar Acción'):
    with st.spinner('Realizando análisis profesional...'):
        datos = obtener_datos_completos(ticker_input)
        
        if not datos:
            st.error(f"Error: No se pudo encontrar el ticker '{ticker_input}'. Verifica que sea correcto.")
        else:
            puntuaciones, justificaciones = calcular_puntuaciones_y_justificaciones(datos)
            pesos = {'calidad': 0.4, 'valoracion': 0.3, 'salud': 0.2, 'dividendos': 0.1}
            nota_ponderada = (puntuaciones['calidad'] * pesos['calidad'] +
                              puntuaciones['valoracion'] * pesos['valoracion'] +
                              puntuaciones['salud'] * pesos['salud'] +
                              puntuaciones['dividendos'] * pesos['dividendos'])
            
            nota_final = max(0, nota_ponderada - puntuaciones['penalizador_geo'])

            st.header(f"Informe Profesional: {datos['nombre']} ({ticker_input})")
            
            st.markdown(f"### 🧭 Nota Global del Compás: **{nota_final:.1f} / 10**")
            # ... (Veredictos)

            with st.expander("1. Identidad y Riesgo Geopolítico", expanded=True):
                # ... (Info de Identidad y Riesgo Geo)
                pass
            
            # --- NUEVA SECCIÓN DE CONSENSO Y MOAT ---
            col_moat, col_analistas = st.columns(2)
            with col_moat:
                with st.container(border=True):
                    st.subheader(f"Fortaleza del Moat [Nota: {puntuaciones['moat']}/10]")
                    st.caption(justificaciones['moat'])
            with col_analistas:
                with st.container(border=True):
                    st.subheader("Consenso de Analistas")
                    recomendacion = datos.get('recomendacion_analistas', 'N/A').replace('_', ' ').title()
                    st.metric("Recomendación Media", recomendacion)
                    st.metric("Precio Objetivo Medio", f"{datos.get('precio_objetivo', 'N/A')}")

            # ... (Resto de columnas de métricas)

            st.header("Análisis Gráfico Histórico")
            financials_hist, dividends_hist, prices_hist = obtener_datos_historicos(ticker_input)
            fig = crear_graficos_profesionales(ticker_input, financials_hist, dividends_hist, prices_hist)
            
            if fig:
                st.pyplot(fig)
                st.subheader("Banderas Rojas (Red Flags)")
                banderas = analizar_banderas_rojas(datos, financials_hist)
                if banderas:
                    for bandera in banderas:
                        st.warning(bandera)
                else:
                    st.success("✅ No se han detectado banderas rojas significativas.")
            else:
                st.warning("No se pudieron generar los gráficos históricos por falta de datos.")
            
            # LEYENDA DINÁMICA Y COMPLETA
            with st.expander(f"Leyenda y Benchmarks para el Sector: {datos['sector'].upper()}", expanded=False):
                # ... (código completo de la leyenda)
                pass

