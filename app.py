import streamlit as st
import yfinance as yf
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

# --- CONFIGURACIÓN DE LA PÁGINA WEB Y ESTILOS ---
st.set_page_config(page_title="El Analizador de Acciones de Sr. Outfit", page_icon="📈", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #0E1117; color: #FAFAFA; }
    h1, h2, h3 { color: #D4AF37; }
    .st-emotion-cache-1r6slb0 { border: 1px solid #D4AF37 !important; border-radius: 10px; padding: 15px !important; margin-bottom: 1rem; }
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

# --- Benchmarks Centralizados y Completos para los 11 Sectores GICS ---
SECTOR_BENCHMARKS = {
    'Information Technology': {'roe_excelente': 25, 'roe_bueno': 18, 'margen_excelente': 25, 'margen_bueno': 18, 'margen_neto_excelente': 20, 'margen_neto_bueno': 15, 'rev_growth_excelente': 15, 'rev_growth_bueno': 10, 'per_barato': 25, 'per_justo': 35, 'pb_barato': 4, 'pb_justo': 8, 'payout_bueno': 60, 'payout_aceptable': 80},
    'Health Care': {'roe_excelente': 20, 'roe_bueno': 15, 'margen_excelente': 20, 'margen_bueno': 15, 'margen_neto_excelente': 15, 'margen_neto_bueno': 10, 'rev_growth_excelente': 10, 'rev_growth_bueno': 6, 'per_barato': 20, 'per_justo': 30, 'pb_barato': 3, 'pb_justo': 5, 'payout_bueno': 60, 'payout_aceptable': 80},
    'Financial Services': {'roe_excelente': 12, 'roe_bueno': 10, 'margen_excelente': 15, 'margen_bueno': 10, 'margen_neto_excelente': 10, 'margen_neto_bueno': 8, 'rev_growth_excelente': 8, 'rev_growth_bueno': 4, 'per_barato': 12, 'per_justo': 18, 'pb_barato': 1, 'pb_justo': 1.5, 'payout_bueno': 70, 'payout_aceptable': 90},
    'Industrials': {'roe_excelente': 18, 'roe_bueno': 14, 'margen_excelente': 15, 'margen_bueno': 10, 'margen_neto_excelente': 8, 'margen_neto_bueno': 6, 'rev_growth_excelente': 10, 'rev_growth_bueno': 5, 'per_barato': 20, 'per_justo': 25, 'pb_barato': 2.5, 'pb_justo': 4, 'payout_bueno': 60, 'payout_aceptable': 80},
    'Utilities': {'roe_excelente': 10, 'roe_bueno': 8, 'margen_excelente': 15, 'margen_bueno': 12, 'margen_neto_excelente': 8, 'margen_neto_bueno': 5, 'rev_growth_excelente': 5, 'rev_growth_bueno': 3, 'per_barato': 18, 'per_justo': 22, 'pb_barato': 1.5, 'pb_justo': 2, 'payout_bueno': 80, 'payout_aceptable': 95},
    'Consumer Discretionary': {'roe_excelente': 18, 'roe_bueno': 14, 'margen_excelente': 12, 'margen_bueno': 8, 'margen_neto_excelente': 7, 'margen_neto_bueno': 5, 'rev_growth_excelente': 12, 'rev_growth_bueno': 7, 'per_barato': 20, 'per_justo': 28, 'pb_barato': 3, 'pb_justo': 5, 'payout_bueno': 60, 'payout_aceptable': 80},
    'Consumer Staples': {'roe_excelente': 20, 'roe_bueno': 15, 'margen_excelente': 15, 'margen_bueno': 10, 'margen_neto_excelente': 8, 'margen_neto_bueno': 5, 'rev_growth_excelente': 7, 'rev_growth_bueno': 4, 'per_barato': 20, 'per_justo': 25, 'pb_barato': 4, 'pb_justo': 6, 'payout_bueno': 70, 'payout_aceptable': 85},
    'Energy': {'roe_excelente': 15, 'roe_bueno': 10, 'margen_excelente': 10, 'margen_bueno': 7, 'margen_neto_excelente': 8, 'margen_neto_bueno': 5, 'rev_growth_excelente': 8, 'rev_growth_bueno': 0, 'per_barato': 15, 'per_justo': 20, 'pb_barato': 1.5, 'pb_justo': 2.5, 'payout_bueno': 60, 'payout_aceptable': 80},
    'Materials': {'roe_excelente': 15, 'roe_bueno': 12, 'margen_excelente': 12, 'margen_bueno': 8, 'margen_neto_excelente': 7, 'margen_neto_bueno': 5, 'rev_growth_excelente': 10, 'rev_growth_bueno': 5, 'per_barato': 18, 'per_justo': 25, 'pb_barato': 2, 'pb_justo': 3, 'payout_bueno': 60, 'payout_aceptable': 80},
    'Real Estate': {'roe_excelente': 8, 'roe_bueno': 6, 'margen_excelente': 20, 'margen_bueno': 15, 'margen_neto_excelente': 15, 'margen_neto_bueno': 10, 'rev_growth_excelente': 8, 'rev_growth_bueno': 4, 'per_barato': 25, 'per_justo': 35, 'pb_barato': 2, 'pb_justo': 3, 'payout_bueno': 90, 'payout_aceptable': 100},
    'Communication Services': {'roe_excelente': 15, 'roe_bueno': 12, 'margen_excelente': 18, 'margen_bueno': 12, 'margen_neto_excelente': 12, 'margen_neto_bueno': 9, 'rev_growth_excelente': 12, 'rev_growth_bueno': 7, 'per_barato': 22, 'per_justo': 30, 'pb_barato': 3, 'pb_justo': 5, 'payout_bueno': 60, 'payout_aceptable': 80},
    'Default': {'roe_excelente': 15, 'roe_bueno': 12, 'margen_excelente': 15, 'margen_bueno': 10, 'margen_neto_excelente': 8, 'margen_neto_bueno': 5, 'rev_growth_excelente': 10, 'rev_growth_bueno': 5, 'per_barato': 20, 'per_justo': 25, 'pb_barato': 2, 'pb_justo': 4, 'payout_bueno': 60, 'payout_aceptable': 80}
}

# --- BLOQUE 1: OBTENCIÓN DE DATOS ---
@st.cache_data(ttl=900)
def obtener_datos_completos(ticker):
    stock = yf.Ticker(ticker)
    info = stock.info
    if not info or info.get('longName') is None:
        return None
    
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

    # --- CAMBIO: Acortar la descripción ---
    descripcion_completa = info.get('longBusinessSummary', 'No disponible.')
    descripcion_corta = 'No disponible.'
    if descripcion_completa and descripcion_completa != 'No disponible.':
        primer_punto = descripcion_completa.find('.')
        if primer_punto != -1:
            descripcion_corta = descripcion_completa[:primer_punto + 1]
        else:
            descripcion_corta = descripcion_completa # Mantener como está si no hay punto
            
    return {
        "nombre": info.get('longName', 'N/A'), "sector": info.get('sector', 'N/A'),
        "pais": info.get('country', 'N/A'), "industria": info.get('industry', 'N/A'),
        "descripcion": descripcion_corta,
        "roe": roe * 100 if roe is not None else 0, 
        "margen_operativo": op_margin * 100 if op_margin is not None else 0,
        "margen_beneficio": info.get('profitMargins', 0) * 100, 
        "deuda_patrimonio": info.get('debtToEquity'), "ratio_corriente": info.get('currentRatio'), 
        "per": info.get('trailingPE'), "per_adelantado": info.get('forwardPE'), 
        "p_fcf": p_fcf,
        "raw_fcf": free_cash_flow, # Dato raw para chequear si es negativo
        "p_b": info.get('priceToBook'),
        "crecimiento_ingresos": info.get('revenueGrowth', 0) * 100,
        "yield_dividendo": div_yield * 100 if div_yield is not None else 0,
        "payout_ratio": payout * 100 if payout is not None else 0,
        "recomendacion_analistas": info.get('recommendationKey', 'N/A'),
        "precio_objetivo": info.get('targetMeanPrice'), "precio_actual": info.get('currentPrice'),
    }

@st.cache_data(ttl=3600)
def obtener_datos_historicos_y_tecnicos(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        if not isinstance(info, dict) or not info:
            st.warning(f"No se pudo obtener la información básica para {ticker}. El ticker podría no ser válido o estar delistado.")
            return {}

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
        
        if hist_10y.empty:
            st.warning(f"No se encontraron datos históricos de precios para {ticker}. El análisis técnico y de valoración histórica no estará disponible.")
            return {
                "financials_charts": financials_for_charts, "dividends_charts": dividends_for_charts,
                "per_hist": None, "pfcf_hist": None, "yield_hist": None,
                "tech_data": pd.DataFrame()
            }

        # --- CÁLCULO DE MÉTRICAS HISTÓRICAS (VERSIÓN SIMPLIFICADA Y ESTABLE) ---
        pers, pfcfs = [], []
        
        possible_share_keys = ['Share Issued', 'Ordinary Shares Number', 'Basic Shares Outstanding', 'Total Common Shares Outstanding']
        share_key_found = next((key for key in possible_share_keys if key in balance_sheet_raw.index), None)
        
        net_income_key = 'Net Income Applicable To Common Shares' if 'Net Income Applicable To Common Shares' in financials_raw.index else 'Net Income'
        
        if not financials_raw.empty and share_key_found:
            for col_date in financials_raw.columns:
                if col_date in balance_sheet_raw.columns and col_date in cashflow_raw.columns:
                    net_income = financials_raw.loc[net_income_key, col_date]
                    fcf = cashflow_raw.loc['Free Cash Flow', col_date] if 'Free Cash Flow' in cashflow_raw.index else None
                    shares = balance_sheet_raw.loc[share_key_found, col_date]

                    if pd.notna(shares) and shares > 0:
                        start_of_year = col_date - pd.DateOffset(years=1)
                        price_data_year = stock.history(start=start_of_year, end=col_date, interval="1d")

                        if not price_data_year.empty:
                            average_price_for_year = price_data_year['Close'].mean()
                            
                            if pd.notna(net_income) and net_income > 0:
                                eps = net_income / shares
                                if eps > 0:
                                    per_for_year = average_price_for_year / eps
                                    if 0 < per_for_year < 200: 
                                        pers.append(per_for_year)

                            if pd.notna(fcf) and fcf > 0:
                                fcf_per_share = fcf / shares
                                if fcf_per_share > 0:
                                    pfcf_for_year = average_price_for_year / fcf_per_share
                                    if 0 < pfcf_for_year < 200:
                                        pfcfs.append(pfcf_for_year)
        
        per_historico = np.mean(pers) if pers else None
        pfcf_historico = np.mean(pfcfs) if pfcfs else None
        
        yield_historico = None
        divs_10y = stock.dividends.loc[hist_10y.index[0]:]
        
        if not divs_10y.empty:
            annual_dividends = divs_10y.resample('YE').sum()
            annual_prices = hist_10y['Close'].resample('YE').mean()
            
            df_yield = pd.concat([annual_dividends, annual_prices], axis=1).dropna()
            df_yield.columns = ['Dividends', 'Price']
            
            if not df_yield.empty:
                annual_yields = (df_yield['Dividends'] / df_yield['Price']) * 100
                yield_historico = annual_yields.mean()

        end_date_1y = hist_10y.index.max()
        start_date_1y = end_date_1y - pd.DateOffset(days=365)
        hist_1y = hist_10y[hist_10y.index >= start_date_1y].copy()
        
        hist_1y['SMA50'] = hist_1y['Close'].rolling(window=50).mean()
        hist_1y['SMA200'] = hist_1y['Close'].rolling(window=200).mean()
        delta = hist_1y['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        hist_1y['RSI'] = 100 - (100 / (1 + rs))

        return {
            "financials_charts": financials_for_charts, "dividends_charts": dividends_for_charts,
            "per_hist": per_historico,
            "pfcf_hist": pfcf_historico,
            "yield_hist": yield_historico,
            "tech_data": hist_1y
        }
    except Exception:
        return {}

# --- BLOQUE 2: LÓGICA DE PUNTUACIÓN Y ANÁLISIS ---
def analizar_banderas_rojas(datos, financials):
    banderas = []
    if datos.get('sector') != 'Real Estate' and datos.get('payout_ratio', 0) > 100:
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
    
    sector_bench = SECTOR_BENCHMARKS.get(sector, SECTOR_BENCHMARKS['Default'])
    
    paises_seguros = ['United States', 'Canada', 'Germany', 'Switzerland', 'Netherlands', 'United Kingdom', 'France', 'Denmark', 'Sweden', 'Norway', 'Finland', 'Australia', 'New Zealand', 'Japan', 'Ireland', 'Austria', 'Belgium', 'Luxembourg', 'Singapore']
    paises_precaucion = ['Spain', 'Italy', 'South Korea', 'Taiwan', 'India', 'Chile', 'Poland', 'Czech Republic', 'Portugal', 'Israel', 'United Arab Emirates', 'Qatar', 'Malaysia', 'Thailand', 'Saudi Arabia', 'Kuwait', 'Hong Kong']
    paises_alto_riesgo = ['China', 'Brazil', 'Russia', 'Argentina', 'Turkey', 'Mexico', 'South Africa', 'Indonesia', 'Vietnam', 'Nigeria', 'Egypt', 'Pakistan', 'Colombia', 'Peru', 'Philippines']
    
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
    if datos['crecimiento_ingresos'] > sector_bench['rev_growth_excelente']: nota_calidad += 2
    elif datos['crecimiento_ingresos'] > sector_bench['rev_growth_bueno']: nota_calidad += 1
    puntuaciones['calidad'] = min(10, nota_calidad)
    justificaciones['calidad'] = "Rentabilidad, márgenes y crecimiento de élite." if puntuaciones['calidad'] >= 8 else "Negocio de buena calidad."

    # --- LÓGICA DE DEUDA INTELIGENTE POR SECTOR ---
    nota_salud = 0
    deuda_ratio = datos['deuda_patrimonio']
    SECTORES_ALTA_DEUDA = ['Financial Services', 'Utilities', 'Communication Services', 'Real Estate']
    
    if sector in SECTORES_ALTA_DEUDA:
        if isinstance(deuda_ratio, (int, float)):
            if deuda_ratio < 150: nota_salud = 8
            elif deuda_ratio < 250: nota_salud = 6
            else: nota_salud = 4
        else: nota_salud = 4
    else:
        if isinstance(deuda_ratio, (int, float)):
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
    
    # --- LÓGICA DE VALORACIÓN CON P/B Y FCF NEGATIVO ---
    nota_multiplos = 0
    if sector == 'Real Estate':
        if datos['p_fcf'] and datos['p_fcf'] < 16: nota_multiplos += 8
        elif datos['p_fcf'] and datos['p_fcf'] < 22: nota_multiplos += 5
    else:
        if datos['per'] and datos['per'] < sector_bench['per_barato']: nota_multiplos += 4
        if datos['p_fcf'] and datos['p_fcf'] < 20: nota_multiplos += 3
        
    SECTORES_PB_RELEVANTES = ['Financial Services', 'Industrials', 'Materials', 'Energy', 'Utilities', 'Real Estate']
    if sector in SECTORES_PB_RELEVANTES and datos['p_b']:
        if datos['p_b'] < sector_bench['pb_barato']: nota_multiplos += 3
        elif datos['p_b'] < sector_bench['pb_justo']: nota_multiplos += 1
    
    if datos.get('raw_fcf') is not None and datos['raw_fcf'] < 0:
        nota_multiplos -= 3

    nota_analistas, margen_seguridad = 0, 0
    if datos['precio_actual'] and datos['precio_objetivo']:
        margen_seguridad = ((datos['precio_objetivo'] - datos['precio_actual']) / datos['precio_actual']) * 100
        if margen_seguridad > 25: nota_analistas = 10
        elif margen_seguridad > 15: nota_analistas = 8
        else: nota_analistas = 5
    puntuaciones['margen_seguridad_analistas'] = margen_seguridad

    # --- ¡NUEVO! Tres márgenes de seguridad históricos ---
    potencial_per, potencial_yield = 0, 0
    per_historico = hist_data.get('per_hist')
    if per_historico and datos['per'] and datos['per'] > 0:
        potencial_per = ((per_historico / datos['per']) - 1) * 100
    puntuaciones['margen_seguridad_per'] = potencial_per

    yield_historico = hist_data.get('yield_hist')
    if yield_historico and datos['yield_dividendo'] and yield_historico > 0:
        potencial_yield = ((datos['yield_dividendo'] / yield_historico) - 1) * 100
    puntuaciones['margen_seguridad_yield'] = potencial_yield
    
    nota_historica = 0
    if potencial_per > 15: nota_historica += 3
    if potencial_yield > 15: nota_historica += 3
    nota_historica = min(10, nota_historica)

    nota_valoracion_base = (nota_multiplos * 0.3) + (nota_analistas * 0.4) + (nota_historica * 0.3)
    
    per_actual = datos.get('per')
    per_adelantado = datos.get('per_adelantado')
    if per_actual and per_adelantado:
        if per_adelantado < per_actual * 0.9:
            nota_valoracion_base += 1
        elif per_adelantado > per_actual:
            nota_valoracion_base -= 1

    if puntuaciones['calidad'] < 3:
        nota_valoracion_base *= 0.5
    elif puntuaciones['calidad'] < 5:
        nota_valoracion_base *= 0.75

    puntuaciones['valoracion'] = max(0, min(10, nota_valoracion_base))
    if puntuaciones['valoracion'] >= 8: justificaciones['valoracion'] = "Valoración muy atractiva desde múltiples ángulos."
    else: justificaciones['valoracion'] = "Valoración razonable o exigente."

    nota_dividendos = 0
    if datos['yield_dividendo'] > 3.5: nota_dividendos += 4
    elif datos['yield_dividendo'] > 2: nota_dividendos += 2
    if 0 < datos['payout_ratio'] < sector_bench['payout_bueno']: nota_dividendos += 4
    elif 0 < datos['payout_ratio'] < sector_bench['payout_aceptable']: nota_dividendos += 2
    if hist_data.get('yield_hist') and datos['yield_dividendo'] > hist_data['yield_hist']:
        nota_dividendos += 2
    puntuaciones['dividendos'] = min(10, nota_dividendos)
    justificaciones['dividendos'] = "Dividendo excelente y potencialmente infravalorado." if puntuaciones['dividendos'] >= 8 else "Dividendo sólido."
    
    justificaciones['blue_chip_analysis'] = None
    current_yield = datos.get('yield_dividendo')
    historical_yield = hist_data.get('yield_hist')
    current_per = datos.get('per')
    historical_per = hist_data.get('per_hist')

    if current_yield and historical_yield and current_per and historical_per:
        per_is_lower = current_per < historical_per
        yield_is_higher = current_yield > historical_yield
        
        if per_is_lower and yield_is_higher:
            per_is_much_lower = current_per < historical_per * 0.8
            yield_is_much_higher = current_yield > historical_yield * 1.2

            if per_is_much_lower and yield_is_much_higher:
                analysis = "🟢 Muy Interesante"
                description = "Tanto el PER está significativamente por debajo de su media como el Yield está muy por encima. Señal de valoración muy atractiva."
            else:
                analysis = "🟡 Interesante"
                description = "El PER está por debajo de su media y el Yield por encima. Señal de valoración atractiva."
            
            justificaciones['blue_chip_analysis'] = {'label': analysis, 'description': description}

        elif per_is_lower or yield_is_higher:
            analysis = "🔵 Señal Mixta"
            if per_is_lower:
                description = "El PER es inferior a su media, pero el Yield no es superior. Señal de valoración parcialmente positiva."
            else:
                description = "El Yield es superior a su media, pero el PER no es inferior. Señal de valoración parcialmente positiva."
            justificaciones['blue_chip_analysis'] = {'label': analysis, 'description': description}

    return puntuaciones, justificaciones, SECTOR_BENCHMARKS


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

    fig, ax = plt.subplots(figsize=(2.5, 2.5), subplot_kw=dict(polar=True))
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
    fig, ax = plt.subplots(figsize=(2.5, 1.5))
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

def crear_grafico_tecnico(data):
    # Gráfico más pequeño
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 5), gridspec_kw={'height_ratios': [3, 1]}, sharex=True)
    fig.patch.set_facecolor('#0E1117')
    
    ax1.set_facecolor('#0E1117')
    ax1.plot(data.index, data['Close'], label='Precio', color='#87CEEB', linewidth=2)
    # --- CAMBIO DE COLOR ---
    ax1.plot(data.index, data['SMA50'], label='Media Móvil 50 días', color='#FFA500', linestyle='--') # Ahora es naranja
    ax1.plot(data.index, data['SMA200'], label='Media Móvil 200 días', color='#FF0000', linestyle='--') # Ahora es rojo
    ax1.set_title('Análisis Técnico del Precio (Último Año)', color='white')
    ax1.legend()
    ax1.grid(color='gray', linestyle='--', linewidth=0.5)
    ax1.tick_params(axis='y', colors='white')
    ax1.spines['top'].set_color('white'); ax1.spines['bottom'].set_color('white'); ax1.spines['left'].set_color('white'); ax1.spines['right'].set_color('white')

    ax2.set_facecolor('#0E1117')
    ax2.plot(data.index, data['RSI'], label='RSI', color='#DA70D6')
    ax2.axhline(70, color='red', linestyle='--', linewidth=1)
    ax2.axhline(30, color='green', linestyle='--', linewidth=1)
    ax2.set_ylim(0, 100)
    ax2.set_ylabel('RSI', color='white')
    ax2.grid(color='gray', linestyle='--', linewidth=0.5)
    ax2.tick_params(axis='x', colors='white')
    ax2.tick_params(axis='y', colors='white')
    ax2.spines['top'].set_color('white'); ax2.spines['bottom'].set_color('white'); ax2.spines['left'].set_color('white'); ax2.spines['right'].set_color('white')
    
    plt.tight_layout()
    return fig

@st.cache_data(ttl=3600)
def crear_graficos_financieros(ticker, financials, dividends):
    try:
        if financials is None or financials.empty: return None
        años = [d.year for d in financials.index]
        # Gráfico más pequeño
        fig, axs = plt.subplots(2, 2, figsize=(8, 5))
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
        if value > 20:
            color_class = "color-green"
            prose = f"Alto Potencial: +{value:.2f}%"
        elif value > 0:
            color_class = "color-green"
            prose = f"Potencial: +{value:.2f}%"
        else:
            color_class = "color-red"
            prose = f"Riesgo de Caída: {value:.2f}%"
    
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
    display_text = recommendation
    if any(term in rec_lower for term in ['buy', 'outperform', 'strong']):
        color_class = "color-green"
        display_text = "Muy Interesante"
    elif any(term in rec_lower for term in ['sell', 'underperform']):
        color_class = "color-red"
        display_text = "Poco Interesante"
    elif 'hold' in rec_lower:
        color_class = "color-orange"
        display_text = "Neutral"
    return f'<div class="metric-container"><div class="metric-label">Recomendación Media</div><div class="metric-value {color_class}">{display_text}</div></div>'

def mostrar_metrica_blue_chip(label, current_value, historical_value, is_percent=False, lower_is_better=False):
    color_class = "color-orange" # Neutral/orange for equal values
    
    is_comparable = isinstance(current_value, (int, float)) and isinstance(historical_value, (int, float))

    if is_comparable:
        if lower_is_better:
            if current_value < historical_value: color_class = "color-green"
            elif current_value > historical_value: color_class = "color-red"
        else: # higher is better
            if current_value > historical_value: color_class = "color-green"
            elif current_value < historical_value: color_class = "color-red"

    if is_percent:
        formatted_current = f"{current_value:.2f}%" if isinstance(current_value, (int, float)) else "N/A"
        formatted_historical = f"vs {historical_value:.2f}%" if isinstance(historical_value, (int, float)) else ""
    else:
        formatted_current = f"{current_value:.2f}" if isinstance(current_value, (int, float)) else "N/A"
        formatted_historical = f"vs {historical_value:.2f}" if isinstance(historical_value, (int, float)) else ""

    st.markdown(f'''
    <div class="metric-container">
        <div class="metric-label">{label}</div>
        <div class="metric-value {color_class}">{formatted_current}</div>
        <div class="metric-label" style="line-height: 1; color: #FAFAFA;">{formatted_historical}</div>
    </div>
    ''', unsafe_allow_html=True)

def generar_leyenda_dinamica(datos, puntuaciones, sector_bench, justificaciones, tech_data):
    highlight_style = 'style="background-color: #FFFF00; color: #0E1117; padding: 2px 5px; border-radius: 3px;"'

    # --- Leyenda de Calidad ---
    roe = datos.get('roe', 0)
    l_roe_exc_raw = f"<strong>Excelente:</strong> > {sector_bench['roe_excelente']}%"
    l_roe_bueno_raw = f"<strong>Bueno:</strong> > {sector_bench['roe_bueno']}%"
    l_roe_alerta_raw = f"<strong>Alerta:</strong> < {sector_bench['roe_bueno']}%"
    
    l_roe_exc = f"<span {highlight_style}>{l_roe_exc_raw}</span>" if roe > sector_bench['roe_excelente'] else l_roe_exc_raw
    l_roe_bueno = f"<span {highlight_style}>{l_roe_bueno_raw}</span>" if sector_bench['roe_bueno'] < roe <= sector_bench['roe_excelente'] else l_roe_bueno_raw
    l_roe_alerta = f"<span {highlight_style}>{l_roe_alerta_raw}</span>" if roe <= sector_bench['roe_bueno'] else l_roe_alerta_raw

    margen_op = datos.get('margen_operativo', 0)
    l_mop_exc_raw = f"<strong>Excelente:</strong> > {sector_bench['margen_excelente']}%"
    l_mop_bueno_raw = f"<strong>Bueno:</strong> > {sector_bench['margen_bueno']}%"
    l_mop_alerta_raw = f"<strong>Alerta:</strong> < {sector_bench['margen_bueno']}%"
    l_mop_exc = f"<span {highlight_style}>{l_mop_exc_raw}</span>" if margen_op > sector_bench['margen_excelente'] else l_mop_exc_raw
    l_mop_bueno = f"<span {highlight_style}>{l_mop_bueno_raw}</span>" if sector_bench['margen_bueno'] < margen_op <= sector_bench['margen_excelente'] else l_mop_bueno_raw
    l_mop_alerta = f"<span {highlight_style}>{l_mop_alerta_raw}</span>" if margen_op <= sector_bench['margen_bueno'] else l_mop_alerta_raw
    
    margen_neto = datos.get('margen_beneficio', 0)
    l_mneto_exc_raw = f"<strong>Excelente:</strong> > {sector_bench['margen_neto_excelente']}%"
    l_mneto_bueno_raw = f"<strong>Bueno:</strong> > {sector_bench['margen_neto_bueno']}%"
    l_mneto_alerta_raw = f"<strong>Alerta:</strong> < {sector_bench['margen_neto_bueno']}%"
    l_mneto_exc = f"<span {highlight_style}>{l_mneto_exc_raw}</span>" if margen_neto > sector_bench['margen_neto_excelente'] else l_mneto_exc_raw
    l_mneto_bueno = f"<span {highlight_style}>{l_mneto_bueno_raw}</span>" if sector_bench['margen_neto_bueno'] < margen_neto <= sector_bench['margen_neto_excelente'] else l_mneto_bueno_raw
    l_mneto_alerta = f"<span {highlight_style}>{l_mneto_alerta_raw}</span>" if margen_neto <= sector_bench['margen_neto_bueno'] else l_mneto_alerta_raw

    rev_growth = datos.get('crecimiento_ingresos', 0)
    l_rev_exc_raw = f"<strong>Excelente:</strong> > {sector_bench['rev_growth_excelente']}%"
    l_rev_bueno_raw = f"<strong>Bueno:</strong> > {sector_bench['rev_growth_bueno']}%"
    l_rev_lento_raw = f"<strong>Lento/Negativo:</strong> < {sector_bench['rev_growth_bueno']}%"

    l_rev_exc = f"<span {highlight_style}>{l_rev_exc_raw}</span>" if rev_growth > sector_bench['rev_growth_excelente'] else l_rev_exc_raw
    l_rev_bueno = f"<span {highlight_style}>{l_rev_bueno_raw}</span>" if sector_bench['rev_growth_bueno'] < rev_growth <= sector_bench['rev_growth_excelente'] else l_rev_bueno_raw
    l_rev_lento = f"<span {highlight_style}>{l_rev_lento_raw}</span>" if rev_growth <= sector_bench['rev_growth_bueno'] else l_rev_lento_raw

    leyenda_calidad = f"""
    - **ROE (Return on Equity):** Mide la rentabilidad sobre el dinero de los accionistas. Para el sector **{datos['sector'].upper()}**, los rangos son:
        - {l_roe_exc}
        - {l_roe_bueno}
        - {l_roe_alerta}
    - **Margen Operativo:** Mide el beneficio de la actividad principal de la empresa, antes de impuestos e intereses.
        - {l_mop_exc}
        - {l_mop_bueno}
        - {l_mop_alerta}
    - **Margen Neto:** Mide el beneficio final que queda para el accionista después de todos los gastos, impuestos e intereses.
        - {l_mneto_exc}
        - {l_mneto_bueno}
        - {l_mneto_alerta}
    - **Crecimiento Ingresos (YoY):** Mide el crecimiento de las ventas año a año. Para el sector **{datos['sector'].upper()}**, los rangos son:
        - {l_rev_exc}
        - {l_rev_bueno}
        - {l_rev_lento}
    """

    # --- Leyenda de Salud Financiera (MEJORADA) ---
    deuda_ratio = datos.get('deuda_patrimonio')
    SECTORES_ALTA_DEUDA = ['Financial Services', 'Utilities', 'Communication Services', 'Real Estate']
    leyenda_deuda = ""
    if isinstance(deuda_ratio, (int, float)):
        if datos['sector'] in SECTORES_ALTA_DEUDA:
            l_deuda_man_raw = "<strong>Manejable:</strong> < 250"
            l_deuda_ele_raw = "<strong>Elevado:</strong> > 250"
            l_deuda_man = f"<span {highlight_style}>{l_deuda_man_raw}</span>" if deuda_ratio < 250 else l_deuda_man_raw
            l_deuda_ele = f"<span {highlight_style}>{l_deuda_ele_raw}</span>" if deuda_ratio >= 250 else l_deuda_ele_raw
            leyenda_deuda = f"""- **Deuda / Patrimonio:** Para el sector **{datos['sector'].upper()}**, que opera con alta deuda, los rangos son:
        - {l_deuda_man}
        - {l_deuda_ele}"""
        else:
            l_deuda_ideal_raw = "<strong>Ideal:</strong> < 40"
            l_deuda_man_raw = "<strong>Manejable:</strong> < 80"
            l_deuda_ele_raw = "<strong>Elevado:</strong> > 80"
            l_deuda_ideal = f"<span {highlight_style}>{l_deuda_ideal_raw}</span>" if deuda_ratio < 40 else l_deuda_ideal_raw
            l_deuda_man = f"<span {highlight_style}>{l_deuda_man_raw}</span>" if 40 <= deuda_ratio < 80 else l_deuda_man_raw
            l_deuda_ele = f"<span {highlight_style}>{l_deuda_ele_raw}</span>" if deuda_ratio >= 80 else l_deuda_ele_raw
            leyenda_deuda = f"""- **Deuda / Patrimonio:** Para el sector **{datos['sector'].upper()}**, los rangos son:
        - {l_deuda_ideal}
        - {l_deuda_man}
        - {l_deuda_ele}"""

    ratio_corriente = datos.get('ratio_corriente')
    leyenda_liquidez = ""
    if isinstance(ratio_corriente, (int, float)):
        l_liq_exc_raw = "<strong>Excelente:</strong> > 2.0"
        l_liq_sal_raw = "<strong>Saludable:</strong> > 1.5"
        l_liq_ace_raw = "<strong>Aceptable:</strong> > 1.0"
        l_liq_rie_raw = "<strong>Zona de Riesgo:</strong> < 1.0"
        l_liq_exc = f"<span {highlight_style}>{l_liq_exc_raw}</span>" if ratio_corriente > 2.0 else l_liq_exc_raw
        l_liq_sal = f"<span {highlight_style}>{l_liq_sal_raw}</span>" if 1.5 < ratio_corriente <= 2.0 else l_liq_sal_raw
        l_liq_ace = f"<span {highlight_style}>{l_liq_ace_raw}</span>" if 1.0 < ratio_corriente <= 1.5 else l_liq_ace_raw
        l_liq_rie = f"<span {highlight_style}>{l_liq_rie_raw}</span>" if ratio_corriente <= 1.0 else l_liq_rie_raw
        leyenda_liquidez = f"""- **Ratio Corriente (Liquidez):** Mide la capacidad de pagar deudas a corto plazo.
        - {l_liq_exc}
        - {l_liq_sal}
        - {l_liq_ace}
        - {l_liq_rie}"""
    
    # Lógica de resaltado para Interpretación Combinada
    is_high_debt_sector = datos['sector'] in SECTORES_ALTA_DEUDA
    baja_deuda = False
    alta_liquidez = False
    if isinstance(deuda_ratio, (int, float)):
        baja_deuda = (deuda_ratio < 250) if is_high_debt_sector else (deuda_ratio < 80)
    if isinstance(ratio_corriente, (int, float)):
        alta_liquidez = ratio_corriente > 1.5

    esc_baja_d_alta_l = baja_deuda and alta_liquidez
    esc_alta_d_alta_l = not baja_deuda and alta_liquidez
    esc_baja_d_baja_l = baja_deuda and not alta_liquidez
    esc_alta_d_baja_l = not baja_deuda and not alta_liquidez

    l_ic_1_raw = "<strong>Baja Deuda / Alta Liquidez:</strong> Fortaleza financiera. El mejor escenario."
    l_ic_2_raw = "<strong>Alta Deuda / Alta Liquidez:</strong> Puede pagar sus deudas, pero el apalancamiento es un riesgo a vigilar."
    l_ic_3_raw = "<strong>Baja Deuda / Baja Liquidez:</strong> Balance conservador, pero podría tener problemas de liquidez a corto plazo."
    l_ic_4_raw = "<strong>Alta Deuda / Baja Liquidez:</strong> El peor escenario. Riesgo de solvencia."

    l_ic_1 = f"<span {highlight_style}>{l_ic_1_raw}</span>" if esc_baja_d_alta_l else l_ic_1_raw
    l_ic_2 = f"<span {highlight_style}>{l_ic_2_raw}</span>" if esc_alta_d_alta_l else l_ic_2_raw
    l_ic_3 = f"<span {highlight_style}>{l_ic_3_raw}</span>" if esc_baja_d_baja_l else l_ic_3_raw
    l_ic_4 = f"<span {highlight_style}>{l_ic_4_raw}</span>" if esc_alta_d_baja_l else l_ic_4_raw

    leyenda_salud = f"""
    {leyenda_deuda}
    {leyenda_liquidez}
    - **Interpretación Combinada:**
        - {l_ic_1}
        - {l_ic_2}
        - {l_ic_3}
        - {l_ic_4}
    """

    # --- Leyenda de Valoración ---
    per = datos.get('per')
    p_fcf = datos.get('p_fcf')
    leyenda_per = ""
    leyenda_pfcf = ""

    if datos.get('sector') == 'Real Estate':
        leyenda_per = "- **PER (Price-to-Earnings):** No es la métrica principal para REITs. Se prefiere el P/FFO (usamos P/FCF como proxy)."
    elif isinstance(per, (int, float)):
        l_per_atr_raw = f"<strong>Atractivo:</strong> < {sector_bench['per_barato']}"
        l_per_jus_raw = f"<strong>Justo:</strong> {sector_bench['per_barato']} - {sector_bench['per_justo']}"
        l_per_car_raw = f"<strong>Caro:</strong> > {sector_bench['per_justo']}"
        l_per_atr = f"<span {highlight_style}>{l_per_atr_raw}</span>" if per < sector_bench['per_barato'] else l_per_atr_raw
        l_per_jus = f"<span {highlight_style}>{l_per_jus_raw}</span>" if sector_bench['per_barato'] <= per <= sector_bench['per_justo'] else l_per_jus_raw
        l_per_car = f"<span {highlight_style}>{l_per_car_raw}</span>" if per > sector_bench['per_justo'] else l_per_car_raw
        leyenda_per = f"""- **PER (Price-to-Earnings):** Mide cuántas veces pagas el beneficio anual. Para el sector **{datos['sector'].upper()}**, los rangos son:
        - {l_per_atr}
        - {l_per_jus}
        - {l_per_car}"""

    if isinstance(p_fcf, (int, float)):
        l_pfcf_atr_raw = "<strong>Atractivo:</strong> < 20"
        l_pfcf_jus_raw = "<strong>Justo:</strong> 20 - 30"
        l_pfcf_car_raw = "<strong>Caro:</strong> > 30"
        if datos.get('sector') == 'Real Estate':
            l_pfcf_atr_raw = "<strong>Atractivo (P/FFO):</strong> < 16"
            l_pfcf_jus_raw = "<strong>Justo (P/FFO):</strong> 16 - 22"
            l_pfcf_car_raw = "<strong>Caro (P/FFO):</strong> > 22"
            l_pfcf_atr = f"<span {highlight_style}>{l_pfcf_atr_raw}</span>" if p_fcf < 16 else l_pfcf_atr_raw
            l_pfcf_jus = f"<span {highlight_style}>{l_pfcf_jus_raw}</span>" if 16 <= p_fcf <= 22 else l_pfcf_jus_raw
            l_pfcf_car = f"<span {highlight_style}>{l_pfcf_car_raw}</span>" if p_fcf > 22 else l_pfcf_car_raw
        else:
            l_pfcf_atr = f"<span {highlight_style}>{l_pfcf_atr_raw}</span>" if p_fcf < 20 else l_pfcf_atr_raw
            l_pfcf_jus = f"<span {highlight_style}>{l_pfcf_jus_raw}</span>" if 20 <= p_fcf <= 30 else l_pfcf_jus_raw
            l_pfcf_car = f"<span {highlight_style}>{l_pfcf_car_raw}</span>" if p_fcf > 30 else l_pfcf_car_raw
        
        leyenda_pfcf = f"""- **P/FCF (Price-to-Free-Cash-Flow):** Similar al PER, pero usa el flujo de caja libre. Un valor **Negativo es una señal de alerta**.
        - {l_pfcf_atr}
        - {l_pfcf_jus}
        - {l_pfcf_car}"""

    pb = datos.get('p_b')
    leyenda_pb = ""
    if isinstance(pb, (int, float)):
        l_pb_atr_raw = f"<strong>Atractivo:</strong> < {sector_bench['pb_barato']}"
        l_pb_jus_raw = f"<strong>Justo:</strong> {sector_bench['pb_barato']} - {sector_bench['pb_justo']}"
        l_pb_car_raw = f"<strong>Caro:</strong> > {sector_bench['pb_justo']}"
        l_pb_atr = f"<span {highlight_style}>{l_pb_atr_raw}</span>" if pb < sector_bench['pb_barato'] else l_pb_atr_raw
        l_pb_jus = f"<span {highlight_style}>{l_pb_jus_raw}</span>" if sector_bench['pb_barato'] <= pb <= sector_bench['pb_justo'] else l_pb_jus_raw
        l_pb_car = f"<span {highlight_style}>{l_pb_car_raw}</span>" if pb > sector_bench['pb_justo'] else l_pb_car_raw
        leyenda_pb = f"""- **P/B (Price-to-Book):** Compara el precio con el valor contable. Es útil en sectores con activos tangibles (Banca, Industria, etc.). Para **{datos['sector'].upper()}**, los rangos son:
        - {l_pb_atr}
        - {l_pb_jus}
        - {l_pb_car}"""

    leyenda_valoracion = f"""
    {leyenda_per}
    - **PER Adelantado (Forward PE):** Usa beneficios futuros esperados. Si es inferior al PER actual, indica crecimiento y **otorga un bonus a la nota**.
    {leyenda_pfcf}
    {leyenda_pb}
    """

    # --- Leyenda de Dividendos (MEJORADA) ---
    yield_div = datos.get('yield_dividendo', 0)
    l_yield_exc_raw = "<strong>Excelente:</strong> > 3.5%"
    l_yield_bueno_raw = "<strong>Bueno:</strong> > 2.0%"
    l_yield_bajo_raw = "<strong>Bajo:</strong> < 2.0%"

    l_yield_exc = f"<span {highlight_style}>{l_yield_exc_raw}</span>" if yield_div > 3.5 else l_yield_exc_raw
    l_yield_bueno = f"<span {highlight_style}>{l_yield_bueno_raw}</span>" if 2.0 < yield_div <= 3.5 else l_yield_bueno_raw
    l_yield_bajo = f"<span {highlight_style}>{l_yield_bajo_raw}</span>" if yield_div <= 2.0 else l_yield_bajo_raw

    payout = datos.get('payout_ratio', 0)
    l_pay_sal_raw = f"<strong>Saludable:</strong> < {sector_bench['payout_bueno']}%"
    l_pay_pre_raw = f"<strong>Precaución:</strong> > {sector_bench['payout_bueno']}%"
    l_pay_pel_raw = f"<strong>Peligroso:</strong> > {sector_bench['payout_aceptable']}%"
    l_pay_sal = f"<span {highlight_style}>{l_pay_sal_raw}</span>" if 0 < payout < sector_bench['payout_bueno'] else l_pay_sal_raw
    l_pay_pre = f"<span {highlight_style}>{l_pay_pre_raw}</span>" if sector_bench['payout_bueno'] <= payout < sector_bench['payout_aceptable'] else l_pay_pre_raw
    l_pay_pel = f"<span {highlight_style}>{l_pay_pel_raw}</span>" if payout >= sector_bench['payout_aceptable'] else l_pay_pel_raw

    SECTORES_ALTO_PAYOUT = ['Utilities', 'Real Estate', 'Financial Services', 'Consumer Staples', 'Communication Services']
    if datos['sector'] in SECTORES_ALTO_PAYOUT:
        leyenda_payout_intro = f"Indica qué % del beneficio se destina a dividendos. Para el sector **{datos['sector'].upper()}**, que tiene flujos de caja estables o una estructura de reparto especial (ej. REITs), se aceptan ratios más altos:"
    else:
        leyenda_payout_intro = f"Indica qué % del beneficio se destina a dividendos. Para el sector **{datos['sector'].upper()}**, los rangos son:"

    # --- CORRECCIÓN DEL ERROR ---
    # Se asegura de que 'blue_chip_analysis' sea un diccionario antes de intentar acceder a sus claves.
    # Esto evita el error 'NoneType' si los datos históricos no están disponibles.
    blue_chip_analysis_data = justificaciones.get('blue_chip_analysis') or {}
    blue_chip_status = blue_chip_analysis_data.get('label', '')
    
    l_bc_muy_int_raw = "<strong>🟢 Muy Interesante:</strong> PER actual < 80% del histórico Y Yield actual > 120% del histórico."
    l_bc_int_raw = "<strong>🟡 Interesante:</strong> PER actual < histórico Y Yield actual > histórico."
    l_bc_mixta_raw = "<strong>🔵 Señal Mixta:</strong> Solo una de las dos condiciones anteriores se cumple."
    l_bc_neutral_raw = "<strong>⚪ Neutral:</strong> Ninguna de las condiciones anteriores se cumple."

    l_bc_muy_int = f"<span {highlight_style}>{l_bc_muy_int_raw}</span>" if "Muy Interesante" in blue_chip_status else l_bc_muy_int_raw
    l_bc_int = f"<span {highlight_style}>{l_bc_int_raw}</span>" if "Interesante" in blue_chip_status and "Muy" not in blue_chip_status else l_bc_int_raw
    l_bc_mixta = f"<span {highlight_style}>{l_bc_mixta_raw}</span>" if "Mixta" in blue_chip_status else l_bc_mixta_raw
    l_bc_neutral = f"<span {highlight_style}>{l_bc_neutral_raw}</span>" if not blue_chip_status or "Neutral" in blue_chip_status else l_bc_neutral_raw

    leyenda_dividendos = f"""
    - **Rentabilidad (Yield):** Es el porcentaje que recibes anualmente en dividendos sobre el precio de la acción.
        - {l_yield_exc}
        - {l_yield_bueno}
        - {l_yield_bajo}
    - **Ratio de Reparto (Payout):** {leyenda_payout_intro}
        - {l_pay_sal}
        - {l_pay_pre}
        - {l_pay_pel}
    - **Análisis de Valor 'Blue Chip':** Compara la valoración actual con su media histórica para detectar oportunidades.
        - {l_bc_muy_int}
        - {l_bc_int}
        - {l_bc_mixta}
        - {l_bc_neutral}
    """
    
    leyenda_tecnico = ""
    if tech_data is not None and not tech_data.empty:
        last_price = tech_data['Close'].iloc[-1]
        sma200 = tech_data['SMA200'].iloc[-1]
        rsi = tech_data['RSI'].iloc[-1]

        tendencia_alcista = last_price > sma200
        tendencia_bajista = last_price < sma200
        
        l_sma_alcista_raw = "<strong>Señal Alcista 🟢:</strong> El precio está <strong>por encima</strong> de la SMA200."
        l_sma_bajista_raw = "<strong>Señal Bajista 🔴:</strong> El precio está <strong>por debajo</strong> de la SMA200."
        
        l_sma_alcista = f"<span {highlight_style}>{l_sma_alcista_raw}</span>" if tendencia_alcista else l_sma_alcista_raw
        l_sma_bajista = f"<span {highlight_style}>{l_sma_bajista_raw}</span>" if tendencia_bajista else l_sma_bajista_raw

        rsi_sobreventa = rsi < 30
        rsi_neutral = 30 <= rsi <= 70
        rsi_sobrecompra = rsi > 70

        l_rsi_sobreventa_raw = "<strong>Sobreventa (< 30) 🟢:</strong> Potencial señal de compra."
        l_rsi_neutral_raw = "<strong>Neutral (30 - 70) 🟠:</strong> Sin señal clara."
        l_rsi_sobrecompra_raw = "<strong>Sobrecompra (> 70) 🔴:</strong> Potencial señal de venta."

        l_rsi_sobreventa = f"<span {highlight_style}>{l_rsi_sobreventa_raw}</span>" if rsi_sobreventa else l_rsi_sobreventa_raw
        l_rsi_neutral = f"<span {highlight_style}>{l_rsi_neutral_raw}</span>" if rsi_neutral else l_rsi_neutral_raw
        l_rsi_sobrecompra = f"<span {highlight_style}>{l_rsi_sobrecompra_raw}</span>" if rsi_sobrecompra else l_rsi_sobrecompra_raw

        escenario_1 = tendencia_alcista and rsi_sobreventa
        escenario_2 = tendencia_alcista and rsi_neutral
        escenario_3 = tendencia_alcista and rsi_sobrecompra
        escenario_4 = tendencia_bajista and rsi_sobreventa
        escenario_5 = tendencia_bajista and rsi_neutral
        escenario_6 = tendencia_bajista and rsi_sobrecompra

        l_esc_1_raw = "<strong>🟢+🟢 Oportunidad de Compra Óptima:</strong> Tendencia alcista con retroceso (RSI en sobreventa)."
        l_esc_2_raw = "<strong>🟢+🟠 Continuación Alcista:</strong> Tendencia alcista con RSI neutral. Esperar retroceso para comprar."
        l_esc_3_raw = "<strong>🟢+🔴 Riesgo de Corrección:</strong> Tendencia alcista pero con RSI sobrecomprado. Posible recogida de beneficios."
        l_esc_4_raw = "<strong>🔴+🟢 Posible Rebote (Contra Tendencia):</strong> Tendencia bajista con RSI en sobreventa. Alto riesgo."
        l_esc_5_raw = "<strong>🔴+🟠 Continuación Bajista:</strong> Tendencia bajista con RSI neutral. Evitar compras."
        l_esc_6_raw = "<strong>🔴+🔴 Oportunidad de Venta Óptima:</strong> Tendencia bajista con rebote (RSI en sobrecompra)."

        l_esc_1 = f"<span {highlight_style}>{l_esc_1_raw}</span>" if escenario_1 else l_esc_1_raw
        l_esc_2 = f"<span {highlight_style}>{l_esc_2_raw}</span>" if escenario_2 else l_esc_2_raw
        l_esc_3 = f"<span {highlight_style}>{l_esc_3_raw}</span>" if escenario_3 else l_esc_3_raw
        l_esc_4 = f"<span {highlight_style}>{l_esc_4_raw}</span>" if escenario_4 else l_esc_4_raw
        l_esc_5 = f"<span {highlight_style}>{l_esc_5_raw}</span>" if escenario_5 else l_esc_5_raw
        l_esc_6 = f"<span {highlight_style}>{l_esc_6_raw}</span>" if escenario_6 else l_esc_6_raw

        leyenda_tecnico = f"""
        - **Medias Móviles (SMA):** Suavizan el precio para mostrar la tendencia. El número (50 o 200) se refiere a los **últimos días de cotización** (sesiones) que usa para calcular la media.
            - **SMA50 (naranja):** Media de los últimos 50 días. Refleja la tendencia a corto/medio plazo.
            - **SMA200 (roja):** Media de los últimos 200 días. Es el indicador más importante para la tendencia a largo plazo.
            - {l_sma_alcista}
            - {l_sma_bajista}
        - **RSI (Índice de Fuerza Relativa):** Es un **oscilador de momentum** que mide la velocidad y la fuerza de los cambios en el precio. Su utilidad principal es detectar condiciones de **sobrecompra** (el precio ha subido mucho y rápido, posible corrección) o **sobreventa** (el precio ha caído mucho y rápido, posible rebote).
            - {l_rsi_sobreventa}
            - {l_rsi_neutral}
            - {l_rsi_sobrecompra}
        - **Estrategia Combinada:**
            - {l_esc_1}
            - {l_esc_2}
            - {l_esc_3}
            - {l_esc_4}
            - {l_esc_5}
            - {l_esc_6}
        """
    
    # --- Leyenda de Márgenes de Seguridad ---
    ms_analistas = puntuaciones.get('margen_seguridad_analistas', 0)
    ms_per = puntuaciones.get('margen_seguridad_per', 0)
    ms_yield = puntuaciones.get('margen_seguridad_yield', 0)

    l_ms_alto_raw = "<strong>Alto Potencial:</strong> > 20%"
    l_ms_mod_raw = "<strong>Potencial Moderado:</strong> 0% a 20%"
    l_ms_riesgo_raw = "<strong>Riesgo de Caída:</strong> < 0%"

    # Analistas
    l_ms_a_alto = f"<span {highlight_style}>{l_ms_alto_raw}</span>" if ms_analistas > 20 else l_ms_alto_raw
    l_ms_a_mod = f"<span {highlight_style}>{l_ms_mod_raw}</span>" if 0 <= ms_analistas <= 20 else l_ms_mod_raw
    l_ms_a_riesgo = f"<span {highlight_style}>{l_ms_riesgo_raw}</span>" if ms_analistas < 0 else l_ms_riesgo_raw

    # PER
    l_ms_p_alto = f"<span {highlight_style}>{l_ms_alto_raw}</span>" if ms_per > 20 else l_ms_alto_raw
    l_ms_p_mod = f"<span {highlight_style}>{l_ms_mod_raw}</span>" if 0 <= ms_per <= 20 else l_ms_mod_raw
    l_ms_p_riesgo = f"<span {highlight_style}>{l_ms_riesgo_raw}</span>" if ms_per < 0 else l_ms_riesgo_raw

    # Yield
    l_ms_y_alto = f"<span {highlight_style}>{l_ms_alto_raw}</span>" if ms_yield > 20 else l_ms_alto_raw
    l_ms_y_mod = f"<span {highlight_style}>{l_ms_mod_raw}</span>" if 0 <= ms_yield <= 20 else l_ms_mod_raw
    l_ms_y_riesgo = f"<span {highlight_style}>{l_ms_riesgo_raw}</span>" if ms_yield < 0 else l_ms_riesgo_raw

    leyenda_margen_seguridad = f"""
    - **Según Analistas:** Potencial hasta el precio objetivo medio.
        - {l_ms_a_alto}
        - {l_ms_a_mod}
        - {l_ms_a_riesgo}
    - **Según su PER Histórico:** Potencial si el PER actual vuelve a su media.
        - {l_ms_p_alto}
        - {l_ms_p_mod}
        - {l_ms_p_riesgo}
    - **Según su Yield Histórico:** Potencial si el Yield actual vuelve a su media.
        - {l_ms_y_alto}
        - {l_ms_y_mod}
        - {l_ms_y_riesgo}
    """

    return {
        'calidad': leyenda_calidad,
        'salud': leyenda_salud,
        'valoracion': leyenda_valoracion,
        'dividendos': leyenda_dividendos,
        'tecnico': leyenda_tecnico,
        'margen_seguridad': leyenda_margen_seguridad
    }


# --- ESTRUCTURA DE LA APLICACIÓN WEB ---
st.title('El Analizador de Acciones de Sr. Outfit')
st.caption("Herramienta de análisis. Esto no es una recomendación de compra o venta. Realiza tu propio juicio y análisis antes de invertir.")

ticker_input = st.text_input("Introduce el Ticker de la Acción a Analizar (ej. JNJ, MSFT, BABA)", "AAPL").upper()

if st.button('Analizar Acción'):
    with st.spinner('Realizando análisis profesional...'):
        try:
            datos = obtener_datos_completos(ticker_input)
            
            if not datos:
                st.error(f"Error: No se pudo encontrar el ticker '{ticker_input}'. Verifica que sea correcto.")
            else:
                hist_data = obtener_datos_historicos_y_tecnicos(ticker_input)
                
                if not hist_data:
                    st.error(f"No se pudieron obtener datos históricos para '{ticker_input}'. El análisis no puede continuar.")
                else:
                    puntuaciones, justificaciones, benchmarks = calcular_puntuaciones_y_justificaciones(datos, hist_data)
                    sector_bench = benchmarks.get(datos['sector'], benchmarks['Default'])
                    
                    tech_data = hist_data.get('tech_data')
                    leyendas = generar_leyenda_dinamica(datos, puntuaciones, sector_bench, justificaciones, tech_data)
                    
                    pesos = {'calidad': 0.4, 'valoracion': 0.3, 'salud': 0.2, 'dividendos': 0.1}
                    nota_ponderada = sum(puntuaciones.get(k, 0) * v for k, v in pesos.items())
                    nota_final = max(0, nota_ponderada - puntuaciones['penalizador_geo'])

                    st.header(f"Análisis Fundamental: {datos['nombre']} ({ticker_input})")
                    
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
                        
                        if datos['pais'] in ['China', 'Hong Kong']:
                            st.warning("⚠️ **Riesgo Regulatorio (ADR/VIE):** Invertir en empresas chinas a través de ADRs conlleva riesgos adicionales relacionados con la estructura legal (VIE) y posibles cambios regulatorios del gobierno chino que podrían afectar el valor de la inversión.")

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
                                mostrar_metrica_con_color("📈 ROE", datos['roe'], sector_bench['roe_excelente'], sector_bench['roe_bueno'], is_percent=True)
                                mostrar_metrica_con_color("💰 Margen Neto", datos['margen_beneficio'], sector_bench['margen_neto_excelente'], sector_bench['margen_neto_bueno'], is_percent=True)
                            with c2:
                                mostrar_metrica_con_color("📊 Margen Operativo", datos['margen_operativo'], sector_bench['margen_excelente'], sector_bench['margen_bueno'], is_percent=True)
                                mostrar_metrica_con_color("🚀 Crec. Ingresos (YoY)", datos['crecimiento_ingresos'], sector_bench['rev_growth_excelente'], sector_bench['rev_growth_bueno'], is_percent=True)
                            with st.expander("Ver Leyenda Detallada"):
                                st.markdown(leyendas['calidad'], unsafe_allow_html=True)
                    with col2:
                        with st.container(border=True):
                            st.subheader(f"Salud Financiera [{puntuaciones['salud']}/10]")
                            st.caption(justificaciones['salud'])
                            
                            SECTORES_ALTA_DEUDA = ['Financial Services', 'Utilities', 'Communication Services', 'Real Estate']
                            if datos['sector'] in SECTORES_ALTA_DEUDA:
                                deuda_umbral_bueno = 150
                                deuda_umbral_malo = 250
                            else:
                                deuda_umbral_bueno = 40
                                deuda_umbral_malo = 80
                            
                            s1, s2 = st.columns(2)
                            with s1: 
                                mostrar_metrica_con_color("🏦 Deuda / Patrimonio", datos['deuda_patrimonio'], deuda_umbral_bueno, deuda_umbral_malo, lower_is_better=True)
                            with s2: 
                                mostrar_metrica_con_color("💧 Ratio Corriente (Liquidez)", datos['ratio_corriente'], 1.5, 1.0)
                            with st.expander("Ver Leyenda Detallada"):
                                st.markdown(leyendas['salud'], unsafe_allow_html=True)

                    with st.container(border=True):
                        st.subheader(f"Análisis de Valoración [{puntuaciones['valoracion']:.1f}/10]")
                        st.caption(justificaciones['valoracion'])
                        
                        tab1, tab2 = st.tabs(["Múltiplos Actuales", "Análisis Histórico"])
                        
                        with tab1:
                            val1, val2 = st.columns(2)
                            with val1:
                                mostrar_metrica_con_color("⚖️ PER", datos['per'], sector_bench['per_barato'], sector_bench['per_justo'], lower_is_better=True)
                                mostrar_metrica_con_color("🔮 PER Adelantado", datos.get('per_adelantado'), datos.get('per'), lower_is_better=True)
                            with val2:
                                mostrar_metrica_con_color("📚 P/B (Precio/Libros)", datos['p_b'], sector_bench['pb_barato'], sector_bench['pb_justo'], lower_is_better=True)
                                raw_fcf = datos.get('raw_fcf')
                                if raw_fcf is not None and raw_fcf < 0:
                                    st.markdown('<div class="metric-container"><div class="metric-label">🌊 P/FCF</div><div class="metric-value color-red">Negativo</div></div>', unsafe_allow_html=True)
                                else:
                                    mostrar_metrica_con_color("🌊 P/FCF", datos['p_fcf'], 20, 30, lower_is_better=True)

                        with tab2:
                            h1, h2 = st.columns(2)
                            with h1:
                                mostrar_metrica_informativa("🕰️ PER Medio (Histórico)", hist_data.get('per_hist'))
                            with h2:
                                mostrar_metrica_informativa("🌊 P/FCF Medio (Histórico)", hist_data.get('pfcf_hist'))

                        with st.expander("Ver Leyenda Detallada"):
                            st.markdown(leyendas['valoracion'], unsafe_allow_html=True)
                    
                    if datos['yield_dividendo'] > 0:
                        with st.container(border=True):
                            st.subheader(f"Dividendos [{puntuaciones['dividendos']}/10]")
                            st.caption(justificaciones['dividendos'])
                            
                            blue_chip_analysis = justificaciones.get('blue_chip_analysis')
                            if blue_chip_analysis:
                                st.markdown("---")
                                st.markdown(f"#### Análisis de Valor 'Blue Chip': **{blue_chip_analysis['label']}**")
                                bc1, bc2 = st.columns(2)
                                with bc1:
                                    mostrar_metrica_blue_chip("Yield Actual vs Histórico", datos.get('yield_dividendo'), hist_data.get('yield_hist'), is_percent=True, lower_is_better=False)
                                with bc2:
                                    mostrar_metrica_blue_chip("PER Actual vs Histórico", datos.get('per'), hist_data.get('per_hist'), is_percent=False, lower_is_better=True)
                                st.caption(blue_chip_analysis['description'])
                            
                            st.markdown("---")
                            div1, div2 = st.columns(2)
                            with div1: 
                                mostrar_metrica_con_color("💸 Rentabilidad (Yield)", datos['yield_dividendo'], 3.5, 2.0, is_percent=True)
                                mostrar_metrica_con_color("🤲 Ratio de Reparto (Payout)", datos['payout_ratio'], sector_bench['payout_bueno'], sector_bench['payout_aceptable'], lower_is_better=True, is_percent=True)
                            with div2:
                                mostrar_metrica_informativa("📈 Yield Medio (Histórico)", hist_data.get('yield_hist'), is_percent=True)
                            
                            with st.expander("Ver Leyenda Detallada"):
                                st.markdown(leyendas['dividendos'], unsafe_allow_html=True)
                    
                    with st.container(border=True):
                        st.subheader("Potencial de Revalorización (Márgenes de Seguridad)")
                        ms1, ms2, ms3 = st.columns(3)
                        with ms1:
                            mostrar_margen_seguridad("🛡️ Según Analistas", puntuaciones['margen_seguridad_analistas'])
                        with ms2:
                            mostrar_margen_seguridad("📈 Según su PER Histórico", puntuaciones['margen_seguridad_per'])
                        with ms3:
                            mostrar_margen_seguridad("💸 Según su Yield Histórico", puntuaciones['margen_seguridad_yield'])
                        
                        with st.expander("Ver Leyenda Detallada"):
                            st.markdown(leyendas['margen_seguridad'], unsafe_allow_html=True)

                    # --- NUEVA ESTRUCTURA DE DISEÑO ---
                    st.header("Análisis Gráfico y Técnico")
                    
                    col_fin, col_flags = st.columns([2, 1]) # Columna para gráficos financieros y banderas rojas
                    
                    with col_fin:
                        st.subheader("Evolución Financiera")
                        financials_hist = hist_data.get('financials_charts')
                        dividends_hist = hist_data.get('dividends_charts')
                        fig_financieros = crear_graficos_financieros(ticker_input, financials_hist, dividends_hist)
                        if fig_financieros:
                            st.pyplot(fig_financieros)
                        else:
                            st.warning("No se pudieron generar los gráficos financieros históricos.")
                    
                    with col_flags:
                        st.subheader("Banderas Rojas")
                        banderas = analizar_banderas_rojas(datos, financials_hist)
                        if banderas:
                            for bandera in banderas: 
                                st.warning(bandera)
                        else:
                            st.success("✅ No se han detectado banderas rojas significativas.")

                    col_tech, col_tech_legend = st.columns(2) # Columna para gráfico técnico y su leyenda

                    with col_tech:
                        st.subheader("Análisis Técnico")
                        if tech_data is not None and not tech_data.empty:
                            fig_tecnico = crear_grafico_tecnico(tech_data)
                            st.pyplot(fig_tecnico)
                            
                            last_price = tech_data['Close'].iloc[-1]
                            sma50 = tech_data['SMA50'].iloc[-1]
                            sma200 = tech_data['SMA200'].iloc[-1]
                            rsi = tech_data['RSI'].iloc[-1]
                            
                            tendencia_texto = "Lateral 🟠"
                            tendencia_color = "color-orange"
                            if last_price > sma50 and sma50 > sma200:
                                tendencia_texto = "Alcista Fuerte 🟢"
                                tendencia_color = "color-green"
                            elif last_price > sma200:
                                tendencia_texto = "Alcista 🟢"
                                tendencia_color = "color-green"
                            elif last_price < sma50 and sma50 < sma200:
                                tendencia_texto = "Bajista Fuerte 🔴"
                                tendencia_color = "color-red"
                            elif last_price < sma200:
                                tendencia_texto = "Bajista 🔴"
                                tendencia_color = "color-red"

                            st.markdown(f'<div class="metric-container"><div class="metric-label">Tendencia Actual</div><div class="metric-value {tendencia_color}">{tendencia_texto}</div></div>', unsafe_allow_html=True)

                            rsi_texto = f"{rsi:.2f} (Neutral 🟠)"
                            rsi_color = "color-orange"
                            if rsi > 70:
                                rsi_texto = f"{rsi:.2f} (Sobrecompra 🔴)"
                                rsi_color = "color-red"
                            elif rsi < 30:
                                rsi_texto = f"{rsi:.2f} (Sobreventa 🟢)"
                                rsi_color = "color-green"

                            st.markdown(f'<div class="metric-container"><div class="metric-label">Estado RSI</div><div class="metric-value {rsi_color}">{rsi_texto}</div></div>', unsafe_allow_html=True)
                        else:
                            st.warning("No se pudieron generar los datos para el análisis técnico.")
                    
                    with col_tech_legend:
                        st.subheader("Interpretación Técnica")
                        st.markdown(leyendas['tecnico'], unsafe_allow_html=True)

        except TypeError as e:
            st.error(f"Error al procesar los datos para '{ticker_input}'. Es posible que los datos de Yahoo Finance para este ticker estén incompletos o no disponibles temporalmente.")
            st.error(f"Detalle técnico: {e}")
        except Exception as e:
            st.error("El Analizador de Acciones de Sr. Outfit ha encontrado un problema. Por favor, inténtalo de nuevo más tarde.")
            st.error(f"Detalle técnico: {e}")
