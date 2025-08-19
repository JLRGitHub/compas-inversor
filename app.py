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
    .formula-label { font-size: 0.8rem; color: #6c757d; font-style: italic; }
    .color-green { color: #28a745; }
    .color-red { color: #dc3545; }
    .color-orange { color: #fd7e14; }
    .color-white { color: #FAFAFA; }
</style>
""", unsafe_allow_html=True)

# --- Benchmarks Centralizados y Completos para los 11 Sectores GICS ---
SECTOR_BENCHMARKS = {
    'Information Technology': {'roe_excelente': 25, 'roe_bueno': 18, 'margen_excelente': 25, 'margen_bueno': 18, 'margen_neto_excelente': 20, 'margen_neto_bueno': 15, 'rev_growth_excelente': 15, 'rev_growth_bueno': 10, 'per_barato': 25, 'per_justo': 35, 'pb_barato': 4, 'pb_justo': 8, 'payout_bueno': 60, 'payout_aceptable': 80, 'deuda_ebitda_bueno': 2, 'deuda_ebitda_aceptable': 3, 'int_coverage_excelente': 10, 'int_coverage_bueno': 5},
    'Health Care': {'roe_excelente': 20, 'roe_bueno': 15, 'margen_excelente': 20, 'margen_bueno': 15, 'margen_neto_excelente': 15, 'margen_neto_bueno': 10, 'rev_growth_excelente': 10, 'rev_growth_bueno': 6, 'per_barato': 20, 'per_justo': 30, 'pb_barato': 3, 'pb_justo': 5, 'payout_bueno': 60, 'payout_aceptable': 80, 'deuda_ebitda_bueno': 3, 'deuda_ebitda_aceptable': 4, 'int_coverage_excelente': 8, 'int_coverage_bueno': 4},
    'Financial Services': {'roe_excelente': 12, 'roe_bueno': 10, 'margen_excelente': 15, 'margen_bueno': 10, 'margen_neto_excelente': 10, 'margen_neto_bueno': 8, 'rev_growth_excelente': 8, 'rev_growth_bueno': 4, 'per_barato': 12, 'per_justo': 18, 'pb_barato': 1, 'pb_justo': 1.5, 'payout_bueno': 70, 'payout_aceptable': 90, 'deuda_ebitda_bueno': 1, 'deuda_ebitda_aceptable': 2, 'int_coverage_excelente': 5, 'int_coverage_bueno': 3},
    'Industrials': {'roe_excelente': 18, 'roe_bueno': 14, 'margen_excelente': 15, 'margen_bueno': 10, 'margen_neto_excelente': 8, 'margen_neto_bueno': 6, 'rev_growth_excelente': 10, 'rev_growth_bueno': 5, 'per_barato': 20, 'per_justo': 25, 'pb_barato': 2.5, 'pb_justo': 4, 'payout_bueno': 60, 'payout_aceptable': 80, 'deuda_ebitda_bueno': 2.5, 'deuda_ebitda_aceptable': 4, 'int_coverage_excelente': 7, 'int_coverage_bueno': 4},
    'Utilities': {'roe_excelente': 10, 'roe_bueno': 8, 'margen_excelente': 15, 'margen_bueno': 12, 'margen_neto_excelente': 8, 'margen_neto_bueno': 5, 'rev_growth_excelente': 5, 'rev_growth_bueno': 3, 'per_barato': 18, 'per_justo': 22, 'pb_barato': 1.5, 'pb_justo': 2, 'payout_bueno': 80, 'payout_aceptable': 95, 'deuda_ebitda_bueno': 4, 'deuda_ebitda_aceptable': 5.5, 'int_coverage_excelente': 4, 'int_coverage_bueno': 2.5},
    'Consumer Discretionary': {'roe_excelente': 18, 'roe_bueno': 14, 'margen_excelente': 12, 'margen_bueno': 8, 'margen_neto_excelente': 7, 'margen_neto_bueno': 5, 'rev_growth_excelente': 12, 'rev_growth_bueno': 7, 'per_barato': 20, 'per_justo': 28, 'pb_barato': 3, 'pb_justo': 5, 'payout_bueno': 60, 'payout_aceptable': 80, 'deuda_ebitda_bueno': 3, 'deuda_ebitda_aceptable': 4.5, 'int_coverage_excelente': 6, 'int_coverage_bueno': 3.5},
    'Consumer Staples': {'roe_excelente': 20, 'roe_bueno': 15, 'margen_excelente': 15, 'margen_bueno': 10, 'margen_neto_excelente': 8, 'margen_neto_bueno': 5, 'rev_growth_excelente': 7, 'rev_growth_bueno': 4, 'per_barato': 20, 'per_justo': 25, 'pb_barato': 4, 'pb_justo': 6, 'payout_bueno': 70, 'payout_aceptable': 85, 'deuda_ebitda_bueno': 3, 'deuda_ebitda_aceptable': 4.5, 'int_coverage_excelente': 7, 'int_coverage_bueno': 4},
    'Energy': {'roe_excelente': 15, 'roe_bueno': 10, 'margen_excelente': 10, 'margen_bueno': 7, 'margen_neto_excelente': 8, 'margen_neto_bueno': 5, 'rev_growth_excelente': 8, 'rev_growth_bueno': 0, 'per_barato': 15, 'per_justo': 20, 'pb_barato': 1.5, 'pb_justo': 2.5, 'payout_bueno': 60, 'payout_aceptable': 80, 'deuda_ebitda_bueno': 2, 'deuda_ebitda_aceptable': 3, 'int_coverage_excelente': 8, 'int_coverage_bueno': 5},
    'Materials': {'roe_excelente': 15, 'roe_bueno': 12, 'margen_excelente': 12, 'margen_bueno': 8, 'margen_neto_excelente': 7, 'margen_neto_bueno': 5, 'rev_growth_excelente': 10, 'rev_growth_bueno': 5, 'per_barato': 18, 'per_justo': 25, 'pb_barato': 2, 'pb_justo': 3, 'payout_bueno': 60, 'payout_aceptable': 80, 'deuda_ebitda_bueno': 2.5, 'deuda_ebitda_aceptable': 4, 'int_coverage_excelente': 6, 'int_coverage_bueno': 3.5},
    'Real Estate': {'roe_excelente': 8, 'roe_bueno': 6, 'margen_excelente': 20, 'margen_bueno': 15, 'margen_neto_excelente': 15, 'margen_neto_bueno': 10, 'rev_growth_excelente': 8, 'rev_growth_bueno': 4, 'per_barato': 25, 'per_justo': 35, 'pb_barato': 2, 'pb_justo': 3, 'payout_bueno': 90, 'payout_aceptable': 100, 'deuda_ebitda_bueno': 5, 'deuda_ebitda_aceptable': 7, 'int_coverage_excelente': 3, 'int_coverage_bueno': 2},
    'Communication Services': {'roe_excelente': 15, 'roe_bueno': 12, 'margen_excelente': 18, 'margen_bueno': 12, 'margen_neto_excelente': 12, 'margen_neto_bueno': 9, 'rev_growth_excelente': 12, 'rev_growth_bueno': 7, 'per_barato': 22, 'per_justo': 30, 'pb_barato': 3, 'pb_justo': 5, 'payout_bueno': 60, 'payout_aceptable': 80, 'deuda_ebitda_bueno': 3, 'deuda_ebitda_aceptable': 4.5, 'int_coverage_excelente': 6, 'int_coverage_bueno': 3.5},
    'Default': {'roe_excelente': 15, 'roe_bueno': 12, 'margen_excelente': 15, 'margen_bueno': 10, 'margen_neto_excelente': 8, 'margen_neto_bueno': 5, 'rev_growth_excelente': 10, 'rev_growth_bueno': 5, 'per_barato': 20, 'per_justo': 25, 'pb_barato': 2, 'pb_justo': 4, 'payout_bueno': 60, 'payout_aceptable': 80, 'deuda_ebitda_bueno': 3, 'deuda_ebitda_aceptable': 5, 'int_coverage_excelente': 5, 'int_coverage_bueno': 3}
}

# --- BLOQUE 1: OBTENCIÓN DE DATOS ---
@st.cache_data(ttl=900)
def obtener_datos_completos(ticker):
    stock = yf.Ticker(ticker)
    info = stock.info
    if not info or info.get('longName') is None:
        return None
    
    financials = stock.financials
    balance_sheet = stock.balance_sheet
    
    # --- Cálculo robusto de métricas financieras ---
    ebit = financials.loc['EBIT'].iloc[0] if 'EBIT' in financials.index and not financials.loc['EBIT'].empty else None
    interest_expense = financials.loc['Interest Expense'].iloc[0] if 'Interest Expense' in financials.index and not financials.loc['Interest Expense'].empty else None
    
    interest_coverage = None
    if ebit is not None and interest_expense is not None:
        interest_coverage = ebit / abs(interest_expense) if interest_expense != 0 else float('inf')

    deuda_ebitda = info.get('debtToEbitda')
    if deuda_ebitda is None:
        net_debt = info.get('netDebt')
        ebitda = info.get('ebitda')
        if net_debt is None:
            total_debt = balance_sheet.loc['Total Debt'].iloc[0] if 'Total Debt' in balance_sheet.index else 0
            cash = balance_sheet.loc['Cash And Cash Equivalents'].iloc[0] if 'Cash And Cash Equivalents' in balance_sheet.index else 0
            net_debt = total_debt - cash
        if ebitda is None:
            depreciation_key = 'Depreciation And Amortization' if 'Depreciation And Amortization' in financials.index else 'Reconciled Depreciation'
            depreciation = financials.loc[depreciation_key].iloc[0] if depreciation_key in financials.index else 0
            ebitda = ebit + depreciation if ebit else None
        
        if net_debt is not None and ebitda is not None and ebitda > 0:
            deuda_ebitda = net_debt / ebitda
    
    payout = info.get('payoutRatio')
    dividend_rate = info.get('dividendRate')
    precio = info.get('currentPrice')
    div_yield = (dividend_rate / precio) if dividend_rate and precio and precio > 0 else 0
    
    if payout is not None and (payout > 1.5 or payout < 0):
        trailing_eps = info.get('trailingEps')
        if trailing_eps and dividend_rate and trailing_eps > 0:
            payout = dividend_rate / trailing_eps
        else:
            payout = None

    free_cash_flow = info.get('freeCashflow')
    market_cap = info.get('marketCap')
    p_fcf = (market_cap / free_cash_flow) if market_cap and free_cash_flow and free_cash_flow > 0 else None

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
        "roe": info.get('returnOnEquity', 0) * 100 if info.get('returnOnEquity') is not None else 0,
        "margen_operativo": info.get('operatingMargins', 0) * 100 if info.get('operatingMargins') is not None else 0,
        "margen_beneficio": info.get('profitMargins', 0) * 100 if info.get('profitMargins') is not None else 0,
        "deuda_patrimonio": info.get('debtToEquity'), "ratio_corriente": info.get('currentRatio'),
        "per": info.get('trailingPE'), "per_adelantado": info.get('forwardPE'),
        "p_fcf": p_fcf,
        "raw_fcf": free_cash_flow,
        "p_b": info.get('priceToBook'),
        "crecimiento_ingresos_yoy": info.get('revenueGrowth', 0) * 100 if info.get('revenueGrowth') is not None else 0,
        "yield_dividendo": div_yield * 100,
        "payout_ratio": payout * 100 if payout is not None else 0,
        "recomendacion_analistas": info.get('recommendationKey', 'N/A'),
        "precio_objetivo": info.get('targetMeanPrice'), "precio_actual": info.get('currentPrice'),
        "bpa": info.get('trailingEps'),
        "crecimiento_beneficios_yoy": info.get('earningsGrowth'),
        "dividendo_por_accion": dividend_rate,
        "deuda_ebitda": deuda_ebitda,
        "interest_coverage": interest_coverage
    }

def calculate_cagr(end_value, start_value, years):
    if start_value is None or end_value is None or start_value <= 0 or years <= 0:
        return None
    return ((end_value / start_value) ** (1 / years) - 1) * 100

@st.cache_data(ttl=3600)
def obtener_datos_historicos_y_tecnicos(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        if not isinstance(info, dict) or not info:
            st.warning(f"No se pudo obtener la información básica para {ticker}.")
            return {}

        financials_raw = stock.financials
        balance_sheet_raw = stock.balance_sheet
        cashflow_raw = stock.cashflow
        
        financials_for_charts, dividends_for_charts = None, None
        cagr_rev, cagr_net, cagr_fcf = None, None, None

        if not financials_raw.empty:
            financials_annual = financials_raw.T.sort_index(ascending=True)
            if len(financials_annual) >= 4:
                years = (financials_annual.index[-1] - financials_annual.index[0]).days / 365.25
                if years > 0:
                    cagr_rev = calculate_cagr(financials_annual['Total Revenue'].iloc[-1], financials_annual['Total Revenue'].iloc[0], years)
                    cagr_net = calculate_cagr(financials_annual['Net Income'].iloc[-1], financials_annual['Net Income'].iloc[0], years)
        
        if not cashflow_raw.empty:
            cashflow_annual = cashflow_raw.T.sort_index(ascending=True)
            if 'Free Cash Flow' in cashflow_annual.columns and len(cashflow_annual) >= 4:
                years_cf = (cashflow_annual.index[-1] - cashflow_annual.index[0]).days / 365.25
                if years_cf > 0:
                    cagr_fcf = calculate_cagr(cashflow_annual['Free Cash Flow'].iloc[-1], cashflow_annual['Free Cash Flow'].iloc[0], years_cf)

        if not financials_raw.empty and not balance_sheet_raw.empty and not cashflow_raw.empty:
            financials = financials_raw.T.sort_index(ascending=True).tail(4)
            balance_sheet = balance_sheet_raw.T.sort_index(ascending=True).tail(4)
            cashflow = cashflow_raw.T.sort_index(ascending=True).tail(4)
            dividends_chart_data = stock.dividends.resample('YE').sum().tail(5)
            
            financials['Operating Margin'] = financials.get('Operating Income', 0) / financials.get('Total Revenue', 1)
            financials['Total Debt'] = balance_sheet.get('Total Debt', 0)
            financials['ROE'] = financials['Net Income'] / balance_sheet.get('Total Stockholder Equity', 1)
            
            if 'Free Cash Flow' not in cashflow.columns:
                capex = cashflow.get('Capital Expenditure', cashflow.get('Capital Expenditures', 0))
                op_cash = cashflow.get('Total Cash From Operating Activities', 0)
                cashflow['Free Cash Flow'] = op_cash + capex
            
            financials['Free Cash Flow'] = cashflow['Free Cash Flow']
            financials_for_charts, dividends_for_charts = financials, dividends_chart_data

        hist_10y = stock.history(period="10y")
        
        if hist_10y.empty:
            st.warning(f"No se encontraron datos históricos de precios para {ticker}.")
            return {"financials_charts": financials_for_charts, "dividends_charts": dividends_for_charts, "cagr_rev_5y": cagr_rev, "cagr_net_5y": cagr_net, "cagr_fcf_5y": cagr_fcf}
        
        # --- Cálculo Robusto de PER y Yield Histórico ---
        pers = []
        annual_yields = []
        if not financials_raw.empty and not balance_sheet_raw.empty:
            net_income_key = 'Net Income Applicable To Common Shares' if 'Net Income Applicable To Common Shares' in financials_raw.index else 'Net Income'
            share_key_found = next((key for key in ['Share Issued', 'Ordinary Shares Number', 'Basic Shares Outstanding', 'Total Common Shares Outstanding'] if key in balance_sheet_raw.index), None)
            
            if share_key_found:
                for col_date in financials_raw.columns:
                    net_income = financials_raw.loc[net_income_key, col_date]
                    shares = balance_sheet_raw.loc[share_key_found, col_date]
                    if pd.notna(net_income) and pd.notna(shares) and shares > 0 and net_income > 0:
                        eps = net_income / shares
                        price_data_year = hist_10y[hist_10y.index.year == col_date.year]
                        if not price_data_year.empty:
                            avg_price = price_data_year['Close'].mean()
                            per_year = avg_price / eps
                            if 0 < per_year < 200:
                                pers.append(per_year)
        
        divs_10y = stock.dividends
        if not divs_10y.empty:
            annual_dividends = divs_10y.resample('YE').sum()
            annual_prices = hist_10y['Close'].resample('YE').mean()
            df_yield = pd.concat([annual_dividends, annual_prices], axis=1).dropna()
            df_yield.columns = ['Dividends', 'Price']
            if not df_yield.empty:
                annual_yields = ((df_yield['Dividends'] / df_yield['Price']) * 100).tolist()

        per_historico = np.mean(pers) if pers else None
        yield_historico = np.mean(annual_yields) if annual_yields else None

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
            "per_hist": per_historico, "yield_hist": yield_historico,
            "tech_data": hist_1y,
            "cagr_rev_5y": cagr_rev, "cagr_net_5y": cagr_net, "cagr_fcf_5y": cagr_fcf
        }
    except Exception as e:
        st.error(f"Ocurrió un error al obtener datos históricos: {e}")
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
    if datos.get('raw_fcf', 0) < 0:
        banderas.append("🔴 **Flujo de Caja Libre Negativo:** La empresa está quemando más dinero del que genera.")
    if datos.get('interest_coverage') is not None and datos.get('interest_coverage') < 2:
        banderas.append("🔴 **Cobertura de Intereses Baja:** El beneficio operativo apenas cubre el pago de intereses de la deuda.")
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
    if datos['roe'] > sector_bench['roe_excelente']: nota_calidad += 2.5
    elif datos['roe'] > sector_bench['roe_bueno']: nota_calidad += 1.5
    if datos['margen_operativo'] > sector_bench['margen_excelente']: nota_calidad += 2.5
    elif datos['margen_operativo'] > sector_bench['margen_bueno']: nota_calidad += 1.5
    if datos['margen_beneficio'] > sector_bench.get('margen_neto_excelente', 8): nota_calidad += 2
    elif datos['margen_beneficio'] > sector_bench.get('margen_neto_bueno', 5): nota_calidad += 1
    
    cagr_rev_5y = hist_data.get('cagr_rev_5y')
    if cagr_rev_5y is not None:
        if cagr_rev_5y > sector_bench['rev_growth_excelente']: nota_calidad += 2
        elif cagr_rev_5y > sector_bench['rev_growth_bueno']: nota_calidad += 1
    if datos['crecimiento_ingresos_yoy'] > sector_bench['rev_growth_excelente']: nota_calidad += 1
    
    puntuaciones['calidad'] = min(10, nota_calidad)
    justificaciones['calidad'] = "Rentabilidad, márgenes y crecimiento de élite." if puntuaciones['calidad'] >= 8 else "Negocio de buena calidad."

    nota_salud = 0
    deuda_ebitda = datos.get('deuda_ebitda')
    if deuda_ebitda is not None:
        if deuda_ebitda < sector_bench['deuda_ebitda_bueno']: nota_salud += 4
        elif deuda_ebitda < sector_bench['deuda_ebitda_aceptable']: nota_salud += 2
    
    interest_coverage = datos.get('interest_coverage')
    if interest_coverage is not None:
        if interest_coverage > sector_bench['int_coverage_excelente']: nota_salud += 4
        elif interest_coverage > sector_bench['int_coverage_bueno']: nota_salud += 2
        
    ratio_corriente = datos.get('ratio_corriente')
    if ratio_corriente is not None and ratio_corriente > 1.5:
        nota_salud += 2
        
    if datos.get('raw_fcf', 0) <= 0:
        nota_salud -= 4

    puntuaciones['salud'] = max(0, min(10, nota_salud))
    justificaciones['salud'] = "Balance muy sólido y solvente." if puntuaciones['salud'] >= 8 else "Salud financiera aceptable."
    
    nota_multiplos = 0
    if sector == 'Real Estate':
        if datos['p_fcf'] and datos['p_fcf'] < 16: nota_multiplos += 8
        elif datos['p_fcf'] and datos['p_fcf'] < 22: nota_multiplos += 5
    else:
        if datos['per'] and datos['per'] < sector_bench['per_barato']: nota_multiplos += 4
        if datos['p_fcf'] and datos['p_fcf'] < 20: nota_multiplos += 4
        
    SECTORES_PB_RELEVANTES = ['Financial Services', 'Industrials', 'Materials', 'Energy', 'Utilities', 'Real Estate']
    if sector in SECTORES_PB_RELEVANTES and datos['p_b']:
        if datos['p_b'] < sector_bench['pb_barato']: nota_multiplos += 2
    
    if datos.get('raw_fcf') is not None and datos['raw_fcf'] < 0:
        nota_multiplos -= 4

    nota_analistas, margen_seguridad = 0, 0
    if datos['precio_actual'] and datos['precio_objetivo']:
        margen_seguridad = ((datos['precio_objetivo'] - datos['precio_actual']) / datos['precio_actual']) * 100
        if margen_seguridad > 25: nota_analistas = 10
        elif margen_seguridad > 15: nota_analistas = 8
        else: nota_analistas = 5
    puntuaciones['margen_seguridad_analistas'] = margen_seguridad

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
    
    bpa = datos.get('bpa')
    crecimiento_yoy = datos.get('crecimiento_beneficios_yoy')
    per = datos.get('per')
    div_accion = datos.get('dividendo_por_accion')
    yield_hist = hist_data.get('yield_hist')

    puntuaciones['valor_graham'] = None
    if bpa and bpa > 0 and crecimiento_yoy is not None:
        g = min(crecimiento_yoy * 100, 20) if crecimiento_yoy > 0 else 0
        puntuaciones['valor_graham'] = bpa * (8.5 + 2 * g)

    puntuaciones['peg_lynch'] = None
    if per and per > 0 and crecimiento_yoy is not None and crecimiento_yoy > 0:
        puntuaciones['peg_lynch'] = per / (crecimiento_yoy * 100)

    puntuaciones['valor_weiss'] = None
    if div_accion and div_accion > 0 and yield_hist and yield_hist > 0:
        puntuaciones['valor_weiss'] = div_accion / (yield_hist / 100)

    return puntuaciones, justificaciones, SECTOR_BENCHMARKS

# --- BLOQUE 3: GRÁFICOS Y PRESENTACIÓN ---
def crear_grafico_radar(puntuaciones, score):
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
    ax1.plot(data.index, data['SMA50'], label='Media Móvil 50 días', color='#FFA500', linestyle='--')
    ax1.plot(data.index, data['SMA200'], label='Media Móvil 200 días', color='#FF0000', linestyle='--')
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

def mostrar_metrica_con_color(label, value, umbral_bueno, umbral_malo=None, lower_is_better=False, is_percent=False, is_currency=False):
    if value is None:
        formatted_value = "N/A"
        color_class = "color-white"
    else:
        if umbral_malo is None: umbral_malo = umbral_bueno * 1.25 if lower_is_better else umbral_bueno * 0.8
        color_class = "color-white"
        try:
            numeric_value = float(str(value).replace('%', ''))
            if lower_is_better:
                if numeric_value < umbral_bueno: color_class = "color-green"
                elif numeric_value > umbral_malo: color_class = "color-red"
                else: color_class = "color-orange"
            else:
                if numeric_value > umbral_bueno: color_class = "color-green"
                elif numeric_value < umbral_malo: color_class = "color-red"
                else: color_class = "color-orange"
        except (ValueError, TypeError): pass
        
        if is_percent: formatted_value = f"{value:.2f}%"
        elif is_currency: formatted_value = f"${value/1e9:.2f}B" if abs(value) >= 1e9 else f"${value/1e6:.2f}M"
        else: formatted_value = f"{value:.2f}"
    
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

def mostrar_metrica_informativa(label, value, is_percent=False, potential_pct=None):
    formatted_value = "N/A"
    if isinstance(value, (int, float)):
        formatted_value = f"{value:.2f}%" if is_percent else f"{value:.2f}"
    
    if potential_pct is not None:
        color_class = "color-green" if potential_pct > 0 else "color-red"
        sign = "+" if potential_pct > 0 else ""
        formatted_value += f' <span class="{color_class}">({sign}{potential_pct:.2f}%)</span>'

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
    color_class = "color-orange" 
    
    is_comparable = isinstance(current_value, (int, float)) and isinstance(historical_value, (int, float))

    if is_comparable:
        if lower_is_better:
            if current_value < historical_value: color_class = "color-green"
            elif current_value > historical_value: color_class = "color-red"
        else: 
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

def mostrar_valor_formula(label, formula, valor_calculado, precio_actual):
    if valor_calculado is None or precio_actual is None:
        prose = "No aplicable"
        color_class = "color-white"
    else:
        potential_pct = ((valor_calculado - precio_actual) / precio_actual) * 100
        sign = "+" if potential_pct > 0 else ""
        color_class = "color-green" if potential_pct > 0 else "color-red"
        prose = f"{valor_calculado:.2f} <span class='{color_class}'>({sign}{potential_pct:.2f}%)</span>"
    
    st.markdown(f'''
    <div class="metric-container">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{prose}</div>
        <div class="formula-label">{formula}</div>
    </div>
    ''', unsafe_allow_html=True)

def generar_leyenda_dinamica(datos, hist_data, puntuaciones, justificaciones, sector_bench, tech_data):
    highlight_style = 'style="background-color: #D4AF37; color: #0E1117; padding: 2px 5px; border-radius: 3px;"'
    
    def highlight(condition, text):
        return f"<span {highlight_style}>{text}</span>" if condition else text

    # --- Leyenda de Calidad ---
    roe = datos.get('roe', 0)
    margen_op = datos.get('margen_operativo', 0)
    margen_neto = datos.get('margen_beneficio', 0)
    cagr_rev = hist_data.get('cagr_rev_5y') if hist_data else None
    yoy_rev = datos.get('crecimiento_ingresos_yoy', 0)
    
    leyenda_calidad = f"""
    - **ROE (Return on Equity):** Mide la rentabilidad que obtiene la empresa sobre el dinero invertido por los accionistas. Un ROE alto y constante indica un negocio de calidad. Los rangos se ajustan para el sector **{datos['sector']}**.<br>
        - {highlight(roe > sector_bench['roe_excelente'], f"**Excelente:** > {sector_bench['roe_excelente']}%")}<br>
        - {highlight(sector_bench['roe_bueno'] < roe <= sector_bench['roe_excelente'], f"**Bueno:** > {sector_bench['roe_bueno']}%")}<br>
        - {highlight(roe <= sector_bench['roe_bueno'], f"**Alerta:** < {sector_bench['roe_bueno']}%")}
    <br><br>
    - **Margen Operativo:** Indica qué porcentaje de cada euro vendido se convierte en beneficio antes de intereses e impuestos. Un margen alto sugiere una ventaja competitiva.<br>
        - {highlight(margen_op > sector_bench['margen_excelente'], f"**Excelente:** > {sector_bench['margen_excelente']}%")}<br>
        - {highlight(sector_bench['margen_bueno'] < margen_op <= sector_bench['margen_excelente'], f"**Bueno:** > {sector_bench['margen_bueno']}%")}<br>
        - {highlight(margen_op <= sector_bench['margen_bueno'], f"**Alerta:** < {sector_bench['margen_bueno']}%")}
    <br><br>
    - **Margen Neto:** Es el beneficio final. Indica el porcentaje de cada euro vendido que queda para el accionista después de pagar absolutamente todos los gastos.<br>
        - {highlight(margen_neto > sector_bench['margen_neto_excelente'], f"**Excelente:** > {sector_bench['margen_neto_excelente']}%")}<br>
        - {highlight(sector_bench['margen_neto_bueno'] < margen_neto <= sector_bench['margen_neto_excelente'], f"**Bueno:** > {sector_bench['margen_neto_bueno']}%")}<br>
        - {highlight(margen_neto <= sector_bench['margen_neto_bueno'], f"**Alerta:** < {sector_bench['margen_neto_bueno']}%")}
    <br><br>
    - **Crecimiento Ingresos (CAGR 5 Años):** Mide la tasa de crecimiento anual compuesta de las ventas en los últimos 5 años. Es un indicador clave de la consistencia del negocio.<br>
    """
    if cagr_rev is not None:
        leyenda_calidad += f"""
        - {highlight(cagr_rev > sector_bench['rev_growth_excelente'], f"**Excelente:** > {sector_bench['rev_growth_excelente']}%")}<br>
        - {highlight(sector_bench['rev_growth_bueno'] < cagr_rev <= sector_bench['rev_growth_excelente'], f"**Bueno:** > {sector_bench['rev_growth_bueno']}%")}<br>
        - {highlight(cagr_rev <= sector_bench['rev_growth_bueno'], f"**Lento/Negativo:** < {sector_bench['rev_growth_bueno']}%")}
    """
    else:
        leyenda_calidad += " - *No hay datos suficientes para el cálculo a 5 años.*"
        
    leyenda_calidad += f"""
    <br><br>
    - **Crecimiento Ingresos (YoY):** Mide el crecimiento de las ventas en el último año. Sirve para ver el momento actual de la empresa.<br>
        - {highlight(yoy_rev > sector_bench['rev_growth_excelente'], f"**Excelente:** > {sector_bench['rev_growth_excelente']}%")}<br>
        - {highlight(sector_bench['rev_growth_bueno'] < yoy_rev <= sector_bench['rev_growth_excelente'], f"**Bueno:** > {sector_bench['rev_growth_bueno']}%")}<br>
        - {highlight(yoy_rev <= sector_bench['rev_growth_bueno'], f"**Lento/Negativo:** < {sector_bench['rev_growth_bueno']}%")}
    """

    # --- Leyenda de Salud Financiera ---
    deuda_ebitda = datos.get('deuda_ebitda')
    int_coverage = datos.get('interest_coverage')
    ratio_corriente = datos.get('ratio_corriente')

    leyenda_salud = f"- **Deuda Neta / EBITDA:** El ratio de deuda más importante. Mide cuántos años de ganancias operativas (EBITDA) costaría pagar toda la deuda neta. Los rangos se ajustan para el sector **{datos['sector']}**.<br>"
    if deuda_ebitda is not None:
        leyenda_salud += f"""
        - {highlight(deuda_ebitda < sector_bench['deuda_ebitda_bueno'], f"**Saludable:** < {sector_bench['deuda_ebitda_bueno']}x")}<br>
        - {highlight(sector_bench['deuda_ebitda_bueno'] <= deuda_ebitda < sector_bench['deuda_ebitda_aceptable'], f"**Precaución:** {sector_bench['deuda_ebitda_bueno']}x - {sector_bench['deuda_ebitda_aceptable']}x")}<br>
        - {highlight(deuda_ebitda >= sector_bench['deuda_ebitda_aceptable'], f"**Riesgo Elevado:** > {sector_bench['deuda_ebitda_aceptable']}x")}
    """
    else:
        leyenda_salud += " - *No aplicable o datos no disponibles.*"

    leyenda_salud += f"<br><br>- **Ratio Cobertura de Intereses:** Mide cuántas veces la empresa puede pagar sus gastos por intereses anuales utilizando su beneficio operativo (EBIT). Es la prueba de fuego de la solvencia. Los rangos se ajustan para el sector **{datos['sector']}**.<br>"
    if int_coverage is not None:
         leyenda_salud += f"""
        - {highlight(int_coverage > sector_bench['int_coverage_excelente'], f"**Excelente:** > {sector_bench['int_coverage_excelente']}x")}<br>
        - {highlight(sector_bench['int_coverage_bueno'] < int_coverage <= sector_bench['int_coverage_excelente'], f"**Bueno:** > {sector_bench['int_coverage_bueno']}x")}<br>
        - {highlight(int_coverage <= sector_bench['int_coverage_bueno'], f"**Alerta:** < {sector_bench['int_coverage_bueno']}x")}
    """
    else:
        leyenda_salud += " - *No aplicable o datos no disponibles.*"
    
    leyenda_salud += "<br><br>- **Ratio Corriente (Liquidez):** Mide la capacidad de pagar deudas a corto plazo (en menos de un año) con sus activos a corto plazo.<br>"
    if ratio_corriente is not None:
        leyenda_salud += f"""
        - {highlight(ratio_corriente > 2.0, "**Excelente:** > 2.0")}<br>
        - {highlight(1.5 < ratio_corriente <= 2.0, "**Saludable:** > 1.5")}<br>
        - {highlight(1.0 < ratio_corriente <= 1.5, "**Aceptable:** > 1.0")}<br>
        - {highlight(ratio_corriente <= 1.0, "**Zona de Riesgo:** < 1.0")}
    """
    leyenda_salud += "<br><br>- **Flujo de Caja Libre (FCF):** Es el dinero real que le queda a la empresa después de sus gastos operativos y de inversión. Es el oxígeno del negocio.<br>"
    raw_fcf = datos.get('raw_fcf')
    if raw_fcf is not None:
        leyenda_salud += f"""
        - {highlight(raw_fcf > 0, "🟢 **Positivo:** La empresa genera más efectivo del que gasta.")}<br>
        - {highlight(raw_fcf <= 0, "🔴 **Negativo:** La empresa está quemando efectivo.")}
        """

    # --- Leyenda de Valoración ---
    per = datos.get('per')
    p_fcf = datos.get('p_fcf')
    pb = datos.get('p_b')
    valor_graham = puntuaciones.get('valor_graham')
    precio_actual = datos.get('precio_actual')
    peg = puntuaciones.get('peg_lynch')
    valor_weiss = puntuaciones.get('valor_weiss')
    
    leyenda_valoracion = ""
    if datos.get('sector') == 'Real Estate':
        leyenda_valoracion += "- **PER:** No es la métrica principal para REITs.<br>"
    elif per is not None:
        leyenda_valoracion += f"""- **PER (Price-to-Earnings):** Mide cuántas veces se está pagando el beneficio neto anual de la empresa. Los rangos se ajustan para el sector **{datos['sector']}**.<br>
        - {highlight(per < sector_bench['per_barato'], f"**Atractivo:** < {sector_bench['per_barato']}")}<br>
        - {highlight(sector_bench['per_barato'] <= per <= sector_bench['per_justo'], f"**Justo:** {sector_bench['per_barato']} - {sector_bench['per_justo']}")}<br>
        - {highlight(per > sector_bench['per_justo'], f"**Caro:** > {sector_bench['per_justo']}")}"""

    if p_fcf is not None:
        p_fcf_barato, p_fcf_justo = (16, 22) if datos.get('sector') == 'Real Estate' else (20, 30)
        leyenda_valoracion += f"""<br><br>- **P/FCF (Price-to-Free-Cash-Flow):** Mide cuántas veces se está pagando el flujo de caja libre. Es más difícil de manipular que el beneficio neto.<br>
        - {highlight(p_fcf < p_fcf_barato, f"**Atractivo:** < {p_fcf_barato}")}<br>
        - {highlight(p_fcf_barato <= p_fcf <= p_fcf_justo, f"**Justo:** {p_fcf_barato} - {p_fcf_justo}")}<br>
        - {highlight(p_fcf > p_fcf_justo, f"**Caro:** > {p_fcf_justo}")}"""
    
    leyenda_valoracion += "<br><br>---<br><b>Fórmulas Clásicas de Valoración:</b>"
    leyenda_valoracion += f"<br>- **Valor Intrínseco (B. Graham):** Estima el valor 'real' de una acción basado en sus beneficios y crecimiento esperado."
    if valor_graham and precio_actual:
        leyenda_valoracion += f'<br>  - {highlight(precio_actual < valor_graham, "Infravalorada: Precio actual por debajo del valor intrínseco.")}'
        leyenda_valoracion += f'<br>  - {highlight(precio_actual >= valor_graham, "Sobrevalorada: Precio actual por encima del valor intrínseco.")}'
    else:
        leyenda_valoracion += f'<br>  - {highlight(True, "No aplicable: Requiere beneficios y crecimiento positivos.")}'
        
    leyenda_valoracion += f"<br>- **Ratio PEG (Peter Lynch):** Relaciona el PER con el crecimiento de los beneficios."
    if peg:
        leyenda_valoracion += f'<br>  - {highlight(peg < 1, "Barato (PEG < 1): El precio parece bajo en relación al crecimiento.")}'
        leyenda_valoracion += f'<br>  - {highlight(peg >= 1, "Caro (PEG > 1): El precio parece alto para su crecimiento.")}'
    else:
        leyenda_valoracion += f'<br>  - {highlight(True, "No aplicable: Requiere PER y crecimiento positivos.")}'
        
    leyenda_valoracion += f"<br>- **Valor por Dividendo (G. Weiss):** Estima un precio justo asumiendo que el Yield volverá a su media histórica."
    if valor_weiss and precio_actual:
        leyenda_valoracion += f'<br>  - {highlight(precio_actual < valor_weiss, "Atractivo por Dividendo: El precio actual está por debajo del valor estimado.")}'
        leyenda_valoracion += f'<br>  - {highlight(precio_actual >= valor_weiss, "Poco Atractivo por Dividendo: El precio actual está por encima del valor estimado.")}'
    else:
        leyenda_valoracion += f'<br>  - {highlight(True, "No aplicable: Requiere que la empresa pague dividendos.")}'

    # --- Leyenda de Dividendos ---
    yield_div = datos.get('yield_dividendo', 0)
    payout = datos.get('payout_ratio', 0)
    
    leyenda_dividendos = f"""
    - **Rentabilidad (Yield):** Es el porcentaje que recibes anualmente en dividendos sobre el precio de la acción. Es tu 'alquiler' por ser propietario.<br>
        - {highlight(yield_div > 3.5, "Excelente: > 3.5%")}<br>
        - {highlight(2.0 < yield_div <= 3.5, "Bueno: > 2.0%")}<br>
        - {highlight(yield_div <= 2.0, "Bajo: < 2.0%")}
    <br><br>
    - **Ratio de Reparto (Payout):** Indica qué porcentaje del beneficio se destina a dividendos. Un payout bajo da margen para crecer, uno alto puede ser insostenible. Los rangos se ajustan para el sector **{datos['sector']}**.<br>
        - {highlight(0 < payout < sector_bench['payout_bueno'], f"Saludable: < {sector_bench['payout_bueno']}%")}<br>
        - {highlight(sector_bench['payout_bueno'] <= payout < sector_bench['payout_aceptable'], f"Precaución: > {sector_bench['payout_bueno']}%")}<br>
        - {highlight(payout >= sector_bench['payout_aceptable'], f"Peligroso: > {sector_bench['payout_aceptable']}%")}
    """

    # --- Leyenda Técnica ---
    leyenda_tecnico = ""
    if tech_data is not None and not tech_data.empty:
        last_price = tech_data['Close'].iloc[-1]
        sma200 = tech_data['SMA200'].iloc[-1]
        rsi = tech_data['RSI'].iloc[-1]
        tendencia_alcista = last_price > sma200
        rsi_sobreventa = rsi < 30
        rsi_sobrecompra = rsi > 70
        leyenda_tecnico = f"""
        - **Medias Móviles (SMA200):**<br>
            - {highlight(tendencia_alcista, "Señal Alcista 🟢: El precio está por encima de la media de 200 sesiones, indicando una tendencia a largo plazo positiva. Estrategia: buscar compras en retrocesos.")}<br>
            - {highlight(not tendencia_alcista, "Señal Bajista 🔴: El precio está por debajo de la media de 200 sesiones, indicando una tendencia a largo plazo negativa. Estrategia: evitar compras o buscar ventas.")}
        <br><br>
        - **RSI (Índice de Fuerza Relativa):**<br>
            - {highlight(rsi_sobreventa, "Sobreventa (< 30) 🟢: El activo ha caído de forma brusca. Podría indicar una oportunidad de compra por rebote, pero con riesgo si la tendencia principal es bajista.")}<br>
            - {highlight(rsi_sobrecompra, "Sobrecompra (> 70) 🔴: El activo ha subido de forma brusca. Podría indicar una futura corrección o una pausa en la subida. Es una señal para ser cauteloso.")}
        """

    # --- Leyenda Margen de Seguridad ---
    ms_analistas = puntuaciones.get('margen_seguridad_analistas', 0)
    ms_per = puntuaciones.get('margen_seguridad_per', 0)
    ms_yield = puntuaciones.get('margen_seguridad_yield', 0)
    leyenda_margen_seguridad = f"""
    - **Según Analistas:** Potencial hasta el precio objetivo medio.<br>
        - {highlight(ms_analistas > 20, "Alto Potencial: > 20%")}<br>
        - {highlight(0 <= ms_analistas <= 20, "Potencial Moderado: 0% a 20%")}<br>
        - {highlight(ms_analistas < 0, "Riesgo de Caída: < 0%")}
    <br><br>
    - **Según su PER Histórico:** Potencial si el PER actual vuelve a su media.<br>
        - {highlight(ms_per > 20, "Alto Potencial: > 20%")}<br>
        - {highlight(0 <= ms_per <= 20, "Potencial Moderado: 0% a 20%")}<br>
        - {highlight(ms_per < 0, "Riesgo de Caída: < 0%")}
    <br><br>
    - **Según su Yield Histórico:** Potencial si el Yield actual vuelve a su media.<br>
        - {highlight(ms_yield > 20, "Alto Potencial: > 20%")}<br>
        - {highlight(0 <= ms_yield <= 20, "Potencial Moderado: 0% a 20%")}<br>
        - {highlight(ms_yield < 0, "Riesgo de Caída: < 0%")}
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
                    leyendas = generar_leyenda_dinamica(datos, hist_data, puntuaciones, justificaciones, sector_bench, tech_data)
                    
                    pesos = {'calidad': 0.4, 'valoracion': 0.3, 'salud': 0.2, 'dividendos': 0.1}
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
                            st.warning("⚠️ **Riesgo Regulatorio (ADR/VIE):** Invertir en empresas chinas a través de ADRs conlleva riesgos adicionales.")
                        st.caption(justificaciones['geopolitico'])
                        st.write(f"**Descripción:** {datos['descripcion']}")
                    
                    with st.container(border=True):
                        st.subheader("Consenso de Analistas")
                        col_rec, col_obj = st.columns(2)
                        with col_rec:
                            recomendacion_str = datos.get('recomendacion_analistas', 'N/A').replace('_', ' ').title()
                            st.markdown(get_recommendation_html(recomendacion_str), unsafe_allow_html=True)
                        with col_obj:
                            mostrar_metrica_informativa("Precio Objetivo Analistas", datos.get('precio_objetivo'), potential_pct=puntuaciones.get('margen_seguridad_analistas'))

                    col1, col2 = st.columns(2)
                    with col1:
                        with st.container(border=True):
                            st.subheader(f"Calidad del Negocio [{puntuaciones['calidad']:.1f}/10]")
                            st.caption(justificaciones['calidad'])
                            c1, c2 = st.columns(2)
                            with c1:
                                mostrar_metrica_con_color("📈 ROE", datos['roe'], sector_bench['roe_excelente'], sector_bench['roe_bueno'], is_percent=True)
                                mostrar_metrica_con_color("💰 Margen Neto", datos['margen_beneficio'], sector_bench['margen_neto_excelente'], sector_bench['margen_neto_bueno'], is_percent=True)
                                mostrar_metrica_con_color("🚀 Crec. Ingresos (5a)", hist_data.get('cagr_rev_5y'), sector_bench['rev_growth_excelente'], sector_bench['rev_growth_bueno'], is_percent=True)
                            with c2:
                                mostrar_metrica_con_color("📊 Margen Operativo", datos['margen_operativo'], sector_bench['margen_excelente'], sector_bench['margen_bueno'], is_percent=True)
                                mostrar_metrica_con_color("🔥 Crec. Ingresos (YoY)", datos['crecimiento_ingresos_yoy'], sector_bench['rev_growth_excelente'], sector_bench['rev_growth_bueno'], is_percent=True)
                            with st.expander("Ver Leyenda Detallada"):
                                st.markdown(leyendas['calidad'], unsafe_allow_html=True)
                    with col2:
                        with st.container(border=True):
                            st.subheader(f"Salud Financiera [{puntuaciones['salud']:.1f}/10]")
                            st.caption(justificaciones['salud'])
                            s1, s2, s3 = st.columns(3)
                            with s1:
                                mostrar_metrica_con_color("⚡ Deuda Neta/EBITDA", datos['deuda_ebitda'], sector_bench['deuda_ebitda_bueno'], sector_bench['deuda_ebitda_aceptable'], lower_is_better=True)
                            with s2:
                                mostrar_metrica_con_color("🛡️ Cobertura Intereses", datos['interest_coverage'], sector_bench['int_coverage_excelente'], sector_bench['int_coverage_bueno'])
                            with s3:
                                mostrar_metrica_con_color("💧 Ratio Corriente", datos['ratio_corriente'], 1.5, 1.0)
                            
                            st.markdown("---")
                            mostrar_metrica_con_color("💰 Flujo de Caja Libre (FCF)", datos.get('raw_fcf'), 0, -1, is_currency=True)

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
                                if datos.get('raw_fcf') is not None and datos['raw_fcf'] < 0:
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
                            
                            mostrar_valor_formula("Valor Intrínseco (Graham)", "BPA * (8.5 + 2 * Crecimiento)", puntuaciones.get('valor_graham'), precio_actual)
                            mostrar_valor_formula("Valor por Dividendo (Weiss)", "Dividendo / Yield Histórico", puntuaciones.get('valor_weiss'), precio_actual)

                            peg_lynch = puntuaciones.get('peg_lynch')
                            prose, color_class = ("No aplicable", "color-white")
                            if peg_lynch is not None:
                                if peg_lynch < 1: prose, color_class = f"Barato ({peg_lynch:.2f})", "color-green"
                                elif peg_lynch > 1.5: prose, color_class = f"Caro ({peg_lynch:.2f})", "color-red"
                                else: prose, color_class = f"Justo ({peg_lynch:.2f})", "color-orange"
                            st.markdown(f'''<div class="metric-container">
                                            <div class="metric-label">Ratio PEG (Lynch)</div>
                                            <div class="metric-value {color_class}">{prose}</div>
                                            <div class="formula-label">PER / Crecimiento Beneficios</div>
                                        </div>''', unsafe_allow_html=True)

                        with st.expander("Ver Leyenda Detallada"):
                            st.markdown(leyendas['valoracion'], unsafe_allow_html=True)
                    
                    if datos['yield_dividendo'] > 0:
                        with st.container(border=True):
                            st.subheader(f"Dividendos [{puntuaciones['dividendos']:.1f}/10]")
                            st.caption(justificaciones['dividendos'])
                            
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
                            
                            tendencia_texto, tendencia_color = "Lateral 🟠", "color-orange"
                            if last_price > sma50 and sma50 > sma200: tendencia_texto, tendencia_color = "Alcista Fuerte 🟢", "color-green"
                            elif last_price > sma200: tendencia_texto, tendencia_color = "Alcista 🟢", "color-green"
                            elif last_price < sma50 and sma50 < sma200: tendencia_texto, tendencia_color = "Bajista Fuerte 🔴", "color-red"
                            elif last_price < sma200: tendencia_texto, tendencia_color = "Bajista 🔴", "color-red"
                            st.markdown(f'<div class="metric-container"><div class="metric-label">Tendencia Actual</div><div class="metric-value {tendencia_color}">{tendencia_texto}</div></div>', unsafe_allow_html=True)

                            rsi_texto, rsi_color = f"{rsi:.2f} (Neutral 🟠)", "color-orange"
                            if rsi > 70: rsi_texto, rsi_color = f"{rsi:.2f} (Sobrecompra 🔴)", "color-red"
                            elif rsi < 30: rsi_texto, rsi_color = f"{rsi:.2f} (Sobreventa 🟢)", "color-green"
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
