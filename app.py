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
    .st-emotion-cache-1r6slb0, [data-testid="stVerticalBlock"] > [style*="flex-direction: column;"] > [data-testid="stVerticalBlock"] { border: 1px solid #D4AF37 !important; border-radius: 10px; padding: 15px !important; margin-bottom: 1rem; }
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
    'Information Technology': {'roe_excelente': 25, 'roe_bueno': 18, 'roe_alerta': 18, 'margen_excelente': 25, 'margen_bueno': 18, 'margen_alerta': 18, 'margen_neto_excelente': 20, 'margen_neto_bueno': 15, 'margen_neto_alerta': 15, 'rev_growth_excelente': 15, 'rev_growth_bueno': 10, 'rev_growth_alerta': 10, 'fcf_growth_excelente': 15, 'fcf_growth_bueno': 10, 'fcf_growth_alerta': 10, 'per_barato': 25, 'per_justo': 35, 'pb_barato': 4, 'pb_justo': 8, 'payout_bueno': 60, 'payout_aceptable': 80, 'deuda_ebitda_bueno': 2, 'deuda_ebitda_aceptable': 3, 'deuda_patrimonio_bueno': 0.7, 'deuda_patrimonio_aceptable': 1.5, 'int_coverage_excelente': 10, 'int_coverage_bueno': 5},
    'Health Care': {'roe_excelente': 20, 'roe_bueno': 15, 'roe_alerta': 15, 'margen_excelente': 20, 'margen_bueno': 15, 'margen_alerta': 15, 'margen_neto_excelente': 15, 'margen_neto_bueno': 10, 'margen_neto_alerta': 10, 'rev_growth_excelente': 10, 'rev_growth_bueno': 6, 'rev_growth_alerta': 6, 'fcf_growth_excelente': 10, 'fcf_growth_bueno': 6, 'fcf_growth_alerta': 6, 'per_barato': 20, 'per_justo': 30, 'pb_barato': 3, 'pb_justo': 5, 'payout_bueno': 60, 'payout_aceptable': 80, 'deuda_ebitda_bueno': 3, 'deuda_ebitda_aceptable': 4, 'deuda_patrimonio_bueno': 1.0, 'deuda_patrimonio_aceptable': 2.0, 'int_coverage_excelente': 8, 'int_coverage_bueno': 4},
    'Financials': {'roe_excelente': 12, 'roe_bueno': 10, 'roe_alerta': 10, 'margen_excelente': 15, 'margen_bueno': 10, 'margen_alerta': 10, 'margen_neto_excelente': 10, 'margen_neto_bueno': 8, 'margen_neto_alerta': 8, 'rev_growth_excelente': 8, 'rev_growth_bueno': 4, 'rev_growth_alerta': 4, 'fcf_growth_excelente': 8, 'fcf_growth_bueno': 4, 'fcf_growth_alerta': 4, 'per_barato': 12, 'per_justo': 18, 'pb_barato': 1, 'pb_justo': 1.5, 'payout_bueno': 70, 'payout_aceptable': 90, 'deuda_ebitda_bueno': 1, 'deuda_ebitda_aceptable': 2, 'deuda_patrimonio_bueno': 2.0, 'deuda_patrimonio_aceptable': 4.0, 'int_coverage_excelente': 5, 'int_coverage_bueno': 3},
    'Industrials': {'roe_excelente': 18, 'roe_bueno': 14, 'roe_alerta': 14, 'margen_excelente': 15, 'margen_bueno': 10, 'margen_alerta': 10, 'margen_neto_excelente': 8, 'margen_neto_bueno': 6, 'margen_neto_alerta': 6, 'rev_growth_excelente': 10, 'rev_growth_bueno': 5, 'rev_growth_alerta': 5, 'fcf_growth_excelente': 10, 'fcf_growth_bueno': 5, 'fcf_growth_alerta': 5, 'per_barato': 20, 'per_justo': 25, 'pb_barato': 2.5, 'pb_justo': 4, 'payout_bueno': 60, 'payout_aceptable': 80, 'deuda_ebitda_bueno': 2.5, 'deuda_ebitda_aceptable': 4, 'deuda_patrimonio_bueno': 1.0, 'deuda_patrimonio_aceptable': 2.0, 'int_coverage_excelente': 7, 'int_coverage_bueno': 4},
    'Utilities': {'roe_excelente': 10, 'roe_bueno': 8, 'roe_alerta': 8, 'margen_excelente': 15, 'margen_bueno': 12, 'margen_alerta': 12, 'margen_neto_excelente': 8, 'margen_neto_bueno': 5, 'margen_neto_alerta': 5, 'rev_growth_excelente': 5, 'rev_growth_bueno': 3, 'rev_growth_alerta': 3, 'fcf_growth_excelente': 5, 'fcf_growth_bueno': 3, 'fcf_growth_alerta': 3, 'per_barato': 18, 'per_justo': 22, 'pb_barato': 1.5, 'pb_justo': 2, 'payout_bueno': 80, 'payout_aceptable': 95, 'deuda_ebitda_bueno': 4, 'deuda_ebitda_aceptable': 5.5, 'deuda_patrimonio_bueno': 1.5, 'deuda_patrimonio_aceptable': 2.5, 'int_coverage_excelente': 4, 'int_coverage_bueno': 2.5},
    'Consumer Discretionary': {'roe_excelente': 18, 'roe_bueno': 14, 'roe_alerta': 14, 'margen_excelente': 12, 'margen_bueno': 8, 'margen_alerta': 8, 'margen_neto_excelente': 7, 'margen_neto_bueno': 5, 'margen_neto_alerta': 5, 'rev_growth_excelente': 12, 'rev_growth_bueno': 7, 'rev_growth_alerta': 7, 'fcf_growth_excelente': 12, 'fcf_growth_bueno': 7, 'fcf_growth_alerta': 7, 'per_barato': 20, 'per_justo': 28, 'pb_barato': 3, 'pb_justo': 5, 'payout_bueno': 60, 'payout_aceptable': 80, 'deuda_ebitda_bueno': 3, 'deuda_ebitda_aceptable': 4.5, 'deuda_patrimonio_bueno': 1.0, 'deuda_patrimonio_aceptable': 2.5, 'int_coverage_excelente': 6, 'int_coverage_bueno': 3.5},
    'Consumer Staples': {'roe_excelente': 20, 'roe_bueno': 15, 'roe_alerta': 15, 'margen_excelente': 15, 'margen_bueno': 10, 'margen_alerta': 10, 'margen_neto_excelente': 8, 'margen_neto_bueno': 5, 'margen_neto_alerta': 5, 'rev_growth_excelente': 7, 'rev_growth_bueno': 4, 'rev_growth_alerta': 4, 'fcf_growth_excelente': 7, 'fcf_growth_bueno': 4, 'fcf_growth_alerta': 4, 'per_barato': 20, 'per_justo': 25, 'pb_barato': 4, 'pb_justo': 6, 'payout_bueno': 70, 'payout_aceptable': 85, 'deuda_ebitda_bueno': 3, 'deuda_ebitda_aceptable': 4.5, 'deuda_patrimonio_bueno': 1.2, 'deuda_patrimonio_aceptable': 2.5, 'int_coverage_excelente': 7, 'int_coverage_bueno': 4},
    'Energy': {'roe_excelente': 15, 'roe_bueno': 10, 'roe_alerta': 10, 'margen_excelente': 10, 'margen_bueno': 7, 'margen_alerta': 7, 'margen_neto_excelente': 8, 'margen_neto_bueno': 5, 'margen_neto_alerta': 5, 'rev_growth_excelente': 8, 'rev_growth_bueno': 0, 'rev_growth_alerta': 0, 'fcf_growth_excelente': 8, 'fcf_growth_bueno': 0, 'fcf_growth_alerta': 0, 'per_barato': 15, 'per_justo': 20, 'pb_barato': 1.5, 'pb_justo': 2.5, 'payout_bueno': 60, 'payout_aceptable': 80, 'deuda_ebitda_bueno': 2, 'deuda_ebitda_aceptable': 3, 'deuda_patrimonio_bueno': 0.8, 'deuda_patrimonio_aceptable': 1.5, 'int_coverage_excelente': 8, 'int_coverage_bueno': 5},
    'Materials': {'roe_excelente': 15, 'roe_bueno': 12, 'roe_alerta': 12, 'margen_excelente': 12, 'margen_bueno': 8, 'margen_alerta': 8, 'margen_neto_excelente': 7, 'margen_neto_bueno': 5, 'margen_neto_alerta': 5, 'rev_growth_excelente': 10, 'rev_growth_bueno': 5, 'rev_growth_alerta': 5, 'fcf_growth_excelente': 10, 'fcf_growth_bueno': 5, 'fcf_growth_alerta': 5, 'per_barato': 18, 'per_justo': 25, 'pb_barato': 2, 'pb_justo': 3, 'payout_bueno': 60, 'payout_aceptable': 80, 'deuda_ebitda_bueno': 2.5, 'deuda_ebitda_aceptable': 4, 'deuda_patrimonio_bueno': 0.8, 'deuda_patrimonio_aceptable': 1.5, 'int_coverage_excelente': 6, 'int_coverage_bueno': 3.5},
    'Real Estate': {'roe_excelente': 8, 'roe_bueno': 6, 'roe_alerta': 6, 'margen_excelente': 20, 'margen_bueno': 15, 'margen_alerta': 15, 'margen_neto_excelente': 15, 'margen_neto_bueno': 10, 'margen_neto_alerta': 10, 'rev_growth_excelente': 8, 'rev_growth_bueno': 4, 'rev_growth_alerta': 4, 'fcf_growth_excelente': 8, 'fcf_growth_bueno': 4, 'fcf_growth_alerta': 4, 'per_barato': 25, 'per_justo': 35, 'pb_barato': 2, 'pb_justo': 3, 'payout_bueno': 90, 'payout_aceptable': 100, 'deuda_ebitda_bueno': 5, 'deuda_ebitda_aceptable': 7, 'deuda_patrimonio_bueno': 1.5, 'deuda_patrimonio_aceptable': 3.0, 'int_coverage_excelente': 3, 'int_coverage_bueno': 2},
    'Communication Services': {'roe_excelente': 15, 'roe_bueno': 12, 'roe_alerta': 12, 'margen_excelente': 18, 'margen_bueno': 12, 'margen_alerta': 12, 'margen_neto_excelente': 12, 'margen_neto_bueno': 9, 'margen_neto_alerta': 9, 'rev_growth_excelente': 12, 'rev_growth_bueno': 7, 'rev_growth_alerta': 7, 'fcf_growth_excelente': 12, 'fcf_growth_bueno': 7, 'fcf_growth_alerta': 7, 'per_barato': 22, 'per_justo': 30, 'pb_barato': 3, 'pb_justo': 5, 'payout_bueno': 60, 'payout_aceptable': 80, 'deuda_ebitda_bueno': 3, 'deuda_ebitda_aceptable': 4.5, 'deuda_patrimonio_bueno': 1.0, 'deuda_patrimonio_aceptable': 2.0, 'int_coverage_excelente': 6, 'int_coverage_bueno': 3.5},
    'Default': {'roe_excelente': 15, 'roe_bueno': 12, 'roe_alerta': 12, 'margen_excelente': 15, 'margen_bueno': 10, 'margen_alerta': 10, 'margen_neto_excelente': 8, 'margen_neto_bueno': 5, 'margen_neto_alerta': 5, 'rev_growth_excelente': 10, 'rev_growth_bueno': 5, 'rev_growth_alerta': 5, 'fcf_growth_excelente': 10, 'fcf_growth_bueno': 5, 'fcf_growth_alerta': 5, 'per_barato': 20, 'per_justo': 25, 'pb_barato': 2, 'pb_justo': 4, 'payout_bueno': 60, 'payout_aceptable': 80, 'deuda_ebitda_bueno': 3, 'deuda_ebitda_aceptable': 5, 'deuda_patrimonio_bueno': 1.0, 'deuda_patrimonio_aceptable': 2.0, 'int_coverage_excelente': 5, 'int_coverage_bueno': 3}
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
    cashflow = stock.cashflow
    
    # --- CÁLCULO MANUAL Y FIABLE DE MÉTRICAS DE DEUDA Y CAPITAL ---
    ebit = financials.loc['EBIT'].iloc[0] if 'EBIT' in financials.index and not financials.loc['EBIT'].empty else None
    interest_expense = financials.loc['Interest Expense'].iloc[0] if 'Interest Expense' in financials.index and not financials.loc['Interest Expense'].empty else None
    
    interest_coverage = None
    if ebit is not None and interest_expense is not None and interest_expense != 0:
        interest_coverage = ebit / abs(interest_expense)
    
    deuda_ebitda = None
    total_debt = balance_sheet.loc['Total Debt'].iloc[0] if 'Total Debt' in balance_sheet.index and not balance_sheet.loc['Total Debt'].empty else info.get('totalDebt')
    cash = balance_sheet.loc['Cash And Cash Equivalents'].iloc[0] if 'Cash And Cash Equivalents' in balance_sheet.index and not balance_sheet.loc['Cash And Cash Equivalents'].empty else info.get('totalCash')
    ebitda = info.get('ebitda')

    if total_debt is not None and cash is not None and ebitda is not None and ebitda > 0:
        net_debt = total_debt - cash
        deuda_ebitda = net_debt / ebitda
    
    roe = info.get('returnOnEquity', 0) * 100
    
    # --- CÁLCULO DE RECOMPRAS NETAS (%) ---
    net_buybacks_pct = None
    try:
        shares_key = 'Basic Average Shares' if 'Basic Average Shares' in financials.index else 'Diluted Average Shares'
        if shares_key in financials.index and len(financials.columns) >= 2:
            shares_series = financials.loc[shares_key].dropna().loc[lambda x: x > 0]
            if len(shares_series) >= 2:
                shares_final = shares_series.iloc[0]
                shares_initial = shares_series.iloc[1]
                if shares_initial > 0:
                    net_buybacks_pct = ((shares_initial - shares_final) / shares_initial) * 100
    except Exception:
        net_buybacks_pct = None

    # --- LÓGICA DE DIVIDENDOS Y PAYOUT ---
    payout = info.get('payoutRatio')
    dividend_rate = info.get('dividendRate')
    precio = info.get('currentPrice')
    div_yield = (dividend_rate / precio) * 100 if dividend_rate and precio and precio > 0 else 0
    
    if payout is not None and (payout > 1.5 or payout < 0):
        trailing_eps = info.get('trailingEps')
        if trailing_eps and dividend_rate and trailing_eps > 0:
            payout = dividend_rate / trailing_eps
        else:
            payout = None

    free_cash_flow = info.get('freeCashflow')
    market_cap = info.get('marketCap')
    p_fcf = (market_cap / free_cash_flow) if market_cap and free_cash_flow and free_cash_flow > 0 else None

    # --- NUEVO: CÁLCULO DE PAYOUT SOBRE FCF ---
    payout_fcf_ratio = None
    dividends_paid = cashflow.loc['Cash Dividends Paid'].iloc[0] if 'Cash Dividends Paid' in cashflow.index and not cashflow.loc['Cash Dividends Paid'].empty else None
    if dividends_paid is not None and free_cash_flow is not None and free_cash_flow > 0:
        payout_fcf_ratio = abs(dividends_paid) / free_cash_flow

    descripcion_completa = info.get('longBusinessSummary', 'No disponible.')
    descripcion_corta = 'No disponible.'
    if descripcion_completa and descripcion_completa != 'No disponible.':
        first_period = descripcion_completa.find('.')
        if first_period != -1:
            second_period = descripcion_completa.find('.', first_period + 1)
            if second_period != -1:
                descripcion_corta = descripcion_completa[:second_period + 1].strip()
            else:
                descripcion_corta = descripcion_completa.strip()
    
    return {
        "nombre": info.get('longName', 'N/A'), "sector": info.get('sector', 'N/A'),
        "pais": info.get('country', 'N/A'), "industria": info.get('industry', 'N/A'),
        "descripcion": descripcion_corta,
        "roe": roe,
        "margen_operativo": info.get('operatingMargins', 0) * 100 if info.get('operatingMargins') is not None else 0,
        "margen_beneficio": info.get('profitMargins', 0) * 100 if info.get('profitMargins') is not None else 0,
        "ratio_corriente": info.get('currentRatio'),
        "per": info.get('trailingPE'), "per_adelantado": info.get('forwardPE'),
        "p_fcf": p_fcf,
        "raw_fcf": free_cash_flow,
        "p_b": info.get('priceToBook'),
        "crecimiento_ingresos_yoy": info.get('revenueGrowth', 0) * 100 if info.get('revenueGrowth') is not None else 0,
        "yield_dividendo": div_yield,
        "payout_ratio": payout * 100 if payout is not None else 0,
        "payout_fcf_ratio": payout_fcf_ratio * 100 if payout_fcf_ratio is not None else None,
        "recomendacion_analistas": info.get('recommendationKey', 'N/A'),
        "precio_objetivo": info.get('targetMeanPrice'), "precio_actual": info.get('currentPrice'),
        "bpa": info.get('trailingEps'),
        "crecimiento_beneficios_yoy": info.get('earningsGrowth'),
        "deuda_ebitda": deuda_ebitda,
        "interest_coverage": interest_coverage,
        "beta": info.get('beta', 'N/A'),
        "net_buybacks_pct": net_buybacks_pct,
        "financial_currency": info.get('financialCurrency', 'USD'),
        "market_cap": market_cap
    }

def calculate_cagr(end_value, start_value, years):
    if start_value is None or end_value is None or start_value <= 0 or years <= 0:
        return None
    try:
        return ((end_value / start_value) ** (1 / years) - 1) * 100
    except (ZeroDivisionError, ValueError):
        return None

@st.cache_data(ttl=3600)
def obtener_datos_historicos_y_tecnicos(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        if not isinstance(info, dict) or not info:
            return {}

        financials_raw = stock.financials
        balance_sheet_raw = stock.balance_sheet
        cashflow_raw = stock.cashflow
        
        financials_for_charts, dividends_for_charts = None, None
        cagr_rev, cagr_fcf = None, None

        if not financials_raw.empty:
            financials_annual = financials_raw.T.sort_index(ascending=True)
            if len(financials_annual) >= 5:
                years = 5
                start_year = financials_annual.index[-1].year - years
                start_rev_series = financials_annual[financials_annual.index.year == start_year].get('Total Revenue', pd.Series())
                start_rev = start_rev_series.iloc[0] if not start_rev_series.empty else None
                end_rev = financials_annual['Total Revenue'].iloc[-1] if 'Total Revenue' in financials_annual.columns else None
                cagr_rev = calculate_cagr(end_rev, start_rev, years)
            
            if cagr_rev is None and len(financials_annual) >= 3:
                years = 3
                start_year = financials_annual.index[-1].year - years
                start_rev_series = financials_annual[financials_annual.index.year == start_year].get('Total Revenue', pd.Series())
                start_rev = start_rev_series.iloc[0] if not start_rev_series.empty else None
                end_rev = financials_annual['Total Revenue'].iloc[-1] if 'Total Revenue' in financials_annual.columns else None
                cagr_rev = calculate_cagr(end_rev, start_rev, years)
        
        if not cashflow_raw.empty:
            cashflow_annual = cashflow_raw.T.sort_index(ascending=True)
            fcf_key = next((key for key in ['Free Cash Flow', 'Net Cash Flow From Continuing Investing Activities'] if key in cashflow_annual.columns), None)
            if fcf_key and len(cashflow_annual) >= 5:
                years_cf = 5
                start_year = cashflow_annual.index[-1].year - years_cf
                start_fcf_series = cashflow_annual[cashflow_annual.index.year == start_year].get(fcf_key, pd.Series())
                start_fcf = start_fcf_series.iloc[0] if not start_fcf_series.empty else None
                end_fcf = cashflow_annual[fcf_key].iloc[-1]
                cagr_fcf = calculate_cagr(end_fcf, start_fcf, years_cf)
            
            if cagr_fcf is None and fcf_key and len(cashflow_annual) >= 3:
                years_cf = 3
                start_year = cashflow_annual.index[-1].year - years_cf
                start_fcf_series = cashflow_annual[cashflow_annual.index.year == start_year].get(fcf_key, pd.Series())
                start_fcf = start_fcf_series.iloc[0] if not start_fcf_series.empty else None
                end_fcf = cashflow_annual[fcf_key].iloc[-1]
                cagr_fcf = calculate_cagr(end_fcf, start_fcf, years_cf)

        if not financials_raw.empty and not balance_sheet_raw.empty and not cashflow_raw.empty:
            financials = financials_raw.T.sort_index(ascending=True).tail(4)
            balance_sheet = balance_sheet_raw.T.sort_index(ascending=True).tail(4)
            cashflow = cashflow_raw.T.sort_index(ascending=True).tail(4)
            dividends_chart_data = stock.dividends.resample('YE').sum().tail(5)
            
            financials['Operating Margin'] = financials.get('Operating Income', 0) / financials.get('Total Revenue', 1)
            financials['Total Debt'] = balance_sheet.get('Total Debt', 0)
            financials['ROE'] = financials.get('Net Income', 0) / balance_sheet.get('Total Stockholder Equity', 1)
            
            if 'Free Cash Flow' not in cashflow.columns:
                capex = cashflow.get('Capital Expenditure', cashflow.get('Capital Expenditures', 0))
                op_cash = cashflow.get('Total Cash From Operating Activities', 0)
                cashflow['Free Cash Flow'] = op_cash + capex
            
            financials['Free Cash Flow'] = cashflow['Free Cash Flow']
            financials_for_charts, dividends_for_charts = financials, dividends_chart_data

        hist_10y = stock.history(period="10y")
        
        if hist_10y.empty:
            return {"financials_charts": financials_for_charts, "dividends_charts": dividends_for_charts, "per_hist": None, "yield_hist": None, "tech_data": None, "cagr_rev": cagr_rev, "cagr_fcf": cagr_fcf}
        
        pers, annual_yields = [], []
        per_historico, yield_historico = None, None
        
        # --- MODIFICADO: Se calcula siempre el PER Histórico, pero con advertencia si no es USD ---
        financial_currency = info.get('financialCurrency', 'USD')
        if financial_currency != 'USD':
            st.warning(f"⚠️ **Precaución con el PER Histórico:** La divisa de los estados financieros ({financial_currency}) no es USD. El cálculo del PER histórico puede ser impreciso debido a las fluctuaciones del tipo de cambio.")
        
        if not financials_raw.empty:
            net_income_key = 'Net Income'
            share_key = 'Basic Average Shares' if 'Basic Average Shares' in financials_raw.index else 'Diluted Average Shares'
            if net_income_key in financials_raw.index and share_key in financials_raw.index:
                for col_date in financials_raw.columns:
                    net_income = financials_raw.loc[net_income_key, col_date]
                    shares = financials_raw.loc[share_key, col_date]
                    if pd.notna(net_income) and pd.notna(shares) and shares > 0 and net_income > 0:
                        eps = net_income / shares
                        price_data_year = hist_10y[hist_10y.index.year == col_date.year]
                        if not price_data_year.empty:
                            avg_price = price_data_year['Close'].mean()
                            per_year = avg_price / eps
                            if 0 < per_year < 200:
                                pers.append(per_year)
        per_historico = np.mean(pers) if pers else None

        # --- Yield histórico se calcula siempre ---
        divs_10y = stock.dividends
        if not divs_10y.empty:
            annual_dividends = divs_10y.resample('YE').sum()
            annual_prices = hist_10y['Close'].resample('YE').mean()
            df_yield = pd.concat([annual_dividends, annual_prices], axis=1).dropna()
            df_yield.columns = ['Dividends', 'Price']
            if not df_yield.empty and 'Price' in df_yield and 'Dividends' in df_yield:
                annual_yields = ((df_yield['Dividends'] / df_yield['Price']) * 100).tolist()
        yield_historico = np.mean(annual_yields) if annual_yields else None

        # --- Análisis Técnico ---
        tech_data = None
        if not hist_10y.empty:
            end_date_1y = hist_10y.index.max()
            start_date_1y = end_date_1y - pd.DateOffset(days=365)
            tech_data = hist_10y[hist_10y.index >= start_date_1y].copy()
            
            if not tech_data.empty:
                tech_data['SMA50'] = tech_data['Close'].rolling(window=50).mean()
                tech_data['SMA200'] = tech_data['Close'].rolling(window=200).mean()
                delta = tech_data['Close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                rs = gain / (loss + 1e-10)
                tech_data['RSI'] = 100 - (100 / (1 + rs))

        return {
            "financials_charts": financials_for_charts, "dividends_charts": dividends_for_charts,
            "per_hist": per_historico, "yield_hist": yield_historico,
            "tech_data": tech_data,
            "cagr_rev": cagr_rev, "cagr_fcf": cagr_fcf,
        }
    except Exception as e:
        st.error(f"Se produjo un error al procesar los datos históricos y técnicos. Detalle: {e}")
        return {"financials_charts": None, "dividends_charts": None, "per_hist": None, "yield_hist": None, "tech_data": None, "cagr_rev": None, "cagr_fcf": None}

# --- BLOQUE 2: LÓGICA DE PUNTUACIÓN Y ANÁLISIS ---
def analizar_banderas_rojas(datos, financials):
    banderas = []
    payout_ratio = datos.get('payout_ratio')
    payout_fcf_ratio = datos.get('payout_fcf_ratio')
    
    if datos.get('sector') != 'Real Estate' and payout_ratio is not None and payout_ratio > 100:
        if payout_fcf_ratio is not None and payout_fcf_ratio < 90:
            st.warning(f"🟡 **Payout Elevado pero Sostenible por FCF:** El Payout sobre beneficios es del {payout_ratio:.0f}%, pero el Payout sobre Flujo de Caja Libre es de solo un {payout_fcf_ratio:.0f}%. El dividendo parece cubierto por la caja real.")
        else:
            banderas.append("🔴 **Payout Peligroso:** El ratio de reparto es superior al 100% y no está cubierto por el FCF. El dividendo podría no ser sostenible.")

    if financials is not None and not financials.empty:
        if 'Operating Margin' in financials.columns and len(financials) >= 3 and (financials['Operating Margin'].iloc[-3:].diff().iloc[1:] < 0).all():
            banderas.append("🔴 **Márgenes Decrecientes:** Los márgenes de beneficio llevan 3 años seguidos bajando.")
        if 'Total Debt' in financials.columns and len(financials) >= 3 and financials['Total Debt'].iloc[-1] > financials['Total Debt'].iloc[-3] * 1.5:
            banderas.append("🔴 **Deuda Creciente:** La deuda total ha aumentado significativamente.")
    if datos.get('raw_fcf') is not None and datos.get('raw_fcf', 0) < 0:
        banderas.append("🔴 **Flujo de Caja Libre Negativo:** La empresa está quemando más dinero del que genera.")
    if datos.get('interest_coverage') is not None and datos.get('interest_coverage') < 2:
        banderas.append("🔴 **Cobertura de Intereses Baja:** El beneficio operativo apenas cubre el pago de intereses.")
    if datos.get('ratio_corriente') is not None and datos.get('ratio_corriente') < 1.0:
        banderas.append("🔴 **Ratio Corriente (Liquidez) Baja:** Podría tener problemas para cubrir obligaciones a corto plazo.")
    if datos.get('market_cap') is not None and datos.get('market_cap') < 250000000:
        banderas.append("🔴 **Baja Capitalización de Mercado:** Inferior a $250M, puede implicar mayor volatilidad.")
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
    elif pais not in paises_seguros and pais != 'N/A': nota_geo, justificacion_geo, penalizador_geo = 5, "PRECAUCIÓN: Jurisdicción no clasificada.", 2.0
    puntuaciones['geopolitico'], justificaciones['geopolitico'], puntuaciones['penalizador_geo'] = nota_geo, justificacion_geo, penalizador_geo

    nota_calidad = 0
    if datos.get('roe') is not None and datos['roe'] > sector_bench['roe_excelente']: nota_calidad += 2.5
    elif datos.get('roe') is not None and datos['roe'] > sector_bench['roe_bueno']: nota_calidad += 1.5
    if datos.get('margen_operativo') is not None and datos['margen_operativo'] > sector_bench['margen_excelente']: nota_calidad += 2.5
    elif datos.get('margen_operativo') is not None and datos['margen_operativo'] > sector_bench['margen_bueno']: nota_calidad += 1.5
    if datos.get('margen_beneficio') is not None and datos['margen_beneficio'] > sector_bench.get('margen_neto_excelente', 8): nota_calidad += 2
    elif datos.get('margen_beneficio') is not None and datos['margen_beneficio'] > sector_bench.get('margen_neto_bueno', 5): nota_calidad += 1
    
    cagr_rev = hist_data.get('cagr_rev')
    if cagr_rev is not None and not np.isnan(cagr_rev):
        if cagr_rev > sector_bench['rev_growth_excelente']: nota_calidad += 2
        elif cagr_rev > sector_bench['rev_growth_bueno']: nota_calidad += 1
    if datos.get('crecimiento_ingresos_yoy') is not None and datos['crecimiento_ingresos_yoy'] > sector_bench['rev_growth_excelente']: nota_calidad += 1
    
    puntuaciones['calidad'] = min(10, nota_calidad)
    justificaciones['calidad'] = "Rentabilidad, márgenes y crecimiento de élite." if puntuaciones['calidad'] >= 8 else "Negocio de buena calidad."

    nota_salud = 0
    if sector != 'Financials':
        deuda_ebitda = datos.get('deuda_ebitda')
        if deuda_ebitda is not None and not np.isnan(deuda_ebitda):
            if deuda_ebitda < 0: nota_salud += 2.5
            elif deuda_ebitda < sector_bench['deuda_ebitda_bueno']: nota_salud += 2.5
            elif deuda_ebitda < sector_bench['deuda_ebitda_aceptable']: nota_salud += 1.5

    interest_coverage = datos.get('interest_coverage')
    if interest_coverage is not None:
        if interest_coverage > sector_bench['int_coverage_excelente']: nota_salud += 2.5
        elif interest_coverage > sector_bench['int_coverage_bueno']: nota_salud += 1.5
        
    ratio_corriente = datos.get('ratio_corriente')
    if ratio_corriente is not None and ratio_corriente > 1.5:
        nota_salud += 2.5
        
    if datos.get('raw_fcf', 0) is not None and datos.get('raw_fcf', 0) <= 0:
        nota_salud -= 4
    
    # --- RESTAURADO: Puntuación para Crecimiento de FCF ---
    cagr_fcf = hist_data.get('cagr_fcf')
    if cagr_fcf is not None and not np.isnan(cagr_fcf) and cagr_fcf > 0:
        nota_salud += 1
    elif cagr_fcf is not None and not np.isnan(cagr_fcf) and cagr_fcf < 0:
        nota_salud -= 1

    puntuaciones['salud'] = max(0, min(10, nota_salud))
    justificaciones['salud'] = "Balance muy sólido y solvente." if puntuaciones['salud'] >= 8 else "Salud financiera aceptable."
    
    nota_multiplos = 0
    if sector == 'Real Estate':
        if datos.get('p_fcf') is not None and datos['p_fcf'] < 16: nota_multiplos += 8
        elif datos.get('p_fcf') is not None and datos['p_fcf'] < 22: nota_multiplos += 5
    else:
        if datos.get('per') is not None and datos['per'] > 0 and not np.isnan(datos['per']):
            if datos['per'] < sector_bench['per_barato']: nota_multiplos += 4
            elif datos['per'] < sector_bench['per_justo']: nota_multiplos += 2
        
        if datos.get('p_fcf') is not None and datos['p_fcf'] > 0 and not np.isnan(datos['p_fcf']):
            if datos['p_fcf'] < 20: nota_multiplos += 4
            elif datos['p_fcf'] < 30: nota_multiplos += 2

    SECTORES_PB_RELEVANTES = ['Financials', 'Industrials', 'Materials', 'Energy', 'Utilities', 'Real Estate']
    if sector in SECTORES_PB_RELEVANTES and datos.get('p_b') is not None and not np.isnan(datos['p_b']):
        if datos['p_b'] < sector_bench['pb_barato']: nota_multiplos += 2
    
    if datos.get('raw_fcf') is not None and datos['raw_fcf'] < 0:
        nota_multiplos -= 4

    nota_analistas, margen_seguridad = 0, 0
    if datos.get('precio_actual') is not None and datos.get('precio_objetivo') is not None:
        margen_seguridad = ((datos['precio_objetivo'] - datos['precio_actual']) / datos['precio_actual']) * 100
        if margen_seguridad > 25: nota_analistas = 10
        elif margen_seguridad > 15: nota_analistas = 8
        elif margen_seguridad > 5: nota_analistas = 5
    puntuaciones['margen_seguridad_analistas'] = margen_seguridad

    potencial_per, potencial_yield = 0, 0
    per_historico = hist_data.get('per_hist')
    if per_historico is not None and datos.get('per') is not None and datos['per'] > 0 and per_historico > 0:
        potencial_per = ((per_historico / datos['per']) - 1) * 100
    puntuaciones['margen_seguridad_per'] = potencial_per

    yield_historico = hist_data.get('yield_hist')
    if yield_historico is not None and datos.get('yield_dividendo') is not None and datos['yield_dividendo'] > 0 and yield_historico > 0:
        potencial_yield = ((datos['yield_dividendo'] - yield_historico) / yield_historico) * 100
    else:
        potencial_yield = None
    puntuaciones['margen_seguridad_yield'] = potencial_yield
    
    nota_historica = 0
    if potencial_per is not None and potencial_per > 15: nota_historica += 5
    if potencial_yield is not None and potencial_yield > 15: nota_historica += 5
    nota_historica = min(10, nota_historica)

    nota_valoracion_base = (nota_multiplos * 0.4) + (nota_analistas * 0.3) + (nota_historica * 0.3)
    
    per_actual = datos.get('per')
    per_adelantado = datos.get('per_adelantado')
    if per_actual is not None and per_adelantado is not None and per_actual > 0 and per_adelantado > 0:
        if per_adelantado < per_actual * 0.9:
            nota_valoracion_base += 1
        elif per_adelantado > per_actual:
            nota_valoracion_base -= 1

    if puntuaciones['calidad'] < 3:
        nota_valoracion_base *= 0.5
    elif puntuaciones['calidad'] < 5:
        nota_valoracion_base *= 0.75

    puntuaciones['valoracion'] = max(0, min(10, nota_valoracion_base))
    if puntuaciones['valoracion'] >= 8: justificaciones['valoracion'] = "Valoración muy atractiva."
    else: justificaciones['valoracion'] = "Valoración razonable o exigente."

    nota_dividendos = 0
    if datos.get('yield_dividendo') is not None and datos['yield_dividendo'] > 3.5: nota_dividendos += 5
    elif datos.get('yield_dividendo') is not None and datos['yield_dividendo'] > 2: nota_dividendos += 3
    
    if datos.get('payout_ratio') is not None and 0 < datos['payout_ratio'] < sector_bench['payout_bueno']: nota_dividendos += 5
    elif datos.get('payout_ratio') is not None and 0 < datos['payout_ratio'] < sector_bench['payout_aceptable']: nota_dividendos += 3

    net_buybacks_pct = datos.get('net_buybacks_pct')
    if net_buybacks_pct is not None and not np.isnan(net_buybacks_pct):
        if net_buybacks_pct > 1:
            nota_dividendos += 2
        elif net_buybacks_pct < -1:
            nota_dividendos -= 2
    
    puntuaciones['dividendos'] = min(10, nota_dividendos)
    justificaciones['dividendos'] = "Dividendo excelente y sostenible." if puntuaciones['dividendos'] >= 8 else "Dividendo sólido."
    
    per = datos.get('per')
    crecimiento_yoy = datos.get('earningsGrowth')
    
    puntuaciones['peg_lynch'] = None
    if per is not None and per > 0 and crecimiento_yoy is not None and crecimiento_yoy > 0:
        puntuaciones['peg_lynch'] = per / (crecimiento_yoy * 100)

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
    if 'SMA50' in data.columns and not data['SMA50'].isnull().all():
        ax1.plot(data.index, data['SMA50'], label='Media Móvil 50 días', color='#FFA500', linestyle='--')
    if 'SMA200' in data.columns and not data['SMA200'].isnull().all():
        ax1.plot(data.index, data['SMA200'], label='Media Móvil 200 días', color='#FF0000', linestyle='--')
    ax1.set_title('Análisis Técnico del Precio (Último Año)', color='white')
    ax1.legend()
    ax1.grid(color='gray', linestyle='--', linewidth=0.5)
    ax1.tick_params(axis='y', colors='white')
    ax1.spines['top'].set_color('white'); ax1.spines['bottom'].set_color('white'); ax1.spines['left'].set_color('white'); ax1.spines['right'].set_color('white')

    ax2.set_facecolor('#0E1117')
    if 'RSI' in data.columns and not data['RSI'].isnull().all():
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

def mostrar_crecimiento_con_color(label, value, umbral_excelente, umbral_bueno):
    if value is None or (isinstance(value, float) and np.isnan(value)):
        formatted_value = "N/A"
        color_class = "color-white"
    else:
        try:
            numeric_value = float(str(value).replace('%', ''))
            if numeric_value > umbral_excelente:
                color_class = "color-green"
            elif numeric_value > umbral_bueno:
                color_class = "color-orange"
            else:
                color_class = "color-red"
            formatted_value = f"{numeric_value:.2f}%"
        except (ValueError, TypeError):
            formatted_value = "N/A"
            color_class = "color-white"
    
    st.markdown(f'<div class="metric-container"><div class="metric-label">{label}</div><div class="metric-value {color_class}">{formatted_value}</div></div>', unsafe_allow_html=True)

def mostrar_metrica_con_color(label, value, umbral_bueno, umbral_malo=None, lower_is_better=False, is_percent=False, is_currency=False):
    if value is None or (isinstance(value, float) and np.isnan(value)):
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
    if isinstance(value, (int, float)) and not np.isnan(value):
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
    if isinstance(value, (int, float)) and not np.isnan(value):
        formatted_value = f"{value:.2f}%" if is_percent else f"{value:.2f}"
    
    if potential_pct is not None and not np.isnan(potential_pct):
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
    
    is_comparable = (isinstance(current_value, (int, float)) and not np.isnan(current_value)) and \
                      (isinstance(historical_value, (int, float)) and not np.isnan(historical_value))

    if is_comparable:
        if lower_is_better:
            if current_value < historical_value: color_class = "color-green"
            elif current_value > historical_value: color_class = "color-red"
        else: 
            if current_value > historical_value: color_class = "color-green"
            elif current_value < historical_value: color_class = "color-red"

    if is_percent:
        formatted_current = f"{current_value:.2f}%" if isinstance(current_value, (int, float)) and not np.isnan(current_value) else "N/A"
        formatted_historical = f"vs {historical_value:.2f}%" if isinstance(historical_value, (int, float)) and not np.isnan(historical_value) else ""
    else:
        formatted_current = f"{current_value:.2f}" if isinstance(current_value, (int, float)) and not np.isnan(current_value) else "N/A"
        formatted_historical = f"vs {historical_value:.2f}" if isinstance(historical_value, (int, float)) and not np.isnan(historical_value) else ""

    st.markdown(f'''
    <div class="metric-container">
        <div class="metric-label">{label}</div>
        <div class="metric-value {color_class}">{formatted_current}</div>
        <div class="metric-label" style="line-height: 1; color: #FAFAFA;">{formatted_historical}</div>
    </div>
    ''', unsafe_allow_html=True)

def generar_leyenda_dinamica(datos, hist_data, puntuaciones, sector_bench, tech_data):
    highlight_style = 'style="background-color: #D4AF37; color: #0E1117; padding: 2px 5px; border-radius: 3px;"'
    
    def highlight(condition, text):
        return f"<span {highlight_style}>{text}</span>" if condition else text

    # --- Leyenda de Calidad ---
    roe = datos.get('roe', 0)
    margen_op = datos.get('margen_operativo', 0)
    margen_neto = datos.get('margen_beneficio', 0)
    cagr_rev = hist_data.get('cagr_rev')
    yoy_rev = datos.get('crecimiento_ingresos_yoy', 0)
    
    leyenda_calidad = f"""
- **ROE (Return on Equity):** Mide la rentabilidad que la empresa es capaz de sacar de nuestro dinero, el de los accionistas. Un ROE alto es un indicativo de un negocio fuerte y bien gestionado.<br>
Rangos para el sector **{datos['sector']}**:<br>
    - {highlight(roe > sector_bench['roe_excelente'], f"**Excelente:** > {sector_bench['roe_excelente']}%")}<br>
    - {highlight(sector_bench['roe_bueno'] < roe <= sector_bench['roe_excelente'], f"**Bueno:** > {sector_bench['roe_bueno']}%")}<br>
    - {highlight(roe <= sector_bench['roe_bueno'], f"**Alerta:** < {sector_bench['roe_bueno']}%")}
<br><br>
- **Margen Operativo:** El porcentaje de beneficio que le queda a la empresa de sus ventas tras pagar los costes de producción y gestión. Un margen alto refleja una **fuerte ventaja competitiva**.<br>
Rangos para el sector **{datos['sector']}**:<br>
    - {highlight(margen_op > sector_bench['margen_excelente'], f"**Excelente:** > {sector_bench['margen_excelente']}%")}<br>
    - {highlight(sector_bench['margen_bueno'] < margen_op <= sector_bench['margen_excelente'], f"**Bueno:** > {sector_bench['margen_bueno']}%")}<br>
    - {highlight(margen_op <= sector_bench['margen_bueno'], f"**Alerta:** < {sector_bench['margen_bueno']}%")}
<br><br>
- **Margen Neto:** El porcentaje final de las ventas que se convierte en beneficio para el accionista. Es el "dinero de verdad" que queda después de todos los gastos e impuestos.<br>
Rangos para el sector **{datos['sector']}**:<br>
    - {highlight(margen_neto > sector_bench['margen_neto_excelente'], f"**Excelente:** > {sector_bench['margen_neto_excelente']}%")}<br>
    - {highlight(sector_bench['margen_neto_bueno'] < margen_neto <= sector_bench['margen_neto_excelente'], f"**Bueno:** > {sector_bench['margen_neto_bueno']}%")}<br>
    - {highlight(margen_neto <= sector_bench['margen_neto_bueno'], f"**Alerta:** < {sector_bench['margen_neto_bueno']}%")}
<br><br>
- **Crecimiento Ingresos (CAGR):** El crecimiento anual compuesto de las ventas. Indica la salud y el potencial a largo plazo.<br>
Rangos para el sector **{datos['sector']}**:<br>
"""
    if cagr_rev is not None and not np.isnan(cagr_rev):
        leyenda_calidad += f"""
    - {highlight(cagr_rev > sector_bench['rev_growth_excelente'], f"**Excelente:** > {sector_bench['rev_growth_excelente']}%")}<br>
    - {highlight(sector_bench['rev_growth_bueno'] < cagr_rev <= sector_bench['rev_growth_excelente'], f"**Bueno:** > {sector_bench['rev_growth_bueno']}%")}<br>
    - {highlight(cagr_rev <= sector_bench['rev_growth_bueno'], f"**Lento/Negativo:** < {sector_bench['rev_growth_bueno']}%")}
"""
    else:
        leyenda_calidad += " - <i>Datos no disponibles.</i>"
        
    leyenda_calidad += f"""
<br><br>
- **Crecimiento Ingresos (YoY):** El crecimiento de ventas en el último año. Indica la salud actual del negocio.<br>
Rangos para el sector **{datos['sector']}**:<br>
    - {highlight(yoy_rev > sector_bench['rev_growth_excelente'], f"**Excelente:** > {sector_bench['rev_growth_excelente']}%")}<br>
    - {highlight(yoy_rev is not None and sector_bench['rev_growth_bueno'] < yoy_rev <= sector_bench['rev_growth_excelente'], f"**Bueno:** > {sector_bench['rev_growth_bueno']}%")}<br>
    - {highlight(yoy_rev is not None and yoy_rev <= sector_bench['rev_growth_bueno'], f"**Lento/Negativo:** < {sector_bench['rev_growth_bueno']}%")}
"""

    # --- Leyenda de Salud Financiera ---
    deuda_ebitda = datos.get('deuda_ebitda')
    int_coverage = datos.get('interest_coverage')
    raw_fcf = datos.get('raw_fcf')
    cagr_fcf = hist_data.get('cagr_fcf')
    ratio_corriente = datos.get('ratio_corriente')

    leyenda_salud = f"""
- **Ratio Corriente (Liquidez):** Mide si la empresa puede pagar sus deudas a corto plazo con sus activos a corto plazo. Un valor de 1.5 o más es saludable.<br>
Rangos:<br>
    - {highlight(ratio_corriente is not None and ratio_corriente > 1.5, "**Líquido:** > 1.5x")}<br>
    - {highlight(ratio_corriente is not None and 1.0 <= ratio_corriente <= 1.5, "**Suficiente:** 1.0x - 1.5x")}<br>
    - {highlight(ratio_corriente is not None and ratio_corriente < 1.0, "**Riesgo:** < 1.0x")}
<br><br>
- **Deuda Neta / EBITDA:** Indica en cuántos años la empresa podría pagar su deuda neta con sus ganancias operativas. Un valor bajo es mejor.<br>
Rangos para el sector **{datos['sector']}**:<br>"""
    if datos['sector'] == 'Financials':
        leyenda_salud += " - <i>No aplicable para el sector Financiero.</i>"
    elif deuda_ebitda is not None and not np.isnan(deuda_ebitda):
        leyenda_salud += f"""
- {highlight(deuda_ebitda < sector_bench['deuda_ebitda_bueno'], f"**Saludable:** < {sector_bench['deuda_ebitda_bueno']}x")}<br>
- {highlight(deuda_ebitda >= sector_bench['deuda_ebitda_bueno'] and deuda_ebitda <= sector_bench['deuda_ebitda_aceptable'], f"**Precaución:** {sector_bench['deuda_ebitda_bueno']}x - {sector_bench['deuda_ebitda_aceptable']}x")}<br>
- {highlight(deuda_ebitda > sector_bench['deuda_ebitda_aceptable'], f"**Riesgo Elevado:** > {sector_bench['deuda_ebitda_aceptable']}x")}
"""
    else:
        leyenda_salud += " - <i>Datos no disponibles.</i>"

    leyenda_salud += f"""<br><br>- **Cobertura de Intereses:** Indica cuántas veces el beneficio operativo (EBIT) cubre los gastos de intereses de su deuda. Un ratio alto reduce el riesgo financiero.<br>"""
    if int_coverage is not None and not np.isnan(int_coverage):
        leyenda_salud += f"""
- {highlight(int_coverage > sector_bench['int_coverage_excelente'], f"**Excelente:** > {sector_bench['int_coverage_excelente']}x")}<br>
- {highlight(int_coverage >= sector_bench['int_coverage_bueno'] and int_coverage <= sector_bench['int_coverage_excelente'], f"**Bueno:** > {sector_bench['int_coverage_bueno']}x")}<br>
- {highlight(int_coverage < sector_bench['int_coverage_bueno'], f"**Alerta:** < {sector_bench['int_coverage_bueno']}x")}
"""
    else:
        leyenda_salud += " - <i>Datos no disponibles.</i>"
    
    leyenda_salud += """<br><br>- **Flujo de Caja Libre (FCF):** Es el dinero real que el negocio genera. Un FCF positivo es vital para el crecimiento y los dividendos.<br>"""
    if raw_fcf is not None and not np.isnan(raw_fcf):
        leyenda_salud += f"""
- {highlight(raw_fcf > 0, "🟢 **Positivo:** La empresa genera más efectivo del que gasta.")}<br>
- {highlight(raw_fcf <= 0, "🔴 **Negativo:** La empresa está quemando efectivo. No es sostenible a largo plazo.")}
"""
    else:
        leyenda_salud += f" - <i>{highlight(True, 'Datos no disponibles.')}</i>"
        
    leyenda_salud += f"""
<br><br>
- **Crecimiento de FCF (CAGR):** El crecimiento anual compuesto del Flujo de Caja Libre.<br>
Rangos para el sector **{datos['sector']}**:<br>
"""
    if cagr_fcf is not None and not np.isnan(cagr_fcf):
        leyenda_salud += f"""
    - {highlight(cagr_fcf > sector_bench['fcf_growth_excelente'], f"**Excelente:** > {sector_bench['fcf_growth_excelente']}%")}<br>
    - {highlight(sector_bench['fcf_growth_bueno'] < cagr_fcf <= sector_bench['fcf_growth_excelente'], f"**Bueno:** > {sector_bench['fcf_growth_bueno']}%")}<br>
    - {highlight(cagr_fcf <= sector_bench['fcf_growth_bueno'], f"**Lento/Negativo:** < {sector_bench['fcf_growth_bueno']}%")}
"""
    else:
        leyenda_salud += " - <i>Datos no disponibles.</i>"

    # --- Leyenda de Valoración ---
    per = datos.get('per')
    p_fcf = datos.get('p_fcf')
    p_b = datos.get('p_b')
    
    leyenda_valoracion = f"""
- **PER (Price-to-Earnings):** Indica cuántas veces el beneficio anual se paga al comprar la acción. Un PER bajo es atractivo si la empresa es de calidad.<br>
Rangos para el sector **{datos['sector']}**:<br>
"""
    if datos.get('sector') == 'Real Estate':
        leyenda_valoracion += " - <i>No es la métrica principal para los REITs. Es mejor usar P/FCF.</i>"
    elif per is not None and per > 0 and not np.isnan(per):
        leyenda_valoracion += f"""
    - {highlight(per < sector_bench['per_barato'], f"**Atractivo:** < {sector_bench['per_barato']}")}<br>
    - {highlight(per >= sector_bench['per_barato'] and per <= sector_bench['per_justo'], f"**Justo:** {sector_bench['per_barato']} - {sector_bench['per_justo']}")}<br>
    - {highlight(per > sector_bench['per_justo'], f"**Caro:** > {sector_bench['per_justo']}")}"""
    else:
        leyenda_valoracion += f"""- {highlight(True, "**No aplicable (negativo o N/A).**")}"""

    if p_fcf is not None and p_fcf > 0 and not np.isnan(p_fcf):
        p_fcf_barato, p_fcf_justo = (16, 22) if datos.get('sector') == 'Real Estate' else (20, 30)
        leyenda_valoracion += f"""<br><br>- **P/FCF (Price-to-Free-Cash-Flow):** Mide el precio de la acción contra el dinero real que genera. Es un ratio más robusto que el PER.<br>
Rangos:<br>
    - {highlight(p_fcf < p_fcf_barato, f"**Atractivo:** < {p_fcf_barato}")}<br>
    - {highlight(p_fcf_barato <= p_fcf <= p_fcf_justo, f"**Justo:** {p_fcf_barato} - {p_fcf_justo}")}<br>
    - {highlight(p_fcf > p_fcf_justo, f"**Caro:** > {p_fcf_justo}")}"""
    else:
        leyenda_valoracion += f"""<br><br>- **P/FCF:** {highlight(True, "**No aplicable (negativo o N/A).**")}"""
    
    leyenda_valoracion += f"""<br><br>- **P/B (Precio/Libros):** Compara el precio con su valor contable. Es útil para sectores con activos tangibles (banca, industria). Es menos relevante para empresas de tecnología o marcas.<br>"""
    if p_b is not None and not np.isnan(p_b):
        leyenda_valoracion += f"""Rangos para el sector **{datos['sector']}**:<br>
    - {highlight(p_b < sector_bench['pb_barato'], f"**Atractivo:** < {sector_bench['pb_barato']}")}<br>
    - {highlight(p_b >= sector_bench['pb_barato'] and p_b <= sector_bench['pb_justo'], f"**Justo:** {sector_bench['pb_barato']} - {sector_bench['pb_justo']}")}<br>
    - {highlight(p_b > sector_bench['pb_justo'], f"**Caro:** > {sector_bench['pb_justo']}")}"""
    else:
        leyenda_valoracion += f""" - {highlight(True, "**No aplicable o datos no disponibles.**")}"""

    # --- Leyenda PEG ---
    peg = puntuaciones.get('peg_lynch')
    leyenda_peg = f"""- **Ratio PEG (Peter Lynch):** Relaciona el PER con el crecimiento de los beneficios (<code>PER / Crecimiento %</code>). Un valor por debajo de 1 puede indicar que la acción está infravalorada en relación a su crecimiento.<br>
Rangos:<br>"""
    if peg is not None and not np.isnan(peg) and peg > 0:
        leyenda_peg += f' - {highlight(peg < 1, "**Interesante (PEG < 1)**")}<br>'
        leyenda_peg += f' - {highlight(1 <= peg <= 1.5, "**Neutral (PEG 1-1.5)**")}<br>'
        leyenda_peg += f' - {highlight(peg > 1.5, "**No Interesante (PEG > 1.5)**")}'
    else:
        leyenda_peg += f' - {highlight(True, "**No aplicable.**")}'

    # --- Leyenda de Dividendos & Recompras (Simplificada) ---
    yield_div = datos.get('yield_dividendo', 0)
    payout = datos.get('payout_ratio', 0)
    net_buybacks_pct = datos.get('net_buybacks_pct')
    
    leyenda_dividendos = f"""
- **Rentabilidad (Yield):** El porcentaje de tu inversión que recibes anualmente en forma de dividendos.<br>
Rangos:<br>
    - {highlight(yield_div > 3.5, "**Excelente:** > 3.5%")}<br>
    - {highlight(2.0 < yield_div <= 3.5, "**Bueno:** > 2.0%")}<br>
    - {highlight(yield_div <= 2.0, "**Bajo:** < 2.0%")}
<br><br>
- **Ratio de Reparto (Payout):** El porcentaje del beneficio que la empresa destina a dividendos. Un payout sostenible deja margen para reinvertir en el negocio.<br>
Rangos para el sector **{datos['sector']}**:<br>
    - {highlight(0 < payout < sector_bench['payout_bueno'], f"**Saludable:** < {sector_bench['payout_bueno']}%")}<br>
    - {highlight(payout >= sector_bench['payout_bueno'] and payout <= sector_bench['payout_aceptable'], f"**Precaución:** {sector_bench['payout_bueno']}% - {sector_bench['payout_aceptable']}%")}<br>
    - {highlight(payout > sector_bench['payout_aceptable'], f"**Peligroso:** > {sector_bench['payout_aceptable']}%")}
<br><br>
- **Recompras Netas (%):** Mide el cambio en el número de acciones. Un valor positivo (recompras) es bueno para el accionista, uno negativo (dilución) es malo.<br>
"""
    if net_buybacks_pct is not None and not np.isnan(net_buybacks_pct):
        leyenda_dividendos += f"""
    - {highlight(net_buybacks_pct > 1, "**🟢 Aumento de Valor:** Recompra de acciones.")}<br>
    - {highlight(-1 <= net_buybacks_pct <= 1, "**⚪ Neutral:** Número de acciones estable.")}<br>
    - {highlight(net_buybacks_pct < -1, "**🔴 Dilución:** Emisión de nuevas acciones.")}<br>
"""
    else:
        leyenda_dividendos += f"    - {highlight(True, '<i>**Desconocido.**</i>')}"

    # --- Leyenda Técnica ---
    leyenda_tecnico = ""
    if tech_data is not None and not tech_data.empty:
        last_price = tech_data['Close'].iloc[-1] if not tech_data['Close'].empty else None
        sma50 = tech_data['SMA50'].iloc[-1] if not tech_data['SMA50'].isnull().all() else None
        sma200 = tech_data['SMA200'].iloc[-1] if not tech_data['SMA200'].isnull().all() else None
        rsi_series = tech_data.get('RSI', pd.Series(dtype=float))
        rsi = rsi_series.iloc[-1] if not rsi_series.empty and pd.notna(rsi_series.iloc[-1]) else None
        beta = datos.get('beta')
        
        tendencia_alcista_largo = pd.notna(last_price) and pd.notna(sma200) and last_price > sma200
        tendencia_alcista_corto = pd.notna(last_price) and pd.notna(sma50) and last_price > sma50
        rsi_sobreventa = pd.notna(rsi) and rsi < 30
        rsi_sobrecompra = pd.notna(rsi) and rsi > 70
        
        resumen_texto = "Los indicadores no ofrecen una señal de compra o venta particularmente fuerte."
        if (tendencia_alcista_largo or tendencia_alcista_corto) and rsi_sobreventa:
            resumen_texto = "La acción está en una tendencia positiva y el RSI indica sobreventa. Esta combinación podría ser una señal de compra interesante, ya que la acción podría rebotar dentro de su tendencia principal."
        elif (tendencia_alcista_largo or tendencia_alcista_corto) and rsi_sobrecompra:
            resumen_texto = "La acción está en una tendencia positiva, pero el RSI indica que está sobrecomprada. Esto podría sugerir una pausa o corrección inminente antes de continuar con la tendencia."
        elif (not tendencia_alcista_largo and not tendencia_alcista_corto) and rsi_sobreventa:
            resumen_texto = "A pesar de que el RSI muestra sobreventa, la tendencia general es bajista. Cuidado, el rebote podría ser solo temporal dentro de una tendencia negativa más fuerte."
        
        leyenda_tecnico = f"""
- **Medias Móviles (SMA):** La SMA200 (largo plazo) y la SMA50 (corto plazo) indican la tendencia del precio. Si el precio está por encima, la tendencia es positiva.<br>
    - {highlight(tendencia_alcista_largo, "Señal Alcista 🟢:")} Precio > SMA200.
    - {highlight(not tendencia_alcista_largo, "Señal Bajista 🔴:")} Precio < SMA200.
<br><br>
- **RSI (Índice de Fuerza Relativa):** Mide si una acción ha subido o bajado demasiado rápido. Un valor < 30 indica sobreventa (posible rebote) y > 70 sobrecompra (posible corrección).<br>
    - {highlight(rsi_sobreventa, "Sobreventa (< 30) 🟢:")} Potencial de rebote.
    - {highlight(pd.notna(rsi) and 30 <= rsi <= 70, "Neutral (30-70) 🟠:")} Sin señal clara.
    - {highlight(rsi_sobrecompra, "Sobrecompra (> 70) 🔴:")} Riesgo de corrección.
<br><br>
- **Veredicto Técnico Combinado:**<br>
<span style="background-color: #D4AF37; color: #0E1117; padding: 2px 5px; border-radius: 3px;">{resumen_texto}</span>
<br><br>
- **Beta:** Mide la volatilidad de la acción en comparación con el mercado (S&P 500). Un valor de 1.0 significa que la acción se mueve en línea con el mercado.<br>
    - {highlight(isinstance(beta, (int, float)) and beta > 1.2, "Volátil (Beta > 1.2):")} La acción se mueve de forma más agresiva que el mercado.<br>
    - {highlight(isinstance(beta, (int, float)) and 0.8 <= beta <= 1.2, "En línea (Beta 0.8-1.2):")} La acción se mueve de forma similar al mercado.<br>
    - {highlight(isinstance(beta, (int, float)) and 0 <= beta < 0.8, "Defensiva (Beta < 0.8):")} La acción es menos volátil que el mercado.<br>
    - {highlight(isinstance(beta, (int, float)) and beta < 0, "Anticíclica (Beta < 0):")} La acción se mueve en dirección opuesta al mercado.<br>
    - {highlight(not isinstance(beta, (int, float)) or pd.isna(beta), "No disponible.")}
"""
    else:
        leyenda_tecnico = "No se pudieron generar los datos para el análisis técnico."

    # --- Leyenda Margen de Seguridad ---
    ms_analistas = puntuaciones.get('margen_seguridad_analistas', 0)
    ms_per = puntuaciones.get('margen_seguridad_per', 0)
    ms_yield = puntuaciones.get('margen_seguridad_yield')
    
    leyenda_margen_seguridad = f"""
- **Según Analistas:** Potencial hasta el precio objetivo medio de los analistas.<br>
    - {highlight(ms_analistas > 20, "Alto Potencial: > 20%")}<br>
    - {highlight(0 <= ms_analistas <= 20, "Potencial Moderado: 0% a 20%")}<br>
    - {highlight(ms_analistas < 0, "Riesgo de Caída: < 0%")}
<br><br>
- **Según su PER Histórico:** Compara el PER actual con su media histórica.<br>
"""
    if datos.get('financial_currency') != 'USD':
        leyenda_margen_seguridad += f"""<small><i>(Nota: Para acciones no-USD como esta, este valor es una aproximación y puede ser impreciso.)</i></small><br>"""
    
    leyenda_margen_seguridad += f"""
    - {highlight(ms_per > 20, "Alto Potencial: > 20%")}<br>
    - {highlight(0 <= ms_per <= 20, "Potencial Moderado: 0% a 20%")}<br>
    - {highlight(ms_per < 0, "Riesgo de Caída: < 0%")}
<br><br>
- **Según su Yield Histórico:** Compara el yield actual con su media histórica.<br>
    - {highlight(ms_yield is not None and ms_yield > 20, "Alto Potencial: > 20%")}<br>
    - {highlight(ms_yield is not None and 0 <= ms_yield <= 20, "Potencial Moderado: 0% a 20%")}<br>
    - {highlight(ms_yield is not None and ms_yield < 0, "Riesgo de Caída: < 0%")}
"""
    return {'calidad': leyenda_calidad, 'salud': leyenda_salud, 'valoracion': leyenda_valoracion, 'peg': leyenda_peg, 'dividendos': leyenda_dividendos, 'tecnico': leyenda_tecnico, 'margen_seguridad': leyenda_margen_seguridad}


# --- ESTRUCTURA DE LA APLICACIÓN WEB ---
st.title('El Analizador de Acciones de Sr. Outfit')
st.caption("Herramienta de análisis. Esto no es una recomendación de compra o venta. Realiza tu propio juicio y análisis antes de invertir.")

ticker_input = st.text_input("Introduce el Ticker de la Acción a Analizar (ej. JNJ, MSFT, BABA)", "GOOGL").upper()

if st.button('Analizar Acción'):
    with st.spinner('Realizando análisis profesional...'):
        try:
            datos = obtener_datos_completos(ticker_input)
            
            if not datos:
                st.error(f"Error: No se pudo encontrar el ticker '{ticker_input}'. Verifica que sea correcto.")
            else:
                hist_data = obtener_datos_historicos_y_tecnicos(ticker_input)
                
                if hist_data and (hist_data.get('financials_charts') is None or hist_data.get('financials_charts').empty):
                    st.warning(f"No se pudieron obtener todos los datos históricos para '{ticker_input}'. El análisis puede estar incompleto.")
                
                puntuaciones, justificaciones, benchmarks = calcular_puntuaciones_y_justificaciones(datos, hist_data)
                sector_bench = benchmarks.get(datos['sector'], benchmarks['Default'])
                tech_data = hist_data.get('tech_data')
                leyendas = generar_leyenda_dinamica(datos, hist_data, puntuaciones, sector_bench, tech_data)
                
                calidad_score = puntuaciones.get('calidad', 0)
                valoracion_score = puntuaciones.get('valoracion', 0)
                salud_score = puntuaciones.get('salud', 0)
                dividendos_score = puntuaciones.get('dividendos', 0)

                pesos = {'calidad': 0.4, 'valoracion': 0.3, 'salud': 0.2, 'dividendos': 0.1}
                nota_ponderada = (calidad_score * pesos['calidad'] +
                                  valoracion_score * pesos['valoracion'] +
                                  salud_score * pesos['salud'] +
                                  dividendos_score * pesos['dividendos'])
                
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
                    st.markdown(f"**Sector:** {datos['sector']} | **Industria:** {datos['industria']}")
                    geo_nota = puntuaciones['geopolitico']
                    if geo_nota >= 8: st.markdown(f"**País:** {datos['pais']} | **Nivel de Riesgo:** BAJO 🟢")
                    else: st.markdown(f"**País:** {datos['pais']} | **Nivel de Riesgo:** PRECAUCIÓN 🟠")
                    
                    if datos['pais'] in ['China', 'Hong Kong']:
                        st.warning("⚠️ **Riesgo Regulatorio (ADR/VIE):** Invertir en empresas chinas a través de ADRs conlleva riesgos adicionales.")
                    st.caption(justificaciones['geopolitico'])
                    st.write(f"Descripción: {datos['descripcion']}")
                
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
                            cagr_rev_val = hist_data.get('cagr_rev')
                            mostrar_crecimiento_con_color("🚀 Crec. Ingresos (CAGR)", cagr_rev_val, sector_bench['rev_growth_excelente'], sector_bench['rev_growth_bueno'])
                        with c2:
                            mostrar_metrica_con_color("📊 Margen Operativo", datos['margen_operativo'], sector_bench['margen_excelente'], sector_bench['margen_bueno'], is_percent=True)
                            yoy_rev_val = datos.get('crecimiento_ingresos_yoy')
                            mostrar_crecimiento_con_color("🔥 Crec. Ingresos (YoY)", yoy_rev_val, sector_bench['rev_growth_excelente'], sector_bench['rev_growth_bueno'])
                        with st.expander("Ver Leyenda Detallada"):
                            st.markdown(leyendas['calidad'], unsafe_allow_html=True)
                with col2:
                    with st.container(border=True):
                        st.subheader(f"Salud Financiera [{puntuaciones['salud']:.1f}/10]")
                        st.caption(justificaciones['salud'])
                        s1, s2 = st.columns(2)
                        with s1:
                            deuda_ebitda_val = datos.get('deuda_ebitda')
                            if deuda_ebitda_val is not None and (isinstance(deuda_ebitda_val, float) and deuda_ebitda_val < 0):
                                st.markdown(f'<div class="metric-container"><div class="metric-label">⚡ Deuda Neta/EBITDA</div><div class="metric-value color-green">Negativa ({deuda_ebitda_val:.2f})</div></div>', unsafe_allow_html=True)
                            else:
                                mostrar_metrica_con_color("⚡ Deuda Neta/EBITDA", deuda_ebitda_val, sector_bench['deuda_ebitda_bueno'], sector_bench['deuda_ebitda_aceptable'], lower_is_better=True)
                            mostrar_metrica_con_color("💧 Ratio Corriente (Liquidez)", datos['ratio_corriente'], 1.5, 1.0)
                            cagr_fcf_val = hist_data.get('cagr_fcf')
                            mostrar_crecimiento_con_color("🌊 Crecimiento FCF (CAGR)", cagr_fcf_val, sector_bench['fcf_growth_excelente'], sector_bench['fcf_growth_bueno'])
                        with s2:
                            mostrar_metrica_con_color("🛡️ Cobertura Intereses", datos['interest_coverage'], sector_bench['int_coverage_excelente'], sector_bench['int_coverage_bueno'])
                            mostrar_metrica_con_color("💰 Flujo de Caja Libre (FCF)", datos.get('raw_fcf'), 0, -1, is_currency=True)
                        with st.expander("Ver Leyenda Detallada"):
                            st.markdown(leyendas['salud'], unsafe_allow_html=True)
                
                with st.container(border=True):
                    st.subheader(f"Análisis de Valoración [{puntuaciones['valoracion']:.1f}/10]")
                    st.caption(justificaciones['valoracion'])
                    
                    tab1, tab2 = st.tabs(["Múltiplos Actuales", "Análisis Histórico"])
                    
                    with tab1:
                        val1, val2, val3 = st.columns(3)
                        with val1:
                            mostrar_metrica_con_color("⚖️ PER", datos.get('per'), sector_bench['per_barato'], sector_bench['per_justo'], lower_is_better=True)
                        with val2:
                            mostrar_metrica_con_color("🌊 P/FCF", datos['p_fcf'], 20, 30, lower_is_better=True)
                        with val3:
                            mostrar_metrica_con_color("📚 P/B", datos['p_b'], sector_bench['pb_barato'], sector_bench['pb_justo'], lower_is_better=True)

                    with tab2:
                        if hist_data.get('per_hist') is None and hist_data.get('yield_hist') is None:
                            st.info("El análisis histórico no está disponible para esta acción.")
                        else:
                            h1, h2 = st.columns(2)
                            with h1:
                                mostrar_metrica_blue_chip("PER Actual vs Histórico", datos.get('per'), hist_data.get('per_hist'), lower_is_better=True)
                            with h2:
                                mostrar_metrica_blue_chip("Yield Actual vs Histórico", datos.get('yield_dividendo'), hist_data.get('yield_hist'), is_percent=True)

                    with st.expander("Ver Leyenda Detallada de Múltiplos"):
                        st.markdown(leyendas['valoracion'], unsafe_allow_html=True)

                with st.container(border=True):
                    st.subheader("Ratio PEG (Peter Lynch)")
                    peg_lynch = puntuaciones.get('peg_lynch')
                    prose, color_class = ("No aplicable", "color-white")
                    if peg_lynch is not None and not np.isnan(peg_lynch) and peg_lynch > 0:
                        if peg_lynch < 1: prose, color_class = f"Interesante ({peg_lynch:.2f})", "color-green"
                        elif peg_lynch > 1.5: prose, color_class = f"No Interesante ({peg_lynch:.2f})", "color-red"
                        else: prose, color_class = f"Neutral ({peg_lynch:.2f})", "color-orange"
                    st.markdown(f'<div class="metric-container" style="text-align:center;"><div class="metric-label">Ratio PEG (Lynch)</div><div class="metric-value {color_class}">{prose}</div><div class="formula-label">PER / Crecimiento Beneficios (%)</div></div>', unsafe_allow_html=True)
                    with st.expander("Ver Leyenda Detallada"):
                        st.markdown(leyendas['peg'], unsafe_allow_html=True)

                if datos.get('yield_dividendo') is not None and datos['yield_dividendo'] > 0:
                    with st.container(border=True):
                        st.subheader(f"Dividendos & Recompras [{puntuaciones['dividendos']:.1f}/10]")
                        st.caption(justificaciones['dividendos'])
                        
                        div1, div2, div3 = st.columns(3)
                        with div1:  
                            mostrar_metrica_con_color("💸 Rentabilidad (Yield)", datos['yield_dividendo'], 3.5, 2.0, is_percent=True)
                        with div2:
                            mostrar_metrica_con_color("🤲 Payout (Beneficios)", datos['payout_ratio'], sector_bench['payout_bueno'], sector_bench['payout_aceptable'], lower_is_better=True, is_percent=True)
                        with div3:
                            net_buybacks_display = f"{datos['net_buybacks_pct']:.2f}%" if datos['net_buybacks_pct'] is not None and not np.isnan(datos['net_buybacks_pct']) else "N/A"
                            color_buybacks = "color-white"
                            if datos['net_buybacks_pct'] is not None and not np.isnan(datos['net_buybacks_pct']):
                                if datos['net_buybacks_pct'] > 1: color_buybacks = "color-green"
                                elif datos['net_buybacks_pct'] < -1: color_buybacks = "color-red"
                            st.markdown(f'<div class="metric-container"><div class="metric-label">🔁 Recompras netas</div><div class="metric-value {color_buybacks}">{net_buybacks_display}</div></div>', unsafe_allow_html=True)
                        
                        with st.expander("Ver Leyenda Detallada"):
                            st.markdown(leyendas['dividendos'], unsafe_allow_html=True)
                
                with st.container(border=True):
                    st.subheader("Potencial de Revalorización (Márgenes de Seguridad)")
                    ms1, ms2, ms3 = st.columns(3)
                    with ms1:
                        mostrar_margen_seguridad("🛡️ Según Analistas", puntuaciones['margen_seguridad_analistas'])
                    with ms2:
                        mostrar_margen_seguridad("📈 Según su PER Histórico", puntuaciones['margen_seguridad_per'])
                        mostrar_metrica_blue_chip("PER Actual vs Histórico", datos.get('per'), hist_data.get('per_hist'), lower_is_better=True)
                    with ms3:
                        mostrar_margen_seguridad("💸 Según su Yield Histórico", puntuaciones['margen_seguridad_yield'])
                        mostrar_metrica_blue_chip("Yield Actual vs Histórico", datos.get('yield_dividendo'), hist_data.get('yield_hist'), is_percent=True)
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
                    st.subheader("Banderas de Alerta")
                    banderas = analizar_banderas_rojas(datos, financials_hist)
                    if not banderas:
                        st.success("✅ No se han detectado banderas rojas significativas.")
                    # Las banderas amarillas y rojas se muestran desde la función analizar_banderas_rojas

                col_tech, col_tech_legend = st.columns(2)
                with col_tech:
                    st.subheader("Análisis Técnico")
                    if tech_data is not None and not tech_data.empty:
                        fig_tecnico = crear_grafico_tecnico(tech_data)
                        st.pyplot(fig_tecnico)
                        
                        # --- CÓDIGO RESTAURADO ---
                        last_price_val = tech_data['Close'].iloc[-1] if not tech_data.empty else None
                        sma50_val = tech_data['SMA50'].iloc[-1] if not tech_data['SMA50'].isnull().all() else None
                        sma200_val = tech_data['SMA200'].iloc[-1] if not tech_data['SMA200'].isnull().all() else None
                        rsi = tech_data.get('RSI', pd.Series(dtype=float)).iloc[-1] if 'RSI' in tech_data.columns and not tech_data['RSI'].isnull().all() else None
                        beta = datos.get('beta')
                        
                        tendencia_texto, tendencia_color = "Lateral 🟠", "color-orange"
                        if last_price_val is not None and sma50_val is not None and sma200_val is not None:
                            if last_price_val > sma50_val and sma50_val > sma200_val: tendencia_texto, tendencia_color = "Alcista Fuerte 🟢", "color-green"
                            elif last_price_val > sma200_val: tendencia_texto, tendencia_color = "Alcista 🟢", "color-green"
                            elif last_price_val < sma50_val and sma50_val < sma200_val: tendencia_texto, tendencia_color = "Bajista Fuerte 🔴", "color-red"
                            elif last_price_val < sma200_val: tendencia_texto, tendencia_color = "Bajista 🔴", "color-red"
                        
                        st.markdown(f'<div class="metric-container"><div class="metric-label">Tendencia Actual</div><div class="metric-value {tendencia_color}">{tendencia_texto}</div></div>', unsafe_allow_html=True)

                        rsi_texto, rsi_color = "N/A", "color-white"
                        if rsi is not None and not np.isnan(rsi):
                            rsi_texto = f"{rsi:.2f} (Neutral 🟠)"
                            rsi_color = "color-orange"
                            if rsi > 70: rsi_texto, rsi_color = f"{rsi:.2f} (Sobrecompra 🔴)", "color-red"
                            elif rsi < 30: rsi_texto, rsi_color = f"{rsi:.2f} (Sobreventa 🟢)", "color-green"
                            
                        st.markdown(f'<div class="metric-container"><div class="metric-label">Estado RSI</div><div class="metric-value {rsi_color}">{rsi_texto}</div></div>', unsafe_allow_html=True)
                        
                        beta_texto = f"{beta:.2f}" if isinstance(beta, (int, float)) and not np.isnan(beta) else 'N/A'
                        st.markdown(f'<div class="metric-container"><div class="metric-label">Beta</div><div class="metric-value color-white">{beta_texto}</div></div>', unsafe_allow_html=True)
                        # --- FIN DEL CÓDIGO RESTAURADO ---

                    else:
                        st.warning("No se pudieron generar los datos para el análisis técnico.")
                
                with col_tech_legend:
                    st.subheader("Interpretación Técnica")
                    st.markdown(leyendas['tecnico'], unsafe_allow_html=True)

        except TypeError as e:
            st.error(f"Error al procesar los datos para '{ticker_input}'. Es posible que los datos de Yahoo Finance estén incompletos.")
            st.error(f"Detalle técnico: {e}")
        except Exception as e:
            st.error("Ha ocurrido un problema inesperado. Por favor, inténtalo de nuevo más tarde.")
            st.error(f"Detalle técnico: {e}")
