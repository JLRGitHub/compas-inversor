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
    'Information Technology': {'roic_excelente': 20, 'roic_bueno': 15, 'conversion_caja_excelente': 100, 'conversion_caja_bueno': 80, 'deuda_ebitda_bueno': 2, 'deuda_ebitda_precaucion': 3, 'cobertura_intereses_excelente': 10, 'cobertura_intereses_bueno': 6, 'margen_excelente': 25, 'margen_bueno': 18, 'per_barato': 25, 'per_justo': 35, 'pb_barato': 4, 'pb_justo': 8, 'payout_bueno': 60, 'payout_aceptable': 80, 'rev_growth_excelente': 15, 'rev_growth_bueno': 10},
    'Health Care': {'roic_excelente': 15, 'roic_bueno': 12, 'conversion_caja_excelente': 90, 'conversion_caja_bueno': 70, 'deuda_ebitda_bueno': 3, 'deuda_ebitda_precaucion': 4, 'cobertura_intereses_excelente': 8, 'cobertura_intereses_bueno': 5, 'margen_excelente': 20, 'margen_bueno': 15, 'per_barato': 20, 'per_justo': 30, 'pb_barato': 3, 'pb_justo': 5, 'payout_bueno': 60, 'payout_aceptable': 80, 'rev_growth_excelente': 10, 'rev_growth_bueno': 6},
    'Financial Services': {'roic_excelente': 10, 'roic_bueno': 8, 'conversion_caja_excelente': 0, 'conversion_caja_bueno': 0, 'deuda_ebitda_bueno': 0, 'deuda_ebitda_precaucion': 0, 'cobertura_intereses_excelente': 0, 'cobertura_intereses_bueno': 0, 'margen_excelente': 15, 'margen_bueno': 10, 'per_barato': 12, 'per_justo': 18, 'pb_barato': 1, 'pb_justo': 1.5, 'payout_bueno': 70, 'payout_aceptable': 90, 'rev_growth_excelente': 8, 'rev_growth_bueno': 4},
    'Industrials': {'roic_excelente': 12, 'roic_bueno': 9, 'conversion_caja_excelente': 90, 'conversion_caja_bueno': 70, 'deuda_ebitda_bueno': 3, 'deuda_ebitda_precaucion': 4.5, 'cobertura_intereses_excelente': 7, 'cobertura_intereses_bueno': 4, 'margen_excelente': 15, 'margen_bueno': 10, 'per_barato': 20, 'per_justo': 25, 'pb_barato': 2.5, 'pb_justo': 4, 'payout_bueno': 60, 'payout_aceptable': 80, 'rev_growth_excelente': 10, 'rev_growth_bueno': 5},
    'Utilities': {'roic_excelente': 7, 'roic_bueno': 5, 'conversion_caja_excelente': 70, 'conversion_caja_bueno': 50, 'deuda_ebitda_bueno': 4, 'deuda_ebitda_precaucion': 6, 'cobertura_intereses_excelente': 4, 'cobertura_intereses_bueno': 2, 'margen_excelente': 15, 'margen_bueno': 12, 'per_barato': 18, 'per_justo': 22, 'pb_barato': 1.5, 'pb_justo': 2, 'payout_bueno': 80, 'payout_aceptable': 95, 'rev_growth_excelente': 5, 'rev_growth_bueno': 3},
    'Consumer Discretionary': {'roic_excelente': 15, 'roic_bueno': 12, 'conversion_caja_excelente': 90, 'conversion_caja_bueno': 70, 'deuda_ebitda_bueno': 3.5, 'deuda_ebitda_precaucion': 5, 'cobertura_intereses_excelente': 7, 'cobertura_intereses_bueno': 4, 'margen_excelente': 12, 'margen_bueno': 8, 'per_barato': 20, 'per_justo': 28, 'pb_barato': 3, 'pb_justo': 5, 'payout_bueno': 60, 'payout_aceptable': 80, 'rev_growth_excelente': 12, 'rev_growth_bueno': 7},
    'Consumer Staples': {'roic_excelente': 18, 'roic_bueno': 13, 'conversion_caja_excelente': 100, 'conversion_caja_bueno': 80, 'deuda_ebitda_bueno': 3.5, 'deuda_ebitda_precaucion': 5, 'cobertura_intereses_excelente': 8, 'cobertura_intereses_bueno': 5, 'margen_excelente': 15, 'margen_bueno': 10, 'per_barato': 20, 'per_justo': 25, 'pb_barato': 4, 'pb_justo': 6, 'payout_bueno': 70, 'payout_aceptable': 85, 'rev_growth_excelente': 7, 'rev_growth_bueno': 4},
    'Energy': {'roic_excelente': 12, 'roic_bueno': 8, 'conversion_caja_excelente': 100, 'conversion_caja_bueno': 70, 'deuda_ebitda_bueno': 2.5, 'deuda_ebitda_precaucion': 4, 'cobertura_intereses_excelente': 8, 'cobertura_intereses_bueno': 5, 'margen_excelente': 10, 'margen_bueno': 7, 'per_barato': 15, 'per_justo': 20, 'pb_barato': 1.5, 'pb_justo': 2.5, 'payout_bueno': 60, 'payout_aceptable': 80, 'rev_growth_excelente': 8, 'rev_growth_bueno': 0},
    'Materials': {'roic_excelente': 12, 'roic_bueno': 9, 'conversion_caja_excelente': 80, 'conversion_caja_bueno': 60, 'deuda_ebitda_bueno': 3, 'deuda_ebitda_precaucion': 4.5, 'cobertura_intereses_excelente': 7, 'cobertura_intereses_bueno': 4, 'margen_excelente': 12, 'margen_bueno': 8, 'per_barato': 18, 'per_justo': 25, 'pb_barato': 2, 'pb_justo': 3, 'payout_bueno': 60, 'payout_aceptable': 80, 'rev_growth_excelente': 10, 'rev_growth_bueno': 5},
    'Real Estate': {'roic_excelente': 6, 'roic_bueno': 4, 'conversion_caja_excelente': 0, 'conversion_caja_bueno': 0, 'deuda_ebitda_bueno': 6, 'deuda_ebitda_precaucion': 8, 'cobertura_intereses_excelente': 3, 'cobertura_intereses_bueno': 1.5, 'margen_excelente': 20, 'margen_bueno': 15, 'per_barato': 25, 'per_justo': 35, 'pb_barato': 2, 'pb_justo': 3, 'payout_bueno': 90, 'payout_aceptable': 100, 'rev_growth_excelente': 8, 'rev_growth_bueno': 4},
    'Communication Services': {'roic_excelente': 14, 'roic_bueno': 10, 'conversion_caja_excelente': 90, 'conversion_caja_bueno': 70, 'deuda_ebitda_bueno': 3, 'deuda_ebitda_precaucion': 4.5, 'cobertura_intereses_excelente': 6, 'cobertura_intereses_bueno': 4, 'margen_excelente': 18, 'margen_bueno': 12, 'per_barato': 22, 'per_justo': 30, 'pb_barato': 3, 'pb_justo': 5, 'payout_bueno': 60, 'payout_aceptable': 80, 'rev_growth_excelente': 12, 'rev_growth_bueno': 7},
    'Default': {'roic_excelente': 12, 'roic_bueno': 10, 'conversion_caja_excelente': 80, 'conversion_caja_bueno': 60, 'deuda_ebitda_bueno': 3, 'deuda_ebitda_precaucion': 5, 'cobertura_intereses_excelente': 6, 'cobertura_intereses_bueno': 4, 'margen_excelente': 15, 'margen_bueno': 10, 'per_barato': 20, 'per_justo': 25, 'pb_barato': 2, 'pb_justo': 4, 'payout_bueno': 60, 'payout_aceptable': 80, 'rev_growth_excelente': 10, 'rev_growth_bueno': 5}
}

# --- BLOQUE 1: OBTENCIÓN DE DATOS ---
@st.cache_data(ttl=900)
def obtener_datos_completos(ticker):
    stock = yf.Ticker(ticker)
    info = stock.info
    if not info or info.get('longName') is None:
        return None
    
    # Datos básicos
    roe = info.get('returnOnEquity')
    op_margin = info.get('operatingMargins')
    payout = info.get('payoutRatio')
    dividend_rate = info.get('dividendRate')
    precio = info.get('currentPrice')
    market_cap = info.get('marketCap')
    free_cash_flow = info.get('freeCashflow')
    net_income = info.get('netIncomeToCommon')
    
    # Cálculos derivados
    div_yield = (dividend_rate / precio) if dividend_rate and precio and precio > 0 else 0
        
    if payout is not None and (payout > 1.5 or payout < 0):
        trailing_eps = info.get('trailingEps')
        if trailing_eps and dividend_rate and trailing_eps > 0:
            payout = dividend_rate / trailing_eps
        else:
            payout = None
    
    p_fcf = (market_cap / free_cash_flow) if market_cap and free_cash_flow and free_cash_flow > 0 else None

    # --- NUEVOS DATOS ---
    ebit = info.get('ebit')
    total_debt = info.get('totalDebt')
    total_equity = info.get('totalStockholderEquity')
    tax_rate = info.get('effectiveTaxRate')
    interest_expense = info.get('interestExpense')
    net_debt = info.get('netDebt')
    ebitda = info.get('ebitda')
    
    # ROIC
    roic = None
    if ebit and total_debt and total_equity and tax_rate:
        invested_capital = total_debt + total_equity
        if invested_capital > 0:
            nopat = ebit * (1 - tax_rate)
            roic = (nopat / invested_capital) * 100

    # Cobertura de Intereses
    interest_coverage = None
    if ebit and interest_expense and interest_expense != 0:
        interest_coverage = abs(ebit / interest_expense)

    # Deuda Neta / EBITDA
    deuda_ebitda = (net_debt / ebitda) if net_debt and ebitda and ebitda > 0 else None

    # Conversión de Caja
    cash_conversion = (free_cash_flow / net_income * 100) if free_cash_flow and net_income and net_income > 0 else 0

    # Rentabilidad por Recompra
    buybacks = None
    try:
        cashflow_df = stock.cashflow
        if not cashflow_df.empty and 'Repurchase Of Stock' in cashflow_df.index:
            buybacks = cashflow_df.loc['Repurchase Of Stock'].iloc[0] * -1 # Es un valor negativo
    except Exception:
        buybacks = None # Si falla, lo dejamos como None

    buyback_yield = (buybacks / market_cap * 100) if buybacks and market_cap else 0

    descripcion_completa = info.get('longBusinessSummary', 'No disponible.')
    descripcion_corta = 'No disponible.'
    if descripcion_completa and descripcion_completa != 'No disponible.':
        primer_punto = descripcion_completa.find('.')
        if primer_punto != -1:
            descripcion_corta = descripcion_completa[:primer_punto + 1]
        else:
            descripcion_corta = descripcion_completa
            
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
        "raw_fcf": free_cash_flow,
        "p_b": info.get('priceToBook'),
        "crecimiento_ingresos": info.get('revenueGrowth', 0) * 100,
        "yield_dividendo": div_yield * 100 if div_yield is not None else 0,
        "payout_ratio": payout * 100 if payout is not None else 0,
        "recomendacion_analistas": info.get('recommendationKey', 'N/A'),
        "precio_objetivo": info.get('targetMeanPrice'), "precio_actual": info.get('currentPrice'),
        "bpa": info.get('trailingEps'),
        "crecimiento_beneficios": info.get('earningsGrowth'),
        "dividendo_por_accion": info.get('dividendRate'),
        "deuda_ebitda": deuda_ebitda,
        "roic": roic,
        "cobertura_intereses": interest_coverage,
        "conversion_caja": cash_conversion,
        "buyback_yield": buyback_yield
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
            shares_key = next((key for key in ['Basic Average Shares', 'Share Issued', 'Ordinary Shares Number'] if key in balance_sheet_raw.index), None)
            if shares_key:
                shares = balance_sheet.get(shares_key, 0)
                financials['EPS'] = financials['Net Income'] / shares
            else:
                financials['EPS'] = 0

            financials_for_charts, dividends_for_charts = financials, dividends_chart_data

        hist_10y = stock.history(period="10y")
        
        if hist_10y.empty:
            st.warning(f"No se encontraron datos históricos de precios para {ticker}. El análisis técnico y de valoración histórica no estará disponible.")
            return {
                "financials_charts": financials_for_charts, "dividends_charts": dividends_for_charts,
                "per_hist": None, "pfcf_hist": None, "yield_hist": None,
                "tech_data": pd.DataFrame()
            }

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
    if datos.get('payout_ratio') is not None and datos.get('payout_ratio') > 100 and datos.get('sector') != 'Real Estate':
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
    if datos.get('roic') is not None and datos.get('roic') > sector_bench['roic_excelente']: nota_calidad += 3
    elif datos.get('roic') is not None and datos.get('roic') > sector_bench['roic_bueno']: nota_calidad += 2
    if datos.get('margen_operativo') is not None and datos.get('margen_operativo') > sector_bench['margen_excelente']: nota_calidad += 2
    elif datos.get('margen_operativo') is not None and datos.get('margen_operativo') > sector_bench['margen_bueno']: nota_calidad += 1
    if datos.get('conversion_caja') is not None and datos.get('conversion_caja') > sector_bench['conversion_caja_excelente']: nota_calidad += 3
    elif datos.get('conversion_caja') is not None and datos.get('conversion_caja') > sector_bench['conversion_caja_bueno']: nota_calidad += 2
    if datos.get('crecimiento_ingresos') is not None and datos.get('crecimiento_ingresos') > sector_bench.get('rev_growth_excelente', 10): nota_calidad += 2
    elif datos.get('crecimiento_ingresos') is not None and datos.get('crecimiento_ingresos') > sector_bench.get('rev_growth_bueno', 5): nota_calidad += 1
    puntuaciones['calidad'] = min(10, nota_calidad)
    justificaciones['calidad'] = "Rentabilidad, márgenes y crecimiento de élite." if puntuaciones['calidad'] >= 8 else "Negocio de buena calidad."

    nota_salud = 0
    deuda_ratio = datos.get('deuda_patrimonio')
    SECTORES_ALTA_DEUDA = ['Financial Services', 'Utilities', 'Communication Services', 'Real Estate']
    
    if sector in SECTORES_ALTA_DEUDA:
        if deuda_ratio is not None and deuda_ratio < 150: nota_salud += 3
        elif deuda_ratio is not None and deuda_ratio < 250: nota_salud += 1
    else:
        if deuda_ratio is not None and deuda_ratio < 40: nota_salud += 3
        elif deuda_ratio is not None and deuda_ratio < 80: nota_salud += 2
    
    ratio_corriente = datos.get('ratio_corriente')
    if ratio_corriente is not None and ratio_corriente > 2.0: nota_salud += 2
    elif ratio_corriente is not None and ratio_corriente > 1.5: nota_salud += 1

    deuda_ebitda = datos.get('deuda_ebitda')
    if deuda_ebitda is not None and sector != 'Financial Services':
        if deuda_ebitda < sector_bench['deuda_ebitda_bueno']: nota_salud += 3
        elif deuda_ebitda < sector_bench['deuda_ebitda_precaucion']: nota_salud += 1
    
    cobertura_intereses = datos.get('cobertura_intereses')
    if cobertura_intereses is not None and sector != 'Financial Services':
        if cobertura_intereses > sector_bench['cobertura_intereses_excelente']: nota_salud += 2
        elif cobertura_intereses > sector_bench['cobertura_intereses_bueno']: nota_salud += 1

    puntuaciones['salud'] = min(10, nota_salud)
    justificaciones['salud'] = "Balance muy sólido y líquido." if puntuaciones['salud'] >= 8 else "Salud financiera aceptable."
    
    nota_multiplos = 0
    if sector == 'Real Estate':
        if datos.get('p_fcf') and datos.get('p_fcf') < 16: nota_multiplos += 8
        elif datos.get('p_fcf') and datos.get('p_fcf') < 22: nota_multiplos += 5
    else:
        if datos.get('per') and datos.get('per') < sector_bench['per_barato']: nota_multiplos += 4
        if datos.get('p_fcf') and datos.get('p_fcf') < 20: nota_multiplos += 3
        
    SECTORES_PB_RELEVANTES = ['Financial Services', 'Industrials', 'Materials', 'Energy', 'Utilities', 'Real Estate']
    if sector in SECTORES_PB_RELEVANTES and datos.get('p_b'):
        if datos.get('p_b') < sector_bench['pb_barato']: nota_multiplos += 3
        elif datos.get('p_b') < sector_bench['pb_justo']: nota_multiplos += 1
    
    if datos.get('raw_fcf') is not None and datos['raw_fcf'] < 0:
        nota_multiplos -= 3

    nota_analistas, margen_seguridad = 0, 0
    if datos.get('precio_actual') and datos.get('precio_objetivo'):
        margen_seguridad = ((datos['precio_objetivo'] - datos['precio_actual']) / datos['precio_actual']) * 100
        if margen_seguridad > 25: nota_analistas = 10
        elif margen_seguridad > 15: nota_analistas = 8
        else: nota_analistas = 5
    puntuaciones['margen_seguridad_analistas'] = margen_seguridad

    potencial_per, potencial_yield = 0, 0
    per_historico = hist_data.get('per_hist')
    if per_historico and datos.get('per') and datos.get('per') > 0:
        potencial_per = ((per_historico / datos['per']) - 1) * 100
    puntuaciones['margen_seguridad_per'] = potencial_per

    yield_historico = hist_data.get('yield_hist')
    if yield_historico and datos.get('yield_dividendo') and yield_historico > 0:
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

    nota_retorno = 0
    if datos.get('yield_dividendo', 0) > 3.5: nota_retorno += 4
    elif datos.get('yield_dividendo', 0) > 2: nota_retorno += 2
    if 0 < datos.get('payout_ratio', 101) < sector_bench['payout_bueno']: nota_retorno += 4
    elif 0 < datos.get('payout_ratio', 101) < sector_bench['payout_aceptable']: nota_retorno += 2
    if datos.get('buyback_yield', 0) > 2: nota_retorno += 2
    elif datos.get('buyback_yield', 0) > 0: nota_retorno += 1
    puntuaciones['retorno_accionista'] = min(10, nota_retorno)
    justificaciones['retorno_accionista'] = "Excelente retorno al accionista (dividendos y recompras)." if puntuaciones['retorno_accionista'] >= 8 else "Sólido retorno al accionista."
    
    bpa = datos.get('bpa')
    crecimiento = datos.get('crecimiento_beneficios')
    per = datos.get('per')
    div_accion = datos.get('dividendo_por_accion')
    yield_hist = hist_data.get('yield_hist')

    puntuaciones['valor_graham'] = None
    if bpa and bpa > 0 and crecimiento:
        g = min(crecimiento * 100, 20)
        puntuaciones['valor_graham'] = bpa * (8.5 + 2 * g)

    puntuaciones['peg_lynch'] = None
    if per and per > 0 and crecimiento and crecimiento > 0:
        puntuaciones['peg_lynch'] = per / (crecimiento * 100)

    puntuaciones['valor_weiss'] = None
    if div_accion and div_accion > 0 and yield_hist and yield_hist > 0:
        puntuaciones['valor_weiss'] = div_accion / (yield_hist / 100)

    return puntuaciones, justificaciones, SECTOR_BENCHMARKS


# --- BLOQUE 3: GRÁFICOS Y PRESENTACIÓN ---
def crear_grafico_radar(puntuaciones, score):
    labels = ['Calidad', 'Valoración', 'Salud Fin.', 'Retorno Acc.']
    stats = [
        puntuaciones.get('calidad', 0), 
        puntuaciones.get('valoracion', 0), 
        puntuaciones.get('salud', 0), 
        puntuaciones.get('retorno_accionista', 0)
    ]

    angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist()
    stats = np.concatenate((stats,[stats[0]]))
    angles = np.concatenate((angles,[angles[0]]))

    fig, ax = plt.subplots(figsize=(3.5, 3.5), subplot_kw=dict(polar=True))
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

    ax.text(0, 0, f'{score:.1f}', ha='center', va='center', fontsize=36, color='white', weight='bold')
    ax.text(0, 0, '\n\n\nNota Global', ha='center', va='center', fontsize=12, color='gray')

    return fig

def crear_grafico_tecnico(data):
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 5), gridspec_kw={'height_ratios': [3, 1]}, sharex=True)
    fig.patch.set_facecolor('#0E1117')
    
    ax1.set_facecolor('#0E1117')
    ax1.plot(data.index, data['Close'], label='Precio', color='#87CEEB', linewidth=2)
    ax1.plot(data.index, data['SMA50'], label='Media Móvil 50 días', color='#FF0000', linestyle='--') # Rojo
    ax1.plot(data.index, data['SMA200'], label='Media Móvil 200 días', color='#FFA500', linestyle='--') # Naranja
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

        axs[1, 0].bar(años, financials['EPS'], label='BPA/EPS', color='lightgreen')
        axs[1, 0].set_title('3. Evolución del Beneficio por Acción'); axs[1, 0].legend()

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

def mostrar_valor_intrinseco(label, valor_calculado, precio_actual):
    if valor_calculado is None or precio_actual is None:
        prose = "No aplicable"
        color_class = "color-white"
    else:
        potencial = ((valor_calculado / precio_actual) - 1) * 100
        if precio_actual < valor_calculado:
            color_class = "color-green"
            prose = f"Infravalorada ({valor_calculado:.2f}) <span style='font-size: 0.9rem; color: #adb5bd;'> (+{potencial:.1f}%)</span>"
        else:
            color_class = "color-red"
            prose = f"Sobrevalorada ({valor_calculado:.2f}) <span style='font-size: 0.9rem; color: #adb5bd;'> ({potencial:.1f}%)</span>"
    
    st.markdown(f'''
    <div class="metric-container">
        <div class="metric-label">{label}</div>
        <div class="metric-value {color_class}">{prose}</div>
    </div>
    ''', unsafe_allow_html=True)

def generar_leyenda_dinamica(datos, puntuaciones, sector_bench, justificaciones, tech_data):
    highlight_style = 'style="background-color: #FFFF00; color: #0E1117; padding: 2px 5px; border-radius: 3px;"'

    # --- Leyenda de Calidad ---
    roic = datos.get('roic')
    l_roic_exc_raw = f"<strong>Excelente:</strong> > {sector_bench['roic_excelente']}%"
    l_roic_bueno_raw = f"<strong>Bueno:</strong> > {sector_bench['roic_bueno']}%"
    l_roic_alerta_raw = f"<strong>Alerta:</strong> < {sector_bench['roic_bueno']}%"
    l_roic_na_raw = "<strong>No aplicable:</strong> Métrica no estándar para el sector financiero, cuyo modelo de negocio es diferente."
    
    if datos['sector'] == 'Financial Services':
        leyenda_roic = f"- **ROIC (Retorno sobre Capital Invertido):** {l_roic_na_raw}"
    elif roic is not None:
        l_roic_exc = f"<span {highlight_style}>{l_roic_exc_raw}</span>" if roic > sector_bench['roic_excelente'] else l_roic_exc_raw
        l_roic_bueno = f"<span {highlight_style}>{l_roic_bueno_raw}</span>" if sector_bench['roic_bueno'] < roic <= sector_bench['roic_excelente'] else l_roic_bueno_raw
        l_roic_alerta = f"<span {highlight_style}>{l_roic_alerta_raw}</span>" if roic <= sector_bench['roic_bueno'] else l_roic_alerta_raw
        leyenda_roic = f"""- **ROIC (Retorno sobre Capital Invertido):** Mide la rentabilidad real del negocio sobre todo el capital (deuda + patrimonio). Es un indicador clave de calidad.
        - {l_roic_exc}
        - {l_roic_bueno}
        - {l_roic_alerta}"""
    else:
        leyenda_roic = f"- **ROIC:** No disponible."

    margen_op = datos.get('margen_operativo')
    l_mop_exc_raw = f"<strong>Excelente:</strong> > {sector_bench['margen_excelente']}%"
    l_mop_bueno_raw = f"<strong>Bueno:</strong> > {sector_bench['margen_bueno']}%"
    l_mop_alerta_raw = f"<strong>Alerta:</strong> < {sector_bench['margen_bueno']}%"
    l_mop_exc = f"<span {highlight_style}>{l_mop_exc_raw}</span>" if margen_op is not None and margen_op > sector_bench['margen_excelente'] else l_mop_exc_raw
    l_mop_bueno = f"<span {highlight_style}>{l_mop_bueno_raw}</span>" if margen_op is not None and sector_bench['margen_bueno'] < margen_op <= sector_bench['margen_excelente'] else l_mop_bueno_raw
    l_mop_alerta = f"<span {highlight_style}>{l_mop_alerta_raw}</span>" if margen_op is not None and margen_op <= sector_bench['margen_bueno'] else l_mop_alerta_raw
    
    conversion_caja = datos.get('conversion_caja')
    l_cc_exc_raw = "<strong>Excelente:</strong> > 100%"
    l_cc_bueno_raw = "<strong>Bueno:</strong> > 80%"
    l_cc_alerta_raw = "<strong>Alerta:</strong> < 80%"
    l_cc_na_raw = "<strong>No aplicable:</strong> Métrica no estándar para el sector financiero."

    if datos['sector'] == 'Financial Services':
        leyenda_conversion_caja = f"- **Conversión de Caja (FCF/Beneficio):** {l_cc_na_raw}"
    elif conversion_caja is not None:
        l_cc_exc = f"<span {highlight_style}>{l_cc_exc_raw}</span>" if conversion_caja > 100 else l_cc_exc_raw
        l_cc_bueno = f"<span {highlight_style}>{l_cc_bueno_raw}</span>" if 80 < conversion_caja <= 100 else l_cc_bueno_raw
        l_cc_alerta = f"<span {highlight_style}>{l_cc_alerta_raw}</span>" if conversion_caja <= 80 else l_cc_alerta_raw
        leyenda_conversion_caja = f"""- **Conversión de Caja (FCF/Beneficio):** Mide qué % del beneficio se convierte en dinero real.
        - {l_cc_exc}
        - {l_cc_bueno}
        - {l_cc_alerta}"""
    else:
        leyenda_conversion_caja = "- **Conversión de Caja:** No disponible."


    leyenda_calidad = f"""
    {leyenda_roic}
    - **Margen Operativo:** Mide el beneficio de la actividad principal de la empresa.
        - {l_mop_exc}
        - {l_mop_bueno}
        - {l_mop_alerta}
    {leyenda_conversion_caja}
    """

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
    
    deuda_ebitda = datos.get('deuda_ebitda')
    leyenda_deuda_ebitda = ""
    if datos['sector'] == 'Financial Services':
        leyenda_deuda_ebitda = "- **Deuda Neta / EBITDA:** No es una métrica estándar para el sector financiero, ya que su modelo de negocio se basa en el apalancamiento y la 'deuda' es su materia prima."
    elif isinstance(deuda_ebitda, (int, float)):
        l_de_saludable_raw = f"<strong>Saludable:</strong> < {sector_bench['deuda_ebitda_bueno']}x"
        l_de_precaucion_raw = f"<strong>Precaución:</strong> {sector_bench['deuda_ebitda_bueno']}x - {sector_bench['deuda_ebitda_precaucion']}x"
        l_de_riesgo_raw = f"<strong>Riesgo Elevado:</strong> > {sector_bench['deuda_ebitda_precaucion']}x"
        l_de_saludable = f"<span {highlight_style}>{l_de_saludable_raw}</span>" if deuda_ebitda < sector_bench['deuda_ebitda_bueno'] else l_de_saludable_raw
        l_de_precaucion = f"<span {highlight_style}>{l_de_precaucion_raw}</span>" if sector_bench['deuda_ebitda_bueno'] <= deuda_ebitda <= sector_bench['deuda_ebitda_precaucion'] else l_de_precaucion_raw
        l_de_riesgo = f"<span {highlight_style}>{l_de_riesgo_raw}</span>" if deuda_ebitda > sector_bench['deuda_ebitda_precaucion'] else l_de_riesgo_raw
        leyenda_deuda_ebitda = f"""- **Deuda Neta / EBITDA:** Mide los años que tardaría la empresa en pagar su deuda con su beneficio bruto.
        - {l_de_saludable}
        - {l_de_precaucion}
        - {l_de_riesgo}"""

    cobertura_intereses = datos.get('cobertura_intereses')
    leyenda_cobertura = ""
    if datos['sector'] == 'Financial Services':
        leyenda_cobertura = "- **Cobertura de Intereses:** No es una métrica estándar para el sector financiero, ya que los gastos por intereses son parte de su coste operativo principal."
    elif isinstance(cobertura_intereses, (int, float)):
        l_ci_excelente_raw = f"<strong>Excelente:</strong> > {sector_bench['cobertura_intereses_excelente']}x"
        l_ci_buena_raw = f"<strong>Buena:</strong> > {sector_bench['cobertura_intereses_bueno']}x"
        l_ci_alerta_raw = f"<strong>Alerta:</strong> < {sector_bench['cobertura_intereses_bueno']}x"
        l_ci_excelente = f"<span {highlight_style}>{l_ci_excelente_raw}</span>" if cobertura_intereses > sector_bench['cobertura_intereses_excelente'] else l_ci_excelente_raw
        l_ci_buena = f"<span {highlight_style}>{l_ci_buena_raw}</span>" if sector_bench['cobertura_intereses_bueno'] < cobertura_intereses <= sector_bench['cobertura_intereses_excelente'] else l_ci_buena_raw
        l_ci_alerta = f"<span {highlight_style}>{l_ci_alerta_raw}</span>" if cobertura_intereses <= sector_bench['cobertura_intereses_bueno'] else l_ci_alerta_raw
        leyenda_cobertura = f"""- **Cobertura de Intereses:** Mide cuántas veces puede pagar los intereses de su deuda con su beneficio operativo.
        - {l_ci_excelente}
        - {l_ci_buena}
        - {l_ci_alerta}"""


    leyenda_salud = f"""
    {leyenda_deuda}
    {leyenda_liquidez}
    {leyenda_deuda_ebitda}
    {leyenda_cobertura}
    """

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

    valor_graham = puntuaciones.get('valor_graham')
    precio_actual = datos.get('precio_actual')

    l_graham_infra_raw = "<strong>Infravalorada:</strong> El precio actual está por debajo del Valor Intrínseco."
    l_graham_sobre_raw = "<strong>Sobrevalorada:</strong> El precio actual está por encima del Valor Intrínseco."
    l_graham_na_raw = "<strong>No aplicable:</strong> Requiere beneficios y crecimiento positivos."
    
    if valor_graham and precio_actual:
        leyenda_graham = f"<span {highlight_style}>{l_graham_infra_raw}</span>" if precio_actual < valor_graham else f"<span {highlight_style}>{l_graham_sobre_raw}</span>"
    else:
        leyenda_graham = f"<span {highlight_style}>{l_graham_na_raw}</span>"

    peg = puntuaciones.get('peg_lynch')
    l_peg_barato_raw = "<strong>Barato (PEG < 1):</strong> El precio parece bajo en relación al crecimiento."
    l_peg_justo_raw = "<strong>Justo (PEG ≈ 1):</strong> El precio parece adecuado para su crecimiento."
    l_peg_caro_raw = "<strong>Caro (PEG > 1):</strong> El precio parece alto para su crecimiento."
    l_peg_na_raw = "<strong>No aplicable:</strong> Requiere PER y crecimiento positivos."

    if peg:
        if peg < 1: leyenda_peg = f"<span {highlight_style}>{l_peg_barato_raw}</span>"
        elif peg > 1.5: leyenda_peg = f"<span {highlight_style}>{l_peg_caro_raw}</span>"
        else: leyenda_peg = f"<span {highlight_style}>{l_peg_justo_raw}</span>"
    else:
        leyenda_peg = f"<span {highlight_style}>{l_peg_na_raw}</span>"
    
    valor_weiss = puntuaciones.get('valor_weiss')
    l_weiss_atractivo_raw = "<strong>Atractivo por Dividendo:</strong> El precio actual está por debajo del Valor por Dividendo."
    l_weiss_poco_atractivo_raw = "<strong>Poco Atractivo por Dividendo:</strong> El precio actual está por encima del Valor por Dividendo."
    l_weiss_na_raw = "<strong>No aplicable:</strong> Requiere que la empresa pague dividendos."

    if valor_weiss and precio_actual:
        leyenda_weiss = f"<span {highlight_style}>{l_weiss_atractivo_raw}</span>" if precio_actual < valor_weiss else f"<span {highlight_style}>{l_weiss_poco_atractivo_raw}</span>"
    else:
        leyenda_weiss = f"<span {highlight_style}>{l_weiss_na_raw}</span>"

    leyenda_valoracion = f"""
    {leyenda_per}
    {leyenda_pfcf}
    {leyenda_pb}
    ---
    **Fórmulas Clásicas de Valoración:**
    - **Valor Intrínseco (B. Graham):** Estima el valor "real" de una acción basado en sus beneficios y crecimiento esperado.
        - {leyenda_graham}
    - **Ratio PEG (Peter Lynch):** Relaciona el PER con el crecimiento de los beneficios.
        - {leyenda_peg}
    - **Valor por Dividendo (G. Weiss):** Estima un precio justo asumiendo que el Yield volverá a su media histórica.
        - {leyenda_weiss}
    """

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

    leyenda_dividendos = f"""
    - **Rentabilidad (Yield):** Es el porcentaje que recibes anualmente en dividendos sobre el precio de la acción.
        - {l_yield_exc}
        - {l_yield_bueno}
        - {l_yield_bajo}
    - **Ratio de Reparto (Payout):** {leyenda_payout_intro}
        - {l_pay_sal}
        - {l_pay_pre}
        - {l_pay_pel}
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

        l_esc_1_raw = "<strong>🟢+🟢 Oportunidad Interesante Óptima:</strong> Tendencia alcista con retroceso (RSI en sobreventa)."
        l_esc_2_raw = "<strong>🟢+🟠 Continuación Alcista:</strong> Tendencia alcista con RSI neutral. Esperar retroceso."
        l_esc_3_raw = "<strong>🟢+🔴 Riesgo de Corrección:</strong> Tendencia alcista pero con RSI sobrecomprado. Posible señal de peligro."
        l_esc_4_raw = "<strong>🔴+🟢 Posible Rebote (Contra Tendencia):</strong> Tendencia bajista con RSI en sobreventa. Alto riesgo."
        l_esc_5_raw = "<strong>🔴+🟠 Continuación Bajista:</strong> Tendencia bajista con RSI neutral. Evitar."
        l_esc_6_raw = "<strong>🔴+🔴 Señal de Peligro Óptima:</strong> Tendencia bajista con rebote (RSI en sobrecompra)."

        l_esc_1 = f"<span {highlight_style}>{l_esc_1_raw}</span>" if escenario_1 else l_esc_1_raw
        l_esc_2 = f"<span {highlight_style}>{l_esc_2_raw}</span>" if escenario_2 else l_esc_2_raw
        l_esc_3 = f"<span {highlight_style}>{l_esc_3_raw}</span>" if escenario_3 else l_esc_3_raw
        l_esc_4 = f"<span {highlight_style}>{l_esc_4_raw}</span>" if escenario_4 else l_esc_4_raw
        l_esc_5 = f"<span {highlight_style}>{l_esc_5_raw}</span>" if escenario_5 else l_esc_5_raw
        l_esc_6 = f"<span {highlight_style}>{l_esc_6_raw}</span>" if escenario_6 else l_esc_6_raw

        leyenda_tecnico = f"""
        - **Medias Móviles (SMA):** Suavizan el precio para mostrar la tendencia. El número (50 o 200) se refiere a los **últimos días de cotización** (sesiones) que usa para calcular la media.
            - **SMA50 (roja):** Media de los últimos 50 días. Refleja la tendencia a corto/medio plazo.
            - **SMA200 (naranja):** Media de los últimos 200 días. Es el indicador más importante para la tendencia a largo plazo.
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
    
    ms_analistas = puntuaciones.get('margen_seguridad_analistas', 0)
    ms_per = puntuaciones.get('margen_seguridad_per', 0)
    ms_yield = puntuaciones.get('margen_seguridad_yield', 0)

    l_ms_alto_raw = "<strong>Alto Potencial:</strong> > 20%"
    l_ms_mod_raw = "<strong>Potencial Moderado:</strong> 0% a 20%"
    l_ms_riesgo_raw = "<strong>Riesgo de Caída:</strong> < 0%"

    l_ms_a_alto = f"<span {highlight_style}>{l_ms_alto_raw}</span>" if ms_analistas > 20 else l_ms_alto_raw
    l_ms_a_mod = f"<span {highlight_style}>{l_ms_mod_raw}</span>" if 0 <= ms_analistas <= 20 else l_ms_mod_raw
    l_ms_a_riesgo = f"<span {highlight_style}>{l_ms_riesgo_raw}</span>" if ms_analistas < 0 else l_ms_riesgo_raw

    l_ms_p_alto = f"<span {highlight_style}>{l_ms_alto_raw}</span>" if ms_per > 20 else l_ms_alto_raw
    l_ms_p_mod = f"<span {highlight_style}>{l_ms_mod_raw}</span>" if 0 <= ms_per <= 20 else l_ms_mod_raw
    l_ms_p_riesgo = f"<span {highlight_style}>{l_ms_riesgo_raw}</span>" if ms_per < 0 else l_ms_riesgo_raw

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
                    
                    pesos = {'calidad': 0.35, 'valoracion': 0.25, 'salud': 0.25, 'retorno_accionista': 0.15}
                    nota_ponderada = sum(puntuaciones.get(k, 0) * v for k, v in pesos.items())
                    nota_final = max(0, nota_ponderada - puntuaciones['penalizador_geo'])

                    st.header(f"Análisis Fundamental: {datos['nombre']} ({ticker_input})")
                    
                    st.markdown(f"### 🧭 Veredicto del Analizador: **{nota_final:.1f} / 10**")
                    if nota_final >= 7.5: st.success("Veredicto: Empresa EXCEPCIONAL a un precio potencialmente atractivo.")
                    elif nota_final >= 6: st.info("Veredicto: Empresa de ALTA CALIDAD a un precio razonable.")
                    else: st.warning("Veredicto: Empresa SÓLIDA, pero vigilar valoración o riesgos.")

                    col1, col2, col3 = st.columns([1, 2, 1])
                    with col2:
                        st.subheader("Resumen y Nota Global")
                        fig_radar = crear_grafico_radar(puntuaciones, nota_final)
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
                                mostrar_metrica_con_color("🏆 ROIC", datos['roic'], sector_bench['roic_excelente'], sector_bench['roic_bueno'], is_percent=True)
                                mostrar_metrica_con_color("📊 Margen Operativo", datos['margen_operativo'], sector_bench['margen_excelente'], sector_bench['margen_bueno'], is_percent=True)
                            with c2:
                                mostrar_metrica_con_color("💵 Conversión de Caja", datos['conversion_caja'], sector_bench['conversion_caja_excelente'], sector_bench['conversion_caja_bueno'], is_percent=True)
                                mostrar_metrica_con_color("🚀 Crec. Ingresos (YoY)", datos.get('crecimiento_ingresos', 0), sector_bench.get('rev_growth_excelente', 10), sector_bench.get('rev_growth_bueno', 5), is_percent=True)
                            with st.expander("Ver Leyenda Detallada"):
                                st.markdown(leyendas['calidad'], unsafe_allow_html=True)
                    with col2:
                        with st.container(border=True):
                            st.subheader(f"Salud Financiera [{puntuaciones['salud']}/10]")
                            st.caption(justificaciones['salud'])
                            
                            s1, s2, s3 = st.columns(3)
                            with s1: 
                                mostrar_metrica_con_color("🏦 Deuda / Patrimonio", datos['deuda_patrimonio'], 80, 150, lower_is_better=True)
                            with s2: 
                                mostrar_metrica_con_color("💧 Ratio Corriente", datos['ratio_corriente'], 1.5, 1.0)
                            with s3:
                                mostrar_metrica_con_color("⚡ Deuda Neta/EBITDA", datos['deuda_ebitda'], sector_bench['deuda_ebitda_bueno'], sector_bench['deuda_ebitda_precaucion'], lower_is_better=True)
                            
                            st.markdown("---")
                            mostrar_metrica_con_color("🛡️ Cobertura de Intereses", datos['cobertura_intereses'], sector_bench['cobertura_intereses_excelente'], sector_bench['cobertura_intereses_bueno'])

                            with st.expander("Ver Leyenda Detallada"):
                                st.markdown(leyendas['salud'], unsafe_allow_html=True)

                    with st.container(border=True):
                        st.subheader(f"Análisis de Valoración [{puntuaciones['valoracion']:.1f}/10]")
                        st.caption(justificaciones['valoracion'])
                        
                        tab1, tab2, tab3 = st.tabs(["Múltiplos Actuales", "Análisis Histórico", "Valor Intrínseco (Fórmulas Clásicas)"])
                        
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

                        with tab3:
                            precio_actual = datos.get('precio_actual')
                            st.metric("Precio Actual", f"{precio_actual:.2f}" if precio_actual else "N/A")
                            st.markdown("---")
                            
                            mostrar_valor_intrinseco("Valor Intrínseco (Graham)", puntuaciones.get('valor_graham'), precio_actual)
                            
                            precio_seguro = puntuaciones.get('valor_graham') * 0.67 if puntuaciones.get('valor_graham') else None
                            mostrar_valor_intrinseco("Precio de Compra 'Seguro'", precio_seguro, precio_actual)

                            mostrar_valor_intrinseco("Valor por Dividendo (Weiss)", puntuaciones.get('valor_weiss'), precio_actual)
                            
                            peg_lynch = puntuaciones.get('peg_lynch')
                            if peg_lynch is None:
                                prose = "No aplicable"
                                color_class = "color-white"
                            elif peg_lynch < 1:
                                prose = f"Barato ({peg_lynch:.2f})"
                                color_class = "color-green"
                            elif peg_lynch > 1.5:
                                prose = f"Caro ({peg_lynch:.2f})"
                                color_class = "color-red"
                            else:
                                prose = f"Justo ({peg_lynch:.2f})"
                                color_class = "color-orange"
                            
                            st.markdown(f'<div class="metric-container"><div class="metric-label">Ratio PEG (Lynch)</div><div class="metric-value {color_class}">{prose}</div></div>', unsafe_allow_html=True)

                        with st.expander("Ver Leyenda Detallada"):
                            st.markdown(leyendas['valoracion'], unsafe_allow_html=True)
                    
                    with st.container(border=True):
                        st.subheader(f"Retorno al Accionista [{puntuaciones['retorno_accionista']}/10]")
                        st.caption(justificaciones['retorno_accionista'])
                        
                        div1, div2 = st.columns(2)
                        with div1: 
                            mostrar_metrica_con_color("💸 Rentabilidad (Yield)", datos['yield_dividendo'], 3.5, 2.0, is_percent=True)
                        with div2:
                            mostrar_metrica_con_color("🤲 Ratio de Reparto (Payout)", datos['payout_ratio'], sector_bench['payout_bueno'], sector_bench['payout_aceptable'], lower_is_better=True, is_percent=True)
                        
                        with st.expander("Ver Leyenda Detallada"):
                            st.markdown(leyendas['dividendos'], unsafe_allow_html=True)
                    
                    with st.container(border=True):
                        st.subheader("Potencial de Revalorización (Márgenes de Seguridad)")
                        ms1, ms2, ms3 = st.columns(3)
                        with ms1:
                            mostrar_margen_seguridad("🛡️ Según Analistas", puntuaciones['margen_seguridad_analistas'])
                        with ms2:
                            mostrar_margen_seguridad("📈 Según su PER Histórico", puntuaciones['margen_seguridad_per'])
                            mostrar_metrica_blue_chip("PER Actual vs Histórico", datos.get('per'), hist_data.get('per_hist'), is_percent=False, lower_is_better=True)
                        with ms3:
                            mostrar_margen_seguridad("💸 Según su Yield Histórico", puntuaciones['margen_seguridad_yield'])
                            mostrar_metrica_blue_chip("Yield Actual vs Histórico", datos.get('yield_dividendo'), hist_data.get('yield_hist'), is_percent=True, lower_is_better=False)
                        
                        with st.expander("Ver Leyenda Detallada"):
                            st.markdown(leyendas['margen_seguridad'], unsafe_allow_html=True)

                    st.header("Análisis Gráfico y Técnico")
                    
                    col_fin, col_flags = st.columns([2, 1])
                    
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

                    col_tech, col_tech_legend = st.columns(2)

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
