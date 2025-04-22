import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly
import plotly.express as px
import os

# Set page configuration to use the entire width
st.set_page_config(page_title="Your App Title", layout="wide")
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
    numeric_cols = new_df.select_dtypes(include=['float64', 'int64']).columns.tolist()
    numeric_cols.remove('Size')  # Exclude 'Size' from percentage conversion
    for col in numeric_cols:
        new_df[col] = (new_df[col] * 100).round(2)
    
    new_df['Size'] = new_df['Size'].astype(int)    

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
    
    if filter_family != "All":
        new_df = new_df[new_df["Family"] == filter_family]
    
    new_df = new_df[(new_df["Size"] >= filter_size[0]) & (new_df["Size"] <= filter_size[1])]

    total_columns = [col for col in new_df.columns if col.endswith('_total')]
    if total_columns:  # Only apply performance filter if there are total columns
        performance_mask = new_df[total_columns].ge(filter_performance).any(axis=1)
        new_df = new_df[performance_mask]
    
    # Only apply styling if we have data
    if not new_df.empty:
        
#        styled_df = new_df.style.format({col: "{:.2f}" for col in numeric_cols})  # Format for display
        styled_df = new_df.style.apply(highlight_top_3).format({col: "{:.2f}" for col in numeric_cols})
        st.divider()
        st.markdown("<h3 style='text-align: left; color: #537992;font-family: 'Bebas Neue';'>RESULTS</h3>", unsafe_allow_html=True)

        st.write(styled_df)
        

        # Create bar chart
        # Get numeric columns (excluding 'Size')
        numeric_cols = new_df.select_dtypes(include=['float64', 'int64']).columns.tolist()
        if 'Size' in numeric_cols:
            numeric_cols.remove('Size')
            
        if numeric_cols:  # Only create chart if we have numeric columns
            #st.subheader("Performance Visualization")
            st.divider()
            st.markdown("<h3 style='text-align: left; color: #537992;font-family: 'Bebas Neue';'>PERFORMANCE VISUALISATION</h3>", unsafe_allow_html=True)

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
#f=open("logos/LIST_2016_rgb_H75px.png","rb")
#f2=open("headlines_summary_small_titles.tsv",encoding="utf-8")
#st.write("Current Working Directory:", os.getcwd())
st.markdown(
       """
       <style>
       .logo-container {
           position: absolute;
           top: 10px;
           right: 10px;
       }
       </style>
       <div class="logo-container">
       </div>
       """,
       unsafe_allow_html=True
   )
col1, col2,col3 = st.columns([1,1,3])

with col1:
    st.image("./logos/LIST_2016_rgb_H75px.png", width=250, use_container_width =False)
with col2:
    st.image("./logos/cropped-Logo_INLL_largeur_quadri-Copy-1.png", width=250, use_container_width =False)

st.markdown("<h1 style='text-align: center; color: #537992;font-family: 'Bebas Neue';'><b>HOW WELL DO LLMS UNDERSTAND LUXEMBOURGISH?</b></h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: left;font-family: 'Arial';'>Large Language Models (LLMs) have reshaped the AI landscape in recent years. They are becoming omnipresent, being used by private users and companies alike. However, LLMs are developed mainly for widespread languages such as English, Spanish, or German, leaving languages such as Luxembourgish on the sidelines.  </p>", unsafe_allow_html=True)

st.markdown("<p style='text-align: left;font-family: 'Arial';'>In this project, we aimed to test the linguistic capabilities of LLMs in Luxembourgish. In collaboration with the Institut National des Langues Luxembourg, we used language proficiency exams to evaluate the performance of 45 current-day LLMs.</p>", unsafe_allow_html=True)
st.markdown("<h2 style='text-align: left; color: #537992;font-family: 'Bebas Neue';'>HOW DOES IT WORK?</h2>", unsafe_allow_html=True)
st.markdown("<p style='text-align: left;font-family: 'Arial';'>Using official language exams crafted by experts at INLL, we systematically test LLMs by letting them solve each question and grade their overall performance. There are 630 multiple-choice questions in total, each belonging to one out of four broad categories (Vocabulary, Grammar, Reading Comprehension, Listening Comprehension) and a <a href='https://www.efset.org/cefr/'>CEFR level</a> (A1, A2, B1, B2, C1, C2).  The performance of the LLMs for each category and CEFR level is expressed as a percentage of correctyly answered questions.</p>", unsafe_allow_html=True)
st.markdown("<h2 style='text-align: left; color: #537992;font-family: 'Bebas Neue';'>HOW TO USE THIS LEADERBOARD?</h2>", unsafe_allow_html=True)
st.markdown("<p style='text-align: left;font-family: 'Arial';>Below, you find the control panel for filtering the leaderboard. You can select a desired CEFR level and category to filter the table accordingly. In addition, you can choose to display only open-source/closed-source models, select a specific language models family (e.g. only Llama models), select a specific size range of LLM parameters, or display models that correctly answered a given percentage of questions. To help with readability, the highest performing models are highlighted in green.</p>", unsafe_allow_html=True)
st.markdown("<p style='text-align: left;font-family: 'Arial';>Underneath the table, you find a bar chart showing the performance of the LLMs for each category and CEFR level to help compare the performance of the LLMs.</p>", unsafe_allow_html=True)
#Control panel for column/row selectionst.markdown("<p style='text-align: left;font-family: 'Arial';'Below, you find the controls for filtering the leaderboard. You can select a desired CEFR level and category to filter the table accordingly. In addition, you choose to display only open-source or closed-source models, or select a specific language models family (e.g. only Llama models). To help with readability, the highest performing models are highlighted in green.</p>", unsafe_allow_html=True)
st.markdown("<h2 style='text-align: left; color: #537992;font-family: 'Bebas Neue';'>LEADERBOARD</h2>", unsafe_allow_html=True)
st.divider()
#st.markdown("<h3 style='text-align: left; color: #537992;font-family: 'Bebas Neue';'>CONTROL PANEL</h3>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align: left; color: #537992;font-family: 'Bebas Neue';'>Control Panel</h3>", unsafe_allow_html=True)

with st.container(border =True):

    

    col1, col2, col3, col4 = st.columns(4)
    with col3:
        filter_open_closed = st.radio("Filter closed/open LLMs", ["All", "Open", "Closed"])
        filter_family = st.selectbox("Select LLM Family:", ["All", 'Aya', 'Claude', 'Command-R', 'DeepSeek', 'Falcon', 'Gemini', 'Gemma', 'GLM', 'GPT', 'Llama', 'Mistral', 'Phi', 'Qwen', 'StableLM', 'WizardLM'])
    with col1:
        filter_level = st.radio("Filter CEFR level", ["All", "A1", "A2", "B1", "B2", "C1", "C2"])
    with col2:
        filter_category = st.radio("Filter Test Category", ["All", "VOCAB", "GRAMMAR", "RC", "LC", "total"],index = 5)

    col1, col2 = st.columns([1, 2])
    with col1:
        filter_size = st.slider("Select size range of LLM parameters:", value=[0, 700])
        filter_performance = st.select_slider("Show LLMs with minimum performance of :", options=[e * 10 for e in range(0, 11)])

    st.markdown("</div>", unsafe_allow_html=True)  #

# Print results.
update_table()
