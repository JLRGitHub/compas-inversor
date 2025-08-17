# app.py
# -----------------------------------------------------------------------------
# El Analizador de Acciones de Sr. Outfit - v47.3 (Versión Definitiva)
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
st.set_page_config(page_title="El Analizador de Acciones de Sr. Outfit", page_icon="📈", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #0E1117; color: #FAFAFA; }
    h1, h2, h3 { color: #D4AF37; }
    .st-emotion-cache-1r6slb0 { border: 1px solid #D4AF37 !important; border-radius: 10px; padding: 15px !important; }
    .stButton>button { background-color: #D4AF37; color: #0E1117; border-radius: 8px; border: 1px solid #D4AF37; font-weight: bold; }
    
    /* Estilos para métricas con colores dinámicos */
    .metric-container { margin-bottom: 10px; padding-top: 5px; }
    .metric-label { font-size: 1rem; color: #adb5bd; }
    .metric-value { font-size: 1.75rem; font-weight: bold; line-height: 1.2; }
    .color-green { color: #28a745; }
    .color-red { color: #dc3545; }
    .color-orange { color: #fd7e14; }
    .color-white { color: #FAFAFA; }
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
    
    free_cash_flow = info.get('freeCashflow')
    market_cap = info.get('marketCap')
    p_fcf = (market_cap / free_cash_flow) if market_cap and free_cash_flow and free_cash_flow > 0 else None
            
    return {
        "nombre": info.get('longName', 'N/A'), "sector": info.get('sector', 'N/A'),
        "pais": info.get('country', 'N/A'), "industria": info.get('industry', 'N/A'),
        "descripcion": info.get('longBusinessSummary', 'No disponible.'),
        "roe": roe * 100 if roe is not None else 0, 
        "margen_operativo": op_margin * 100 if op_margin is not None else 0,
        "margen_beneficio": info.get('profitMargins', 0) * 100, 
        "deuda_patrimonio": info.get('debtToEquity'), "ratio_corriente": info.get('currentRatio'), 
        "per": info.get('trailingPE'), "per_adelantado": info.get('forwardPE'), 
        "p_fcf": p_fcf,
        "crecimiento_ingresos": info.get('revenueGrowth', 0) * 100,
        "yield_dividendo": div_yield * 100 if div_yield is not None else 0,
        "payout_ratio": payout * 100 if payout is not None else 0,
        "recomendacion_analistas": info.get('recommendationKey', 'N/A'),
        "precio_objetivo": info.get('targetMeanPrice'), "precio_actual": info.get('currentPrice'),
    }

@st.cache_data(ttl=3600)
def obtener_datos_historicos(ticker):
    try:
        stock = yf.Ticker(ticker)
        
        financials_raw = stock.financials
        balance_sheet_raw = stock.balance_sheet
        cashflow_raw = stock.cashflow
        
        financials_for_charts, dividends_for_charts = None, None
        
        if not financials_raw.empty and not balance_sheet_raw.empty and not cashflow_raw.empty:
            financials = financials_raw.T.sort_index(ascending=True).tail(4)
            balance_sheet = balance_sheet_raw.T.sort_index(ascending=True).tail(4)
            cashflow = cashflow_raw.T.sort_index(ascending=True).tail(4)
            dividends_chart_data = stock.dividends.resample('YE').sum().tail(5)
            
            financials['Operating Margin'] = financials.get('Operating Income', 0) / financials.get('Total Revenue', 1)
            financials['Total Debt'] = balance_sheet.get('Total Debt', 0)
            financials['ROE'] = financials['Net Income'] / balance_sheet.get('Total Stockholder Equity', 1)
            capex = cashflow.get('Capital Expenditure', cashflow.get('Capital Expenditures', 0))
            op_cash = cashflow.get('Total Cash From Operating Activities', 0)
            financials['Free Cash Flow'] = op_cash + capex
            financials_for_charts, dividends_for_charts = financials, dividends_chart_data

        hist_10y = stock.history(period="10y")
        
        pers, pfcfs = [], []
        possible_share_keys = ['Share Issued', 'Ordinary Shares Number', 'Basic Shares Outstanding', 'Total Common Shares Outstanding']
        share_key_found = next((key for key in possible_share_keys if key in balance_sheet_raw.index), None)
        
        if not financials_raw.empty and share_key_found:
            for col_date in financials_raw.columns:
                if col_date in balance_sheet_raw.columns and col_date in cashflow_raw.columns:
                    net_income = financials_raw.loc['Net Income', col_date]
                    fcf = cashflow_raw.loc['Free Cash Flow', col_date]
                    shares = balance_sheet_raw.loc[share_key_found, col_date]

                    if pd.notna(shares) and shares > 0:
                        price_data = stock.history(start=col_date, end=col_date + pd.Timedelta(days=5), interval="1d")
                        if not price_data.empty:
                            price = price_data['Close'].iloc[0]
                            market_cap = price * shares
                            
                            if pd.notna(net_income) and net_income > 0:
                                per = market_cap / net_income
                                if 0 < per < 100: pers.append(per)
                            
                            if pd.notna(fcf) and fcf > 0:
                                pfcf = market_cap / fcf
                                if 0 < pfcf < 100: pfcfs.append(pfcf)
        
        per_historico_10y = np.mean(pers) if pers else None
        per_historico_5y = np.mean(pers[-5:]) if len(pers) >= 5 else per_historico_10y
        pfcf_historico_10y = np.mean(pfcfs) if pfcfs else None
        pfcf_historico_5y = np.mean(pfcfs[-5:]) if len(pfcfs) >= 5 else pfcf_historico_10y
        
        yield_historico_10y, yield_historico_5y = None, None
        divs_10y = stock.dividends.loc[hist_10y.index[0]:]
        
        if not divs_10y.empty:
            annual_dividends = divs_10y.resample('YE').sum()
            annual_prices = hist_10y['Close'].resample('YE').mean()
            
            df_yield = pd.concat([annual_dividends, annual_prices], axis=1).dropna()
            df_yield.columns = ['Dividends', 'Price']
            
            if not df_yield.empty:
                annual_yields = (df_yield['Dividends'] / df_yield['Price']) * 100
                yield_historico_10y = annual_yields.mean()
                yield_historico_5y = annual_yields.tail(5).mean()

        return {
            "financials_charts": financials_for_charts, "dividends_charts": dividends_for_charts,
            "per_5y": per_historico_5y, "per_10y": per_historico_10y,
            "pfcf_5y": pfcf_historico_5y, "pfcf_10y": pfcf_historico_10y,
            "yield_5y": yield_historico_5y, "yield_10y": yield_historico_10y
        }
    except Exception:
        return {}

# --- BLOQUE 2: LÓGICA DE PUNTUACIÓN Y ANÁLISIS ---
def analizar_banderas_rojas(datos, financials):
    banderas = []
    if datos['payout_ratio'] > 100:
        banderas.append("🔴 **Payout Peligroso:** El ratio de reparto de dividendos es superior al 100%.")
    if financials is not None and not financials.empty:
        if 'Operating Margin' in financials.columns and len(financials) >= 3 and (financials['Operating Margin'].diff().iloc[-2:] < 0).all():
            banderas.append("🔴 **Márgenes Decrecientes:** Los márgenes de beneficio llevan 3 años seguidos bajando.")
        if 'Total Debt' in financials.columns and len(financials) >= 3 and financials['Total Debt'].iloc[-1] > financials['Total Debt'].iloc[-3] * 1.5:
            banderas.append("🔴 **Deuda Creciente:** La deuda total ha aumentado significativamente.")
    return banderas

def calcular_puntuaciones_y_justificaciones(datos, hist_data):
    puntuaciones, justificaciones = {}, {}
    sector, pais = datos['sector'], datos['pais']
    
    benchmarks = {
        'Technology': {'roe_excelente': 25, 'roe_bueno': 18, 'margen_excelente': 25, 'margen_bueno': 18, 'margen_neto_excelente': 20, 'margen_neto_bueno': 15, 'per_barato': 25, 'per_justo': 35, 'payout_bueno': 60, 'payout_aceptable': 80},
        'Healthcare': {'roe_excelente': 20, 'roe_bueno': 15, 'margen_excelente': 20, 'margen_bueno': 15, 'margen_neto_excelente': 15, 'margen_neto_bueno': 10, 'per_barato': 20, 'per_justo': 30, 'payout_bueno': 60, 'payout_aceptable': 80},
        'Financial Services': {'roe_excelente': 12, 'roe_bueno': 10, 'margen_excelente': 15, 'margen_bueno': 10, 'margen_neto_excelente': 10, 'margen_neto_bueno': 8, 'per_barato': 12, 'per_justo': 18, 'payout_bueno': 70, 'payout_aceptable': 90},
        'Industrials': {'roe_excelente': 18, 'roe_bueno': 14, 'margen_excelente': 15, 'margen_bueno': 10, 'margen_neto_excelente': 8, 'margen_neto_bueno': 6, 'per_barato': 20, 'per_justo': 25, 'payout_bueno': 60, 'payout_aceptable': 80},
        'Utilities': {'roe_excelente': 10, 'roe_bueno': 8, 'margen_excelente': 15, 'margen_bueno': 12, 'margen_neto_excelente': 8, 'margen_neto_bueno': 5, 'per_barato': 18, 'per_justo': 22, 'payout_bueno': 80, 'payout_aceptable': 95},
        'Default': {'roe_excelente': 15, 'roe_bueno': 12, 'margen_excelente': 15, 'margen_bueno': 10, 'margen_neto_excelente': 8, 'margen_neto_bueno': 5, 'per_barato': 20, 'per_justo': 25, 'payout_bueno': 60, 'payout_aceptable': 80}
    }
    sector_bench = benchmarks.get(sector, benchmarks['Default'])
    
    paises_seguros = ['United States', 'Canada', 'Germany', 'Switzerland', 'Netherlands', 'United Kingdom', 'France', 'Denmark', 'Sweden', 'Norway', 'Finland', 'Australia', 'New Zealand', 'Japan', 'Ireland']
    paises_precaucion = ['Spain', 'Italy', 'South Korea', 'Taiwan', 'India']
    paises_alto_riesgo = ['China', 'Brazil', 'Russia', 'Argentina', 'Turkey', 'Mexico']
    nota_geo, justificacion_geo, penalizador_geo = 10, "Jurisdicción estable y predecible.", 0
    if pais in paises_precaucion: nota_geo, justificacion_geo, penalizador_geo = 6, "PRECAUCIÓN: Jurisdicción con cierta volatilidad.", 1.5
    elif pais in paises_alto_riesgo: nota_geo, justificacion_geo, penalizador_geo = 2, "ALTO RIESGO: Jurisdicción con alta inestabilidad.", 3.0
    elif pais not in paises_seguros: nota_geo, justificacion_geo, penalizador_geo = 5, "PRECAUCIÓN: Jurisdicción no clasificada.", 2.0
    puntuaciones['geopolitico'], justificaciones['geopolitico'], puntuaciones['penalizador_geo'] = nota_geo, justificacion_geo, penalizador_geo

    nota_calidad = 0
    if datos['roe'] > sector_bench['roe_excelente']: nota_calidad += 3
    elif datos['roe'] > sector_bench['roe_bueno']: nota_calidad += 2
    if datos['margen_operativo'] > sector_bench['margen_excelente']: nota_calidad += 3
    elif datos['margen_operativo'] > sector_bench['margen_bueno']: nota_calidad += 2
    if datos['margen_beneficio'] > sector_bench.get('margen_neto_excelente', 8): nota_calidad += 2
    elif datos['margen_beneficio'] > sector_bench.get('margen_neto_bueno', 5): nota_calidad += 1
    if datos['crecimiento_ingresos'] > 15: nota_calidad += 2
    elif datos['crecimiento_ingresos'] > 8: nota_calidad += 1
    puntuaciones['calidad'] = min(10, nota_calidad)
    justificaciones['calidad'] = "Rentabilidad, márgenes y crecimiento de élite." if puntuaciones['calidad'] >= 8 else "Negocio de buena calidad."

    nota_salud = 0
    deuda_ratio = datos['deuda_patrimonio']
    if sector in ['Financial Services', 'Utilities']: nota_salud, justificaciones['salud'] = 7, "Sector intensivo en capital."
    elif isinstance(deuda_ratio, (int, float)):
        if deuda_ratio < 40: nota_salud = 8
        elif deuda_ratio < 80: nota_salud = 6
        else: nota_salud = 4
    else: nota_salud = 4
    
    ratio_corriente = datos['ratio_corriente']
    if isinstance(ratio_corriente, (int, float)):
        if ratio_corriente > 2.0: nota_salud += 2
        elif ratio_corriente > 1.5: nota_salud += 1
    
    puntuaciones['salud'] = min(10, nota_salud)
    justificaciones['salud'] = "Balance muy sólido y líquido." if puntuaciones['salud'] >= 8 else "Salud financiera aceptable."
    
    nota_multiplos = 0
    if datos['per'] and datos['per'] < sector_bench['per_barato']: nota_multiplos += 5
    if datos['p_fcf'] and datos['p_fcf'] < 20: nota_multiplos += 5
    
    nota_analistas, margen_seguridad = 0, 0
    if datos['precio_actual'] and datos['precio_objetivo']:
        margen_seguridad = ((datos['precio_objetivo'] - datos['precio_actual']) / datos['precio_actual']) * 100
        if margen_seguridad > 25: nota_analistas = 10
        elif margen_seguridad > 15: nota_analistas = 8
        else: nota_analistas = 5
    puntuaciones['margen_seguridad_analistas'] = margen_seguridad

    nota_historica, potencial_per = 0, 0
    per_historico = hist_data.get('per_10y')
    if per_historico and datos['per'] and datos['per'] > 0:
        potencial_per = ((per_historico / datos['per']) - 1) * 100
        if potencial_per > 30: nota_historica = 10
        elif potencial_per > 15: nota_historica = 8
        else: nota_historica = 5
    puntuaciones['margen_seguridad_historico'] = potencial_per
    
    nota_valoracion_base = (nota_multiplos * 0.3) + (nota_analistas * 0.4) + (nota_historica * 0.3)
    
    per_actual = datos.get('per')
    per_adelantado = datos.get('per_adelantado')
    if per_actual and per_adelantado:
        if per_adelantado < per_actual * 0.9:
            nota_valoracion_base += 1
        elif per_adelantado > per_actual:
            nota_valoracion_base -= 1

    puntuaciones['valoracion'] = max(0, min(10, nota_valoracion_base))
    if puntuaciones['valoracion'] >= 8: justificaciones['valoracion'] = "Valoración muy atractiva desde múltiples ángulos."
    else: justificaciones['valoracion'] = "Valoración razonable o exigente."

    nota_dividendos = 0
    if datos['yield_dividendo'] > 3.5: nota_dividendos += 4
    elif datos['yield_dividendo'] > 2: nota_dividendos += 2
    if 0 < datos['payout_ratio'] < sector_bench['payout_bueno']: nota_dividendos += 4
    elif 0 < datos['payout_ratio'] < sector_bench['payout_aceptable']: nota_dividendos += 2
    if hist_data.get('yield_10y') and datos['yield_dividendo'] > hist_data['yield_10y']:
        nota_dividendos += 2
    puntuaciones['dividendos'] = min(10, nota_dividendos)
    justificaciones['dividendos'] = "Dividendo excelente y potencialmente infravalorado." if puntuaciones['dividendos'] >= 8 else "Dividendo sólido."
    
    return puntuaciones, justificaciones, benchmarks

# --- BLOQUE 3: GRÁFICOS Y PRESENTACIÓN ---
def crear_grafico_radar(puntuaciones):
    labels = ['Calidad', 'Valoración', 'Salud Fin.', 'Dividendos']
    stats = [
        puntuaciones.get('calidad', 0), 
        puntuaciones.get('valoracion', 0), 
        puntuaciones.get('salud', 0), 
        puntuaciones.get('dividendos', 0)
    ]

    angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist()
    stats = np.concatenate((stats,[stats[0]]))
    angles = np.concatenate((angles,[angles[0]]))

    fig, ax = plt.subplots(figsize=(3, 3), subplot_kw=dict(polar=True))
    fig.patch.set_facecolor('#0E1117')
    ax.set_facecolor('#0E1117')
    
    ax.plot(angles, stats, color='#D4AF37', linewidth=2)
    ax.fill(angles, stats, color='#D4AF37', alpha=0.25)
    
    ax.set_yticklabels([])
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels, color='white', size=10)
    ax.set_ylim(0, 10)
    
    ax.spines['polar'].set_color('white')
    ax.grid(color='gray', linestyle='--', linewidth=0.5)

    return fig

def crear_grafico_gauge(score):
    fig, ax = plt.subplots(figsize=(3, 1.8))
    fig.patch.set_facecolor('#0E1117')
    
    colors = ['#dc3545', '#fd7e14', '#28a745']
    values = [4, 2, 4]

    ax.pie([*values, sum(values)], colors=[*colors, '#0E1117'], startangle=180, counterclock=False, radius=1, wedgeprops={'width':0.3})
    
    angle = (1 - score / 10) * 180
    ax.arrow(0, 0, -0.8 * np.cos(np.radians(angle)), 0.8 * np.sin(np.radians(angle)),
             width=0.02, head_width=0.05, head_length=0.1, fc='white', ec='white')
    
    ax.text(0, -0.1, f'{score:.1f}', ha='center', va='center', fontsize=20, color='white', weight='bold')
    ax.text(0, -0.4, 'Nota Global', ha='center', va='center', fontsize=10, color='gray')
    
    ax.set_aspect('equal')
    plt.tight_layout()
    return fig

@st.cache_data(ttl=3600)
def crear_graficos_profesionales(ticker, financials, dividends):
    try:
        if financials is None or financials.empty: return None
        años = [d.year for d in financials.index]
        fig, axs = plt.subplots(2, 2, figsize=(15, 10))
        plt.style.use('dark_background')
        fig.patch.set_facecolor('#0E1117')
        
        for ax in axs.flat:
            ax.tick_params(colors='white', which='both', bottom=False, left=False)
            for spine in ax.spines.values(): spine.set_color('white')
            ax.yaxis.label.set_color('white'); ax.xaxis.label.set_color('white'); ax.title.set_color('white')
            ax.set_xticks(años)
            ax.set_xticklabels(años)

        axs[0, 0].bar(años, financials['Total Revenue'] / 1e9, label='Ingresos', color='#87CEEB')
        axs[0, 0].bar(años, financials['Net Income'] / 1e9, label='Beneficio Neto', color='#D4AF37', width=0.5)
        axs[0, 0].set_title('1. Crecimiento (Billones)'); axs[0, 0].legend()

        ax2 = axs[0, 1]
        ax2_twin = ax2.twinx()
        line1, = ax2.plot(años, financials['ROE'] * 100, color='purple', marker='o', label='ROE (%)')
        line2, = ax2_twin.plot(años, financials['Operating Margin'] * 100, color='#D4AF37', marker='s', label='Margen Op. (%)')
        ax2.set_title('2. Rentabilidad')
        ax2.legend(handles=[line1, line2])

        axs[1, 0].bar(años, financials['Net Income'] / 1e9, label='Beneficio Neto (B)', color='royalblue')
        axs[1, 0].plot(años, financials['Free Cash Flow'] / 1e9, label='FCF (B)', color='green', marker='o', linestyle='--')
        axs[1, 0].set_title('3. Beneficio vs. Caja Real'); axs[1, 0].legend()

        if dividends is not None and not dividends.empty:
            axs[1, 1].bar(dividends.index.year, dividends, label='Dividendo/Acción', color='orange')
        axs[1, 1].set_title('4. Retorno al Accionista')
        
        plt.tight_layout(rect=[0, 0.03, 1, 0.95])
        return fig
    except Exception:
        return None

def mostrar_metrica_con_color(label, value, umbral_bueno, umbral_malo=None, lower_is_better=False, is_percent=False):
    if umbral_malo is None: umbral_malo = umbral_bueno * 1.25 if lower_is_better else umbral_bueno * 0.8
    color_class = "color-white"
    try:
        numeric_value = float(str(value).replace('%', ''))
        if lower_is_better:
            if numeric_value < umbral_bueno: color_class = "color-green"
            elif numeric_value > umbral_malo: color_class = "color-red"
        else:
            if numeric_value > umbral_bueno: color_class = "color-green"
            elif numeric_value < umbral_malo: color_class = "color-red"
    except (ValueError, TypeError): pass
    
    formatted_value = f"{value:.2f}%" if is_percent and isinstance(value, (int, float)) else (f"{value:.2f}" if isinstance(value, (int, float)) else "N/A")
    st.markdown(f'<div class="metric-container"><div class="metric-label">{label}</div><div class="metric-value {color_class}">{formatted_value}</div></div>', unsafe_allow_html=True)

def mostrar_margen_seguridad(label, value):
    color_class = "color-white"
    prose = "N/A"
    if isinstance(value, (int, float)):
        if value > 0:
            color_class = "color-green"
            prose = f"Podría aumentar un +{value:.2f}%"
        else:
            color_class = "color-red"
            prose = f"Podría disminuir un {value:.2f}%"
    
    st.markdown(f'''
    <div class="metric-container">
        <div class="metric-label">{label}</div>
        <div class="metric-value {color_class}">{prose}</div>
    </div>
    ''', unsafe_allow_html=True)

def mostrar_metrica_informativa(label, value, is_percent=False):
    formatted_value = "N/A"
    if isinstance(value, (int, float)):
        formatted_value = f"{value:.2f}%" if is_percent else f"{value:.2f}"
    st.markdown(f'''
    <div class="metric-container">
        <div class="metric-label">{label}</div>
        <div class="metric-value color-white">{formatted_value}</div>
    </div>
    ''', unsafe_allow_html=True)

def get_recommendation_html(recommendation):
    rec_lower = recommendation.lower()
    color_class = "color-white"
    if any(term in rec_lower for term in ['buy', 'outperform', 'strong']):
        color_class = "color-green"
    elif any(term in rec_lower for term in ['sell', 'underperform']):
        color_class = "color-red"
    elif 'hold' in rec_lower:
        color_class = "color-orange"
    return f'<div class="metric-container"><div class="metric-label">Recomendación Media</div><div class="metric-value {color_class}">{recommendation}</div></div>'

# --- ESTRUCTURA DE LA APLICACIÓN WEB ---
st.title('El Analizador de Acciones de Sr. Outfit')
st.caption("Herramienta de análisis. Esto no es una recomendación de compra o venta. Realiza tu propio juicio y análisis antes de invertir.")

ticker_input = st.text_input("Introduce el Ticker de la Acción a Analizar (ej. JNJ, MSFT, BABA)", "AAPL").upper()

if st.button('Analizar Acción'):
    with st.spinner('Realizando análisis profesional...'):
        datos = obtener_datos_completos(ticker_input)
        
        if not datos:
            st.error(f"Error: No se pudo encontrar el ticker '{ticker_input}'. Verifica que sea correcto.")
        else:
            hist_data = obtener_datos_historicos(ticker_input)
            puntuaciones, justificaciones, benchmarks = calcular_puntuaciones_y_justificaciones(datos, hist_data)
            sector_bench = benchmarks.get(datos['sector'], benchmarks['Default'])
            
            pesos = {'calidad': 0.4, 'valoracion': 0.3, 'salud': 0.2, 'dividendos': 0.1}
            nota_ponderada = sum(puntuaciones.get(k, 0) * v for k, v in pesos.items())
            nota_final = max(0, nota_ponderada - puntuaciones['penalizador_geo'])

            st.header(f"Informe Profesional: {datos['nombre']} ({ticker_input})")
            
            st.markdown(f"### 🧭 Veredicto del Analizador: **{nota_final:.1f} / 10**")
            if nota_final >= 7.5: st.success("Veredicto: Empresa EXCEPCIONAL a un precio potencialmente atractivo.")
            elif nota_final >= 6: st.info("Veredicto: Empresa de ALTA CALIDAD a un precio razonable.")
            else: st.warning("Veredicto: Empresa SÓLIDA, pero vigilar valoración o riesgos.")

            col_gauge, col_radar = st.columns([0.7, 1])
            with col_gauge:
                st.subheader("Nota Global")
                fig_gauge = crear_grafico_gauge(nota_final)
                st.pyplot(fig_gauge)
            with col_radar:
                st.subheader("Resumen de Fortalezas")
                fig_radar = crear_grafico_radar(puntuaciones)
                st.pyplot(fig_radar)

            with st.expander("1. Identidad y Riesgo Geopolítico", expanded=True):
                st.write(f"**Sector:** {datos['sector']} | **Industria:** {datos['industria']}")
                geo_nota = puntuaciones['geopolitico']
                if geo_nota >= 8: st.markdown(f"**País:** {datos['pais']} | **Nivel de Riesgo:** BAJO 🟢")
                else: st.markdown(f"**País:** {datos['pais']} | **Nivel de Riesgo:** PRECAUCIÓN 🟠")
                st.caption(justificaciones['geopolitico'])
                st.write(f"**Descripción:** {datos['descripcion']}")
            
            with st.container(border=True):
                st.subheader("Consenso de Analistas")
                recomendacion_str = datos.get('recomendacion_analistas', 'N/A').replace('_', ' ').title()
                st.markdown(get_recommendation_html(recomendacion_str), unsafe_allow_html=True)

            col1, col2 = st.columns(2)
            with col1:
                with st.container(border=True):
                    st.subheader(f"Calidad del Negocio [{puntuaciones['calidad']}/10]")
                    st.caption(justificaciones['calidad'])
                    c1, c2 = st.columns(2)
                    with c1:
                        mostrar_metrica_con_color("📈 ROE", datos['roe'], 20, 15, is_percent=True)
                        mostrar_metrica_con_color("💰 Margen Neto", datos['margen_beneficio'], 15, 10, is_percent=True)
                    with c2:
                        mostrar_metrica_con_color("📊 Margen Operativo", datos['margen_operativo'], 20, 15, is_percent=True)
                        mostrar_metrica_con_color("🚀 Crec. Ingresos (YoY)", datos['crecimiento_ingresos'], 15, 8, is_percent=True)
                    with st.expander("Ver Leyenda Detallada"):
                        st.markdown(f"""
                        - **ROE (Return on Equity):** Mide la rentabilidad sobre el dinero de los accionistas. Para el sector **{datos['sector'].upper()}**, se considera **Excelente > {sector_bench['roe_excelente']}%**. Un ROE muy alto (>50%) puede estar 'inflado' por una deuda elevada.
                        - **Márgenes (Operativo y Neto):** Indican el % de beneficio sobre las ventas. Para este sector, un **Margen Operativo Excelente es > {sector_bench['margen_excelente']}%** y un **Margen Neto Excelente es > {sector_bench['margen_neto_excelente']}%**. Es una señal de alerta si el Margen Neto es superior al Operativo, ya que puede indicar beneficios extraordinarios no recurrentes.
                        - **Crecimiento Ingresos:** Mide el crecimiento de las ventas. Un crecimiento de doble dígito (>10%) es una señal muy positiva.
                        """)
            with col2:
                with st.container(border=True):
                    st.subheader(f"Salud Financiera [{puntuaciones['salud']}/10]")
                    st.caption(justificaciones['salud'])
                    s1, s2 = st.columns(2)
                    with s1: mostrar_metrica_con_color("🏦 Deuda / Patrimonio", datos['deuda_patrimonio'], 40, 80, lower_is_better=True)
                    with s2: mostrar_metrica_con_color("💧 Ratio Corriente", datos['ratio_corriente'], 1.5, 1.0)
                    with st.expander("Ver Leyenda Detallada"):
                        st.markdown("""
                        - **Deuda / Patrimonio (Debt to Equity):** Compara la deuda con los fondos propios. Un valor bajo (< 40) indica un balance muy conservador. **Esta nota se combina con el Ratio Corriente para la puntuación final.**
                        - **Ratio Corriente (Current Ratio):** Mide la capacidad de pagar deudas a corto plazo. Un valor > 1.5 es muy saludable y **aporta puntos extra a la nota de salud financiera.**
                        """)

            with st.container(border=True):
                st.subheader(f"Análisis de Valoración [{puntuaciones['valoracion']:.1f}/10]")
                st.caption(justificaciones['valoracion'])
                
                tab1, tab2 = st.tabs(["Resumen y Potencial", "Análisis Histórico"])
                
                with tab1:
                    val1, val2 = st.columns(2)
                    with val1:
                        st.markdown("##### Múltiplos (Presente)")
                        mostrar_metrica_con_color("⚖️ PER", datos['per'], sector_bench['per_barato'], sector_bench['per_justo'], lower_is_better=True)
                        mostrar_metrica_con_color("🔮 PER Adelantado", datos['per_adelantado'], datos.get('per', 999), lower_is_better=True)
                        mostrar_metrica_con_color("🌊 P/FCF", datos['p_fcf'], 20, 30, lower_is_better=True)
                    with val2:
                        st.markdown("##### Márgenes de Seguridad")
                        mostrar_margen_seguridad("🛡️ Según Expertos (Futuro)", puntuaciones['margen_seguridad_analistas'])
                        mostrar_margen_seguridad("📈 Según Histórico (Pasado)", puntuaciones['margen_seguridad_historico'])
                
                with tab2:
                    h1, h2 = st.columns(2)
                    with h1:
                        mostrar_metrica_informativa("🕰️ PER Medio (5A)", hist_data.get('per_5y'))
                        mostrar_metrica_informativa("🕰️ PER Medio (10A)", hist_data.get('per_10y'))
                    with h2:
                        mostrar_metrica_informativa("🌊 P/FCF Medio (5A)", hist_data.get('pfcf_5y'))
                        mostrar_metrica_informativa("🌊 P/FCF Medio (10A)", hist_data.get('pfcf_10y'))

                with st.expander("Ver Leyenda Detallada"):
                    st.markdown(f"""
                    - **Múltiplos:** Miden cuántas veces estás pagando los beneficios (PER) o el flujo de caja (P/FCF). Para el sector **{datos['sector'].upper()}**, un **PER atractivo es < {sector_bench['per_barato']}**. El **PER Adelantado** usa beneficios futuros esperados; si es menor que el PER actual, indica crecimiento y **suma un bonus a la nota**.
                    - **Márgenes de Seguridad:** Miden el potencial de revalorización. El de **Expertos** se basa en el precio objetivo de los analistas (futuro), y el **Histórico** en si la acción volviera a su PER medio de los últimos 10 años (pasado).
                    - **Análisis Histórico:** Compara los múltiplos actuales con sus medias de 5 y 10 años para ver si la empresa está cara o barata respecto a su propia historia.
                    """)

            if datos['yield_dividendo'] > 0:
                with st.container(border=True):
                    st.subheader(f"Dividendos [{puntuaciones['dividendos']}/10]")
                    st.caption(justificaciones['dividendos'])
                    div1, div2 = st.columns(2)
                    with div1: 
                        mostrar_metrica_con_color("💸 Rentabilidad (Yield)", datos['yield_dividendo'], 3.5, 2.0, is_percent=True)
                        mostrar_metrica_con_color("🤲 Ratio de Reparto (Payout)", datos['payout_ratio'], sector_bench['payout_bueno'], sector_bench['payout_aceptable'], lower_is_better=True, is_percent=True)
                    with div2:
                        mostrar_metrica_informativa("📈 Yield Medio (5A)", hist_data.get('yield_5y'), is_percent=True)
                        mostrar_metrica_informativa("📈 Yield Medio (10A)", hist_data.get('yield_10y'), is_percent=True)
                    with st.expander("Ver Leyenda Detallada"):
                        st.markdown(f"""
                        - **Rentabilidad (Yield):** Es el porcentaje que recibes anualmente en dividendos en relación al precio de la acción.
                        - **Ratio de Reparto (Payout):** Indica qué porcentaje del beneficio se destina a pagar dividendos. Para el sector **{datos['sector'].upper()}**, un payout saludable es **< {sector_bench['payout_bueno']}%**.
                        - **Yield Medio (5A y 10A):** Es la rentabilidad por dividendo media histórica. Si el Yield actual es **superior a esta media**, puede ser una señal de que la acción está barata. **Otorga un bonus a la nota de dividendos.**
                        """)

            st.header("Análisis Gráfico y Banderas Rojas")
            financials_hist = hist_data.get('financials_charts')
            dividends_hist = hist_data.get('dividends_charts')
            fig = crear_graficos_profesionales(ticker_input, financials_hist, dividends_hist)
            if fig:
                st.pyplot(fig)
                st.subheader("Banderas Rojas (Red Flags)")
                banderas = analizar_banderas_rojas(datos, financials_hist)
                if banderas:
                    for bandera in banderas: st.warning(bandera)
                else:
                    st.success("✅ No se han detectado banderas rojas significativas.")
            else:
                st.warning("No se pudieron generar los gráficos históricos.")


