import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly
import plotly.express as px

# Create a connection object.
conn = st.connection("gsheets", type=GSheetsConnection)
url="https://docs.google.com/spreadsheets/d/1pfKrg_XDlyP7TSSo1MWlTAgVDZ9Cwz6LXuNO7eHEhr0/edit?usp=sharing"
df = conn.read(spreadsheet=url)


def highlight_top_3(col):
    # Skip non-numeric columns, empty columns, or the Size column
    if col.dtype != 'float64' and col.dtype != 'int64' or len(col) == 0 or col.name == 'Size':
        return [''] * len(col)
    
    # Create colors list with same length as column
    colors = pd.Series([''] * len(col), index=col.index)
    
    # Get indices of top 3 values, but limit to actual number of values
    n_values = min(3, len(col))
    top_3_idx = col.nlargest(n_values).index
    
    # Assign different shades of green to top values
    green_colors = ['background-color: #90EE90', 'background-color: #C1FFC1', 'background-color: #F0FFF0']
    
    for idx, color in zip(top_3_idx, green_colors[:n_values]):
        colors[idx] = color
    
    return colors

#updates table depending on values chosen in control panel below
def update_table():
    new_df = df
    if filter_open_closed != "All":    
        new_df = new_df[new_df["Closed_Open"] == filter_open_closed]
    
    # Initialize selected columns with basic columns in specific order
    basic_columns = ['LLM', 'Size', 'Family', 'Closed_Open']
    selected_columns = set()  # Using a set to ensure uniqueness
    
    # Build the column selection pattern based on filters
    if filter_level != "All" and filter_category != "All":
        pattern = f"{filter_level}_{filter_category}"
        selected_columns.update([col for col in new_df.columns if pattern in col])
    else:
        if filter_level != "All":
            selected_columns.update([col for col in new_df.columns if filter_level in col])
        
        if filter_category != "All":
            selected_columns.update([col for col in new_df.columns if filter_category in col])
        
        if filter_level == "All" and filter_category == "All":
            selected_columns = set(new_df.columns) - set(basic_columns)
    
    # Convert set back to list, sort for consistent order, and prepend basic columns
    selected_columns = basic_columns + sorted(list(selected_columns - set(basic_columns)))
    new_df = new_df[selected_columns]
    
    # Convert Size column to integer
    new_df['Size'] = new_df['Size']
    
    if filter_family != "All":
        new_df = new_df[new_df["Family"] == filter_family]
    
    new_df = new_df[(new_df["Size"] >= filter_size[0]) & (new_df["Size"] <= filter_size[1])]

    total_columns = [col for col in new_df.columns if col.endswith('_total')]
    if total_columns:  # Only apply performance filter if there are total columns
        performance_mask = new_df[total_columns].ge(filter_performance).any(axis=1)
        new_df = new_df[performance_mask]
    
    # Only apply styling if we have data
    if not new_df.empty:
        styled_df = new_df.style.apply(highlight_top_3)
        st.write(styled_df)
        
        # Create bar chart
        # Get numeric columns (excluding 'Size')
        numeric_cols = new_df.select_dtypes(include=['float64', 'int64']).columns.tolist()
        if 'Size' in numeric_cols:
            numeric_cols.remove('Size')
            
        if numeric_cols:  # Only create chart if we have numeric columns
            st.subheader("Performance Visualization")
            
            # Create grouped bar chart using plotly
            
            chart_data = new_df.melt(
                id_vars=['LLM'],
                value_vars=numeric_cols,
                var_name='Metric',
                value_name='Score'
            )
            
            fig = px.bar(
                chart_data,
                x='LLM',
                y='Score',
                color='Metric',
                barmode='group',
                height=400,
                title='Performance Metrics by LLM',
                color_discrete_sequence=px.colors.qualitative.Pastel

            )
            
            # Update layout for better readability
            fig.update_layout(
                xaxis_title="LLM Model",
                yaxis_title="Performance",
                legend_title="Level_Category",
                plot_bgcolor='white'
            )
            
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.write("No data matches the selected filters.")


#Control panel for column/row selection
col1, col2,col3,col4 = st.columns(4)
with col1:
    filter_open_closed=st.radio("Filter closed/open LLMs",["All","Open","Closed"])
with col2:
    filter_level=st.radio("Filter CEFR level",["All","A1","A2","B1","B2"])
with col3:
    filter_category=st.radio("Filter Test Category",["All","VOCAB","GRAMMAR","RC","LC","total"])
with col4:
    filter_family=st.selectbox("Select LLM Family:",["All",'Aya','Claude','Command-R','DeepSeek','Falcon','Gemini','Gemma','GLM','GPT','Llama','Mistral','Phi','Qwen','StableLM','WizardLM'])
filter_size=st.slider("Select size range of LLM parameters:",value=[0,700])
filter_performance=st.select_slider("Show LLMs with minimum performance of :",options=[e*.1 for e in range(0,11)])



# Print results.
update_table()
