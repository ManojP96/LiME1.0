import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from Eda_functions import format_numbers,line_plot,summary
import numpy as np
from Transformation_functions import check_box
from Transformation_functions import apply_lag,apply_adstock,top_correlated_feature
import pickle
from st_aggrid import AgGrid
from st_aggrid import GridOptionsBuilder,GridUpdateMode
from utilities import set_header,initialize_data,load_local_css
from st_aggrid import GridOptionsBuilder
import time
import re
st.set_page_config(
  page_title="Data Validation",
  page_icon=":shark:",
  layout="wide",
  initial_sidebar_state='collapsed'
)
load_local_css('styles.css')
set_header()

st.title('Transformations')
st.markdown('#### Instructions:')
st.markdown('Use this section to select ranges of decays and lags for media variables and lags for non media variables if needed. After the transformations are applied select the transformations and variables based on their correlation with the target variable. These selections will be used in further model iterations. ')

# data reading
with open("edited_dataframe.pkl", 'rb') as file:
  df = pickle.load(file)
with open("bucket_data_VB.pkl", 'rb') as file:
  bucket_data_VB= pickle.load(file)
# df=pd.read_excel('data.xlsx')
# prospects=pd.read_excel('data.xlsx',sheet_name='Prospects')
# df['Prospects']=prospects['Prospects']
#spends=pd.read_excel('data.xlsx',sheet_name='SPEND INPUT')
#spends.columns=['Week','Streaming (Spends)','TV (Spends)','Search (Spends)','Digital (Spends)']
df.reset_index(inplace=True)
df['Date'] = pd.to_datetime(df['Date'])
df.set_index('Date',inplace=True)
old_shape=df.shape[1]
with open('Categorised_data.pkl', 'rb') as file:
  Categorised_data = pickle.load(file)
#st.write(Categorised_data)
with open("target_column.pkl", 'rb') as file:
  target_column= pickle.load(file)

#media
media_channel=[col for col in Categorised_data.keys() if Categorised_data[col]['BB'] == "Media" ]
# st.write(media_channel)

Non_media_channel=[col for col in df.columns if col not in media_channel and (Categorised_data[col]['BB']!='Internal' and Categorised_data[col]['BB']!='Dependent')]

internal_channel=[col for col in df.columns if col not in media_channel+Non_media_channel]
# st.write(Non_media_channel)

col=st.columns(3)
with col[0]:
  if st.checkbox('View Media Variables'):
    st.markdown(media_channel)

with col[1]:
  if st.checkbox('View Non media Variables'):
    st.markdown(Non_media_channel)
with col[2]:
  if st.checkbox('View Internal Variables'):
    st.markdown(internal_channel)
# st.text(media_channel+Non_media_channel)

st.header('Data Transformation')
columns = st.columns(2)

with columns[0]:
  slider_value_adstock  = st.slider('Select Global Adstock Range (only applied to media)', 0.0, 1.0, (0.0, 1.0), step=0.05, format="%.2f")
with columns[1]:
  slider_value_lag = st.slider('Select Global Lag Range (applied to media, seasonal, macroeconomic variables)', 0, 5, (0, 6), step=1)

options_ad_lg = media_channel



with st.expander("Select Media Variables (to modify Adstock and Lag)"):
  selected_features_ad_lag, ad_lag_values = check_box(options_ad_lg,ad_stock_value=slider_value_adstock,lag_value=slider_value_lag)
  # st.write('Selected features')
  # st.write('Adstock values')
  #t.text(ad_lag_values)

options_lg = Non_media_channel

# print(options_lg)
with st.expander("Select Non Media Variables (to modify only Lag)"):
  selected_features_lag,lag_values = check_box(options_lg,ad_stock_value=0,lag_value=slider_value_lag,prefix='lag')
  #st.text(lag_values)


summary_df=pd.DataFrame({'Variables':df.columns})
summary_df['Adstock_range']=summary_df['Variables'].map(lambda x:ad_lag_values[x]['adstock'] if x in ad_lag_values.keys() else 'NA' )
summary_df['Lag1']=summary_df['Variables'].map(lambda x:ad_lag_values[x]['lag'] if x in ad_lag_values.keys() else 'NA' )
summary_df['Lag_range']=summary_df['Variables'].map(lambda x:lag_values[x]['lag'] if x in lag_values.keys() else 'NA' )
summary_df['Lag_range']=np.where(summary_df['Lag_range']=='NA',summary_df['Lag1'],summary_df['Lag_range'])
summary_df.drop(['Lag1'],axis=1,inplace=True)
# summary_df['Adstock_range']=summary_df['Variables'].str.extract(r'_adst(\d+\.\d+)', expand=False)
# summary_df['Lag_range']=summary_df['Variables'].str.extract(r'_lag(\d+)', expand=False)
st.write("### Adstock and Lag Summary")
st.dataframe(summary_df,use_container_width=True)


if 'df' not in st.session_state:
  st.session_state['df']=None


if st.button('Apply Transformation'):
  #correlation_container=st.container()
  df = apply_lag(df, lag_values.keys(), lag_values)
  df = apply_lag(df,ad_lag_values.keys(),ad_lag_values)

  ad_stock_columns=[col for col in df.columns if any(item in col for item in ad_lag_values)]
  # st.write(ad_stock_columns)
  #st.write(df.shape)

  for col in ad_stock_columns:
      min=ad_lag_values[col.split('_lag')[0]]['adstock'][0]
      max=ad_lag_values[col.split('_lag')[0]]['adstock'][1]
      for adstock in np.arange(min,max+0.05,0.05):
          if adstock>0:
            df[f'{col}_adst{np.round(adstock,2)}']=apply_adstock(df,col,adstock)
  st.session_state['df']=df
 

  with st.spinner('Take a quick break while transformations are applied'):
    time.sleep(3)
    st.success("Transformations complete!")
  with open("df.pkl", "wb") as f:
    pickle.dump(df, f)
  st.write(f'Total no.of variables before transformation: {old_shape}')
  st.write(f'Total no.of variables after transformation: {df.shape[1]}')
  # if st.checkbox('View Transformed Data'):
  #   st.dataframe(df.applymap(format_numbers).head(10))
  #correlation_container.write(st.session_state['df']) 
st.markdown('## Select Variables for Model Iterations')
bucket=st.selectbox('Select Bucket',[ var for var in bucket_data_VB.keys() if var not in ['Price','Distribution',"Promotion"]])
variables=list(ad_lag_values.keys())+list(lag_values.keys())
f_v=[col for col in variables if Categorised_data[col]['VB']==bucket]
filtered_variable=st.selectbox('Select Variable',f_v)

# if st.button('Filter Variables '):
if "selected_features_model" not in st.session_state:
  st.session_state['selected_features_model']={}

if len(f_v)>0:
  with st.form('Filter'):
    corr_df=top_correlated_feature(st.session_state['df'],filtered_variable,target_column)
    corr_df['Adstock']=corr_df['Media_channel'].map(lambda x:x.split('_adst')[1] if len(x.split('_adst'))>1 else '-')
    #corr_df['lag_1']=corr_df['Media_channel'].map(lambda x:x.split('_lag')[1][0] if len(x.split('_lag'))>1 else '-' )
    corr_df['Lag']=corr_df['Media_channel'].map(lambda x:x.split('_lag')[1][0] if len(x.split('_lag'))>1 else '-' )
    corr_df = corr_df.assign(Bucket=Categorised_data[filtered_variable]['VB'])
    #st.dataframe(corr_df)
      
    gd=GridOptionsBuilder.from_dataframe(corr_df)
    gd.configure_pagination(enabled=True)
    gd.configure_selection(use_checkbox=True,selection_mode='multiple')

    #gd.configure_columns_auto_size_mode(GridOptionsBuilder.configure_columns)
    gridoptions=gd.build()
    table = AgGrid(corr_df,gridOptions=gridoptions,update_mode=GridUpdateMode.SELECTION_CHANGED,fit_columns_on_grid_load=True)
    #st.table(table)
    selected_rows = table["selected_rows"]
    # st.write(selected_rows)

    submit_button = st.form_submit_button(label='Submit Selection')
    if submit_button:
      rows=[str(i.values()).split(',')[2] for i in selected_rows]
      #st.write(rows) 
      rows=[row[2:-1] for row in rows] 
      st.session_state['selected_features_model'][filtered_variable]=rows
      #st.write(st.session_state['selected_features_model'][filtered_variable])


#st.text(st.session_state['selected_features_model'])
st.markdown('**Selected Variables**')

st.markdown("If you haven't explicitly chosen transformed variables, by default, the top three transformations are selected per variable based on correlation with the target. Click on Submit button to finalize.")

if len(st.session_state['selected_features_model'])>0:
  fe=[col for col in st.session_state['selected_features_model'].values() ]
  fed=pd.DataFrame({'Variables_selected':fe
                })


  # Use explode to split each list into multiple rows
  fed = fed.explode('Variables_selected', ignore_index=True)

  # Rename the index to 'index' if needed
  fed = fed.rename_axis('index').reset_index(drop=True)
  fed ['adstock'] = fed ['Variables_selected'].str.extract(r'_adst(\d+\.\d+)', expand=False)
  fed ['lag'] = fed ['Variables_selected'].str.extract(r'_lag(\d+)', expand=False)
  fed['Bucket']=fed['Variables_selected'].map(lambda x: Categorised_data[re.split(r'_adst|_lag',x)[0]]['VB'])
  fed.fillna('-',inplace=True)
  AgGrid(fed,fit_columns_on_grid_load=True)



  if st.button('Submit Changes'):
    # st.write(st.session_state['selected_features_model'].values())
    ad_lag_keys=[col for col in variables if col not in st.session_state['selected_features_model'].keys() ]
    #st.write(ad_lag_keys)
    for col in ad_lag_keys:
      # st.write(col)
      # st.write(st.session_state['df'].columns)
      #st.write(st.session_state['df'].columns[st.session_state['df'].columns.str.contains(col)])
      #st.session_state['selected_features_model'][col]=list(st.session_state['df'].columns[st.session_state['df'].columns.str.contains(col)])
      corr_top3=top_correlated_feature(st.session_state['df'],col,target_column)
      st.session_state['selected_features_model'][col]=list(corr_top3['Media_channel'].head(3).values)
      #st.write(ad_lag_keys)
    #st.write(st.session_state['selected_features_model'])
if st.checkbox("View all Selected Variables (table above will be updated)"):
  # AgGrid(fed,fit_columns_on_grid_load=True,key='nan')


  with open("filtered_variables.pkl", "wb") as f:
            pickle.dump(st.session_state['selected_features_model'], f)

# with open("filtered_variables.pkl", "wb") as f:
#       pickle.dump(st.session_state['selected_features_model'], f)