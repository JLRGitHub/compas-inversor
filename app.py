# app.py
# -----------------------------------------------------------------------------
# El Compás del Inversor - v24.0 (Versión Web Final y Corregida)
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
import pandas as pd # <-- LIBRERÍA QUE FALTABA

# --- CONFIGURACIÓN DE LA PÁGINA WEB Y ESTILOS ---
st.set_page_config(page_title="El Compás del Inversor", page_icon="🧭", layout="wide")

# Estilos CSS para un look profesional (negro y dorado)
st.markdown("""
<style>
    /* Fondo principal */
    .stApp {
        background-color: #0E1117;
        color: #FAFAFA;
    }
    /* Títulos y cabeceras */
    h1, h2, h3 {
        color: #D4AF37; /* Color dorado */
    }
    /* Contenedores de métricas */
    .st-emotion-cache-1r6slb0 {
        border: 1px solid #D4AF37 !important;
        border-radius: 10px;
        padding: 15px !important;
    }
    /* Botón */
    .stButton>button {
        background-color: #D4AF37;
        color: #0E1117;
        border-radius: 8px;
        border: 1px solid #D4AF37;
        font-weight: bold;
    }
    /* Veredictos */
    .stAlert {
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)


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

# --- BLOQUE 2: LÓGICA DE PUNTUACIÓN Y ANÁLISIS ---
@st.cache_data(ttl=3600)
def obtener_datos_historicos(ticker):
    """Obtiene los datos históricos necesarios para los gráficos y las banderas rojas."""
    try:
        stock = yf.Ticker(ticker)
        financials = stock.financials.T.sort_index(ascending=True).tail(4)
        balance_sheet = stock.balance_sheet.T.sort_index(ascending=True).tail(4)
        dividends = stock.dividends.resample('YE').sum().tail(5)
        
        if financials.empty: return None, None
        
        financials['Operating Margin'] = financials.get('Operating Income', 0) / financials.get('Total Revenue', 1)
        financials['Total Debt'] = balance_sheet.get('Total Debt', 0)

        return financials, dividends
    except Exception:
        return None, None

def analizar_banderas_rojas(datos, financials):
    """Analiza los datos en busca de señales de alarma."""
    banderas = []
    # 1. Payout Peligroso
    if datos['payout_ratio'] > 100:
        banderas.append("🔴 **Payout Peligroso:** El ratio de reparto de dividendos es superior al 100%. El dividendo podría no ser sostenible.")
    
    if financials is not None and not financials.empty:
        # 2. Márgenes Decrecientes
        if 'Operating Margin' in financials.columns and len(financials) >= 3:
            # Comprobamos que los datos no sean nulos antes de comparar
            if pd.notna(financials['Operating Margin'].iloc[-1]) and pd.notna(financials['Operating Margin'].iloc[-2]) and pd.notna(financials['Operating Margin'].iloc[-3]):
                if financials['Operating Margin'].iloc[-1] < financials['Operating Margin'].iloc[-2] and financials['Operating Margin'].iloc[-2] < financials['Operating Margin'].iloc[-3]:
                    banderas.append("🔴 **Márgenes Decrecientes:** Los márgenes de beneficio llevan 3 años seguidos bajando, señal de posible pérdida de ventaja competitiva.")
        
        # 3. Deuda Creciente
        if 'Total Debt' in financials.columns and len(financials) >= 3:
            # Comprobamos que la deuda no sea cero para evitar divisiones por cero y que los datos no sean nulos
            if pd.notna(financials['Total Debt'].iloc[-3]) and financials['Total Debt'].iloc[-3] > 0 and pd.notna(financials['Total Debt'].iloc[-1]):
                if financials['Total Debt'].iloc[-1] > financials['Total Debt'].iloc[-3] * 1.5:
                    banderas.append("🔴 **Deuda Creciente:** La deuda total ha aumentado significativamente en los últimos años.")

    return banderas

def calcular_puntuaciones_y_justificaciones(datos):
    """Calcula notas sobre 10 y añade una justificación, ajustando los baremos por sector."""
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
        nota_geo, justificacion_geo, penalizador_geo = 6, "PRECAUCIÓN: Jurisdicción con cierta volatilidad económica o riesgo geopolítico.", 1.5
    elif pais in paises_alto_riesgo:
        nota_geo, justificacion_geo, penalizador_geo = 2, "ALTO RIESGO: Jurisdicción con alta inestabilidad política, regulatoria o económica.", 3.0
    elif pais not in paises_seguros:
        nota_geo, justificacion_geo, penalizador_geo = 5, "PRECAUCIÓN: Jurisdicción no clasificada. Se aplica un criterio de prudencia.", 2.0
    puntuaciones['geopolitico'], justificaciones['geopolitico'], puntuaciones['penalizador_geo'] = nota_geo, justificacion_geo, penalizador_geo

    nota_calidad = 0
    if datos['roe'] > sector_bench.get('roe_excelente', 15): nota_calidad += 5
    elif datos['roe'] > sector_bench.get('roe_bueno', 12): nota_calidad += 4
    if datos['margen_operativo'] > sector_bench.get('margen_excelente', 15): nota_calidad += 5
    elif datos['margen_operativo'] > sector_bench.get('margen_bueno', 10): nota_calidad += 4
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
def crear_graficos_profesionales(ticker):
    """Crea y devuelve una figura con 4 gráficos financieros clave."""
    try:
        stock = yf.Ticker(ticker)
        financials = stock.financials.T.sort_index(ascending=True).tail(4)
        balance_sheet = stock.balance_sheet.T.sort_index(ascending=True).tail(4)
        cashflow = stock.cashflow.T.sort_index(ascending=True).tail(4)
        dividends = stock.dividends.resample('YE').sum().tail(5)
        
        if financials.empty: return None, None

        financials['Operating Margin'] = financials.get('Operating Income', 0) / financials.get('Total Revenue', 1)
        financials['ROE'] = financials['Net Income'] / balance_sheet.get('Total Stockholder Equity', 1)
        capex = cashflow.get('Capital Expenditure', cashflow.get('Capital Expenditures', 0))
        op_cash = cashflow.get('Total Cash From Operating Activities', 0)
        financials['Free Cash Flow'] = op_cash + capex
        financials['Total Debt'] = balance_sheet.get('Total Debt', 0)

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
        axs[0, 0].grid(axis='y', linestyle='--', alpha=0.2)

        # Gráfico 2
        ax2_twin = axs[0, 1].twinx()
        axs[0, 1].plot(años, financials['ROE'] * 100, label='ROE (%)', color='purple', marker='o')
        ax2_twin.plot(años, financials['Operating Margin'] * 100, label='Margen Op. (%)', color='#D4AF37', marker='s')
        axs[0, 1].set_ylabel('ROE (%)', color='purple')
        axs[0, 1].tick_params(axis='y', colors='purple')
        ax2_twin.set_ylabel('Margen Op. (%)', color='#D4AF37')
        ax2_twin.tick_params(axis='y', colors='#D4AF37')
        axs[0, 1].set_title('2. Rentabilidad y Eficiencia')
        axs[0, 1].grid(axis='y', linestyle='--', alpha=0.2)
        
        # Gráfico 3
        axs[1, 0].bar(años, financials['Net Income'] / 1e9, label='Beneficio Neto (B)', color='royalblue')
        axs[1, 0].plot(años, financials['Free Cash Flow'] / 1e9, label='Flujo de Caja Libre (B)', color='green', marker='o', linestyle='--')
        axs[1, 0].set_title('3. Beneficio vs. Caja Real (B)')
        axs[1, 0].legend()
        axs[1, 0].grid(axis='y', linestyle='--', alpha=0.7)

        # Gráfico 4
        axs[1, 1].bar(dividends.index.year, dividends, label='Dividendo por Acción', color='orange')
        axs[1, 1].set_title('4. Retorno al Accionista (Dividendo/Acción)')
        axs[1, 1].set_ylabel('Dividendo Anual')
        axs[1, 1].grid(axis='y', linestyle='--', alpha=0.7)
        
        plt.tight_layout(rect=[0, 0.03, 1, 0.95])
        return fig, financials
    except Exception:
        return None, None

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

            st.header("Análisis Gráfico Histórico")
            fig, financials_hist = crear_graficos_profesionales(ticker_input)
            
            if fig:
                st.pyplot(fig)
                st.subheader("Banderas Rojas (Red Flags)")
                banderas = analizar_banderas_rojas(datos, financials_hist)
                if banderas:
                    for bandera in banderas:
                        st.warning(bandera)
                else:
                    st.success("✅ No se han detectado banderas rojas significativas en el análisis histórico.")
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
