# 📊 Chart Functionality for Company Analysis

This document explains the new chart functionality added to the Company Analysis application.

## 🎯 Overview

The application now includes interactive charts and visualizations that display quarterly financial performance data, making it easier to understand and analyze company financial trends.

## 📈 Available Charts

### 1. Quarterly Comparison Chart
- **Purpose**: Shows financial performance across multiple quarters (up to 2 years)
- **Metrics**: Revenue, Net Income, Gross Profit, Operating Income
- **Format**: 2x2 subplot layout with bar charts
- **Features**: 
  - Hover tooltips with exact values
  - Color-coded metrics
  - Downloadable as PNG

### 2. Year-over-Year Comparison Chart
- **Purpose**: Compares the latest quarter with the same quarter one year earlier
- **Metrics**: Revenue, Net Income, Gross Profit, Operating Income
- **Format**: Grouped bar chart
- **Features**:
  - Side-by-side comparison
  - Clear quarter labeling
  - Downloadable as PNG

### 3. Summary Table
- **Purpose**: Displays quarterly financial data in a clean, tabular format
- **Format**: Interactive DataFrame with formatted values
- **Features**:
  - Values displayed in billions (e.g., $94.8B)
  - Downloadable as CSV
  - Easy to read and compare

## 🚀 How to Use

### In the Streamlit App
1. **Run Analysis**: Enter a company name and click "Run Analysis"
2. **View Charts**: After analysis completes, navigate to the "📈 Financial Charts & Analysis" section
3. **Switch Tabs**: Use the tabs to view different chart types:
   - 📊 Quarterly Comparison
   - 📈 Year-over-Year
   - 📋 Summary Table
4. **Download**: Use the download buttons to save charts and data

### Chart Features
- **Interactive**: Hover over bars to see exact values
- **Responsive**: Charts automatically resize to fit the container
- **Professional**: Clean, business-ready visualizations
- **Exportable**: Download charts as PNG images or data as CSV

## 🔧 Technical Details

### Dependencies
- `plotly`: For interactive chart generation
- `pandas`: For data manipulation and formatting
- `streamlit`: For UI integration

### Data Format
The charts work with the existing financial data structure returned by the `financial_data_tool`:
```python
{
    "quarterly_financials": pd.DataFrame,  # Quarterly financial data
    "company_info": dict,                  # Company metadata
    # ... other financial data
}
```

### Error Handling
- Charts gracefully handle missing or incomplete data
- Fallback messages when charts cannot be generated
- Robust DataFrame conversion with multiple fallback methods

## 📱 UI Integration

### Streamlit Tabs
The charts are organized in tabs for better user experience:
- **Tab 1**: Quarterly Comparison - Multi-quarter performance view
- **Tab 2**: Year-over-Year - Direct quarter comparison
- **Tab 3**: Summary Table - Tabular data view

### Company Information Display
Below the charts, company metadata is displayed in a clean metric format:
- Company Name
- Sector
- Industry  
- Market Cap (formatted in billions)

## 🎨 Customization

### Chart Colors
Charts use a professional color palette:
- Revenue: Blue (#1f77b4)
- Net Income: Orange (#ff7f0e)
- Gross Profit: Green (#2ca02c)
- Operating Income: Red (#d62728)

### Chart Sizes
- Quarterly Comparison: 600px height
- Year-over-Year: 500px height
- All charts: Responsive width (use_container_width=True)

## 🔍 Troubleshooting

### Common Issues
1. **No Charts Displayed**: Check if quarterly financial data is available
2. **Missing Metrics**: Some companies may not report all financial metrics
3. **Data Format Errors**: Charts automatically handle various data formats

### Debug Information
- Check the terminal for any error messages
- Verify that the financial data tool is working correctly
- Ensure the company has sufficient financial data available

## 🚀 Future Enhancements

Potential improvements for future versions:
- Additional chart types (line charts, pie charts)
- Custom date range selection
- Peer company comparison charts
- Export to PowerPoint/Excel
- Real-time data updates
- Custom metric selection

## 📞 Support

If you encounter issues with the chart functionality:
1. Check the console for error messages
2. Verify all dependencies are installed
3. Ensure the company has sufficient financial data
4. Try with a different company to isolate the issue
