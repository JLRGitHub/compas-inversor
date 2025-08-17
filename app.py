# app.py
# -----------------------------------------------------------------------------
# El Compás del Inversor - v30.0 (Versión Web Final y Completa)
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

st.markdown("""
<style>
    .stApp { background-color: #0E1117; color: #FAFAFA; }
    h1, h2, h3 { color: #D4AF37; }
    .st-emotion-cache-1r6slb0 { border: 1px solid #D4AF37 !important; border-radius: 10px; padding: 15px !important; }
    .stButton>button { background-color: #D4AF37; color: #0E1117; border-radius: 8px; border: 1px solid #D4AF37; font-weight: bold; }
    [data-testid="stMetricValue"] { color: #FAFAFA; }
</style>
""", unsafe_allow_html=True)


# --- BLOQUE 1: OBTENCIÓN DE DATOS ---
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
        "deuda_patrimonio": info.get('debtToEquity'), "per": info.get('trailingPE'),
        "yield_dividendo": div_yield * 100 if div_yield is not None else 0,
        "payout_ratio": payout * 100 if payout is not None else 0,
        "precio_actual": precio, "bpa_actual": info.get('trailingEps'),
        "recomendacion_analistas": info.get('recommendationKey', 'N/A'),
        "precio_objetivo": info.get('targetMeanPrice', 'N/A'),
        "ratio_corriente": info.get('currentRatio'),
        "margen_beneficio": info.get('profitMargins', 0) * 100,
        "per_adelantado": info.get('forwardPE'),
        "precio_ventas": info.get('priceToSalesTrailing12Months'),
        "precio_valor_contable": info.get('priceToBook'),
    }

# --- BLOQUE 2: LÓGICA DE PUNTUACIÓN Y ANÁLISIS ---
@st.cache_data(ttl=3600)
def obtener_datos_historicos(ticker):
    try:
        stock = yf.Ticker(ticker)
        financials = stock.financials.T.sort_index(ascending=True).tail(4)
        balance_sheet = stock.balance_sheet.T.sort_index(ascending=True).tail(4)
        cashflow = stock.cashflow.T.sort_index(ascending=True).tail(4)
        dividends = stock.dividends.resample('YE').sum().tail(5)
        hist_precios = stock.history(period="5y")['Close']
        
        if financials.empty: return None, None, None
        
        financials['Operating Margin'] = financials.get('Operating Income', 0) / financials.get('Total Revenue', 1)
        financials['Total Debt'] = balance_sheet.get('Total Debt', 0)
        
        shares_outstanding = stock.info.get('sharesOutstanding')
        if shares_outstanding and shares_outstanding > 0:
            financials['EPS'] = financials['Net Income'] / shares_outstanding
        else:
            financials['EPS'] = np.nan

        financials['ROE'] = financials['Net Income'] / balance_sheet.get('Total Stockholder Equity', 1)
        
        capex = cashflow.get('Capital Expenditure', cashflow.get('Capital Expenditures', 0))
        op_cash = cashflow.get('Total Cash From Operating Activities', 0)
        financials['Free Cash Flow'] = op_cash + capex
        
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

def calcular_puntuaciones_y_justificaciones(datos, margen_seguridad):
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
    
    puntuaciones['moat'] = round((nota_calidad * 0.7) + (nota_salud * 0.3))
    if puntuaciones['moat'] >= 8: justificaciones['moat'] = "Moat Ancho: Negocio dominante y muy defendido."
    elif puntuaciones['moat'] >= 5: justificaciones['moat'] = "Moat Estrecho: Ciertas ventajas competitivas."
    else: justificaciones['moat'] = "Sin Moat Claro: Negocio vulnerable a la competencia."

    nota_valoracion = 0
    if margen_seguridad is not None and margen_seguridad > 25: nota_valoracion = 10
    elif margen_seguridad is not None and margen_seguridad > 10: nota_valoracion = 8
    elif datos['per'] is not None and datos['per'] < sector_bench['per_justo']: nota_valoracion = 5
    else: nota_valoracion = 2
    puntuaciones['valoracion'] = nota_valoracion
    if nota_valoracion >= 8: justificaciones['valoracion'] = "Valoración atractiva con un alto margen de seguridad."
    elif nota_valoracion >= 5: justificaciones['valoracion'] = "Precio justo por un negocio de esta calidad."
    else: justificaciones['valoracion'] = "Valoración exigente, sin margen de seguridad aparente."

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

def calcular_margen_de_seguridad(datos, financials, hist_precios):
    if financials is None or hist_precios is None or 'EPS' not in financials.columns or datos['bpa_actual'] is None:
        return None, None, "Datos insuficientes para el cálculo."

    hist_per = hist_precios.resample('YE').last() / financials['EPS']
    hist_per = hist_per.replace([np.inf, -np.inf], np.nan).dropna()
    
    if hist_per.empty:
        return None, None, "No se pudo calcular el PER histórico medio."
        
    per_medio_hist = hist_per.mean()
    valor_intrinseco = per_medio_hist * datos['bpa_actual']
    margen_seguridad = (1 - (datos['precio_actual'] / valor_intrinseco)) * 100 if valor_intrinseco > 0 else -999

    justificacion = f"Basado en un PER histórico medio de {per_medio_hist:.1f}x y un BPA actual de {datos['bpa_actual']:.2f}."
    
    return valor_intrinseco, margen_seguridad, justificacion

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

        # Gráfico 1
        axs[0, 0].bar(años, financials['Total Revenue'] / 1e9, label='Ingresos', color='#87CEEB')
        axs[0, 0].bar(años, financials['Net Income'] / 1e9, label='Beneficio Neto', color='#D4AF37', width=0.5)
        axs[0, 0].set_title('1. Crecimiento del Negocio (B)')
        axs[0, 0].legend()

        # Gráfico 2
        ax2_twin = axs[0, 1].twinx()
        axs[0, 1].plot(años, financials['ROE'] * 100, label='ROE (%)', color='purple', marker='o')
        ax2_twin.plot(años, financials['Operating Margin'] * 100, label='Margen Op. (%)', color='#D4AF37', marker='s')
        axs[0, 1].set_title('2. Rentabilidad y Eficiencia')
        fig.legend(loc='upper center', bbox_to_anchor=(0.7, 0.9))

        # Gráfico 3
        if hist_precios is not None and not hist_precios.empty and 'EPS' in financials.columns and financials['EPS'].notna().all():
            hist_per = hist_precios.resample('YE').last() / financials['EPS']
            media_per = hist_per.mean()
            axs[1, 0].plot(hist_per.index.year, hist_per, label='PER Histórico', color='cyan', marker='o')
            axs[1, 0].axhline(y=media_per, color='yellow', linestyle='--', label=f'Media 5 Años ({media_per:.1f}x)')
            axs[1, 0].set_title('3. Valoración Histórica (PER)')
            axs[1, 0].legend()
        else:
            axs[1, 0].text(0.5, 0.5, 'Datos de PER histórico no disponibles', ha='center', va='center', color='white')
            axs[1, 0].set_title('3. Valoración Histórica (PER)')

        # Gráfico 4
        if dividends is not None and not dividends.empty:
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
            financials_hist, dividends_hist, prices_hist = obtener_datos_historicos(ticker_input)
            valor_intrinseco, margen_seguridad, justificacion_ms = calcular_margen_de_seguridad(datos, financials_hist, prices_hist)
            puntuaciones, justificaciones = calcular_puntuaciones_y_justificaciones(datos, margen_seguridad)
            
            pesos = {'calidad': 0.4, 'valoracion': 0.3, 'salud': 0.2, 'dividendos': 0.1}
            nota_ponderada = (puntuaciones['calidad'] * pesos['calidad'] +
                              puntuaciones['valoracion'] * pesos['valoracion'] +
                              puntuaciones['salud'] * pesos['salud'] +
                              puntuaciones['dividendos'] * pesos['dividendos'])
            
            nota_final = max(0, nota_ponderada - puntuaciones['penalizador_geo'])

            st.header(f"Informe Profesional: {datos['nombre']} ({ticker_input})")
            
            st.markdown(f"### 🧭 Nota Global del Compás: **{nota_final:.1f} / 10**")
            if nota_final >= 7.5: st.success("Veredicto: Empresa EXCEPCIONAL a un precio potencialmente atractivo.")
            elif nota_final >= 6: st.info("Veredicto: Empresa de ALTA CALIDAD a un precio razonable.")
            elif nota_final >= 4: st.warning("Veredicto: Empresa SÓLIDA, pero vigilar valoración o riesgos.")
            else: st.error("Veredicto: Proceder con CAUTELA. Presenta debilidades o riesgos significativos.")

            with st.expander("1. Identidad y Riesgo Geopolítico", expanded=True):
                st.write(f"**Sector:** {datos['sector']} | **Industria:** {datos['industria']}")
                geo_nota = puntuaciones['geopolitico']
                if geo_nota >= 8: st.markdown(f"**País:** {datos['pais']} | **Nivel de Riesgo:** BAJO 🟢")
                elif geo_nota >= 5: st.markdown(f"**País:** {datos['pais']} | **Nivel de Riesgo:** PRECAUCIÓN 🟠")
                else: st.markdown(f"**País:** {datos['pais']} | **Nivel de Riesgo:** ALTO 🔴")
                st.caption(justificaciones['geopolitico'])
                st.write(f"**Descripción:** {datos['descripcion']}")
            
            col_moat, col_analistas = st.columns(2)
            with col_moat:
                with st.container(border=True):
                    st.subheader(f"Fortaleza del Moat [Nota: {puntuaciones['moat']}/10]", help="Mide la durabilidad de la ventaja competitiva (basado en Calidad y Salud Financiera).")
                    st.caption(justificaciones['moat'])
            with col_analistas:
                with st.container(border=True):
                    st.subheader("Consenso de Analistas", help="Opinión media de los analistas de Wall Street. Tomar como una referencia, no como una verdad absoluta.")
                    recomendacion = datos.get('recomendacion_analistas', 'N/A').replace('_', ' ').title()
                    st.metric("Recomendación Media", recomendacion)
                    st.metric("Precio Objetivo Medio", f"{datos.get('precio_objetivo', 'N/A')}")

            col1, col2 = st.columns(2)
            with col1:
                with st.container(border=True):
                    st.subheader(f"Calidad del Negocio [Nota: {puntuaciones['calidad']}/10]", help="¿Es un negocio rentable y eficiente?")
                    st.caption(justificaciones['calidad'])
                    st.metric("📈 ROE (Rentabilidad)", f"{datos['roe']:.2f}%")
                    st.metric("📊 Margen Operativo", f"{datos['margen_operativo']:.2f}%")
            with col2:
                with st.container(border=True):
                    st.subheader(f"Salud Financiera [Nota: {puntuaciones['salud']}/10]", help="¿Tiene un balance sólido?")
                    st.caption(justificaciones['salud'])
                    st.metric("🏦 Deuda / Patrimonio", f"{datos['deuda_patrimonio']:.2f}" if isinstance(datos['deuda_patrimonio'], (int, float)) else "N/A")
                    st.metric("💧 Ratio Corriente", f"{datos['ratio_corriente']:.2f}" if isinstance(datos['ratio_corriente'], (int, float)) else "N/A")

            col3, col4 = st.columns(2)
            with col3:
                with st.container(border=True):
                    st.subheader(f"Valoración [Nota: {puntuaciones['valoracion']}/10]", help="¿Está la acción a un precio atractivo?")
                    st.caption(justificaciones['valoracion'])
                    st.metric("⚖️ PER (Precio/Beneficio)", f"{datos['per']:.2f}" if isinstance(datos['per'], (int, float)) else "N/A")
                    st.metric("🛡️ Margen de Seguridad", f"{margen_seguridad:.1f}%" if margen_seguridad is not None else "N/A", delta=f"{margen_seguridad:.1f}%" if margen_seguridad is not None else None)
            with col4:
                with st.container(border=True):
                    st.subheader(f"Dividendos [Nota: {puntuaciones['dividendos']}/10]", help="¿Remunera bien al accionista?")
                    st.caption(justificaciones['dividendos'])
                    st.metric("💸 Rentabilidad por Dividendo", f"{datos['yield_dividendo']:.2f}%")
                    st.metric("🤲 Ratio de Reparto (Payout)", f"{datos['payout_ratio']:.2f}%")

            st.header("Análisis Gráfico Histórico")
            fig, financials_hist = obtener_datos_historicos(ticker_input)
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
                benchmarks = {
                    'Technology': {'roe_excelente': 25, 'roe_bueno': 18, 'margen_excelente': 25, 'margen_bueno': 18, 'margen_neto_excelente': 20, 'margen_neto_bueno': 15, 'per_barato': 25, 'per_justo': 35},
                    'Healthcare': {'roe_excelente': 20, 'roe_bueno': 15, 'margen_excelente': 20, 'margen_bueno': 15, 'margen_neto_excelente': 15, 'margen_neto_bueno': 10, 'per_barato': 20, 'per_justo': 30},
                    'Financial Services': {'roe_excelente': 12, 'roe_bueno': 10, 'margen_excelente': 15, 'margen_bueno': 10, 'margen_neto_excelente': 10, 'margen_neto_bueno': 8, 'per_barato': 12, 'per_justo': 18},
                    'Consumer Defensive': {'roe_excelente': 20, 'roe_bueno': 15, 'margen_excelente': 15, 'margen_bueno': 10, 'margen_neto_excelente': 8, 'margen_neto_bueno': 5, 'per_barato': 20, 'per_justo': 25},
                    'Industrials': {'roe_excelente': 18, 'roe_bueno': 14, 'margen_excelente': 15, 'margen_bueno': 10, 'margen_neto_excelente': 8, 'margen_neto_bueno': 6, 'per_barato': 20, 'per_justo': 25},
                    'Utilities': {'roe_excelente': 10, 'roe_bueno': 8, 'margen_excelente': 15, 'margen_bueno': 12, 'margen_neto_excelente': 8, 'margen_neto_bueno': 5, 'per_barato': 18, 'per_justo': 22},
                    'Energy': {'roe_excelente': 15, 'roe_bueno': 10, 'margen_excelente': 10, 'margen_bueno': 7, 'margen_neto_excelente': 8, 'margen_neto_bueno': 5, 'per_barato': 15, 'per_justo': 20},
                    'Basic Materials': {'roe_excelente': 15, 'roe_bueno': 12, 'margen_excelente': 12, 'margen_bueno': 8, 'margen_neto_excelente': 7, 'margen_neto_bueno': 5, 'per_barato': 18, 'per_justo': 25},
                    'Consumer Cyclical': {'roe_excelente': 18, 'roe_bueno': 14, 'margen_excelente': 12, 'margen_bueno': 8, 'margen_neto_excelente': 7, 'margen_neto_bueno': 5, 'per_barato': 20, 'per_justo': 28},
                    'Communication Services': {'roe_excelente': 15, 'roe_bueno': 12, 'margen_excelente': 18, 'margen_bueno': 12, 'margen_neto_excelente': 12, 'margen_neto_bueno': 9, 'per_barato': 22, 'per_justo': 30},
                    'Real Estate': {'roe_excelente': 8, 'roe_bueno': 6, 'margen_excelente': 20, 'margen_bueno': 15, 'margen_neto_excelente': 15, 'margen_neto_bueno': 10, 'per_barato': 25, 'per_justo': 35},
                    'Default': {'roe_excelente': 15, 'roe_bueno': 12, 'margen_excelente': 15, 'margen_bueno': 10, 'margen_neto_excelente': 8, 'margen_neto_bueno': 5, 'per_barato': 20, 'per_justo': 25}
                }
                sector_bench = benchmarks.get(datos['sector'], benchmarks['Default'])
                
                st.markdown("---")
                st.subheader("1. Identidad del Negocio")
                st.write("Esta sección te dice a qué se dedica la empresa. Es el primer filtro: ¿entiendes el negocio?")
                
                st.subheader("2. Calidad del Negocio")
                st.write(f"**📈 ROE:** Mide la rentabilidad del dinero de los accionistas. Para el sector **{datos['sector'].upper()}**, se considera **Excelente > {sector_bench['roe_excelente']}%** y **Bueno > {sector_bench['roe_bueno']}%**.")
                st.write(f"**📊 Margen Operativo:** % de beneficio del negocio principal. Para este sector, se considera **Excelente > {sector_bench['margen_excelente']}%** y **Bueno > {sector_bench['margen_bueno']}%**.")
                st.write(f"**💰 Margen Neto:** % de beneficio final. Para este sector, se considera **Excelente > {sector_bench.get('margen_neto_excelente', 8)}%** y **Bueno > {sector_bench.get('margen_neto_bueno', 5)}%**.")

                st.subheader("3. Salud Financiera")
                st.write("**🏦 Deuda/Patrimonio:** Compara deuda con fondos propios. Un valor **< 100** es generalmente saludable (no aplica a finanzas/utilities).")
                st.write("**💧 Ratio Corriente:** Capacidad de pagar deudas a corto plazo. Un valor **> 1.5** es muy seguro.")
                
                st.subheader("4. Valoración")
                st.write(f"**⚖️ PER:** Veces que pagas los beneficios. Para el sector **{datos['sector'].upper()}**, se considera **Atractivo < {sector_bench['per_barato']}** y **Justo < {sector_bench['per_justo']}**.")
                st.write("**🔮 PER Adelantado:** PER basado en beneficios futuros. Debe ser menor que el PER actual para indicar crecimiento esperado.")
                
                st.subheader("5. Dividendos (Baremo General)")
                st.write("**💸 Yield:** % que recibes en dividendos. **> 3.5%** es atractivo.")
                st.write("**🤲 Payout:** % del beneficio destinado a dividendos. **< 60%** es muy sostenible.")
