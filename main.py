import pandas as pd
import os
import streamlit as st
import plotly.express as px
from datetime import datetime
from dateutil.relativedelta import relativedelta
import requests
import json

# configurations

api_key = '8d3c2e3f51624105b95493f5fcf8a098'

storage_folder = "myfiles"

api_uri = 'https://api.bls.gov/publicAPI/v2/timeseries/data/'


api_collection = [ 
                    "LNS14000000" , # unemployment rate (mandatory)
                    "CES0000000001", # non farm employment (mandatory)
                    "PRS85006092", # Nonfarm Business Unit Labor Costs 
                    "PRS85006112", # Nonfarm Business Real Hourly Compensation
                    "PRS85006152" # Private Nonfarm Business - Multifactor Productivity, annual index (Unadjusted)
                    ]




def PullAllData():    

        # start range of pulling data

        prev_year = (datetime.now() - relativedelta(months=12)).year


        # api call        
        
        headers = {'Content-type': 'application/json'}


        data = json.dumps({"seriesid": api_collection,
        "startyear":str(prev_year),"endyear":datetime.now().year,
        "registrationkey":api_key})
        
        
        p = requests.post(api_uri,data=data, headers=headers)

        # creating dataframe

        api_data = json.loads(p.text)

        for _id in api_collection:

            data_obj = [x for x in api_data['Results']['series'] if x['seriesID'] ==_id]

            api_table = pd.DataFrame.from_dict(data_obj[0]['data'],orient='columns')

            api_table.to_csv(storage_folder+'/'+_id+'.csv',index=False)
    

        return {'status':"Success"}
    

def PullLatestData():

    # api call        
    headers = {'Content-type': 'application/json'}

    # pull data
    data = json.dumps({"seriesid": api_collection,'latest':True,
                        "registrationkey":api_key})

    # making api call
    p = requests.post(api_uri,data=data, headers=headers)

    api_data = json.loads(p.text)

    for _id in api_collection:

        data_obj = [x for x in api_data['Results']['series'] if x['seriesID'] ==_id]

        orig_table = pd.read_csv(storage_folder+'/'+_id+'.csv')

        increm_table = pd.DataFrame.from_dict(data_obj[0]['data'],orient='columns')

        # Append df2 to df1
        append_df = pd.concat([orig_table, increm_table], ignore_index=True)

        append_df.loc[:,'year']=append_df['year'].astype(str)

        # Remove duplicates 
        unique_df = append_df.drop_duplicates(subset=['year','periodName'])

        # writing data back to storage

        unique_df.to_csv(storage_folder+'/'+_id+'.csv',index=False)

        print('pulling latest data')

    
    return {'status':"Success"}



if os.path.exists(storage_folder) == False:

    os.makedirs(storage_folder)

    PullAllData()

#                                                            Part 2 : Dashboard Layer

def PreprocessData(df,start_date, end_date):

    # mappings for month and quarters

    month_q_map = {
        'January': '01', 'February': '02', 'March': '03', 'April': '04', 'May': '05', 'June': '06',
        'July': '07', 'August': '08', 'September': '09', 'October': '10', 
        'November': '11', 'December': '12',
        "1st Quarter":'03','2nd Quarter':"06","3rd Quarter":"09","4th Quarter":"12"
    }

    df['yearMonth'] = df['year'].astype(str) + '-' + df['periodName'].map(month_q_map)

    df['date']=pd.to_datetime(df['yearMonth'])

    df=df.loc[(df['date']>=pd.Timestamp(start_date))&
                (df['date']<=pd.Timestamp(end_date))]
    
    df.reset_index(inplace=True,drop=True)                                

    return df

# Page Title

# Configure the page layout to 'wide'
st.set_page_config(page_title="Dashboard", layout="wide")

st.title("Labor Statistics Dashboard From US Bureau")

st.header('Select A Date Range To View The Data')

col1,col2 = st.columns(2)

with col1:

    start_date = st.date_input("From Date", 
                value=datetime.now() - relativedelta(months=15), 
                min_value=datetime.now() - relativedelta(months=15), 
                max_value=datetime.now())

with col2:

    end_date = st.date_input("Till", 
                value=datetime.now(), 
                min_value=datetime.now() - relativedelta(months=15), 
                max_value=datetime.now())




# Reading the tables

unemp_rate_df = pd.read_csv(storage_folder+'/'+'LNS14000000.csv')

non_farm_emp_df = pd.read_csv(storage_folder+'/'+'CES0000000001.csv')

nonfarm_bu_labor_cost_df = pd.read_csv(storage_folder+'/'+'PRS85006092.csv')

nonfarm_hourly_comp_df = pd.read_csv(storage_folder+'/'+'PRS85006112.csv')

multifactor_prod_df = pd.read_csv(storage_folder+'/'+'PRS85006152.csv')


# filtering by timestamp from sidebar

unemp_rate_df = PreprocessData(unemp_rate_df,start_date,end_date)

non_farm_emp_df = PreprocessData(non_farm_emp_df,start_date,end_date)

nonfarm_bu_labor_cost_df = PreprocessData(nonfarm_bu_labor_cost_df,start_date,end_date)

nonfarm_hourly_comp_df = PreprocessData(nonfarm_hourly_comp_df,start_date,end_date)

multifactor_prod_df = PreprocessData(multifactor_prod_df,start_date,end_date)


# plotting the charts - section 1

st.text('Umemployment Rate As Per US Labor Bureau Yearwise')

st.area_chart(unemp_rate_df[['year','value']], 
                x="year", 
                y="value",x_label='Year',
                y_label='Unemployment Rate',
                use_container_width=True)

st.text('Non Farm Employment As Per US Labor Bureau')

fig = px.pie(non_farm_emp_df, 
            names='periodName',values='value')

st.plotly_chart(fig,use_container_width=True)


col3,col4 =st.columns(2)

with col3:

    st.text('Nonfarm Business Unit Labor Costs')

    st.bar_chart(nonfarm_bu_labor_cost_df, horizontal=True,
                x="yearMonth", y="value", color="year",
                x_label='Month',y_label='Unit Labor Cost',
                use_container_width=True)

with col4:

    st.text('Nonfarm Business Real Hourly Compensation')

    st.bar_chart(nonfarm_hourly_comp_df, 
                x="yearMonth", y="value",horizontal=True,
                x_label='Month',y_label='ID-Private',
                color='year',use_container_width=True)



    
st.text('Private Nonfarm Business - Multifactor Productivity, annual index (Unadjusted)')

st.bar_chart(multifactor_prod_df, 
            x="yearMonth", y="value",color='year',
            x_label='Month',y_label='Wage',
            use_container_width=True,horizontal=True,)





# plotting the tables - section 2


st.subheader('Unemployment Rate - Raw Data')

st.dataframe(unemp_rate_df[["year","period","periodName","latest","value","footnotes"]],use_container_width=True)

st.subheader('Non-farm Employee - Raw Data')

st.dataframe(non_farm_emp_df[["year","period","periodName","latest","value","footnotes"]],use_container_width=True)

st.subheader('Nonfarm Business Unit Labor Costs')

st.dataframe(nonfarm_bu_labor_cost_df[["year","period","periodName","latest","value","footnotes"]],use_container_width=True)

st.subheader('Nonfarm Business Real Hourly Compensation')

st.dataframe(nonfarm_hourly_comp_df[["year","period","periodName","latest","value","footnotes"]],use_container_width=True)

st.subheader('Private Nonfarm Business - Multifactor Productivity, annual index (Unadjusted)')

st.dataframe(multifactor_prod_df[["year","period","periodName","latest","value","footnotes"]],use_container_width=True)



# Incremental Load Button

if st.button('Pull Latest Data'):    

    PullLatestData()

    st.rerun()