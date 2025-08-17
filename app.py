# app.py
# -----------------------------------------------------------------------------
# El Compás del Inversor - v37.0 (Versión Completa y Unificada)
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
from datetime import datetime

# --- CONFIGURACIÓN DE LA PÁGINA WEB Y ESTILOS ---
st.set_page_config(page_title="El Compás del Inversor", page_icon="🧭", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #0E1117; color: #FAFAFA; }
    h1, h2, h3 { color: #D4AF37; }
    .st-emotion-cache-1r6slb0 { border: 1px solid #D4AF37 !important; border-radius: 10px; padding: 15px !important; }
    .stButton>button { background-color: #D4AF37; color: #0E1117; border-radius: 8px; border: 1px solid #D4AF37; font-weight: bold; }
    
    /* Estilos para métricas con colores dinámicos */
    .metric-container { margin-bottom: 10px; }
    .metric-label { font-size: 1rem; color: #adb5bd; }
    .metric-value { font-size: 1.75rem; font-weight: bold; line-height: 1.2; }
    .color-green { color: #28a745; }
    .color-red { color: #dc3545; }
    .color-white { color: #FAFAFA; }
</style>
""", unsafe_allow_html=True)


# --- BLOQUE 1: OBTENCIÓN DE DATOS ---
@st.cache_data(ttl=900)
def obtener_datos_completos(ticker):
    """
    Obtiene un diccionario completo de datos financieros y de negocio para un ticker dado.
    """
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
        "pais": info.get('country', 'N/A'), "industria": info.get('industry', 'N/A'),
        "descripcion": info.get('longBusinessSummary', 'No disponible.'),
        "roe": roe * 100 if roe is not None else 0, 
        "margen_operativo": op_margin * 100 if op_margin is not None else 0,
        "margen_beneficio": info.get('profitMargins', 0) * 100, 
        "deuda_patrimonio": info.get('debtToEquity'), "ratio_corriente": info.get('currentRatio'), 
        "per": info.get('trailingPE'), "per_adelantado": info.get('forwardPE'), 
        "precio_ventas": info.get('priceToSalesTrailing12Months'),
        "yield_dividendo": div_yield * 100 if div_yield is not None else 0,
        "payout_ratio": payout * 100 if payout is not None else 0,
        "recomendacion_analistas": info.get('recommendationKey', 'N/A'),
        "precio_objetivo": info.get('targetMeanPrice'), "precio_actual": info.get('currentPrice'),
        "trailing_eps": info.get('trailingEps')
    }

@st.cache_data(ttl=3600)
def obtener_datos_historicos(ticker):
    """
    Obtiene datos financieros históricos para generar gráficos y calcular el PER medio.
    """
    try:
        stock = yf.Ticker(ticker)
        # Datos para gráficos
        financials_charts = stock.financials.T.sort_index(ascending=True).tail(4)
        balance_sheet_charts = stock.balance_sheet.T.sort_index(ascending=True).tail(4)
        cashflow_charts = stock.cashflow.T.sort_index(ascending=True).tail(4)
        dividends_charts = stock.dividends.resample('YE').sum().tail(5)
        
        if not financials_charts.empty:
            financials_charts['Operating Margin'] = financials_charts.get('Operating Income', 0) / financials_charts.get('Total Revenue', 1)
            financials_charts['Total Debt'] = balance_sheet_charts.get('Total Debt', 0)
            financials_charts['ROE'] = financials_charts['Net Income'] / balance_sheet_charts.get('Total Stockholder Equity', 1)
            capex = cashflow_charts.get('Capital Expenditure', cashflow_charts.get('Capital Expenditures', 0))
            op_cash = cashflow_charts.get('Total Cash From Operating Activities', 0)
            financials_charts['Free Cash Flow'] = op_cash + capex
        else:
            financials_charts, dividends_charts = None, None

        # Datos para PER histórico
        end_date = datetime.now()
        start_date = end_date - pd.DateOffset(years=5)
        hist_prices = stock.history(start=start_date, end=end_date, interval='1y')['Close']
        financials_per = stock.financials
        balance_sheet_per = stock.balance_sheet
        
        per_historico = None
        if not financials_per.empty and 'Net Income' in financials_per.columns:
            pers = []
            for date, price in hist_prices.items():
                year = date.year
                if any(col.year == year for col in financials_per.columns):
                    financial_col = [col for col in financials_per.columns if col.year == year][0]
                    balance_sheet_col = [col for col in balance_sheet_per.columns if col.year == year][0]

                    net_income = financials_per[financial_col].get('Net Income')
                    shares_outstanding = balance_sheet_per[balance_sheet_col].get('Share Issued', stock.info.get('sharesOutstanding'))

                    if net_income and shares_outstanding and shares_outstanding > 0:
                        eps = net_income / shares_outstanding
                        if eps > 0 and price > 0:
                            per = price / eps
                            if 0 < per < 100: pers.append(per)
            per_historico = np.mean(pers) if pers else None
        
        return financials_charts, dividends_charts, per_historico
    except Exception:
        return None, None, None

# --- BLOQUE 2: LÓGICA DE PUNTUACIÓN Y ANÁLISIS ---
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

def calcular_puntuaciones_y_justificaciones(datos, per_historico):
    puntuaciones, justificaciones = {}, {}
    sector, pais = datos['sector'], datos['pais']
    
    benchmarks = {
        'Technology': {'roe_excelente': 25, 'roe_bueno': 18, 'margen_excelente': 25, 'margen_bueno': 18, 'margen_neto_excelente': 20, 'margen_neto_bueno': 15},
        'Healthcare': {'roe_excelente': 20, 'roe_bueno': 15, 'margen_excelente': 20, 'margen_bueno': 15, 'margen_neto_excelente': 15, 'margen_neto_bueno': 10},
        'Financial Services': {'roe_excelente': 12, 'roe_bueno': 10, 'margen_excelente': 15, 'margen_bueno': 10, 'margen_neto_excelente': 10, 'margen_neto_bueno': 8},
        'Default': {'roe_excelente': 15, 'roe_bueno': 12, 'margen_excelente': 15, 'margen_bueno': 10, 'margen_neto_excelente': 8, 'margen_neto_bueno': 5}
    }
    sector_bench = benchmarks.get(sector, benchmarks['Default'])
    
    # Geopolítica
    paises_seguros = ['United States', 'Canada', 'Germany', 'Switzerland', 'Netherlands', 'United Kingdom', 'France', 'Denmark', 'Sweden', 'Norway', 'Finland', 'Australia', 'New Zealand', 'Japan', 'Ireland']
    if pais in paises_seguros: puntuaciones['geopolitico'] = 10
    elif pais in ['Spain', 'Italy', 'South Korea', 'Taiwan', 'India']: puntuaciones['geopolitico'] = 6
    else: puntuaciones['geopolitico'] = 3

    # Calidad
    nota_calidad = 0
    if datos['roe'] > sector_bench['roe_excelente']: nota_calidad += 4
    elif datos['roe'] > sector_bench['roe_bueno']: nota_calidad += 3
    if datos['margen_operativo'] > sector_bench['margen_excelente']: nota_calidad += 3
    elif datos['margen_operativo'] > sector_bench['margen_bueno']: nota_calidad += 2
    if datos['margen_beneficio'] > sector_bench.get('margen_neto_excelente', 8): nota_calidad += 3
    elif datos['margen_beneficio'] > sector_bench.get('margen_neto_bueno', 5): nota_calidad += 2
    puntuaciones['calidad'] = min(10, nota_calidad)
    if puntuaciones['calidad'] >= 8: justificaciones['calidad'] = "Rentabilidad y márgenes de élite para su sector."
    else: justificaciones['calidad'] = "Negocio de buena calidad con márgenes sólidos."

    # Salud Financiera
    deuda_ratio = datos['deuda_patrimonio']
    if sector in ['Financial Services', 'Real Estate', 'Utilities']: puntuaciones['salud'], justificaciones['salud'] = 8, "Sector intensivo en capital."
    elif isinstance(deuda_ratio, (int, float)):
        if deuda_ratio < 40: puntuaciones['salud'] = 10
        elif deuda_ratio < 80: puntuaciones['salud'] = 8
        else: puntuaciones['salud'] = 5
        if puntuaciones['salud'] >= 8: justificaciones['salud'] = "Balance muy sólido y conservador."
        else: justificaciones['salud'] = "Nivel de deuda manejable."
    else: puntuaciones['salud'], justificaciones['salud'] = 5, "Datos de deuda no disponibles."

    # Moat
    puntuaciones['moat'] = round((puntuaciones['calidad'] * 0.7) + (puntuaciones['salud'] * 0.3))
    if puntuaciones['moat'] >= 8: justificaciones['moat'] = "Moat Ancho: Negocio dominante y muy defendido."
    else: justificaciones['moat'] = "Moat Estrecho: Ciertas ventajas competitivas."

    # Valoración
    nota_analistas, margen_seguridad = 0, 0
    if datos['precio_actual'] and datos['precio_objetivo']:
        margen_seguridad = ((datos['precio_objetivo'] - datos['precio_actual']) / datos['precio_actual']) * 100
        if margen_seguridad > 25: nota_analistas = 10
        elif margen_seguridad > 15: nota_analistas = 8
        else: nota_analistas = 5
    puntuaciones['margen_seguridad'] = margen_seguridad

    nota_historica, potencial_per = 0, 0
    if per_historico and datos['per'] and datos['per'] > 0:
        potencial_per = ((per_historico - datos['per']) / datos['per']) * 100
        if potencial_per > 30: nota_historica = 10
        elif potencial_per > 15: nota_historica = 8
        else: nota_historica = 5
    puntuaciones['potencial_per'] = potencial_per
    
    puntuaciones['valoracion'] = (nota_analistas * 0.5) + (nota_historica * 0.5)
    if puntuaciones['valoracion'] >= 8: justificaciones['valoracion'] = "Doble señal de compra: infravalorada tanto por analistas como por su histórico."
    else: justificaciones['valoracion'] = "Valoración razonable o exigente."

    # Dividendos
    nota_dividendos = 0
    if datos['yield_dividendo'] > 3.5: nota_dividendos += 5
    elif datos['yield_dividendo'] > 2: nota_dividendos += 3
    if 0 < datos['payout_ratio'] < 60: nota_dividendos += 5
    elif 0 < datos['payout_ratio'] < 80: nota_dividendos += 3
    puntuaciones['dividendos'] = nota_dividendos
    if nota_dividendos >= 8: justificaciones['dividendos'] = "Dividendo excelente, alto y muy seguro."
    else: justificaciones['dividendos'] = "Dividendo sólido y sostenible."
    
    return puntuaciones, justificaciones, benchmarks

# --- BLOQUE 3: GRÁFICOS Y PRESENTACIÓN ---
def mostrar_metrica_con_color(label, value, umbral_bueno, umbral_malo=None, lower_is_better=False, is_percent=False):
    if umbral_malo is None: umbral_malo = umbral_bueno * 0.8
    color_class = "color-white"
    try:
        numeric_value = float(str(value).replace('%', '').replace('N/A', '0'))
        if lower_is_better:
            if numeric_value < umbral_bueno: color_class = "color-green"
            elif numeric_value > umbral_malo: color_class = "color-red"
        else:
            if numeric_value > umbral_bueno: color_class = "color-green"
            elif numeric_value < umbral_malo: color_class = "color-red"
    except (ValueError, TypeError): pass
    
    formatted_value = f"{value:.2f}%" if is_percent and isinstance(value, (int, float)) else (f"{value:.2f}" if isinstance(value, (int, float)) else "N/A")
    
    st.markdown(f'<div class="metric-container"><div class="metric-label">{label}</div><div class="metric-value {color_class}">{formatted_value}</div></div>', unsafe_allow_html=True)

def crear_graficos_profesionales(financials, dividends):
    try:
        if financials is None or financials.empty: return None
        años = [d.year for d in financials.index]
        fig, axs = plt.subplots(2, 2, figsize=(15, 10))
        plt.style.use('dark_background')
        fig.patch.set_facecolor('#0E1117')
        
        for ax in axs.flat:
            ax.tick_params(colors='white')
            for spine in ax.spines.values(): spine.set_color('white')
            ax.yaxis.label.set_color('white'); ax.xaxis.label.set_color('white'); ax.title.set_color('white')

        axs[0, 0].bar(años, financials['Total Revenue'] / 1e9, label='Ingresos', color='#87CEEB')
        axs[0, 0].bar(años, financials['Net Income'] / 1e9, label='Beneficio Neto', color='#D4AF37', width=0.5)
        axs[0, 0].set_title('1. Crecimiento del Negocio (en Billones)'); axs[0, 0].legend()

        ax2_twin = axs[0, 1].twinx()
        axs[0, 1].plot(años, financials['ROE'] * 100, label='ROE (%)', color='purple', marker='o')
        ax2_twin.plot(años, financials['Operating Margin'] * 100, label='Margen Op. (%)', color='#D4AF37', marker='s')
        axs[0, 1].set_title('2. Rentabilidad y Eficiencia'); fig.legend(loc='upper center', bbox_to_anchor=(0.7, 0.9))

        axs[1, 0].bar(años, financials['Net Income'] / 1e9, label='Beneficio Neto (B)', color='royalblue')
        axs[1, 0].plot(años, financials['Free Cash Flow'] / 1e9, label='Flujo de Caja Libre (B)', color='green', marker='o', linestyle='--')
        axs[1, 0].set_title('3. Beneficio vs. Caja Real (en Billones)'); axs[1, 0].legend()

        if dividends is not None and not dividends.empty:
            axs[1, 1].bar(dividends.index.year, dividends, label='Dividendo por Acción', color='orange')
        axs[1, 1].set_title('4. Retorno al Accionista')
        
        plt.tight_layout(rect=[0, 0.03, 1, 0.95])
        return fig
    except Exception:
        return None

# --- ESTRUCTURA DE LA APLICACIÓN WEB ---
st.title('El Compás del Inversor 🧭')
st.caption("Tu copiloto para la inversión a largo plazo, con doble valoración y análisis visual.")

ticker_input = st.text_input("Introduce el Ticker de la Acción a Analizar (ej. JNJ, MSFT, BABA)", "AAPL").upper()

if st.button('Analizar Acción'):
    with st.spinner('Realizando análisis profesional completo...'):
        datos = obtener_datos_completos(ticker_input)
        
        if not datos:
            st.error(f"Error: No se pudo encontrar el ticker '{ticker_input}'. Verifica que sea correcto.")
        else:
            financials_hist, dividends_hist, per_historico = obtener_datos_historicos(ticker_input)
            puntuaciones, justificaciones, benchmarks = calcular_puntuaciones_y_justificaciones(datos, per_historico)
            sector_bench = benchmarks.get(datos['sector'], benchmarks['Default'])

            pesos = {'calidad': 0.4, 'valoracion': 0.35, 'salud': 0.25}
            nota_final = (puntuaciones['calidad'] * pesos['calidad'] + puntuaciones['valoracion'] * pesos['valoracion'] + puntuaciones['salud'] * pesos['salud'])
            
            st.header(f"Informe Profesional: {datos['nombre']} ({ticker_input})")
            
            st.markdown(f"### 🧭 Nota Global del Compás: **{nota_final:.1f} / 10**")
            if nota_final >= 7.5: st.success("Veredicto: Empresa EXCEPCIONAL a un precio potencialmente atractivo.")
            elif nota_final >= 6: st.info("Veredicto: Empresa de ALTA CALIDAD a un precio razonable.")
            elif nota_final >= 4: st.warning("Veredicto: Empresa SÓLIDA, pero vigilar valoración o riesgos.")
            else: st.error("Veredicto: Proceder con CAUTELA. Presenta debilidades o riesgos significativos.")

            with st.expander("1. Identidad, Moat y Riesgo Geopolítico", expanded=True):
                st.write(f"**Sector:** {datos['sector']} | **Industria:** {datos['industria']}")
                geo_nota = puntuaciones['geopolitico']
                if geo_nota >= 8: st.markdown(f"**País:** {datos['pais']} | **Nivel de Riesgo:** BAJO 🟢")
                elif geo_nota >= 5: st.markdown(f"**País:** {datos['pais']} | **Nivel de Riesgo:** PRECAUCIÓN 🟠")
                else: st.markdown(f"**País:** {datos['pais']} | **Nivel de Riesgo:** ALTO 🔴")
                st.markdown(f"**Fortaleza del Moat [{puntuaciones['moat']}/10]:** *{justificaciones['moat']}*")
                st.write(f"**Descripción:** {datos['descripcion']}")

            col1, col2 = st.columns(2)
            with col1:
                with st.container(border=True):
                    st.subheader(f"Calidad del Negocio [{puntuaciones['calidad']}/10]")
                    st.caption(justificaciones['calidad'])
                    mostrar_metrica_con_color("📈 ROE", datos['roe'], sector_bench['roe_excelente'], sector_bench['roe_bueno'], is_percent=True)
                    mostrar_metrica_con_color("📊 Margen Operativo", datos['margen_operativo'], sector_bench['margen_excelente'], sector_bench['margen_bueno'], is_percent=True)
                    mostrar_metrica_con_color("💰 Margen Neto", datos['margen_beneficio'], sector_bench['margen_neto_excelente'], sector_bench['margen_neto_bueno'], is_percent=True)
            with col2:
                with st.container(border=True):
                    st.subheader(f"Salud Financiera [{puntuaciones['salud']}/10]")
                    st.caption(justificaciones['salud'])
                    mostrar_metrica_con_color("🏦 Deuda / Patrimonio", datos['deuda_patrimonio'], 40, 80, lower_is_better=True)
                    mostrar_metrica_con_color("💧 Ratio Corriente", datos['ratio_corriente'], 1.5, 1.0)

            st.subheader(f"Análisis de Valoración [{puntuaciones['valoracion']:.1f}/10]")
            st.caption(justificaciones['valoracion'])
            val1, val2 = st.columns(2)
            with val1:
                with st.container(border=True):
                    st.subheader("Futuro (Analistas)")
                    mostrar_metrica_con_color("🛡️ Margen de Seguridad", puntuaciones['margen_seguridad'], 25, 15, is_percent=True)
                    st.metric("Precio Objetivo Medio", f"{datos.get('precio_objetivo', 'N/A')}")
            with val2:
                with st.container(border=True):
                    st.subheader("Pasado (Histórico)")
                    mostrar_metrica_con_color("📈 Potencial vs PER Medio", puntuaciones['potencial_per'], 30, 15, is_percent=True)
                    st.metric("PER Medio (5A)", f"{per_historico:.2f}" if per_historico else "N/A")
            
            if datos['yield_dividendo'] > 0:
                with st.container(border=True):
                    st.subheader(f"Dividendos [{puntuaciones['dividendos']}/10]")
                    st.caption(justificaciones['dividendos'])
                    div1, div2 = st.columns(2)
                    with div1: mostrar_metrica_con_color("💸 Rentabilidad (Yield)", datos['yield_dividendo'], 3.5, 2.0, is_percent=True)
                    with div2: mostrar_metrica_con_color("🤲 Ratio de Reparto (Payout)", datos['payout_ratio'], 60, 80, lower_is_better=True, is_percent=True)

            st.header("Análisis Gráfico y Banderas Rojas")
            fig = crear_graficos_profesionales(financials_hist, dividends_hist)
            if fig:
                st.pyplot(fig)
                banderas = analizar_banderas_rojas(datos, financials_hist)
                if banderas:
                    for bandera in banderas: st.warning(bandera)
                else:
                    st.success("✅ No se han detectado banderas rojas significativas.")
            else:
                st.warning("No se pudieron generar los gráficos históricos por falta de datos.")
