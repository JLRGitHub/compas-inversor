# app.py
# -----------------------------------------------------------------------------
# El Compás del Inversor - v18.0 (Versión Web Estable)
# -----------------------------------------------------------------------------
#
# Para ejecutar esta aplicación:
# 1. Guarda este código como 'app.py'.
# 2. Abre una terminal y ejecuta: pip install streamlit yfinance matplotlib numpy
# 3. En la misma terminal, navega a la carpeta donde guardaste el archivo y ejecuta:
#    streamlit run app.py
#
# -----------------------------------------------------------------------------

import streamlit as st
import yfinance as yf
import matplotlib.pyplot as plt
import numpy as np

# --- CONFIGURACIÓN DE LA PÁGINA WEB ---
st.set_page_config(page_title="El Compás del Inversor", page_icon="🧭", layout="wide")

# --- BLOQUE 1: OBTENCIÓN DE DATOS (VERSIÓN ROBUSTA) ---
@st.cache_data(ttl=900) # Cache para no llamar a la API repetidamente
def obtener_datos_completos(ticker):
    """Obtiene un diccionario completo y robusto de datos desde Yahoo Finance."""
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
        "industria": info.get('industry', 'N/A'), "descripcion": info.get('longBusinessSummary', 'No disponible.'),
        "roe": roe * 100 if roe is not None else 0, "margen_operativo": op_margin * 100 if op_margin is not None else 0,
        "margen_beneficio": info.get('profitMargins', 0) * 100, "deuda_patrimonio": info.get('debtToEquity'),
        "ratio_corriente": info.get('currentRatio'), "per": info.get('trailingPE'),
        "per_adelantado": info.get('forwardPE'), "precio_ventas": info.get('priceToSalesTrailing12Months'),
        "precio_valor_contable": info.get('priceToBook'), "yield_dividendo": div_yield * 100 if div_yield is not None else 0,
        "payout_ratio": payout * 100 if payout is not None else 0,
    }

# --- BLOQUE 2: LÓGICA DE PUNTUACIÓN CON CONTEXTO SECTORIAL ---
def calcular_puntuaciones_y_justificaciones(datos):
    """Calcula notas sobre 10 y añade una justificación, ajustando los baremos por sector."""
    puntuaciones = {}
    justificaciones = {}
    sector = datos['sector']
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
    sector_bench = benchmarks.get(sector, benchmarks['Default'])
    nota_calidad = 0
    if datos['roe'] > sector_bench['roe_excelente']: nota_calidad += 4
    elif datos['roe'] > sector_bench['roe_bueno']: nota_calidad += 3
    if datos['margen_operativo'] > sector_bench['margen_excelente']: nota_calidad += 3
    elif datos['margen_operativo'] > sector_bench['margen_bueno']: nota_calidad += 2
    if datos['margen_beneficio'] > sector_bench.get('margen_neto_excelente', 999): nota_calidad += 3
    elif datos['margen_beneficio'] > sector_bench.get('margen_neto_bueno', 999): nota_calidad += 2
    puntuaciones['calidad'] = nota_calidad
    if nota_calidad >= 8: justificaciones['calidad'] = "Rentabilidad y márgenes de élite para su sector."
    else: justificaciones['calidad'] = "Negocio de buena calidad con márgenes y rentabilidad sólidos."
    nota_salud = 0
    deuda_ratio = datos['deuda_patrimonio']
    if sector in ['Financial Services', 'Real Estate', 'Utilities']:
        nota_salud = 8
        justificaciones['salud'] = "Sector intensivo en capital. La deuda es parte del negocio."
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
    nota_valoracion = 0
    per = datos['per']
    if isinstance(per, (int, float)):
        if per < sector_bench['per_barato']: nota_valoracion = 10
        elif per < sector_bench['per_justo']: nota_valoracion = 7
        else: nota_valoracion = 4
    puntuaciones['valoracion'] = nota_valoracion
    if nota_valoracion >= 7: justificaciones['valoracion'] = "Valoración atractiva en comparación con su sector."
    elif nota_valoracion >= 4: justificaciones['valoracion'] = "Precio justo por un negocio de esta calidad."
    else: justificaciones['valoracion'] = "Valoración exigente. El mercado espera un alto crecimiento."
    nota_dividendos = 0
    if datos['yield_dividendo'] > 3.5: nota_dividendos += 5
    elif datos['yield_dividendo'] > 2: nota_dividendos += 3
    if 0 < datos['payout_ratio'] < 60: nota_dividendos += 5
    elif 0 < datos['payout_ratio'] < 80: nota_dividendos += 3
    puntuaciones['dividendos'] = nota_dividendos
    if nota_dividendos >= 8: justificaciones['dividendos'] = "Dividendo excelente, alto y muy seguro."
    elif nota_dividendos >= 5: justificaciones['dividendos'] = "Dividendo sólido y sostenible."
    else: justificaciones['dividendos'] = "El dividendo es bajo o no es una prioridad para la empresa."
    return puntuaciones, justificaciones

# --- ESTRUCTURA DE LA APLICACIÓN WEB ---
st.title('El Compás del Inversor 🧭')
st.caption("Tu copiloto para la inversión a largo plazo. Creado con un inversor exigente.")

ticker_input = st.text_input("Introduce el Ticker de la Acción a Analizar (ej. JNJ, MSFT, AMUN.PA)", "AAPL").upper()

if st.button('Analizar Acción'):
    with st.spinner('Realizando análisis profesional... Esto puede tardar unos segundos.'):
        datos = obtener_datos_completos(ticker_input)
        
        if not datos:
            st.error(f"Error: No se pudo encontrar el ticker '{ticker_input}'. Verifica que sea correcto.")
        else:
            puntuaciones, justificaciones = calcular_puntuaciones_y_justificaciones(datos)
            pesos = {'calidad': 0.4, 'valoracion': 0.3, 'salud': 0.2, 'dividendos': 0.1}
            nota_global = (puntuaciones['calidad'] * pesos['calidad'] +
                           puntuaciones['valoracion'] * pesos['valoracion'] +
                           puntuaciones['salud'] * pesos['salud'] +
                           puntuaciones['dividendos'] * pesos['dividendos'])

            st.header(f"Informe Profesional: {datos['nombre']} ({ticker_input})")
            
            st.markdown(f"### 🧭 Nota Global del Compás: **{nota_global:.1f} / 10**")
            if nota_global >= 8:
                st.success("Veredicto: Empresa EXCEPCIONAL a un precio potencialmente atractivo.")
            elif nota_global >= 6:
                st.info("Veredicto: Empresa de ALTA CALIDAD a un precio razonable.")
            elif nota_global >= 4:
                st.warning("Veredicto: Empresa SÓLIDA, pero vigilar la valoración o algún aspecto de calidad.")
            else:
                st.error("Veredicto: Proceder con CAUTELA. Presenta debilidades significativas.")

            with st.expander("1. Identidad del Negocio", expanded=True):
                st.write(f"**Sector:** {datos['sector']} | **Industria:** {datos['industria']}")
                st.write(f"**Descripción:** {datos['descripcion']}")
            
            # --- Creación de columnas para las métricas ---
            col1, col2 = st.columns(2)
            with col1:
                with st.container(border=True):
                    st.subheader(f"Calidad del Negocio [Nota: {puntuaciones['calidad']}/10]")
                    st.caption(justificaciones['calidad'])
                    st.metric("📈 ROE (Rentabilidad)", f"{datos['roe']:.2f}%")
                    st.metric("📊 Margen Operativo", f"{datos['margen_operativo']:.2f}%")
            with col2:
                with st.container(border=True):
                    st.subheader(f"Salud Financiera [Nota: {puntuaciones['salud']}/10]")
                    st.caption(justificaciones['salud'])
                    st.metric("🏦 Deuda / Patrimonio", f"{datos['deuda_patrimonio']:.2f}" if isinstance(datos['deuda_patrimonio'], (int, float)) else "N/A")
                    st.metric("💧 Ratio Corriente", f"{datos['ratio_corriente']:.2f}" if isinstance(datos['ratio_corriente'], (int, float)) else "N/A")

            col3, col4 = st.columns(2)
            with col3:
                with st.container(border=True):
                    st.subheader(f"Valoración [Nota: {puntuaciones['valoracion']}/10]")
                    st.caption(justificaciones['valoracion'])
                    st.metric("⚖️ PER (Precio/Beneficio)", f"{datos['per']:.2f}" if isinstance(datos['per'], (int, float)) else "N/A")
                    st.metric("🏷️ Precio / Ventas", f"{datos['precio_ventas']:.2f}" if isinstance(datos['precio_ventas'], (int, float)) else "N/A")
            with col4:
                with st.container(border=True):
                    st.subheader(f"Dividendos [Nota: {puntuaciones['dividendos']}/10]")
                    st.caption(justificaciones['dividendos'])
                    st.metric("💸 Rentabilidad por Dividendo", f"{datos['yield_dividendo']:.2f}%")
                    st.metric("🤲 Ratio de Reparto (Payout)", f"{datos['payout_ratio']:.2f}%")

            st.info("Análisis Gráfico Histórico en desarrollo. Próximamente disponible.")

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
                st.write(f"**💰 Margen Neto:** % de beneficio final. Para este sector, se considera **Excelente > {sector_bench['margen_neto_excelente']}%** y **Bueno > {sector_bench['margen_neto_bueno']}%**.")

                st.subheader("3. Salud Financiera")
                st.write("**🏦 Deuda/Patrimonio:** Compara deuda con fondos propios. Un valor **< 100** es generalmente saludable (no aplica a finanzas/utilities).")
                st.write("**💧 Ratio Corriente:** Capacidad de pagar deudas a corto plazo. Un valor **> 1.5** es muy seguro.")
                
                st.subheader("4. Valoración")
                st.write(f"**⚖️ PER:** Veces que pagas los beneficios. Para el sector **{datos['sector'].upper()}**, se considera **Atractivo < {sector_bench['per_barato']}** y **Justo < {sector_bench['per_justo']}**.")
                st.write("**🔮 PER Adelantado:** PER basado en beneficios futuros. Debe ser menor que el PER actual para indicar crecimiento esperado.")
                
                st.subheader("5. Dividendos (Baremo General)")
                st.write("**💸 Yield:** % que recibes en dividendos. **> 3.5%** es atractivo.")
                st.write("**🤲 Payout:** % del beneficio destinado a dividendos. **< 60%** es muy sostenible.")
