import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from Eda_functions import *
import numpy as np
import re
import pickle
#from pandas_profiling import ProfileReport
from ydata_profiling import ProfileReport
from streamlit_pandas_profiling import st_profile_report
import streamlit as st
import streamlit.components.v1 as components
import sweetviz as sv
from utilities import set_header,initialize_data,load_local_css
st.set_page_config(
  page_title="Data Validation",
  page_icon=":shark:",
  layout="wide",
  initial_sidebar_state='collapsed'
)
load_local_css('styles.css')
set_header()



#preprocessing
with open('Categorised_data.pkl', 'rb') as file:
  Categorised_data = pickle.load(file)
with open("edited_dataframe.pkl", 'rb') as file:
  df = pickle.load(file)

df.reset_index(inplace=True)
df['Date'] = pd.to_datetime(df['Date'])


#prospects=pd.read_excel('EDA_Data.xlsx',sheet_name='Prospects')
#spends=pd.read_excel('EDA_Data.xlsx',sheet_name='SPEND INPUT')
#spends.columns=['Week','Streaming (Spends)','TV (Spends)','Search (Spends)','Digital (Spends)']
#df=pd.concat([df,spends],axis=1)

#df['Date'] =pd.to_datetime(df['Date']).dt.strftime('%m/%d/%Y')
#df['Prospects']=prospects['Prospects']
#df.drop(['Week'],axis=1,inplace=True)

#streamlit code

st.title('Data Validation and Insights')
target_variables=[col for col in df.drop('Date',axis=1).columns]
target_column = st.selectbox('Select the Target Feature/Dependent Variable (will be used in all charts as reference)', [col for col in target_variables if Categorised_data[col]['VB']=='Sales'])
with open("target_column.pkl", "wb") as f:
    pickle.dump(target_column, f)
    
#st.write(target_column)
fig=line_plot_target(df, target=target_column, title=f'{target_column} Over Time')
st.plotly_chart(fig, use_container_width=True)

# desired_columns = set([col for col in df.columns if 'imp' in col.lower() or 'cli' in col.lower() or 'spend' in col.lower()])
# # automate?
# desired_columns=list(desired_columns)
# desired_columns.append(target_column)

with open('Categorised_data.pkl', 'rb') as file:
  Categorised_data = pickle.load(file)
#st.write(Categorised_data)

#media

media_channel=[col for col in Categorised_data.keys() if Categorised_data[col]['BB'] == "Media" ]
# st.write(media_channel)

Non_media_channel=[col for col in df.columns if col not in media_channel]




st.markdown('### Annual Data Summary')
st.dataframe(summary(df, media_channel+[target_column], spends=None,Target=True), use_container_width=True)

if st.checkbox('Show raw data'):
    st.write(pd.concat([pd.to_datetime(df['Date']).dt.strftime('%m/%d/%Y'),df.select_dtypes(np.number).applymap(format_numbers)],axis=1))
col1 = st.columns(1)


st.header('1. Media Channels')


selected_media = st.selectbox('Select media', np.unique([Categorised_data[col]['VB'] for col in media_channel]))
# selected_feature=st.multiselect('Select Metric', df.columns[df.columns.str.contains(selected_media,case=False)])
selected_feature=st.selectbox('Select Metric',[col for col in [var for var in media_channel if 'spends' not in var ] if    Categorised_data[col]['VB'] in selected_media ] )
spends_features=[col for col in df.columns if 'spends' in col.lower() or 'cost' in col.lower()]
spends_feature=[col for col in spends_features if col.split('_')[0] in selected_feature.split('_')[0]]
#st.write(spends_features)
#st.write(spends_feature)
#st.write(selected_feature)
if len(spends_feature)==0:  
    st.warning('No spends varaible available for the selected metric in data') 
       
else:
    st.write(f'Selected spends variable {spends_feature[0]} if wrong please name the varaibles properly')
    # Create the dual-axis line plot
    fig_row1 = line_plot(df, x_col='Date', y1_cols=[selected_feature], y2_cols=[target_column], title=f'Analysis of {selected_feature} and {[target_column][0]} Over Time')
    st.plotly_chart(fig_row1, use_container_width=True)
    st.markdown('### Annual Data Summary')
    st.dataframe(summary(df,[selected_feature],spends=spends_feature[0]),use_container_width=True)

 
st.header('2. Non Media Variables')
selected_columns_row = [col for col in df.columns if ("imp" not in col.lower()) and ('cli' not in col.lower() ) and ('spend' not in col.lower()) and col!='Date']
selected_columns_row4 = st.selectbox('Select Channel',selected_columns_row )

if not selected_columns_row4: 
    st.warning('Please select at least one.')
else:
    # Create the dual-axis line plot
    fig_row4 = line_plot(df, x_col='Date', y1_cols=[selected_columns_row4], y2_cols=[target_column], title=f'Analysis of {selected_columns_row4} and {target_column} Over Time')
    st.plotly_chart(fig_row4, use_container_width=True)
    selected_non_media=selected_columns_row4
    sum_df = df[['Date', selected_non_media,target_column]]
    sum_df['Year']=pd.to_datetime(df['Date']).dt.year
    #st.dataframe(df)
    #st.dataframe(sum_df.head(2))
    sum_df=sum_df.groupby('Year').agg('sum')
    sum_df.loc['Grand Total']=sum_df.sum()         
    sum_df=sum_df.applymap(format_numbers) 
    sum_df.fillna('-',inplace=True)
    sum_df=sum_df.replace({"0.0":'-','nan':'-'})
    st.markdown('### Annual Data Summary')    
    st.dataframe(sum_df,use_container_width=True)

options = list(df.select_dtypes(np.number).columns)
st.markdown(' ')
st.markdown(' ')
st.markdown('# Exploratory Data Analysis')
st.markdown(' ')

selected_options = []
num_columns = 4
num_rows = -(-len(options) // num_columns)  # Ceiling division to calculate rows

# Create a grid of checkboxes
st.header('Select Features for Correlation Plot')
selected_options = []
for row in range(num_rows):
    cols = st.columns(num_columns)
    for col in cols:
        if options:
            option = options.pop(0) 
            selected = col.checkbox(option)
            if selected:
                selected_options.append(option)
# Display selected options
#st.write('You selected:', selected_options)
st.pyplot(correlation_plot(df,selected_options,target_column))


if st.button('Generate Profile Report'):
    pr = df.profile_report()

    st_profile_report(pr)

if st.button('Generate Sweetviz Report'):
 
    def generate_report_with_target(df, target_feature):
        report = sv.analyze([df, "Dataset"], target_feat=target_feature)
        return report

    report = generate_report_with_target(df, target_feature=target_column)
    report.show_html()