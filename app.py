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
    'Information Technology': {'roe_excelente': 25, 'roe_bueno': 18, 'roic_excelente': 20, 'roic_bueno': 15, 'margen_excelente': 25, 'margen_bueno': 18, 'margen_neto_excelente': 20, 'margen_neto_bueno': 15, 'bpa_growth_excelente': 15, 'bpa_growth_bueno': 10, 'fcf_growth_excelente': 15, 'fcf_growth_bueno': 10, 'per_barato': 25, 'per_justo': 35, 'pb_barato': 4, 'pb_justo': 8, 'payout_bueno': 60, 'payout_aceptable': 80, 'deuda_ebitda_bueno': 2, 'deuda_ebitda_aceptable': 3, 'int_coverage_excelente': 10, 'int_coverage_bueno': 5},
    'Health Care': {'roe_excelente': 20, 'roe_bueno': 15, 'roic_excelente': 15, 'roic_bueno': 12, 'margen_excelente': 20, 'margen_bueno': 15, 'margen_neto_excelente': 15, 'margen_neto_bueno': 10, 'bpa_growth_excelente': 12, 'bpa_growth_bueno': 7, 'fcf_growth_excelente': 10, 'fcf_growth_bueno': 6, 'per_barato': 20, 'per_justo': 30, 'pb_barato': 3, 'pb_justo': 5, 'payout_bueno': 60, 'payout_aceptable': 80, 'deuda_ebitda_bueno': 3, 'deuda_ebitda_aceptable': 4, 'int_coverage_excelente': 8, 'int_coverage_bueno': 4},
    'Financials': {'roe_excelente': 12, 'roe_bueno': 10, 'roic_excelente': 8, 'roic_bueno': 5, 'margen_excelente': 15, 'margen_bueno': 10, 'margen_neto_excelente': 10, 'margen_neto_bueno': 8, 'bpa_growth_excelente': 10, 'bpa_growth_bueno': 5, 'fcf_growth_excelente': 8, 'fcf_growth_bueno': 4, 'per_barato': 12, 'per_justo': 18, 'pb_barato': 1, 'pb_justo': 1.5, 'payout_bueno': 70, 'payout_aceptable': 90, 'deuda_ebitda_bueno': 1, 'deuda_ebitda_aceptable': 2, 'int_coverage_excelente': 5, 'int_coverage_bueno': 3},
    'Financial Services': {'roe_excelente': 12, 'roe_bueno': 10, 'roic_excelente': 8, 'roic_bueno': 5, 'margen_excelente': 15, 'margen_bueno': 10, 'margen_neto_excelente': 10, 'margen_neto_bueno': 8, 'bpa_growth_excelente': 10, 'bpa_growth_bueno': 5, 'fcf_growth_excelente': 8, 'fcf_growth_bueno': 4, 'per_barato': 12, 'per_justo': 18, 'pb_barato': 1, 'pb_justo': 1.5, 'payout_bueno': 70, 'payout_aceptable': 90, 'deuda_ebitda_bueno': 1, 'deuda_ebitda_aceptable': 2, 'int_coverage_excelente': 5, 'int_coverage_bueno': 3},
    'Industrials': {'roe_excelente': 18, 'roe_bueno': 14, 'roic_excelente': 12, 'roic_bueno': 9, 'margen_excelente': 15, 'margen_bueno': 10, 'margen_neto_excelente': 8, 'margen_neto_bueno': 6, 'bpa_growth_excelente': 10, 'bpa_growth_bueno': 6, 'fcf_growth_excelente': 10, 'fcf_growth_bueno': 5, 'per_barato': 20, 'per_justo': 25, 'pb_barato': 2.5, 'pb_justo': 4, 'payout_bueno': 60, 'payout_aceptable': 80, 'deuda_ebitda_bueno': 2.5, 'deuda_ebitda_aceptable': 4, 'int_coverage_excelente': 7, 'int_coverage_bueno': 4},
    'Utilities': {'roe_excelente': 10, 'roe_bueno': 8, 'roic_excelente': 8, 'roic_bueno': 5, 'margen_excelente': 15, 'margen_bueno': 12, 'margen_neto_excelente': 8, 'margen_neto_bueno': 5, 'bpa_growth_excelente': 6, 'bpa_growth_bueno': 3, 'fcf_growth_excelente': 5, 'fcf_growth_bueno': 3, 'per_barato': 18, 'per_justo': 22, 'pb_barato': 1.5, 'pb_justo': 2, 'payout_bueno': 80, 'payout_aceptable': 95, 'deuda_ebitda_bueno': 4, 'deuda_ebitda_aceptable': 5.5, 'int_coverage_excelente': 4, 'int_coverage_bueno': 2.5},
    'Consumer Discretionary': {'roe_excelente': 18, 'roe_bueno': 14, 'roic_excelente': 15, 'roic_bueno': 12, 'margen_excelente': 12, 'margen_bueno': 8, 'margen_neto_excelente': 7, 'margen_neto_bueno': 5, 'bpa_growth_excelente': 12, 'bpa_growth_bueno': 7, 'fcf_growth_excelente': 12, 'fcf_growth_bueno': 7, 'per_barato': 20, 'per_justo': 28, 'pb_barato': 3, 'pb_justo': 5, 'payout_bueno': 60, 'payout_aceptable': 80, 'deuda_ebitda_bueno': 3, 'deuda_ebitda_aceptable': 4.5, 'int_coverage_excelente': 6, 'int_coverage_bueno': 3.5},
    'Consumer Staples': {'roe_excelente': 20, 'roe_bueno': 15, 'roic_excelente': 15, 'roic_bueno': 12, 'margen_excelente': 15, 'margen_bueno': 10, 'margen_neto_excelente': 8, 'margen_neto_bueno': 5, 'bpa_growth_excelente': 8, 'bpa_growth_bueno': 5, 'fcf_growth_excelente': 7, 'fcf_growth_bueno': 4, 'per_barato': 20, 'per_justo': 25, 'pb_barato': 4, 'pb_justo': 6, 'payout_bueno': 70, 'payout_aceptable': 85, 'deuda_ebitda_bueno': 3, 'deuda_ebitda_aceptable': 4.5, 'int_coverage_excelente': 7, 'int_coverage_bueno': 4},
    'Energy': {'roe_excelente': 15, 'roe_bueno': 10, 'roic_excelente': 10, 'roic_bueno': 7, 'margen_excelente': 10, 'margen_bueno': 7, 'margen_neto_excelente': 8, 'margen_neto_bueno': 5, 'bpa_growth_excelente': 8, 'bpa_growth_bueno': 0, 'fcf_growth_excelente': 8, 'fcf_growth_bueno': 0, 'per_barato': 15, 'per_justo': 20, 'pb_barato': 1.5, 'pb_justo': 2.5, 'payout_bueno': 60, 'payout_aceptable': 80, 'deuda_ebitda_bueno': 2, 'deuda_ebitda_aceptable': 3, 'int_coverage_excelente': 8, 'int_coverage_bueno': 5},
    'Materials': {'roe_excelente': 15, 'roe_bueno': 12, 'roic_excelente': 12, 'roic_bueno': 9, 'margen_excelente': 12, 'margen_bueno': 8, 'margen_neto_excelente': 7, 'margen_neto_bueno': 5, 'bpa_growth_excelente': 10, 'bpa_growth_bueno': 5, 'fcf_growth_excelente': 10, 'fcf_growth_bueno': 5, 'per_barato': 18, 'per_justo': 25, 'pb_barato': 2, 'pb_justo': 3, 'payout_bueno': 60, 'payout_aceptable': 80, 'deuda_ebitda_bueno': 2.5, 'deuda_ebitda_aceptable': 4, 'int_coverage_excelente': 6, 'int_coverage_bueno': 3.5},
    'Real Estate': {'roe_excelente': 8, 'roe_bueno': 6, 'roic_excelente': 6, 'roic_bueno': 4, 'margen_excelente': 20, 'margen_bueno': 15, 'margen_neto_excelente': 15, 'margen_neto_bueno': 10, 'bpa_growth_excelente': 8, 'bpa_growth_bueno': 4, 'fcf_growth_excelente': 8, 'fcf_growth_bueno': 4, 'per_barato': 25, 'per_justo': 35, 'pb_barato': 2, 'pb_justo': 3, 'payout_bueno': 85, 'payout_aceptable': 95, 'deuda_ebitda_bueno': 5, 'deuda_ebitda_aceptable': 7, 'int_coverage_excelente': 3, 'int_coverage_bueno': 2},
    'Communication Services': {'roe_excelente': 15, 'roe_bueno': 12, 'roic_excelente': 15, 'roic_bueno': 12, 'margen_excelente': 18, 'margen_bueno': 12, 'margen_neto_excelente': 12, 'margen_neto_bueno': 9, 'bpa_growth_excelente': 12, 'bpa_growth_bueno': 7, 'fcf_growth_excelente': 12, 'fcf_growth_bueno': 7, 'per_barato': 22, 'per_justo': 30, 'pb_barato': 3, 'pb_justo': 5, 'payout_bueno': 60, 'payout_aceptable': 80, 'deuda_ebitda_bueno': 3, 'deuda_ebitda_aceptable': 4.5, 'int_coverage_excelente': 6, 'int_coverage_bueno': 3.5},
    'Default': {'roe_excelente': 15, 'roe_bueno': 12, 'roic_excelente': 12, 'roic_bueno': 9, 'margen_excelente': 15, 'margen_bueno': 10, 'margen_neto_excelente': 8, 'margen_neto_bueno': 5, 'bpa_growth_excelente': 10, 'bpa_growth_bueno': 5, 'fcf_growth_excelente': 10, 'fcf_growth_bueno': 5, 'per_barato': 20, 'per_justo': 25, 'pb_barato': 2, 'pb_justo': 4, 'payout_bueno': 60, 'payout_aceptable': 80, 'deuda_ebitda_bueno': 3, 'deuda_ebitda_aceptable': 5, 'int_coverage_excelente': 5, 'int_coverage_bueno': 3}
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
    
    # --- CÁLCULO DEL ROIC (con fallback de 3 niveles) ---
    roic = None
    roic_is_approx = False # Flag para saber si usamos ROA

    # Intento 1: Método NOPAT (más preciso)
    try:
        pretax_income = financials.loc['Pretax Income'].iloc[0] if 'Pretax Income' in financials.index else None
        tax_provision = financials.loc['Tax Provision'].iloc[0] if 'Tax Provision' in financials.index else None
        total_equity = balance_sheet.loc['Total Stockholder Equity'].iloc[0] if 'Total Stockholder Equity' in balance_sheet.index else None

        if ebit and pretax_income and tax_provision and total_debt and total_equity and pretax_income > 0:
            effective_tax_rate = tax_provision / pretax_income
            nopat = ebit * (1 - effective_tax_rate)
            invested_capital = total_debt + total_equity
            if invested_capital > 0:
                roic = (nopat / invested_capital) * 100
    except (TypeError, KeyError, IndexError, ZeroDivisionError):
        roic = None

    # Intento 2: Método Beneficio Neto + Intereses (robusto)
    if roic is None:
        try:
            net_income = financials.loc['Net Income'].iloc[0] if 'Net Income' in financials.index else None
            total_equity = balance_sheet.loc['Total Stockholder Equity'].iloc[0] if 'Total Stockholder Equity' in balance_sheet.index else None

            if net_income and interest_expense and total_debt and total_equity:
                numerator = net_income + abs(interest_expense)
                invested_capital = total_debt + total_equity
                if invested_capital > 0:
                    roic = (numerator / invested_capital) * 100
        except (TypeError, KeyError, IndexError, ZeroDivisionError):
            roic = None

    # Intento 3: Red de Seguridad - ROA (Return on Assets)
    if roic is None:
        try:
            total_assets = balance_sheet.loc['Total Assets'].iloc[0] if 'Total Assets' in balance_sheet.index else None
            if ebit and total_assets and total_assets > 0:
                roic = (ebit / total_assets) * 100
                roic_is_approx = True
        except (TypeError, KeyError, IndexError, ZeroDivisionError):
            roic = None

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

    # --- LÓGICA ESPECIAL PARA REITS ---
    if info.get('sector') == 'Real Estate':
        try:
            net_income = financials.loc['Net Income From Continuing Operations'].iloc[0]
            depreciation = cashflow.loc['Depreciation And Amortization'].iloc[0]
            ffo = net_income + depreciation
            dividends_paid = abs(cashflow.loc['Cash Dividends Paid'].iloc[0])
            if ffo > 0:
                payout = dividends_paid / ffo
        except (KeyError, IndexError):
            payout = info.get('payoutRatio') # Fallback al payout normal si no hay datos de FFO
    
    free_cash_flow = info.get('freeCashflow')
    market_cap = info.get('marketCap')
    p_fcf = (market_cap / free_cash_flow) if market_cap and free_cash_flow and free_cash_flow > 0 else None

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
        "roic": roic,
        "roic_is_approx": roic_is_approx,
        "margen_operativo": info.get('operatingMargins', 0) * 100 if info.get('operatingMargins') is not None else 0,
        "margen_beneficio": info.get('profitMargins', 0) * 100 if info.get('profitMargins') is not None else 0,
        "ratio_corriente": info.get('currentRatio'),
        "per": info.get('trailingPE'), "per_adelantado": info.get('forwardPE'),
        "p_fcf": p_fcf,
        "raw_fcf": free_cash_flow,
        "p_b": info.get('priceToBook'),
        "yield_dividendo": div_yield,
        "payout_ratio": payout * 100 if payout is not None else 0,
        "payout_fcf_ratio": payout_fcf_ratio * 100 if payout_fcf_ratio is not None else None,
        "recomendacion_analistas": info.get('recommendationKey', 'N/A'),
        "precio_objetivo": info.get('targetMeanPrice'), "precio_actual": info.get('currentPrice'),
        "bpa": info.get('trailingEps'),
        "bpa_growth_yoy": info.get('earningsGrowth'),
        "deuda_ebitda": deuda_ebitda,
        "interest_coverage": interest_coverage,
        "beta": info.get('beta', 'N/A'),
        "net_buybacks_pct": net_buybacks_pct,
        "financial_currency": info.get('financialCurrency', 'USD'),
        "market_cap": market_cap
    }

def calculate_cagr(end_value, start_value, years):
    if start_value is None or end_value is None or start_value == 0 or years <= 0:
        return None
    if start_value < 0:
        return None
    try:
        sign = -1 if end_value < 0 else 1
        return ((((abs(end_value) + 1e-9) / start_value) ** (1 / years)) - 1) * 100 * sign
    except (ZeroDivisionError, ValueError, TypeError):
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
        cagr_fcf, bpa_cagr, fcf_cagr_period, bpa_cagr_period = None, None, None, None

        if not financials_raw.empty:
            financials_annual = financials_raw.T.sort_index(ascending=True)
            net_income = financials_annual.get('Net Income', pd.Series(dtype=float))
            shares_key = 'Basic Average Shares' if 'Basic Average Shares' in financials_annual.columns else 'Diluted Average Shares'
            shares = financials_annual.get(shares_key, pd.Series(dtype=float))
            
            if not net_income.empty and not shares.empty:
                eps_series = (net_income / shares).dropna()
                if len(eps_series) >= 5:
                    start_eps = eps_series.iloc[-5]
                    end_eps = eps_series.iloc[-1]
                    bpa_cagr = calculate_cagr(end_eps, start_eps, 4)
                    if bpa_cagr is not None: bpa_cagr_period = "5A"
                
                if bpa_cagr is None and len(eps_series) >= 3:
                    start_eps = eps_series.iloc[-3]
                    end_eps = eps_series.iloc[-1]
                    bpa_cagr = calculate_cagr(end_eps, start_eps, 2)
                    if bpa_cagr is not None: bpa_cagr_period = "3A"
        
        if not cashflow_raw.empty:
            cashflow_annual = cashflow_raw.T.sort_index(ascending=True)
            fcf_series = None

            # Attempt 1: Direct 'Free Cash Flow'
            if 'Free Cash Flow' in cashflow_annual.columns:
                fcf_series = cashflow_annual['Free Cash Flow']
            
            # Attempt 2: Manual Calculation (Operating Cashflow - Capex)
            elif 'Total Cash From Operating Activities' in cashflow_annual.columns and ('Capital Expenditure' in cashflow_annual.columns or 'Capital Expenditures' in cashflow_annual.columns):
                op_cash = cashflow_annual['Total Cash From Operating Activities']
                capex_key = 'Capital Expenditure' if 'Capital Expenditure' in cashflow_annual.columns else 'Capital Expenditures'
                capex = cashflow_annual[capex_key]
                fcf_series = op_cash + capex # Capex is negative, so we add
            
            # Attempt 3: Proxy
            elif 'Net Cash Flow From Continuing Investing Activities' in cashflow_annual.columns:
                 fcf_series = cashflow_annual['Net Cash Flow From Continuing Investing Activities']

            if fcf_series is not None and not fcf_series.empty:
                fcf_series = fcf_series.dropna()
                if len(fcf_series) >= 5:
                    years_cf = 4
                    start_fcf = fcf_series.iloc[-5]
                    end_fcf = fcf_series.iloc[-1]
                    cagr_fcf = calculate_cagr(end_fcf, start_fcf, years_cf)
                    if cagr_fcf is not None: fcf_cagr_period = "5A"
                
                if cagr_fcf is None and len(fcf_series) >= 3:
                    years_cf = 2
                    start_fcf = fcf_series.iloc[-3]
                    end_fcf = fcf_series.iloc[-1]
                    cagr_fcf = calculate_cagr(end_fcf, start_fcf, years_cf)
                    if cagr_fcf is not None: fcf_cagr_period = "3A"

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
        hist_max = stock.history(period="max")
        ath_price = None
        if not hist_max.empty:
            ath_price = hist_max['Close'].max()
        
        ath_10y = hist_10y['Close'].max() if not hist_10y.empty else None
        
        if hist_10y.empty:
            return {"financials_charts": financials_for_charts, "dividends_charts": dividends_for_charts, "per_hist": None, "yield_hist": None, "tech_data": None, "cagr_fcf": cagr_fcf, "fcf_cagr_period": fcf_cagr_period, "bpa_cagr": bpa_cagr, "bpa_cagr_period": bpa_cagr_period, "ath_price": ath_price, "ath_10y": ath_10y, "valuation_history": None}
        
        # --- NEW: Historical Valuation Data ---
        valuation_history_data = []
        if not financials_raw.empty and not balance_sheet_raw.empty:
            net_income_key = 'Net Income'
            share_key = 'Basic Average Shares' if 'Basic Average Shares' in financials_raw.index else 'Diluted Average Shares'
            book_value_key = 'Total Stockholder Equity'
            
            for col_date in financials_raw.columns:
                year = col_date.year
                price_data_year = hist_10y[hist_10y.index.year == year]
                if price_data_year.empty: continue
                
                avg_price = price_data_year['Close'].mean()
                
                # P/E Calculation
                net_income = financials_raw.loc[net_income_key, col_date] if net_income_key in financials_raw.index else None
                shares = financials_raw.loc[share_key, col_date] if share_key in financials_raw.index else None
                pe_ratio = None
                if net_income and shares and shares > 0 and net_income > 0:
                    eps = net_income / shares
                    pe_ratio = avg_price / eps
                    if not (0 < pe_ratio < 200): pe_ratio = None
                
                # P/B Calculation
                book_value = balance_sheet_raw.loc[book_value_key, col_date] if book_value_key in balance_sheet_raw.index else None
                pb_ratio = None
                if book_value and shares and shares > 0 and book_value > 0:
                    bvps = book_value / shares
                    pb_ratio = avg_price / bvps
                    if not (0 < pb_ratio < 50): pb_ratio = None
                
                valuation_history_data.append({'Year': year, 'P/E': pe_ratio, 'P/B': pb_ratio})
        
        # --- CORRECCIÓN: Cálculo de PER histórico robusto ---
        valuation_history = pd.DataFrame(valuation_history_data).set_index('Year')
        per_historico = None
        if not valuation_history.empty and 'P/E' in valuation_history.columns:
            pers = valuation_history['P/E'].dropna().tolist()
            if pers:
                per_historico = np.mean(pers)

        divs_10y = stock.dividends
        if not divs_10y.empty:
            annual_dividends = divs_10y.resample('YE').sum()
            annual_prices = hist_10y['Close'].resample('YE').mean()
            df_yield = pd.concat([annual_dividends, annual_prices], axis=1).dropna()
            df_yield.columns = ['Dividends', 'Price']
            if not df_yield.empty and 'Price' in df_yield and 'Dividends' in df_yield:
                annual_yields = ((df_yield['Dividends'] / df_yield['Price']) * 100).tolist()
        yield_historico = np.mean(annual_yields) if annual_yields else None

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
            "cagr_fcf": cagr_fcf, "fcf_cagr_period": fcf_cagr_period,
            "bpa_cagr": bpa_cagr, "bpa_cagr_period": bpa_cagr_period,
            "ath_price": ath_price,
            "ath_10y": ath_10y,
            "valuation_history": valuation_history
        }
    except Exception as e:
        st.error(f"Se produjo un error al procesar los datos históricos y técnicos. Detalle: {e}")
        return {"financials_charts": None, "dividends_charts": None, "per_hist": None, "yield_hist": None, "tech_data": None, "cagr_fcf": None, "fcf_cagr_period": None, "bpa_cagr": None, "bpa_cagr_period": None, "ath_price": None, "ath_10y": None, "valuation_history": None}

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
    if datos.get('raw_fcf') is not None and datos.get('raw_fcf') < 0:
        banderas.append("🔴 **Flujo de Caja Libre Negativo:** La empresa está quemando más dinero del que genera.")
    if datos.get('interest_coverage') is not None and datos.get('interest_coverage') < 2:
        banderas.append("🔴 **Cobertura de Intereses Baja:** El beneficio operativo apenas cubre el pago de intereses.")
    if datos.get('ratio_corriente') is not None and datos.get('ratio_corriente') < 1.0:
        banderas.append("🔴 **Ratio Corriente (Liquidez) Baja:** Podría tener problemas para cubrir obligaciones a corto plazo.")
    if datos.get('market_cap') is not None and datos.get('market_cap') < 250000000:
        banderas.append("🔴 **Baja Capitalización de Mercado:** Inferior a $250M, puede implicar mayor volatilidad.")
    if datos.get('roic') is not None and datos.get('roe') is not None and datos.get('roic') > datos.get('roe'):
        st.warning("🟡 **Apalancamiento Negativo:** El ROIC es superior al ROE. Esto sugiere que el coste de la deuda podría ser mayor que la rentabilidad que genera, destruyendo valor para el accionista.")
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

    # --- NUEVO: Lógica de Puntuación Proporcional ---

    # 1. Calidad
    puntos_obtenidos_calidad, puntos_posibles_calidad = 0, 0
    
    if datos.get('roe') is not None:
        puntos_posibles_calidad += 2.5
        if datos['roe'] > sector_bench['roe_excelente']: puntos_obtenidos_calidad += 2.5
        elif datos['roe'] > sector_bench['roe_bueno']: puntos_obtenidos_calidad += 1.5

    if datos.get('roic') is not None:
        puntos_posibles_calidad += 2.5
        if datos['roic'] > sector_bench['roic_excelente']: puntos_obtenidos_calidad += 2.5
        elif datos['roic'] > sector_bench['roic_bueno']: puntos_obtenidos_calidad += 1.5

    if datos.get('margen_operativo') is not None:
        puntos_posibles_calidad += 2.5
        if datos['margen_operativo'] > sector_bench['margen_excelente']: puntos_obtenidos_calidad += 2.5
        elif datos['margen_operativo'] > sector_bench['margen_bueno']: puntos_obtenidos_calidad += 1.5

    if datos.get('margen_beneficio') is not None:
        puntos_posibles_calidad += 2
        if datos['margen_beneficio'] > sector_bench.get('margen_neto_excelente', 8): puntos_obtenidos_calidad += 2
        elif datos['margen_beneficio'] > sector_bench.get('margen_neto_bueno', 5): puntos_obtenidos_calidad += 1

    bpa_cagr = hist_data.get('bpa_cagr')
    if bpa_cagr is not None and not np.isnan(bpa_cagr):
        puntos_posibles_calidad += 2
        if bpa_cagr > sector_bench['bpa_growth_excelente']: puntos_obtenidos_calidad += 2
        elif bpa_cagr > sector_bench['bpa_growth_bueno']: puntos_obtenidos_calidad += 1
    
    bpa_yoy = datos.get('bpa_growth_yoy')
    if bpa_yoy is not None:
        puntos_posibles_calidad += 1
        if bpa_yoy * 100 > sector_bench['bpa_growth_excelente']: puntos_obtenidos_calidad += 1
    
    puntuaciones['calidad'] = (puntos_obtenidos_calidad / puntos_posibles_calidad) * 10 if puntos_posibles_calidad > 0 else 0
    justificaciones['calidad'] = "Rentabilidad, márgenes y crecimiento de élite." if puntuaciones['calidad'] >= 8 else "Negocio de buena calidad."

    # 2. Salud Financiera
    puntos_obtenidos_salud, puntos_posibles_salud = 0, 0
    
    if sector != 'Financials' and datos.get('deuda_ebitda') is not None and not np.isnan(datos.get('deuda_ebitda')):
        puntos_posibles_salud += 2.5
        deuda_ebitda = datos.get('deuda_ebitda')
        if deuda_ebitda < 0: puntos_obtenidos_salud += 2.5
        elif deuda_ebitda < sector_bench['deuda_ebitda_bueno']: puntos_obtenidos_salud += 2.5
        elif deuda_ebitda < sector_bench['deuda_ebitda_aceptable']: puntos_obtenidos_salud += 1.5

    if datos.get('interest_coverage') is not None:
        puntos_posibles_salud += 2.5
        interest_coverage = datos.get('interest_coverage')
        if interest_coverage > sector_bench['int_coverage_excelente']: puntos_obtenidos_salud += 2.5
        elif interest_coverage > sector_bench['int_coverage_bueno']: puntos_obtenidos_salud += 1.5
        
    if datos.get('ratio_corriente') is not None:
        puntos_posibles_salud += 2.5
        if datos.get('ratio_corriente') > 1.5: puntos_obtenidos_salud += 2.5
        
    cagr_fcf = hist_data.get('cagr_fcf')
    if cagr_fcf is not None and not np.isnan(cagr_fcf):
        puntos_posibles_salud += 2
        if cagr_fcf > sector_bench['fcf_growth_excelente']: puntos_obtenidos_salud += 2
        elif cagr_fcf > sector_bench['fcf_growth_bueno']: puntos_obtenidos_salud += 1

    nota_salud_base = (puntos_obtenidos_salud / puntos_posibles_salud) * 10 if puntos_posibles_salud > 0 else 0
    
    if datos.get('raw_fcf') is not None and datos.get('raw_fcf') < 0:
        nota_salud_base -= 4

    puntuaciones['salud'] = max(0, nota_salud_base)
    justificaciones['salud'] = "Balance muy sólido y solvente." if puntuaciones['salud'] >= 8 else "Salud financiera aceptable."
    
    # 3. Valoración
    puntos_obtenidos_multiplos, puntos_posibles_multiplos = 0, 0

    if sector == 'Real Estate':
        if datos.get('p_fcf') is not None and datos.get('p_fcf') > 0:
            puntos_posibles_multiplos += 8
            if datos['p_fcf'] < 16: puntos_obtenidos_multiplos += 8
            elif datos['p_fcf'] < 22: puntos_obtenidos_multiplos += 5
    else:
        if datos.get('per') is not None and datos.get('per') > 0:
            puntos_posibles_multiplos += 4
            if datos['per'] < sector_bench['per_barato']: puntos_obtenidos_multiplos += 4
            elif datos['per'] < sector_bench['per_justo']: puntos_obtenidos_multiplos += 2
        
        if datos.get('p_fcf') is not None and datos.get('p_fcf') > 0:
            puntos_posibles_multiplos += 4
            if datos['p_fcf'] < 20: puntos_obtenidos_multiplos += 4
            elif datos['p_fcf'] < 30: puntos_obtenidos_multiplos += 2

    SECTORES_PB_RELEVANTES = ['Financials', 'Industrials', 'Materials', 'Energy', 'Utilities', 'Real Estate']
    if sector in SECTORES_PB_RELEVANTES and datos.get('p_b') is not None and datos.get('p_b') > 0:
        puntos_posibles_multiplos += 2
        if datos['p_b'] < sector_bench['pb_barato']: puntos_obtenidos_multiplos += 2
    
    nota_multiplos = (puntos_obtenidos_multiplos / puntos_posibles_multiplos) * 10 if puntos_posibles_multiplos > 0 else 0

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
    if potencial_per > 15: nota_historica += 5
    if potencial_yield is not None and potencial_yield > 15: nota_historica += 5
    nota_historica = min(10, nota_historica)

    nota_valoracion_base = (nota_multiplos * 0.4) + (nota_analistas * 0.3) + (nota_historica * 0.3)
    
    per_actual = datos.get('per')
    per_adelantado = datos.get('per_adelantado')
    if per_actual is not None and per_adelantado is not None and per_actual > 0 and per_adelantado > 0:
        if per_adelantado < per_actual * 0.9: nota_valoracion_base += 1
        elif per_adelantado > per_actual: nota_valoracion_base -= 1

    if puntuaciones['calidad'] < 3: nota_valoracion_base *= 0.5
    elif puntuaciones['calidad'] < 5: nota_valoracion_base *= 0.75

    puntuaciones['valoracion'] = max(0, min(10, nota_valoracion_base))
    if puntuaciones['valoracion'] >= 8: justificaciones['valoracion'] = "Valoración muy atractiva."
    else: justificaciones['valoracion'] = "Valoración razonable o exigente."

    # 4. Dividendos
    puntos_obtenidos_dividendos, puntos_posibles_dividendos = 0, 0
    
    if datos.get('yield_dividendo') is not None and datos.get('yield_dividendo') > 0:
        puntos_posibles_dividendos += 5
        if datos['yield_dividendo'] > 3.5: puntos_obtenidos_dividendos += 5
        elif datos['yield_dividendo'] > 2: puntos_obtenidos_dividendos += 3
    
    if datos.get('payout_ratio') is not None and datos.get('payout_ratio') > 0:
        puntos_posibles_dividendos += 5
        if datos['payout_ratio'] < sector_bench['payout_bueno']: puntos_obtenidos_dividendos += 5
        elif datos['payout_ratio'] < sector_bench['payout_aceptable']: puntos_obtenidos_dividendos += 3

    if datos.get('net_buybacks_pct') is not None:
        puntos_posibles_dividendos += 2
        if datos['net_buybacks_pct'] > 1: puntos_obtenidos_dividendos += 2
        elif datos['net_buybacks_pct'] < -1: puntos_obtenidos_dividendos += 0
    
    nota_dividendos = (puntos_obtenidos_dividendos / puntos_posibles_dividendos) * 10 if puntos_posibles_dividendos > 0 else 0
    
    if yield_historico is not None and datos.get('yield_dividendo') is not None and datos.get('yield_dividendo') < yield_historico:
        nota_dividendos -= 2

    puntuaciones['dividendos'] = max(0, nota_dividendos)
    justificaciones['dividendos'] = "Dividendo excelente y sostenible." if puntuaciones['dividendos'] >= 8 else "Dividendo sólido."
    
    # 5. PEG
    per = datos.get('per')
    crecimiento_yoy = datos.get('bpa_growth_yoy')
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

def crear_grafico_valoracion_historica(valuation_df, current_per, current_pb):
    if valuation_df is None or valuation_df.empty:
        return None
    
    pe_data = valuation_df['P/E'].dropna() if 'P/E' in valuation_df.columns else pd.Series(dtype=float)
    pb_data = valuation_df['P/B'].dropna() if 'P/B' in valuation_df.columns else pd.Series(dtype=float)

    num_charts = 0
    if not pe_data.empty:
        num_charts += 1
    if not pb_data.empty:
        num_charts += 1

    if num_charts == 0:
        return None

    fig, axs = plt.subplots(num_charts, 1, figsize=(8, 3 * num_charts), sharex=True, squeeze=False)
    plt.style.use('dark_background')
    fig.patch.set_facecolor('#0E1117')
    
    current_ax_idx = 0

    # --- P/E Ratio Chart ---
    if not pe_data.empty:
        ax = axs[current_ax_idx, 0]
        ax.set_facecolor('#0E1117')
        ax.plot(pe_data.index, pe_data, marker='o', linestyle='-', color='#87CEEB', label='P/E Histórico')
        
        mean_pe = pe_data.mean()
        std_pe = pe_data.std()
        
        if current_per: ax.axhline(current_per, color='#D4AF37', linestyle='--', label=f'P/E Actual ({current_per:.2f})')
        ax.axhline(mean_pe, color='white', linestyle=':', label=f'Media ({mean_pe:.2f})')
        ax.axhline(mean_pe + std_pe, color='red', linestyle=':', alpha=0.5, label='+1 Desv. Est.')
        ax.axhline(mean_pe - std_pe, color='green', linestyle=':', alpha=0.5, label='-1 Desv. Est.')
        
        ax.set_ylabel('Ratio P/E')
        ax.set_title('Evolución Histórica del P/E Ratio', color='white')
        ax.legend()
        ax.grid(color='gray', linestyle='--', linewidth=0.5)
        current_ax_idx += 1

    # --- P/B Ratio Chart ---
    if not pb_data.empty:
        ax = axs[current_ax_idx, 0]
        ax.set_facecolor('#0E1117')
        ax.plot(pb_data.index, pb_data, marker='o', linestyle='-', color='#90EE90', label='P/B Histórico')
        
        mean_pb = pb_data.mean()
        std_pb = pb_data.std()
        
        if current_pb: ax.axhline(current_pb, color='#D4AF37', linestyle='--', label=f'P/B Actual ({current_pb:.2f})')
        ax.axhline(mean_pb, color='white', linestyle=':', label=f'Media ({mean_pb:.2f})')
        ax.axhline(mean_pb + std_pb, color='red', linestyle=':', alpha=0.5, label='+1 Desv. Est.')
        ax.axhline(mean_pb - std_pb, color='green', linestyle=':', alpha=0.5, label='-1 Desv. Est.')

        ax.set_ylabel('Ratio P/B')
        ax.set_title('Evolución Histórica del P/B Ratio', color='white')
        ax.legend()
        ax.grid(color='gray', linestyle='--', linewidth=0.5)
            
    plt.tight_layout()
    return fig

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

def mostrar_distancia_maximo(label, value, current_price, ath_price):
    color_class = "color-white"
    prose = "N/A"
    if isinstance(value, (int, float)) and not np.isnan(value):
        if value < -40:
            color_class = "color-green"
            prose = f"Caída Fuerte ({value:.2f}%)"
        elif value < -15:
            color_class = "color-orange"
            prose = f"Caída Moderada ({value:.2f}%)"
        else:
            color_class = "color-red"
            prose = f"Cerca de Máximos ({value:.2f}%)"
    
    formatted_prices = f"Actual: ${current_price:.2f} vs Máx: ${ath_price:.2f}" if current_price is not None and ath_price is not None else ""

    st.markdown(f'''
    <div class="metric-container">
        <div class="metric-label">{label}</div>
        <div class="metric-value {color_class}">{prose}</div>
        <div class="metric-label" style="line-height: 1; color: #FAFAFA;">{formatted_prices}</div>
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

def generar_resumen_ejecutivo(datos, puntuaciones, hist_data, sector_bench):
    """
    Genera un análisis textual profundo y profesional de la empresa,
    combinando métricas cuantitativas con una interpretación cualitativa y estética mejorada.
    """
    
    # --- Helper function for colorizing text ---
    def colorize(value, good_threshold, bad_threshold, lower_is_better=False, is_percent=False, is_ratio=False):
        if value is None or (isinstance(value, float) and np.isnan(value)):
            return "N/A"
        
        if is_percent:
            formatted_value = f"{value:.1f}%"
        elif is_ratio:
            formatted_value = f"{value:.1f}x"
        else:
            formatted_value = f"{value:.2f}"
            
        color = "#fd7e14" # Orange
        try:
            numeric_value = float(value)
            if lower_is_better:
                if numeric_value < good_threshold: color = "#28a745" # Green
                elif numeric_value > bad_threshold: color = "#dc3545" # Red
            else:
                if numeric_value > good_threshold: color = "#28a745" # Green
                elif numeric_value < bad_threshold: color = "#dc3545" # Red
        except (ValueError, TypeError):
            pass # Keep orange if not comparable
            
        return f'<span style="color: {color}; font-weight: bold;">{formatted_value}</span>'

    # --- Data Extraction ---
    calidad_score = puntuaciones.get('calidad', 0)
    valoracion_score = puntuaciones.get('valoracion', 0)
    salud_score = puntuaciones.get('salud', 0)
    dividendos_score = puntuaciones.get('dividendos', 0)
    
    roe = datos.get('roe')
    roic = datos.get('roic')
    margen_op = datos.get('margen_operativo')
    bpa_cagr = hist_data.get('bpa_cagr')
    deuda_ebitda = datos.get('deuda_ebitda')
    per = datos.get('per')
    per_hist = hist_data.get('per_hist')
    yield_div = datos.get('yield_dividendo')
    payout = datos.get('payout_ratio')
    net_buybacks = datos.get('net_buybacks_pct')
    
    resumen_parts = []

    # --- 1. Veredicto General ---
    resumen_parts.append('<h6>Veredicto General</h6>')
    veredicto_text = ""
    if calidad_score >= 7.5 and valoracion_score >= 7.5 and salud_score >= 7:
        veredicto_text = "<strong>Oportunidad de Inversión de Alta Convicción:</strong> Nos encontramos ante una empresa excepcional a un precio que parece muy atractivo. Combina un modelo de negocio de élite, una salud financiera robusta y una valoración que ofrece un margen de seguridad considerable."
    elif calidad_score >= 7.5 and valoracion_score < 5:
        veredicto_text = "<strong>Negocio Excepcional a un Precio Exigente:</strong> Estamos ante una joya de negocio, pero su valoración actual es elevada. El mercado reconoce su calidad y la cotiza a múltiplos altos. La inversión aquí depende de la confianza en que su crecimiento futuro justifique el precio actual."
    elif calidad_score < 5 and valoracion_score >= 7.5:
        veredicto_text = "<strong>Posible 'Ganga' con Riesgos (Deep Value):</strong> Esta es una potencial oportunidad de valor profundo, pero no exenta de riesgos. Su bajo precio refleja debilidades en su modelo de negocio. Requiere un análisis más profundo para determinar si es una 'trampa de valor' o un activo genuinamente infravalorado."
    else:
        veredicto_text = "<strong>Empresa Sólida, Inversión Equilibrada:</strong> Se trata de una empresa sólida con una valoración razonable, que presenta un equilibrio entre sus puntos fuertes y sus áreas de mejora. Podría ser un componente estable y fiable en una cartera diversificada."
    
    resumen_parts.append(f'<p style="background-color: #1a1c24; padding: 12px; border-radius: 8px; border: 1px solid #333;">{veredicto_text}</p>')

    # --- 2. Análisis de Calidad del Negocio ---
    resumen_parts.append(f"<h6>✅ Análisis de Calidad del Negocio (Sector: {datos['sector']})</h6>")
    calidad_fortalezas = []
    calidad_debilidades = []

    if roe is not None and roic is not None:
        if roe > sector_bench['roe_excelente'] and roic > sector_bench['roic_excelente']:
            calidad_fortalezas.append(f"Presenta una rentabilidad sobre el capital sobresaliente, con un ROE del {colorize(roe, sector_bench['roe_excelente'], sector_bench['roe_bueno'], is_percent=True)} y un ROIC del {colorize(roic, sector_bench['roic_excelente'], sector_bench['roic_bueno'], is_percent=True)}.")
        elif roe > sector_bench['roe_bueno'] and roic > sector_bench['roic_bueno']:
            calidad_fortalezas.append(f"Muestra una buena rentabilidad, con un ROE del {colorize(roe, sector_bench['roe_excelente'], sector_bench['roe_bueno'], is_percent=True)} y un ROIC del {colorize(roic, sector_bench['roic_excelente'], sector_bench['roic_bueno'], is_percent=True)}, superando los niveles aceptables para su sector.")
        else:
            calidad_debilidades.append(f"Su rentabilidad es un punto débil. El ROE de {colorize(roe, sector_bench['roe_excelente'], sector_bench['roe_bueno'], is_percent=True)} y el ROIC de {colorize(roic, sector_bench['roic_excelente'], sector_bench['roic_bueno'], is_percent=True)} están por debajo de la media del sector.")
    
    if margen_op is not None:
        if margen_op > sector_bench['margen_excelente']:
            calidad_fortalezas.append(f"Opera con unos márgenes de beneficio de élite ({colorize(margen_op, sector_bench['margen_excelente'], sector_bench['margen_bueno'], is_percent=True)}), lo que sugiere fuertes ventajas competitivas.")
        elif margen_op < sector_bench['margen_bueno']:
            calidad_debilidades.append(f"Sus márgenes operativos son ajustados ({colorize(margen_op, sector_bench['margen_excelente'], sector_bench['margen_bueno'], is_percent=True)}), indicando una posible alta competencia.")

    if bpa_cagr is not None:
        if bpa_cagr > sector_bench['bpa_growth_excelente']:
            calidad_fortalezas.append(f"Demuestra un crecimiento de beneficios a largo plazo excepcional (CAGR del {colorize(bpa_cagr, sector_bench['bpa_growth_excelente'], sector_bench['bpa_growth_bueno'], is_percent=True)}).")
        elif bpa_cagr < sector_bench['bpa_growth_bueno']:
            calidad_debilidades.append(f"El crecimiento de beneficios a largo plazo es lento o negativo ({colorize(bpa_cagr, sector_bench['bpa_growth_excelente'], sector_bench['bpa_growth_bueno'], is_percent=True)}).")

    if calidad_fortalezas:
        resumen_parts.append('<strong style="color: #28a745;">Fortalezas:</strong><ul><li>' + "</li><li>".join(calidad_fortalezas) + '</li></ul>')
    if calidad_debilidades:
        resumen_parts.append('<br><strong style="color: #dc3545;">Debilidades:</strong><ul><li>' + "</li><li>".join(calidad_debilidades) + '</li></ul>')
    if not calidad_fortalezas and not calidad_debilidades:
        resumen_parts.append('<p style="font-style: italic; color: #adb5bd;">En esta área, la empresa se encuentra dentro de los parámetros normales para su sector, sin fortalezas o debilidades que destaquen significativamente.</p>')

    # --- 3. Análisis de Salud Financiera ---
    resumen_parts.append(f"<h6>🛡️ Análisis de Salud Financiera</h6>")
    salud_fortalezas = []
    salud_debilidades = []

    if deuda_ebitda is not None:
        if deuda_ebitda < sector_bench['deuda_ebitda_bueno']:
            salud_fortalezas.append(f"Su balance es muy sólido, con un nivel de deuda neta de solo {colorize(deuda_ebitda, sector_bench['deuda_ebitda_bueno'], sector_bench['deuda_ebitda_aceptable'], lower_is_better=True, is_ratio=True)} veces su EBITDA, un ratio muy saludable para el sector {datos['sector']}.")
        elif deuda_ebitda > sector_bench['deuda_ebitda_aceptable']:
            salud_debilidades.append(f"El nivel de apalancamiento es un punto de riesgo. Su deuda neta es de {colorize(deuda_ebitda, sector_bench['deuda_ebitda_bueno'], sector_bench['deuda_ebitda_aceptable'], lower_is_better=True, is_ratio=True)} veces su EBITDA, una cifra elevada para una empresa del sector {datos['sector']}.")

    if datos.get('raw_fcf') is not None and datos.get('raw_fcf') < 0:
        salud_debilidades.append("Actualmente presenta un Flujo de Caja Libre negativo, lo que significa que está quemando más efectivo del que genera. Es una bandera roja importante que requiere vigilancia.")

    if salud_fortalezas:
        resumen_parts.append('<strong style="color: #28a745;">Fortalezas:</strong><ul><li>' + "</li><li>".join(salud_fortalezas) + '</li></ul>')
    if salud_debilidades:
        resumen_parts.append('<br><strong style="color: #dc3545;">Debilidades:</strong><ul><li>' + "</li><li>".join(salud_debilidades) + '</li></ul>')
    if not salud_fortalezas and not salud_debilidades:
        resumen_parts.append('<p style="font-style: italic; color: #adb5bd;">El balance de la compañía se considera adecuado y dentro de la normalidad para su sector, sin puntos de riesgo o solidez excepcionales.</p>')

    # --- 4. Análisis de Valoración ---
    resumen_parts.append(f"<h6>⚖️ Análisis de Valoración</h6>")
    valoracion_oportunidades = []
    valoracion_riesgos = []

    if per is not None and per_hist is not None:
        if per < sector_bench['per_barato'] and per < per_hist * 0.8:
            valoracion_oportunidades.append(f"La valoración por múltiplos parece muy atractiva. Su PER actual de {colorize(per, sector_bench['per_barato'], sector_bench['per_justo'], lower_is_better=True)} no solo es bajo para su sector, sino que cotiza con un descuento significativo frente a su media histórica de {per_hist:.1f}x.")
        elif per > sector_bench['per_justo'] and per > per_hist * 1.2:
            valoracion_riesgos.append(f"La acción parece cara en este momento. Su PER de {colorize(per, sector_bench['per_barato'], sector_bench['per_justo'], lower_is_better=True)} es elevado tanto para su sector como en comparación con su propia historia (media de {per_hist:.1f}x).")
        else:
            base_text = f"La valoración se encuentra en un rango razonable para su sector, con un PER de {colorize(per, sector_bench['per_barato'], sector_bench['per_justo'], lower_is_better=True)}. "
            if per < per_hist * 0.9:
                historical_comparison = f"Sin embargo, cotiza con un <strong>atractivo descuento</strong> frente a su media histórica de {per_hist:.1f}x, lo que podría sugerir una oportunidad."
                valoracion_oportunidades.append(base_text + historical_comparison)
            elif per > per_hist * 1.1:
                historical_comparison = f"No obstante, cotiza con una <strong>prima</strong> sobre su media histórica de {per_hist:.1f}x, indicando que el mercado tiene expectativas más altas que en el pasado."
                valoracion_riesgos.append(base_text + historical_comparison)
            else:
                historical_comparison = f"Este múltiplo está en línea con su propia media histórica de {per_hist:.1f}x."
                valoracion_oportunidades.append(base_text + historical_comparison)

    if valoracion_oportunidades:
        resumen_parts.append('<strong style="color: #28a745;">Oportunidades:</strong><ul><li>' + "</li><li>".join(valoracion_oportunidades) + '</li></ul>')
    if valoracion_riesgos:
        if valoracion_oportunidades:
            resumen_parts.append('<br>')
        resumen_parts.append('<strong style="color: #dc3545;">Riesgos:</strong><ul><li>' + "</li><li>".join(valoracion_riesgos) + '</li></ul>')
    if not valoracion_oportunidades and not valoracion_riesgos:
        resumen_parts.append('<p style="font-style: italic; color: #adb5bd;">La valoración actual no presenta oportunidades ni riesgos evidentes en comparación con su histórico y su sector. Se considera que cotiza a un precio justo.</p>')
    
    # --- 5. Análisis de Retorno al Accionista ---
    resumen_parts.append(f"<h6>💸 Análisis de Retorno al Accionista</h6>")
    dividendos_fortalezas = []
    dividendos_debilidades = []

    if yield_div is not None and yield_div > 0:
        payout_label = "FFO" if datos.get('sector') == 'Real Estate' else "Beneficios"
        if yield_div > 3.5 and payout < sector_bench['payout_bueno']:
            dividendos_fortalezas.append(f"Ofrece un dividendo muy atractivo del {colorize(yield_div, 3.5, 2.0, is_percent=True)} que además parece muy seguro, con un Payout Ratio sobre {payout_label} del {colorize(payout, sector_bench['payout_bueno'], sector_bench['payout_aceptable'], lower_is_better=True, is_percent=True)}.")
        elif payout > sector_bench['payout_aceptable']:
            dividendos_debilidades.append(f"La sostenibilidad del dividendo es una preocupación. El Payout Ratio sobre {payout_label} es del {colorize(payout, sector_bench['payout_bueno'], sector_bench['payout_aceptable'], lower_is_better=True, is_percent=True)}, un nivel muy elevado que podría comprometer futuros pagos.")
        elif deuda_ebitda is not None and deuda_ebitda > sector_bench['deuda_ebitda_aceptable']:
            dividendos_debilidades.append(f"Aunque el Payout es aceptable, el alto nivel de deuda ({colorize(deuda_ebitda, sector_bench['deuda_ebitda_bueno'], sector_bench['deuda_ebitda_aceptable'], lower_is_better=True, is_ratio=True)}) podría presionar la capacidad de la empresa para mantener el dividendo a futuro.")

    if net_buybacks is not None and net_buybacks > 1:
        dividendos_fortalezas.append(f"Además del dividendo, la empresa está recomprando activamente sus propias acciones ({colorize(net_buybacks, 1, -1, is_percent=True)} en el último año), lo que aumenta el valor para el accionista.")

    if dividendos_fortalezas:
        resumen_parts.append('<strong style="color: #28a745;">Fortalezas:</strong><ul><li>' + "</li><li>".join(dividendos_fortalezas) + '</li></ul>')
    if dividendos_debilidades:
        if dividendos_fortalezas:
            resumen_parts.append('<br>')
        resumen_parts.append('<strong style="color: #dc3545;">Debilidades:</strong><ul><li>' + "</li><li>".join(dividendos_debilidades) + '</li></ul>')
    if not dividendos_fortalezas and not dividendos_debilidades:
        resumen_parts.append('<p style="font-style: italic; color: #adb5bd;">La política de retorno al accionista se encuentra en un rango normal, sin puntos especialmente destacables o preocupantes.</p>')

    # --- 6. Perfil de Inversor ---
    resumen_parts.append("<h6>👤 Perfil Ideal de Inversor</h6>")
    perfil_text = ""
    if calidad_score >= 7 and dividendos_score >= 7:
        perfil_text = "<strong>Inversor en Dividendos (DGI):</strong> Busca empresas de alta calidad que ofrezcan una renta estable y creciente. La combinación de un negocio sólido y un dividendo fiable es su principal atractivo."
    elif calidad_score >= 7 and valoracion_score < 5:
        perfil_text = "<strong>Inversor en Crecimiento a un Precio Razonable (GARP):</strong> Dispuesto a pagar un precio justo o ligeramente alto por un negocio de calidad superior con altas expectativas de futuro, esperando que el crecimiento compuesto justifique la valoración."
    elif calidad_score < 5 and valoracion_score >= 7:
        perfil_text = "<strong>Inversor de Valor Profundo (Deep Value):</strong> Busca activos infravalorados que el mercado ha castigado, asumiendo un riesgo mayor a cambio de un potencial de revalorización significativo si la empresa logra dar un giro a su situación."
    else:
        perfil_text = "<strong>Inversor Mixto (Blend):</strong> Busca un equilibrio entre calidad, crecimiento y un precio razonable. Esta empresa encaja en una cartera diversificada como un activo que no destaca excesivamente en ningún área pero que es competente en todas."
    resumen_parts.append(f'<p style="font-style: italic;">{perfil_text}</p>')

    return "".join(resumen_parts)

def generar_leyenda_dinamica(datos, hist_data, puntuaciones, sector_bench, tech_data):
    def highlight(condition, text):
        if condition:
            return f'<span style="font-weight: bold; background-color: #D4AF37; color: #0E1117; padding: 2px 5px; border-radius: 3px;">{text}</span>'
        else:
            return text

    # --- Leyenda de Calidad ---
    roe = datos.get('roe', 0)
    roic = datos.get('roic')
    margen_op = datos.get('margen_operativo', 0)
    bpa_cagr = hist_data.get('bpa_cagr')
    bpa_yoy = datos.get('bpa_growth_yoy')
    bpa_yoy_pct = bpa_yoy * 100 if bpa_yoy is not None else None
    
    leyenda_calidad_parts = [
        "<ul>",
        "<li><b>ROE (Return on Equity):</b> Mide la rentabilidad sobre el capital de los accionistas. Un ROE alto es un indicativo de un negocio fuerte.</li>",
        f"Rangos para el sector <b>{datos['sector']}</b>:",
        "<ul>",
        f"<li>{highlight(roe > sector_bench['roe_excelente'], f'Excelente: > {sector_bench['roe_excelente']}%')}</li>",
        f"<li>{highlight(sector_bench['roe_bueno'] < roe <= sector_bench['roe_excelente'], f'Bueno: > {sector_bench['roe_bueno']}%')}</li>",
        f"<li>{highlight(roe <= sector_bench['roe_bueno'], f'Alerta: < {sector_bench['roe_bueno']}%')}</li>",
        "</ul>",
        "<br>",
        "<li><b>ROIC (Return on Invested Capital):</b> Mide la rentabilidad sobre todo el capital invertido (deuda + patrimonio). Es una métrica de calidad superior al ROE.</li>",
        f"Rangos para el sector <b>{datos['sector']}</b>:",
        "<ul>"
    ]
    if roic is not None and not np.isnan(roic):
        leyenda_calidad_parts.extend([
            f"<li>{highlight(roic > sector_bench['roic_excelente'], f'Excelente: > {sector_bench['roic_excelente']}%')}</li>",
            f"<li>{highlight(sector_bench['roic_bueno'] < roic <= sector_bench['roic_excelente'], f'Bueno: > {sector_bench['roic_bueno']}%')}</li>",
            f"<li>{highlight(roic <= sector_bench['roic_bueno'], f'Alerta: < {sector_bench['roic_bueno']}%')}</li>"
        ])
    else:
        leyenda_calidad_parts.append("<li><i>Datos no disponibles.</i></li>")
    
    leyenda_calidad_parts.extend([
        "</ul>",
        "<b>Relación con el ROE:</b> Si el <b>ROIC es mayor que el ROE</b>, es una señal de alerta 🟡, ya que podría significar que la deuda está destruyendo valor.",
        "<br><br>",
        "<li><b>Margen Operativo:</b> El porcentaje de beneficio que le queda a la empresa de sus ventas. Un margen alto refleja una <b>fuerte ventaja competitiva</b>.</li>",
        f"Rangos para el sector <b>{datos['sector']}</b>:",
        "<ul>",
        f"<li>{highlight(margen_op > sector_bench['margen_excelente'], f'Excelente: > {sector_bench['margen_excelente']}%')}</li>",
        f"<li>{highlight(sector_bench['margen_bueno'] < margen_op <= sector_bench['margen_excelente'], f'Bueno: > {sector_bench['margen_bueno']}%')}</li>",
        f"<li>{highlight(margen_op <= sector_bench['margen_bueno'], f'Alerta: < {sector_bench['margen_bueno']}%')}</li>",
        "</ul>",
        "<br>",
        "<li><b>Crecimiento del BPA (CAGR):</b> Mide la consistencia del crecimiento del beneficio por acción a largo plazo.</li>",
        f"Rangos para el sector <b>{datos['sector']}</b>:",
        "<ul>"
    ])
    if bpa_cagr is not None and not np.isnan(bpa_cagr):
        leyenda_calidad_parts.extend([
            f"<li>{highlight(bpa_cagr > sector_bench['bpa_growth_excelente'], f'Excelente: > {sector_bench['bpa_growth_excelente']}%')}</li>",
            f"<li>{highlight(sector_bench['bpa_growth_bueno'] < bpa_cagr <= sector_bench['bpa_growth_excelente'], f'Bueno: > {sector_bench['bpa_growth_bueno']}%')}</li>",
            f"<li>{highlight(bpa_cagr <= sector_bench['bpa_growth_bueno'], f'Lento/Negativo: < {sector_bench['bpa_growth_bueno']}%')}</li>"
        ])
    else:
        leyenda_calidad_parts.append("<li><i>Datos no disponibles.</i></li>")

    leyenda_calidad_parts.extend([
        "</ul>",
        "<br>",
        "<li><b>Crecimiento del BPA (Interanual - YoY):</b> Mide el momentum actual del negocio.</li>",
        f"Rangos para el sector <b>{datos['sector']}</b>:",
        "<ul>",
        f"<li>{highlight(bpa_yoy_pct is not None and bpa_yoy_pct > sector_bench['bpa_growth_excelente'], f'Excelente: > {sector_bench['bpa_growth_excelente']}%')}</li>",
        f"<li>{highlight(bpa_yoy_pct is not None and sector_bench['bpa_growth_bueno'] < bpa_yoy_pct <= sector_bench['bpa_growth_excelente'], f'Bueno: > {sector_bench['bpa_growth_bueno']}%')}</li>",
        f"<li>{highlight(bpa_yoy_pct is not None and bpa_yoy_pct <= sector_bench['bpa_growth_bueno'], f'Lento/Negativo: < {sector_bench['bpa_growth_bueno']}%')}</li>",
        "</ul>",
        "</ul>"
    ])
    leyenda_calidad = "".join(leyenda_calidad_parts)


    # --- Leyenda de Salud Financiera ---
    deuda_ebitda = datos.get('deuda_ebitda')
    int_coverage = datos.get('interest_coverage')
    raw_fcf = datos.get('raw_fcf')
    cagr_fcf = hist_data.get('cagr_fcf')
    ratio_corriente = datos.get('ratio_corriente')

    leyenda_salud_parts = [
        "<ul>",
        "<li><b>Ratio Corriente (Liquidez):</b> Mide si la empresa puede pagar sus deudas a corto plazo. Un valor de 1.5 o más es saludable.</li>",
        "Rangos:",
        "<ul>",
        f"<li>{highlight(ratio_corriente is not None and ratio_corriente > 1.5, 'Líquido: > 1.5x')}</li>",
        f"<li>{highlight(ratio_corriente is not None and 1.0 <= ratio_corriente <= 1.5, 'Suficiente: 1.0x - 1.5x')}</li>",
        f"<li>{highlight(ratio_corriente is not None and ratio_corriente < 1.0, 'Riesgo: < 1.0x')}</li>",
        "</ul>",
        "<br>",
        "<li><b>Deuda Neta / EBITDA:</b> Indica en cuántos años la empresa podría pagar su deuda. Un valor bajo es mejor.</li>",
        f"Rangos para el sector <b>{datos['sector']}</b>:",
        "<ul>"
    ]
    if datos['sector'] == 'Financials':
        leyenda_salud_parts.append("<li><i>No aplicable para el sector Financiero.</i></li>")
    elif deuda_ebitda is not None and not np.isnan(deuda_ebitda):
        leyenda_salud_parts.extend([
            f"<li>{highlight(deuda_ebitda < sector_bench['deuda_ebitda_bueno'], f'Saludable: < {sector_bench['deuda_ebitda_bueno']}x')}</li>",
            f"<li>{highlight(sector_bench['deuda_ebitda_bueno'] <= deuda_ebitda <= sector_bench['deuda_ebitda_aceptable'], f'Precaución: {sector_bench['deuda_ebitda_bueno']}x - {sector_bench['deuda_ebitda_aceptable']}x')}</li>",
            f"<li>{highlight(deuda_ebitda > sector_bench['deuda_ebitda_aceptable'], f'Riesgo Elevado: > {sector_bench['deuda_ebitda_aceptable']}x')}</li>"
        ])
    else:
        leyenda_salud_parts.append("<li><i>Datos no disponibles.</i></li>")
    
    leyenda_salud_parts.extend([
        "</ul>",
        "<br>",
        "<li><b>Cobertura de Intereses:</b> Indica cuántas veces el beneficio operativo (EBIT) cubre los gastos de intereses.</li>",
        "<ul>"
    ])
    if int_coverage is not None and not np.isnan(int_coverage):
        leyenda_salud_parts.extend([
            f"<li>{highlight(int_coverage > sector_bench['int_coverage_excelente'], f'Excelente: > {sector_bench['int_coverage_excelente']}x')}</li>",
            f"<li>{highlight(sector_bench['int_coverage_bueno'] <= int_coverage <= sector_bench['int_coverage_excelente'], f'Bueno: > {sector_bench['int_coverage_bueno']}x')}</li>",
            f"<li>{highlight(int_coverage < sector_bench['int_coverage_bueno'], f'Alerta: < {sector_bench['int_coverage_bueno']}x')}</li>"
        ])
    else:
        leyenda_salud_parts.append("<li><i>Datos no disponibles.</i></li>")

    leyenda_salud_parts.extend([
        "</ul>",
        "<br>",
        "<li><b>Flujo de Caja Libre (FCF):</b> Es el dinero real que el negocio genera. Un FCF positivo es vital.</li>",
        "<ul>"
    ])
    if raw_fcf is not None and not np.isnan(raw_fcf):
        leyenda_salud_parts.extend([
            f"<li>{highlight(raw_fcf > 0, '🟢 Positivo: La empresa genera más efectivo del que gasta.')}</li>",
            f"<li>{highlight(raw_fcf <= 0, '🔴 Negativo: La empresa está quemando efectivo.')}</li>"
        ])
    else:
        leyenda_salud_parts.append(f"<li><i>{highlight(True, 'Datos no disponibles.')}</i></li>")

    leyenda_salud_parts.extend([
        "</ul>",
        "<br>",
        f"<li><b>Crecimiento de FCF (CAGR):</b> El crecimiento anual compuesto del Flujo de Caja Libre.</li>",
        f"Rangos para el sector <b>{datos['sector']}</b>:",
        "<ul>"
    ])
    if cagr_fcf is not None and not np.isnan(cagr_fcf):
        leyenda_salud_parts.extend([
            f"<li>{highlight(cagr_fcf > sector_bench['fcf_growth_excelente'], f'Excelente: > {sector_bench['fcf_growth_excelente']}%')}</li>",
            f"<li>{highlight(sector_bench['fcf_growth_bueno'] < cagr_fcf <= sector_bench['fcf_growth_excelente'], f'Bueno: > {sector_bench['fcf_growth_bueno']}%')}</li>",
            f"<li>{highlight(cagr_fcf <= sector_bench['fcf_growth_bueno'], f'Lento/Negativo: < {sector_bench['fcf_growth_bueno']}%')}</li>"
        ])
    else:
        leyenda_salud_parts.append("<li><i>Datos no disponibles.</i></li>")
    
    leyenda_salud_parts.extend(["</ul>", "</ul>"])
    leyenda_salud = "".join(leyenda_salud_parts)

    # --- Leyenda de Valoración ---
    per = datos.get('per')
    per_adelantado = datos.get('per_adelantado')
    p_fcf = datos.get('p_fcf')
    p_b = datos.get('p_b')
    
    leyenda_valoracion_parts = [
        "<ul>",
        "<li><b>PER (Price-to-Earnings):</b> Indica cuántas veces el beneficio anual se paga al comprar la acción.</li>",
        f"Rangos para el sector <b>{datos['sector']}</b>:",
        "<ul>"
    ]
    if datos.get('sector') == 'Real Estate':
        leyenda_valoracion_parts.append("<li><i>No es la métrica principal para los REITs. Es mejor usar P/FCF.</i></li>")
    elif per is not None and per > 0 and not np.isnan(per):
        leyenda_valoracion_parts.extend([
            f"<li>{highlight(per < sector_bench['per_barato'], f'Atractivo: < {sector_bench['per_barato']}')}</li>",
            f"<li>{highlight(sector_bench['per_barato'] <= per <= sector_bench['per_justo'], f'Justo: {sector_bench['per_barato']} - {sector_bench['per_justo']}')}</li>",
            f"<li>{highlight(per > sector_bench['per_justo'], f'Caro: > {sector_bench['per_justo']}')}</li>"
        ])
    else:
        leyenda_valoracion_parts.append(f"<li>{highlight(True, 'No aplicable (negativo o N/A).')}</li>")
    
    leyenda_valoracion_parts.extend([
        "</ul>",
        "<br>",
        "<li><b>PER Actual vs Histórico:</b> Compara el PER actual con su media de los últimos años. Un PER por debajo de su media puede indicar una oportunidad de compra si la empresa sigue siendo de calidad.</li>",
        "<br>",
        "<li><b>PER Adelantado (Forward PE):</b> PER calculado con los beneficios esperados. Si es más bajo que el actual, se espera crecimiento.</li>",
        "<ul>",
        f"<li>{highlight(per_adelantado is not None and per is not None and per_adelantado < per, '🟢 Positivo: Se espera crecimiento.')}</li>",
        f"<li>{highlight(per_adelantado is not None and per is not None and per_adelantado >= per, '🔴 Negativo: Se espera estancamiento o caída.')}</li>",
        "</ul>",
        "<br>"
    ])
    
    if p_fcf is not None and p_fcf > 0 and not np.isnan(p_fcf):
        p_fcf_barato, p_fcf_justo = (16, 22) if datos.get('sector') == 'Real Estate' else (20, 30)
        leyenda_valoracion_parts.extend([
            "<li><b>P/FCF (Price-to-Free-Cash-Flow):</b> Mide el precio contra el dinero real que genera. Es más robusto que el PER.</li>",
            "Rangos:",
            "<ul>",
            f"<li>{highlight(p_fcf < p_fcf_barato, f'Atractivo: < {p_fcf_barato}')}</li>",
            f"<li>{highlight(p_fcf_barato <= p_fcf <= p_fcf_justo, f'Justo: {p_fcf_barato} - {p_fcf_justo}')}</li>",
            f"<li>{highlight(p_fcf > p_fcf_justo, f'Caro: > {p_fcf_justo}')}</li>",
            "</ul>"
        ])
    else:
        leyenda_valoracion_parts.append(f"<li><b>P/FCF:</b> {highlight(True, 'No aplicable (negativo o N/A).')}</li>")
        
    leyenda_valoracion_parts.extend([
        "<br>",
        "<li><b>P/B (Precio/Libros):</b> Compara el precio con su valor contable. Útil para sectores con activos tangibles.</li>",
        f"Rangos para el sector <b>{datos['sector']}</b>:",
        "<ul>"
    ])
    if p_b is not None and not np.isnan(p_b):
        leyenda_valoracion_parts.extend([
            f"<li>{highlight(p_b < sector_bench['pb_barato'], f'Atractivo: < {sector_bench['pb_barato']}')}</li>",
            f"<li>{highlight(sector_bench['pb_barato'] <= p_b <= sector_bench['pb_justo'], f'Justo: {sector_bench['pb_barato']} - {sector_bench['pb_justo']}')}</li>",
            f"<li>{highlight(p_b > sector_bench['pb_justo'], f'Caro: > {sector_bench['pb_justo']}')}</li>"
        ])
    else:
        leyenda_valoracion_parts.append(f"<li>{highlight(True, 'No aplicable o datos no disponibles.')}</li>")
    
    leyenda_valoracion_parts.extend(["</ul>", "</ul>"])
    leyenda_valoracion = "".join(leyenda_valoracion_parts)

    # --- Leyenda PEG ---
    peg = puntuaciones.get('peg_lynch')
    leyenda_peg_parts = [
        "<ul>",
        "<li><b>Ratio PEG (Peter Lynch):</b> Relaciona el PER con el crecimiento de los beneficios (<code>PER / Crecimiento %</code>). Un valor por debajo de 1 puede indicar infravaloración.</li>",
        "Rangos:",
        "<ul>"
    ]
    if peg is not None and not np.isnan(peg) and peg > 0:
        leyenda_peg_parts.extend([
            f'<li>{highlight(peg < 1, "Interesante (PEG < 1)")}</li>',
            f'<li>{highlight(1 <= peg <= 1.5, "Neutral (PEG 1-1.5)")}</li>',
            f'<li>{highlight(peg > 1.5, "No Interesante (PEG > 1.5)")}</li>'
        ])
    else:
        leyenda_peg_parts.append(f'<li>{highlight(True, "No aplicable.")}</li>')
    leyenda_peg_parts.extend(["</ul>", "</ul>"])
    leyenda_peg = "".join(leyenda_peg_parts)

    # --- Leyenda de Dividendos & Recompras ---
    yield_div = datos.get('yield_dividendo', 0)
    payout = datos.get('payout_ratio', 0)
    net_buybacks_pct = datos.get('net_buybacks_pct')
    
    leyenda_dividendos_parts = [
        "<ul>",
        "<li><b>Rentabilidad (Yield):</b> El porcentaje de tu inversión que recibes anualmente en dividendos.</li>",
        "Rangos:",
        "<ul>",
        f"<li>{highlight(yield_div > 3.5, 'Excelente: > 3.5%')}</li>",
        f"<li>{highlight(2.0 < yield_div <= 3.5, 'Bueno: > 2.0%')}</li>",
        f"<li>{highlight(yield_div <= 2.0, 'Bajo: < 2.0%')}</li>",
        "</ul>",
        "<br>",
        "<li><b>Yield Actual vs Histórico:</b> Compara el dividendo actual con su media. Un yield superior a la media puede ser una señal de infravaloración.</li>",
        "<br>",
        "<li><b>Ratio de Reparto (Payout):</b> El porcentaje del beneficio destinado a dividendos. Un payout sostenible deja margen para reinvertir.</li>",
        f"Rangos para el sector <b>{datos['sector']}</b>:",
        "<ul>",
        f"<li>{highlight(0 < payout < sector_bench['payout_bueno'], f'Saludable: < {sector_bench['payout_bueno']}%')}</li>",
        f"<li>{highlight(sector_bench['payout_bueno'] <= payout <= sector_bench['payout_aceptable'], f'Precaución: {sector_bench['payout_bueno']}% - {sector_bench['payout_aceptable']}%')}</li>",
        f"<li>{highlight(payout > sector_bench['payout_aceptable'], f'Peligroso: > {sector_bench['payout_aceptable']}%')}</li>",
        "</ul>",
        "<br>",
        "<li><b>Recompras Netas (%):</b> Mide el cambio en el número de acciones. Un valor positivo (recompras) es bueno para el accionista.</li>",
        "<ul>"
    ]
    if net_buybacks_pct is not None and not np.isnan(net_buybacks_pct):
        leyenda_dividendos_parts.extend([
            f"<li>{highlight(net_buybacks_pct > 1, '🟢 Aumento de Valor: Recompra de acciones.')}</li>",
            f"<li>{highlight(-1 <= net_buybacks_pct <= 1, '⚪ Neutral: Número de acciones estable.')}</li>",
            f"<li>{highlight(net_buybacks_pct < -1, '🔴 Dilución: Emisión de nuevas acciones.')}</li>"
        ])
    else:
        leyenda_dividendos_parts.append(f"<li>{highlight(True, '<i>Desconocido.</i>')}</li>")
    leyenda_dividendos_parts.extend(["</ul>", "</ul>"])
    leyenda_dividendos = "".join(leyenda_dividendos_parts)

    # --- Leyenda Técnica ---
    leyenda_tecnico = ""
    if tech_data is not None and not tech_data.empty:
        last_price = tech_data['Close'].iloc[-1] if not tech_data['Close'].empty else None
        sma200 = tech_data['SMA200'].iloc[-1] if not tech_data['SMA200'].isnull().all() else None
        rsi_series = tech_data.get('RSI', pd.Series(dtype=float))
        rsi = rsi_series.iloc[-1] if not rsi_series.empty and pd.notna(rsi_series.iloc[-1]) else None
        beta = datos.get('beta')
        
        tendencia_alcista_largo = pd.notna(last_price) and pd.notna(sma200) and last_price > sma200
        rsi_sobreventa = pd.notna(rsi) and rsi < 30
        rsi_sobrecompra = pd.notna(rsi) and rsi > 70
        
        resumen_texto = "Los indicadores no ofrecen una señal de compra o venta particularmente fuerte."
        if tendencia_alcista_largo and rsi_sobreventa:
            resumen_texto = "La acción está en una tendencia positiva y el RSI indica sobreventa. Esta combinación podría ser una señal de compra interesante."
        elif tendencia_alcista_largo and rsi_sobrecompra:
            resumen_texto = "La acción está en una tendencia positiva, pero el RSI indica que está sobrecomprada. Podría sugerir una corrección inminente."
        elif not tendencia_alcista_largo and rsi_sobreventa:
            resumen_texto = "A pesar de que el RSI muestra sobreventa, la tendencia general es bajista. Cuidado, el rebote podría ser temporal."
        
        leyenda_tecnico_parts = [
            "<ul>",
            "<li><b>Medias Móviles (SMA):</b> La SMA200 (largo plazo) y la SMA50 (corto plazo) indican la tendencia. Si el precio está por encima, la tendencia es positiva.</li>",
            "<ul>",
            f"<li>{highlight(tendencia_alcista_largo, 'Señal Alcista 🟢:')} Precio > SMA200.</li>",
            f"<li>{highlight(not tendencia_alcista_largo, 'Señal Bajista 🔴:')} Precio < SMA200.</li>",
            "</ul>",
            "<br>",
            "<li><b>RSI (Índice de Fuerza Relativa):</b> Mide si una acción ha subido o bajado demasiado rápido.</li>",
            "<ul>",
            f"<li>{highlight(rsi_sobreventa, 'Sobreventa (< 30) 🟢:')} Potencial de rebote.</li>",
            f"<li>{highlight(pd.notna(rsi) and 30 <= rsi <= 70, 'Neutral (30-70) 🟠:')} Sin señal clara.</li>",
            f"<li>{highlight(rsi_sobrecompra, 'Sobrecompra (> 70) 🔴:')} Riesgo de corrección.</li>",
            "</ul>",
            "<br>",
            f'<li><b>Veredicto Técnico Combinado:</b><br><span style="background-color: #D4AF37; color: #0E1117; padding: 2px 5px; border-radius: 3px;">{resumen_texto}</span></li>',
            "<br>",
            "<li><b>Beta:</b> Mide la volatilidad de la acción en comparación con el mercado (S&P 500).</li>",
            "<ul>",
            f"<li>{highlight(isinstance(beta, (int, float)) and beta > 1.2, 'Volátil (Beta > 1.2)')}</li>",
            f"<li>{highlight(isinstance(beta, (int, float)) and 0.8 <= beta <= 1.2, 'En línea (Beta 0.8-1.2)')}</li>",
            f"<li>{highlight(isinstance(beta, (int, float)) and 0 <= beta < 0.8, 'Defensiva (Beta < 0.8)')}</li>",
            f"<li>{highlight(not isinstance(beta, (int, float)) or pd.isna(beta), 'No disponible.')}</li>",
            "</ul>",
            "</ul>"
        ]
        leyenda_tecnico = "".join(leyenda_tecnico_parts)
    else:
        leyenda_tecnico = "No se pudieron generar los datos para el análisis técnico."

    # --- Leyenda Margen de Seguridad ---
    ms_analistas = puntuaciones.get('margen_seguridad_analistas', 0)
    ms_per = puntuaciones.get('margen_seguridad_per', 0)
    ms_yield = puntuaciones.get('margen_seguridad_yield')
    
    leyenda_margen_seguridad_parts = [
        "<ul>",
        "<li><b>Según Analistas:</b> Potencial hasta el precio objetivo medio de los analistas.</li>",
        "<ul>",
        f"<li>{highlight(ms_analistas > 20, 'Alto Potencial: > 20%')}</li>",
        f"<li>{highlight(0 <= ms_analistas <= 20, 'Potencial Moderado: 0% a 20%')}</li>",
        f"<li>{highlight(ms_analistas < 0, 'Riesgo de Caída: < 0%')}</li>",
        "</ul>",
        "<br>",
        "<li><b>Según su PER Histórico:</b> Compara el PER actual con su media de los últimos años. Un PER por debajo de su media puede indicar una oportunidad de compra si la empresa sigue siendo de calidad.</li>"
    ]
    if datos.get('financial_currency') != 'USD':
        leyenda_margen_seguridad_parts.append("<small><i>(Nota: Para acciones no-USD, este valor es una aproximación.)</i></small>")
    
    leyenda_margen_seguridad_parts.extend([
        "<ul>",
        f"<li>{highlight(ms_per > 20, 'Alto Potencial: > 20%')}</li>",
        f"<li>{highlight(0 <= ms_per <= 20, 'Potencial Moderado: 0% a 20%')}</li>",
        f"<li>{highlight(ms_per < 0, 'Riesgo de Caída: < 0%')}</li>",
        "</ul>",
        "<br>",
        "<li><b>Según su Yield Histórico:</b> Compara la rentabilidad por dividendo actual con su media. Un yield superior a la media puede ser una señal de infravaloración.</li>",
        "<ul>",
        f"<li>{highlight(ms_yield is not None and ms_yield > 20, 'Alto Potencial: > 20%')}</li>",
        f"<li>{highlight(ms_yield is not None and 0 <= ms_yield <= 20, 'Potencial Moderado: 0% a 20%')}</li>",
        f"<li>{highlight(ms_yield is not None and ms_yield < 0, 'Riesgo de Caída: < 0%')}</li>",
        "</ul>",
        "<br>",
        "<li><b>Distancia desde Máximo Histórico:</b> Mide la caída desde su precio más alto de todos los tiempos.</li>",
        "</ul>"
    ])
    leyenda_margen_seguridad = "".join(leyenda_margen_seguridad_parts)

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
                sector_bench = benchmarks.get(datos['sector'], SECTOR_BENCHMARKS['Default'])
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
                    st.subheader("Resumen Ejecutivo Profesional")
                    resumen = generar_resumen_ejecutivo(datos, puntuaciones, hist_data, sector_bench)
                    st.markdown(resumen, unsafe_allow_html=True)

                col1, col2 = st.columns(2)
                with col1:
                    with st.container(border=True):
                        st.subheader(f"Calidad del Negocio [{puntuaciones['calidad']:.1f}/10]")
                        st.caption(justificaciones['calidad'])
                        c1, c2, c3 = st.columns(3)
                        with c1:
                            mostrar_metrica_con_color("📈 ROE", datos['roe'], sector_bench['roe_excelente'], sector_bench['roe_bueno'], is_percent=True)
                            mostrar_metrica_con_color("💰 Margen Neto", datos['margen_beneficio'], sector_bench['margen_neto_excelente'], sector_bench['margen_neto_bueno'], is_percent=True)
                        with c2:
                            label_roic = "🏆 ROIC (Aprox. ROA)" if datos.get('roic_is_approx') else "🏆 ROIC"
                            mostrar_metrica_con_color(label_roic, datos['roic'], sector_bench['roic_excelente'], sector_bench['roic_bueno'], is_percent=True)
                            mostrar_metrica_con_color("📊 Margen Operativo", datos['margen_operativo'], sector_bench['margen_excelente'], sector_bench['margen_bueno'], is_percent=True)
                        with c3:
                            bpa_cagr_val = hist_data.get('bpa_cagr')
                            bpa_cagr_period = hist_data.get('bpa_cagr_period', '')
                            mostrar_crecimiento_con_color(f"🚀 Crec. BPA (CAGR {bpa_cagr_period})", bpa_cagr_val, sector_bench['bpa_growth_excelente'], sector_bench['bpa_growth_bueno'])
                            bpa_yoy_val = datos.get('bpa_growth_yoy')
                            bpa_yoy_val_pct = bpa_yoy_val * 100 if bpa_yoy_val is not None else None
                            mostrar_crecimiento_con_color("🔥 Crec. BPA (YoY)", bpa_yoy_val_pct, sector_bench['bpa_growth_excelente'], sector_bench['bpa_growth_bueno'])
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
                            fcf_cagr_period = hist_data.get('fcf_cagr_period', '')
                            mostrar_crecimiento_con_color(f"🌊 Crec. FCF (CAGR {fcf_cagr_period})", cagr_fcf_val, sector_bench['fcf_growth_excelente'], sector_bench['fcf_growth_bueno'])
                        with s2:
                            mostrar_metrica_con_color("🛡️ Cobertura Intereses", datos['interest_coverage'], sector_bench['int_coverage_excelente'], sector_bench['int_coverage_bueno'])
                            mostrar_metrica_con_color("💰 Flujo de Caja Libre (FCF)", datos.get('raw_fcf'), 0, -1, is_currency=True)
                        with st.expander("Ver Leyenda Detallada"):
                            st.markdown(leyendas['salud'], unsafe_allow_html=True)
                
                with st.container(border=True):
                    st.subheader(f"Análisis de Valoración [{puntuaciones['valoracion']:.1f}/10]")
                    st.caption(justificaciones['valoracion'])
                    
                    val1, val2, val3, val4 = st.columns(4)
                    with val1:
                        mostrar_metrica_con_color("⚖️ PER", datos.get('per'), sector_bench['per_barato'], sector_bench['per_justo'], lower_is_better=True)
                    with val2:
                        mostrar_metrica_con_color("🔮 PER Adelantado", datos.get('per_adelantado'), datos.get('per'), lower_is_better=True)
                    with val3:
                        mostrar_metrica_con_color("🌊 P/FCF", datos['p_fcf'], 20, 30, lower_is_better=True)
                    with val4:
                        mostrar_metrica_con_color("📚 P/B", datos['p_b'], sector_bench['pb_barato'], sector_bench['pb_justo'], lower_is_better=True)

                    st.markdown("---")
                    mostrar_metrica_blue_chip("PER Actual vs Histórico", datos.get('per'), hist_data.get('per_hist'), lower_is_better=True)

                    with st.expander("Ver Leyenda Detallada de Múltiplos"):
                        st.markdown(leyendas['valoracion'], unsafe_allow_html=True)
                    
                    with st.expander("Análisis de Valoración Histórica"):
                        fig_hist_val = crear_grafico_valoracion_historica(hist_data.get('valuation_history'), datos.get('per'), datos.get('p_b'))
                        if fig_hist_val:
                            st.pyplot(fig_hist_val)
                        else:
                            st.warning("No hay suficientes datos históricos para generar los gráficos de valoración.")

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
                            mostrar_metrica_blue_chip("Yield Actual vs Histórico", datos.get('yield_dividendo'), hist_data.get('yield_hist'), is_percent=True)
                        with div2:
                            label_payout = "🤲 Payout (FFO)" if datos['sector'] == 'Real Estate' else "🤲 Payout (Beneficios)"
                            mostrar_metrica_con_color(label_payout, datos['payout_ratio'], sector_bench['payout_bueno'], sector_bench['payout_aceptable'], lower_is_better=True, is_percent=True)
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
                    ms1, ms2, ms3, ms4 = st.columns(4)
                    with ms1:
                        mostrar_margen_seguridad("🛡️ Según Analistas", puntuaciones['margen_seguridad_analistas'])
                    with ms2:
                        mostrar_margen_seguridad("📈 Según su PER Histórico", puntuaciones['margen_seguridad_per'])
                    with ms3:
                        mostrar_margen_seguridad("💸 Según su Yield Histórico", puntuaciones['margen_seguridad_yield'])
                    with ms4:
                        ath_10y = hist_data.get('ath_10y')
                        distancia_ath = ((datos.get('precio_actual', 0) - ath_10y) / ath_10y) * 100 if ath_10y and datos.get('precio_actual') else None
                        mostrar_distancia_maximo("📉 Distancia Máx. Histórico (10A)", distancia_ath, datos.get('precio_actual'), ath_10y)
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
                    for bandera in banderas:
                        st.error(bandera)

                col_tech, col_tech_legend = st.columns(2)
                with col_tech:
                    st.subheader("Análisis Técnico")
                    if tech_data is not None and not tech_data.empty:
                        fig_tecnico = crear_grafico_tecnico(tech_data)
                        st.pyplot(fig_tecnico)
                        
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
