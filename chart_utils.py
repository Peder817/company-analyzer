import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import streamlit as st
import matplotlib.pyplot as plt


def make_quarterly_chart(data):
    """Return a matplotlib figure for revenue by quarter if possible, else None."""
    try:
        if data is None:
            return None
        if isinstance(data, dict) and data.get("error"):
            return None

        df = data  # we expect a pandas-like DataFrame
        cols = list(getattr(df, "columns", []))
        if not cols:
            return None

        # Heuristik för kolumnnamn
        lower = {c.lower(): c for c in cols}
        date_col = next((lower[k] for k in ["date", "quarter", "period", "fiscal_quarter"] if k in lower), None)
        rev_col = None
        for c in cols:
            lc = c.lower()
            if any(k in lc for k in ["revenue", "net sales", "sales", "turnover"]):
                rev_col = c
                break

        if not date_col or not rev_col:
            return None

        dfx = df[[date_col, rev_col]].dropna()
        if dfx.empty:
            return None

        fig, ax = plt.subplots()
        ax.plot(dfx[date_col], dfx[rev_col], marker="o")
        ax.set_title("Revenue by Quarter")
        ax.set_xlabel(date_col)
        ax.set_ylabel(rev_col)
        ax.grid(True, alpha=0.3)
        fig.tight_layout()
        return fig
    except Exception:
        return None

def create_quarterly_comparison_chart(quarterly_data: dict, company_name: str):
    """
    Create a chart comparing the latest quarter with the same quarter one year earlier.
    
    Args:
        quarterly_data: Dictionary containing quarterly financial data
        company_name: Name of the company for the chart title
    
    Returns:
        plotly.graph_objects.Figure: The generated chart
    """
    try:
        # Extract quarterly financials
        if "quarterly_financials" not in quarterly_data:
            return None
            
        qf_data = quarterly_data["quarterly_financials"]
        
        # Convert to DataFrame if it's not already
        if not isinstance(qf_data, pd.DataFrame):
            try:
                qf_df = pd.DataFrame(qf_data)
            except Exception:
                # If conversion fails, try to handle it as a dict
                if isinstance(qf_data, dict):
                    qf_df = pd.DataFrame.from_dict(qf_data, orient='index')
                else:
                    return None
        else:
            qf_df = qf_data.copy()
        
        # The data structure has quarters as index, metrics as columns
        # Get the latest 8 quarters (2 years) for comparison
        latest_quarters = qf_df.index[:8]
        
        # Create comparison data
        comparison_data = []
        
        for quarter in latest_quarters:
            quarter_data = {
                'Quarter': quarter,
                'Revenue': qf_df.loc['Total Revenue', quarter] if 'Total Revenue' in qf_df.index else 0,
                'Net Income': qf_df.loc['Net Income', quarter] if 'Net Income' in qf_df.index else 0,
                'Gross Profit': qf_df.loc['Gross Profit', quarter] if 'Gross Profit' in qf_df.index else 0,
                'Operating Income': qf_df.loc['Operating Income', quarter] if 'Operating Income' in qf_df.index else 0
            }
            comparison_data.append(quarter_data)
        
        # Create DataFrame
        df = pd.DataFrame(comparison_data)
        
        # Convert to billions for better readability
        for col in ['Revenue', 'Net Income', 'Gross Profit', 'Operating Income']:
            if col in df.columns:
                df[col] = df[col] / 1e9
        
        # Create subplots
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Revenue (Billions)', 'Net Income (Billions)', 
                          'Gross Profit (Billions)', 'Operating Income (Billions)'),
            specs=[[{"secondary_y": False}, {"secondary_y": False}],
                   [{"secondary_y": False}, {"secondary_y": False}]]
        )
        
        # Add traces for each metric
        metrics = ['Revenue', 'Net Income', 'Gross Profit', 'Operating Income']
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']
        
        for i, (metric, color) in enumerate(zip(metrics, colors)):
            if metric in df.columns:
                row = (i // 2) + 1
                col = (i % 2) + 1
                
                fig.add_trace(
                    go.Bar(
                        x=df['Quarter'],
                        y=df[metric],
                        name=metric,
                        marker_color=color,
                        hovertemplate=f'{metric}: $%{{y:.2f}}B<br>Quarter: %{{x}}<extra></extra>'
                    ),
                    row=row, col=col
                )
        
        # Update layout
        fig.update_layout(
            title=f'{company_name} - Quarterly Financial Performance Comparison',
            height=600,
            showlegend=False,
            title_x=0.5
        )
        
        # Update x-axis labels for better readability
        fig.update_xaxes(tickangle=45)
        
        return fig
        
    except Exception as e:
        print(f"Error creating chart: {str(e)}")
        return None

def create_year_over_year_chart(quarterly_data: dict, company_name: str):
    """
    Create a year-over-year comparison chart showing the latest quarter vs same quarter last year.
    
    Args:
        quarterly_data: Dictionary containing quarterly financial data
        company_name: Name of the company for the chart title
    
    Returns:
        plotly.graph_objects.Figure: The generated chart
    """
    try:
        # Extract quarterly financials
        if "quarterly_financials" not in quarterly_data:
            return None
            
        qf_data = quarterly_data["quarterly_financials"]
        
        # Convert to DataFrame if it's not already
        if not isinstance(qf_data, pd.DataFrame):
            try:
                qf_df = pd.DataFrame(qf_data)
            except Exception:
                # If conversion fails, try to handle it as a dict
                if isinstance(qf_data, dict):
                    qf_df = pd.DataFrame.from_dict(qf_data, orient='index')
                else:
                    return None
        else:
            qf_df = qf_data.copy()
        
        # The data structure has quarters as index, metrics as columns
        # Get the latest 8 quarters (2 years)
        latest_quarters = qf_df.index[:8]
        
        # Find the latest quarter and the same quarter one year ago
        if len(latest_quarters) >= 4:
            latest_q = latest_quarters[0]
            year_ago_q = latest_quarters[4] if len(latest_quarters) > 4 else latest_quarters[0]
            

            
            # Extract key metrics
            metrics = ['Total Revenue', 'Net Income', 'Gross Profit', 'Operating Income']
            current_values = []
            previous_values = []
            metric_names = []
            
            for metric in metrics:
                if metric in qf_df.index:
                    current_val = qf_df.loc[metric, latest_q]
                    previous_val = qf_df.loc[metric, year_ago_q]
                    
                    if pd.notna(current_val) and pd.notna(previous_val):
                        current_values.append(current_val / 1e9)  # Convert to billions
                        previous_values.append(previous_val / 1e9)
                        metric_names.append(metric.replace('Total ', ''))
            
            if current_values:
                # Create the comparison chart
                fig = go.Figure()
                
                # Add bars for current quarter
                fig.add_trace(go.Bar(
                    name=f'{latest_q}',
                    x=metric_names,
                    y=current_values,
                    marker_color='#1f77b4',
                    hovertemplate='%{x}: $%{y:.2f}B<br>Quarter: ' + latest_q + '<extra></extra>'
                ))
                
                # Add bars for previous year quarter
                fig.add_trace(go.Bar(
                    name=f'{year_ago_q}',
                    x=metric_names,
                    y=previous_values,
                    marker_color='#ff7f0e',
                    hovertemplate='%{x}: $%{y:.2f}B<br>Quarter: ' + year_ago_q + '<extra></extra>'
                ))
                
                # Update layout
                fig.update_layout(
                    title=f'{company_name} - Year-over-Year Comparison<br>{latest_q} vs {year_ago_q}',
                    xaxis_title='Financial Metrics',
                    yaxis_title='Amount (Billions USD)',
                    barmode='group',
                    height=500,
                    title_x=0.5
                )
                
                return fig
        
        return None
        
    except Exception as e:
        print(f"Error creating year-over-year chart: {str(e)}")
        return None

def create_simple_quarterly_summary(quarterly_data: dict, company_name: str):
    """
    Create a simple summary table of quarterly data for display in Streamlit.
    
    Args:
        quarterly_data: Dictionary containing quarterly financial data
        company_name: Name of the company
    
    Returns:
        pandas.DataFrame: Summary table
    """
    try:
        if "quarterly_financials" not in quarterly_data:
            return None
            
        qf_data = quarterly_data["quarterly_financials"]
        
        # Convert to DataFrame if it's not already
        if not isinstance(qf_data, pd.DataFrame):
            try:
                qf_df = pd.DataFrame(qf_data)
            except Exception:
                # If conversion fails, try to handle it as a dict
                if isinstance(qf_data, dict):
                    qf_df = pd.DataFrame.from_dict(qf_data, orient='index')
                else:
                    return None
        else:
            qf_df = qf_data.copy()
        
        # The data structure has quarters as index, metrics as columns
        # Get the latest 4 quarters
        latest_quarters = qf_df.index[:4]
        
        # Select key metrics
        key_metrics = ['Total Revenue', 'Net Income', 'Gross Profit', 'Operating Income']
        
        # Create summary table
        summary_data = []
        for metric in key_metrics:
            if metric in qf_df.columns:
                row_data = {'Metric': metric.replace('Total ', '')}
                for quarter in latest_quarters:
                    value = qf_df.loc[quarter, metric]
                    if pd.notna(value):
                        # Format as billions with 2 decimal places
                        row_data[quarter] = f"${value/1e9:.2f}B"
                    else:
                        row_data[quarter] = "N/A"
                summary_data.append(row_data)
        
        if summary_data:
            summary_df = pd.DataFrame(summary_data)
            return summary_df
        
        return None
        
    except Exception as e:
        print(f"Error creating summary table: {str(e)}")
        return None
