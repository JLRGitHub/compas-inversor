# app.py
# -----------------------------------------------------------------------------
# El Compás del Inversor - v19.0 (con Análisis de Riesgo Geopolítico)
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

# --- BLOQUE 1: OBTENCIÓN DE DATOS (VERSIÓN ROBUSTA) ---
@st.cache_data(ttl=900)
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
        "pais": info.get('country', 'N/A'),
        "industria": info.get('industry', 'N/A'), "descripcion": info.get('longBusinessSummary', 'No disponible.'),
        "roe": roe * 100 if roe is not None else 0, "margen_operativo": op_margin * 100 if op_margin is not None else 0,
        "margen_beneficio": info.get('profitMargins', 0) * 100, "deuda_patrimonio": info.get('debtToEquity'),
        "ratio_corriente": info.get('currentRatio'), "per": info.get('trailingPE'),
        "per_adelantado": info.get('forwardPE'), "precio_ventas": info.get('priceToSalesTrailing12Months'),
        "precio_valor_contable": info.get('priceToBook'), "yield_dividendo": div_yield * 100 if div_yield is not None else 0,
        "payout_ratio": payout * 100 if payout is not None else 0,
    }

# --- BLOQUE 2: LÓGICA DE PUNTUACIÓN CON CONTEXTO SECTORIAL Y GEOPOLÍTICO ---
def calcular_puntuaciones_y_justificaciones(datos):
    """Calcula notas sobre 10 y añade una justificación, ajustando los baremos por sector."""
    puntuaciones = {}
    justificaciones = {}
    sector = datos['sector']
    pais = datos['pais']
    
    # --- BAREMOS POR SECTOR ---
    benchmarks = {
        'Technology': {'roe_excelente': 25, 'roe_bueno': 18, 'margen_excelente': 25, 'margen_bueno': 18, 'per_barato': 25, 'per_justo': 35},
        'Financial Services': {'roe_excelente': 12, 'roe_bueno': 10, 'per_barato': 12, 'per_justo': 18},
        'Default': {'roe_excelente': 15, 'roe_bueno': 12, 'margen_excelente': 15, 'margen_bueno': 10, 'per_barato': 20, 'per_justo': 25}
    }
    sector_bench = benchmarks.get(sector, benchmarks['Default'])

    # --- CLASIFICACIÓN DE RIESGO GEOPOLÍTICO ---
    paises_seguros = ['USA', 'Canada', 'Germany', 'Switzerland', 'Netherlands', 'United Kingdom', 'France', 'Denmark', 'Sweden', 'Norway', 'Finland', 'Australia', 'New Zealand', 'Japan']
    paises_precaucion = ['Spain', 'Italy', 'South Korea', 'Taiwan']
    
    nota_geo = 10
    justificacion_geo = "Opera en una jurisdicción estable y predecible."
    penalizador_geo = 0
    
    if pais in paises_precaucion:
        nota_geo = 6
        justificacion_geo = "PRECAUCIÓN: Opera en una jurisdicción con cierta volatilidad económica o riesgo geopolítico."
        penalizador_geo = 1.5
    elif pais not in paises_seguros:
        nota_geo = 2
        justificacion_geo = "ALTO RIESGO: Opera en una jurisdicción con alta inestabilidad política, regulatoria o económica."
        penalizador_geo = 3.0
        
    puntuaciones['geopolitico'] = nota_geo
    justificaciones['geopolitico'] = justificacion_geo
    puntuaciones['penalizador_geo'] = penalizador_geo

    # 1. Calidad
    nota_calidad = 0
    if datos['roe'] > sector_bench['roe_excelente']: nota_calidad += 5
    elif datos['roe'] > sector_bench['roe_bueno']: nota_calidad += 4
    if datos['margen_operativo'] > sector_bench.get('margen_excelente', 15): nota_calidad += 5
    elif datos['margen_operativo'] > sector_bench.get('margen_bueno', 10): nota_calidad += 4
    puntuaciones['calidad'] = nota_calidad
    if nota_calidad >= 8: justificaciones['calidad'] = "Rentabilidad y márgenes de élite para su sector."
    else: justificaciones['calidad'] = "Negocio de buena calidad con márgenes y rentabilidad sólidos."

    # 2. Salud Financiera
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

    # 3. Valoración
    nota_valoracion = 0
    per = datos['per']
    if isinstance(per, (int, float)):
        if per < sector_bench['per_barato']: nota_valoracion = 10
        elif per < sector_bench['per_justo']: nota_valoracion = 7
        else: nota_valoracion = 4
    puntuaciones['valoracion'] = nota_valoracion
    if nota_valoracion >= 7: justificaciones['valoracion'] = "Valoración atractiva en comparación con su sector."
    elif nota_valoracion >= 4: justificaciones['valoracion'] = "Precio justo por un negocio de esta calidad."
    else: justificaciones['valoracion'] = "Valoración exigente."

    # 4. Dividendos
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
            
            # Aplicamos el penalizador geopolítico
            nota_final = nota_ponderada - puntuaciones['penalizador_geo']
            # Nos aseguramos que la nota no sea negativa
            nota_final = max(0, nota_final)

            st.header(f"Informe Profesional: {datos['nombre']} ({ticker_input})")
            
            st.markdown(f"### 🧭 Nota Global del Compás: **{nota_final:.1f} / 10**")
            if nota_final >= 7.5:
                st.success("Veredicto: Empresa EXCEPCIONAL a un precio potencialmente atractivo.")
            elif nota_final >= 6:
                st.info("Veredicto: Empresa de ALTA CALIDAD a un precio razonable.")
            elif nota_final >= 4:
                st.warning("Veredicto: Empresa SÓLIDA, pero vigilar la valoración o algún aspecto de calidad/riesgo.")
            else:
                st.error("Veredicto: Proceder con CAUTELA. Presenta debilidades o riesgos significativos.")

            # --- NUEVO APARTADO DE RIESGO GEOPOLÍTICO ---
            st.subheader("6. Análisis de Riesgo Geopolítico")
            geo_nota = puntuaciones['geopolitico']
            geo_justificacion = justificaciones['geopolitico']
            
            if geo_nota >= 8:
                st.markdown(f"**País:** {datos['pais']} | **Nivel de Riesgo:** BAJO 🟢")
            elif geo_nota >= 5:
                st.markdown(f"**País:** {datos['pais']} | **Nivel de Riesgo:** PRECAUCIÓN 🟠")
            else:
                st.markdown(f"**País:** {datos['pais']} | **Nivel de Riesgo:** ALTO 🔴")
            st.caption(geo_justificacion)
            
            # --- Resto de apartados ---
            with st.expander("1. Identidad del Negocio", expanded=False):
                st.write(f"**Sector:** {datos['sector']} | **Industria:** {datos['industria']}")
                st.write(f"**Descripción:** {datos['descripcion']}")
            
            col1, col2 = st.columns(2)
            with col1:
                with st.container(border=True):
                    st.subheader(f"2. Calidad del Negocio [Nota: {puntuaciones['calidad']}/10]")
                    st.caption(justificaciones['calidad'])
                    st.metric("📈 ROE (Rentabilidad)", f"{datos['roe']:.2f}%")
                    st.metric("📊 Margen Operativo", f"{datos['margen_operativo']:.2f}%")
            with col2:
                with st.container(border=True):
                    st.subheader(f"3. Salud Financiera [Nota: {puntuaciones['salud']}/10]")
                    st.caption(justificaciones['salud'])
                    st.metric("🏦 Deuda / Patrimonio", f"{datos['deuda_patrimonio']:.2f}" if isinstance(datos['deuda_patrimonio'], (int, float)) else "N/A")
                    st.metric("💧 Ratio Corriente", f"{datos['ratio_corriente']:.2f}" if isinstance(datos['ratio_corriente'], (int, float)) else "N/A")

            col3, col4 = st.columns(2)
            with col3:
                with st.container(border=True):
                    st.subheader(f"4. Valoración [Nota: {puntuaciones['valoracion']}/10]")
                    st.caption(justificaciones['valoracion'])
                    st.metric("⚖️ PER (Precio/Beneficio)", f"{datos['per']:.2f}" if isinstance(datos['per'], (int, float)) else "N/A")
                    st.metric("🏷️ Precio / Ventas", f"{datos['precio_ventas']:.2f}" if isinstance(datos['precio_ventas'], (int, float)) else "N/A")
            with col4:
                with st.container(border=True):
                    st.subheader(f"5. Dividendos [Nota: {puntuaciones['dividendos']}/10]")
                    st.caption(justificaciones['dividendos'])
                    st.metric("💸 Rentabilidad por Dividendo", f"{datos['yield_dividendo']:.2f}%")
                    st.metric("🤲 Ratio de Reparto (Payout)", f"{datos['payout_ratio']:.2f}%")
