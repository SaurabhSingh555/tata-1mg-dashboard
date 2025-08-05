import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# Set page config
st.set_page_config(
    page_title="Tata 1mg Pharmaceutical Insights",
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Try to import statsmodels (required for LOWESS trendline)
try:
    import statsmodels.api as sm
    LOWESS_AVAILABLE = True
except ImportError:
    LOWESS_AVAILABLE = False
    st.warning("For full functionality, please install statsmodels: `pip install statsmodels`")

# Load data from CSV with error handling
@st.cache_data
def load_data():
    try:
        df = pd.read_csv('Tata1MG_Realistic_Medicine_Dataset.csv')
        
        # Verify required columns exist
        required_columns = ['City', 'Month', 'Disease', 'Medicine', 'Orders', 'Price']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            st.error(f"Missing required columns: {', '.join(missing_columns)}")
            st.stop()
            
        # Handle competitor price
        competitor_col = None
        possible_names = ['Competitor_Price', 'Competitor Price', 'Comp_Price', 'CompetitorPrice']
        
        for name in possible_names:
            if name in df.columns:
                competitor_col = name
                break
                
        if competitor_col:
            df['Price_Difference'] = df[competitor_col] - df['Price']
            df['Price_Ratio'] = df['Price'] / df[competitor_col]
        else:
            st.warning("Competitor price column not found - using default values")
            df['Price_Difference'] = 0
            df['Price_Ratio'] = 1
            
        # Calculate derived metrics
        df['Revenue'] = df['Orders'] * df['Price']
        df['Profit_Margin'] = df['Price'] * 0.3  # Assuming 30% margin
        df['Total_Profit'] = df['Profit_Margin'] * df['Orders']
        
        return df
        
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        st.stop()

df = load_data()

# Custom CSS
st.markdown("""
<style>
    .main {
        background-color: #f5f5f5;
    }
    .header {
        color: #00a0e3;
        font-size: 36px;
        font-weight: bold;
    }
    .subheader {
        color: #333;
        font-size: 24px;
    }
    .metric-box {
        background-color: white;
        border-radius: 10px;
        padding: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }
    .highlight {
        background-color: #e6f7ff;
        border-left: 4px solid #00a0e3;
        padding: 10px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<p class="header">Tata 1mg Pharmaceutical Sales Insights</p>', unsafe_allow_html=True)
st.markdown("""
This dashboard provides actionable insights to optimize pricing strategy, inventory management, and regional sales performance.
""")

# Key Metrics
st.markdown('<p class="subheader">Key Performance Indicators</p>', unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown('<div class="metric-box">Total Revenue<br><h2>₹{:,.0f}</h2></div>'.format(df['Revenue'].sum()), unsafe_allow_html=True)
with col2:
    st.markdown('<div class="metric-box">Total Orders<br><h2>{:,.0f}</h2></div>'.format(df['Orders'].sum()), unsafe_allow_html=True)
with col3:
    st.markdown('<div class="metric-box">Avg Price Difference<br><h2>₹{:,.1f}</h2></div>'.format(df['Price_Difference'].mean()), unsafe_allow_html=True)
with col4:
    st.markdown('<div class="metric-box">Avg Profit Margin<br><h2>₹{:,.1f}</h2></div>'.format(df['Profit_Margin'].mean()), unsafe_allow_html=True)

# Filters
st.sidebar.header("Filters")
selected_cities = st.sidebar.multiselect("Select Cities", options=df['City'].unique(), default=df['City'].unique())
selected_months = st.sidebar.multiselect("Select Months", options=df['Month'].unique(), default=df['Month'].unique())
selected_diseases = st.sidebar.multiselect("Select Diseases", options=df['Disease'].unique(), default=df['Disease'].unique())
price_range = st.sidebar.slider("Price Range (₹)", min_value=int(df['Price'].min()), max_value=int(df['Price'].max()), 
                              value=(int(df['Price'].min()), int(df['Price'].max())))

# Apply filters
filtered_df = df[
    (df['City'].isin(selected_cities)) &
    (df['Month'].isin(selected_months)) &
    (df['Disease'].isin(selected_diseases)) &
    (df['Price'] >= price_range[0]) &
    (df['Price'] <= price_range[1])
]

# Main Analysis
tab1, tab2, tab3, tab4 = st.tabs(["Sales Overview", "Pricing Strategy", "Regional Analysis", "Recommendations"])

with tab1:
    st.markdown('<p class="subheader">Sales Performance</p>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        fig = px.bar(filtered_df.groupby('City')['Orders'].sum().reset_index(), 
                    x='City', y='Orders', title='Total Orders by City',
                    color='City', color_discrete_sequence=px.colors.qualitative.Pastel)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        fig = px.pie(filtered_df.groupby('Disease')['Orders'].sum().reset_index(), 
                    values='Orders', names='Disease', title='Order Distribution by Disease',
                    hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
        st.plotly_chart(fig, use_container_width=True)
    
    fig = px.line(filtered_df.groupby('Month')['Orders'].sum().reset_index(), 
                 x='Month', y='Orders', title='Monthly Sales Trend',
                 markers=True, line_shape='spline')
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.markdown('<p class="subheader">Pricing Analysis</p>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        fig = go.Figure()
        fig.add_trace(go.Box(y=filtered_df['Price'], name='Our Price', marker_color='#00a0e3'))
        if 'Price_Difference' in df.columns and df['Price_Difference'].sum() > 0:
            fig.add_trace(go.Box(y=filtered_df['Price'] + filtered_df['Price_Difference'], 
                               name='Competitor Price', marker_color='#ff7f0e'))
        fig.update_layout(title='Price Comparison', yaxis_title='Price (₹)')
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        if LOWESS_AVAILABLE:
            fig = px.scatter(filtered_df, x='Price', y='Orders', color='Medicine',
                            title='Price Elasticity Analysis (Orders vs Price)',
                            hover_data=['Medicine', 'Disease', 'City'],
                            trendline="lowess", trendline_color_override="red")
        else:
            fig = px.scatter(filtered_df, x='Price', y='Orders', color='Medicine',
                            title='Price Elasticity Analysis (Orders vs Price)',
                            hover_data=['Medicine', 'Disease', 'City'])
        st.plotly_chart(fig, use_container_width=True)
    
    if 'Price_Difference' in df.columns:
        st.markdown('<p class="subheader">Price Optimization Opportunities</p>', unsafe_allow_html=True)
        price_opp_df = filtered_df[filtered_df['Price_Difference'] > 5].sort_values('Price_Difference', ascending=False)
        if not price_opp_df.empty:
            st.dataframe(price_opp_df[['Medicine', 'City', 'Month', 'Price', 'Price_Difference', 'Orders']]
                        .style.background_gradient(cmap='Blues', subset=['Price_Difference']),
                        use_container_width=True)
        else:
            st.info("No significant price optimization opportunities found with current filters.")

with tab3:
    st.markdown('<p class="subheader">Regional Performance Analysis</p>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        fig = px.bar(filtered_df.groupby('City')['Revenue'].sum().reset_index(), 
                    x='City', y='Revenue', title='Revenue by City',
                    color='City', color_discrete_sequence=px.colors.sequential.Blues_r)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        if 'Price_Difference' in df.columns:
            fig = px.bar(filtered_df.groupby('City')['Price_Difference'].mean().reset_index(), 
                        x='City', y='Price_Difference', 
                        title='Average Price Difference by City',
                        color='Price_Difference', color_continuous_scale='Bluered')
            st.plotly_chart(fig, use_container_width=True)
    
    fig = px.scatter_geo(filtered_df.groupby('City').agg({'Orders': 'sum', 'Revenue': 'sum'}).reset_index(),
                        locations='City', locationmode='country names',
                        color='Revenue', size='Orders',
                        hover_name='City', hover_data=['Revenue', 'Orders'],
                        title='Geographic Sales Distribution',
                        scope='asia', center={'lat': 20, 'lon': 78},
                        projection='natural earth')
    st.plotly_chart(fig, use_container_width=True)

with tab4:
    st.markdown('<p class="subheader">Strategic Recommendations for Tata 1mg</p>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="highlight">
    <h4>📈 Pricing Strategy Recommendations:</h4>
    <ul>
        <li><strong>Selective Price Increases:</strong> For medicines with high demand and low price sensitivity, consider gradual price increases.</li>
        <li><strong>Competitive Pricing:</strong> Maintain competitive pricing for high-volume medicines to drive customer acquisition.</li>
        <li><strong>Dynamic Pricing:</strong> Implement dynamic pricing based on regional competition and demand patterns.</li>
    </ul>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="highlight">
    <h4>🏙️ Regional Strategy Recommendations:</h4>
    <ul>
        <li><strong>Focus on High-Growth Cities:</strong> Allocate more marketing resources to cities showing strong growth potential.</li>
        <li><strong>Localized Promotions:</strong> Create city-specific promotions based on prevalent diseases in each region.</li>
        <li><strong>Inventory Optimization:</strong> Adjust inventory levels based on regional disease patterns and seasonal trends.</li>
    </ul>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="highlight">
    <h4>📊 Data-Driven Opportunities:</h4>
    <ul>
        <li><strong>Predictive Analytics:</strong> Use historical sales data to forecast demand and optimize inventory.</li>
        <li><strong>Customer Segmentation:</strong> Analyze purchase patterns to create targeted marketing campaigns.</li>
        <li><strong>Price Monitoring:</strong> Establish automated price tracking to respond quickly to market changes.</li>
    </ul>
    </div>
    """, unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown("""
**Analysis prepared for Tata 1mg**  
This dashboard demonstrates advanced analytical capabilities and strategic thinking for pharmaceutical e-commerce optimization.
""")