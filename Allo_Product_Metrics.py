import streamlit as st
import os
import pandas as pd
from pandas.io.json import json_normalize
import json
import numpy as np
import requests
import datetime
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    DateRange,
    Dimension,
    Metric,
    RunReportRequest,
)

path = 'Allo_Product_Dashboard-ac51c10481ae.json'

st.set_page_config(layout="wide")

# Variables
chain_id = 1
round_address = "0xD95A1969c41112cEE9A2c931E849bCef36a16F4C"

# filter function
def df_filter(message,df):
        slider_1, slider_2 = st.slider('%s' % (message),0,len(df)-1,[0,len(df)-1],1)

        while len(str(df.iloc[slider_1][1]).replace('.0','')) < 4:
            df.iloc[slider_1,1] = '0' + str(df.iloc[slider_1][1]).replace('.0','')
            
        while len(str(df.iloc[slider_2][1]).replace('.0','')) < 4:
            df.iloc[slider_2,1] = '0' + str(df.iloc[slider_1][1]).replace('.0','')

        start_date = datetime.datetime.strptime(str(df.iloc[slider_1][0]).replace('.0','') + str(df.iloc[slider_1][1]).replace('.0',''),'%Y-%m-%d %H:%M:%S%f')
        start_date = start_date.strftime('%d %b %Y, %I:%M%p')
        
        end_date = datetime.datetime.strptime(str(df.iloc[slider_2][0]).replace('.0','') + str(df.iloc[slider_2][1]).replace('.0',''),'%Y-%m-%d %H:%M:%S%f')
        end_date = end_date.strftime('%d %b %Y, %I:%M%p')

        st.info('Start: **%s**    End: **%s**' % (start_date,end_date))
        
        filtered_df = df.iloc[slider_1:slider_2+1][:].reset_index(drop=True)

        return filtered_df

siteHeader = st.container()

with siteHeader:
  st.title('Allo Product Metrics')
  st.text('In this report, we''ll take a deep dive analysis of general and usage specific metrics for Allo.')

  st.title('Round Overview')
  # Rounds
  round_url = f"https://grants-stack-indexer.fly.dev/data/{chain_id}/rounds.json"
  round_response = requests.request("GET", round_url)
  round_json = round_response.json()
  round_df = pd.json_normalize(round_json)
  # round_df['applicationsStartTime'] = pd.to_datetime(round_df['applicationsStartTime'].astype(int),unit='s')
  # round_df['applicationsEndTime'] = pd.to_datetime(round_df['applicationsEndTime'].astype(int),unit='s')
  # round_df['roundEndTime'] = pd.to_datetime(round_df['roundEndTime'].astype(int),unit='s')
  # round_df['applicationMetadata.lastUpdatedOn'] = pd.to_datetime(round_df['applicationMetadata.lastUpdatedOn'].astype(int),unit='s')

  # filtered_df = df_filter('Move slider to filter data',round_df)

  col1, col2, col3 = st.columns(3)
  col1.metric("QF Round", str(len(round_df.index)), f"+{len(round_df.index)} from yesterday")
  col2.metric("QV Rounds", "N/A", "0 from yesterday")
  col3.metric("Direct Grant Rounds", "N/A", "0 from yesterday")

  col1.metric("Avg Total Contribution Amount (QF)", str(round_df.loc[:, 'amountUSD'].mean().round(2)))
  col2.metric("$ Distribution (Matched funding)", "N/A")
  col3.metric("$ ditribution (Direct donation)", str(round_df.loc[:, 'amountUSD'].sum().round(2)))

  st.title('On-chain Data')

  # Projects
  projects_url = f"https://grants-stack-indexer.fly.dev/data/{chain_id}/rounds/{round_address}/projects.json"
  proj_response = requests.request("GET", projects_url)
  proj_json = proj_response.json()
  project_df = pd.json_normalize(proj_json)

  # Contributors
  contributors_url = f"https://grants-stack-indexer.fly.dev/data/{chain_id}/rounds/{round_address}/contributors.json"
  con_response = requests.request("GET", contributors_url)
  con_json = con_response.json()
  contributors_df = pd.json_normalize(con_json)

  # Votes
  votes_url = f"https://grants-stack-indexer.fly.dev/data/{chain_id}/rounds/{round_address}/votes.json"
  vote_response = requests.request("GET", votes_url)
  vote_json = vote_response.json()
  vote_df = pd.json_normalize(vote_json)


  st.title('App Usage')
  tab1, tab2, tab3 = st.tabs(["Explorer", "Manager", "Builder"])

  with tab1:
    property_id = st.secrets["e_property_id"]
    client = BetaAnalyticsDataClient.from_service_account_info(json.loads(st.secrets["google"]))

    request = RunReportRequest(
    property=f"properties/{property_id}",
    dimensions=[Dimension(name="date")],
    metrics=[Metric(name="activeUsers"), Metric(name="newUsers"), Metric(name="scrolledUsers"), Metric(name="userEngagementDuration"), Metric(name="wauPerMau"), Metric(name="sessions"), Metric(name="sessionsPerUser"), Metric(name='averageSessionDuration'), Metric(name='engagedSessions')],
    date_ranges=[DateRange(start_date="2020-03-31", end_date="today")],
    )
    explorer_response = client.run_report(request)

    date = []
    active_users = []
    new_users = []
    scrolled_users = []
    eng_duration = []
    wau_per_mau = []
    sessions = []
    sessions_per_user = []

    for row in explorer_response.rows:
        date.append(row.dimension_values[0].value)
        active_users.append(int(row.metric_values[0].value))
        new_users.append(int(row.metric_values[1].value))
        scrolled_users.append(int(row.metric_values[2].value))
        eng_duration.append(int(row.metric_values[3].value))
        wau_per_mau.append(float(row.metric_values[4].value))
        sessions.append(float(row.metric_values[5].value))
        sessions_per_user.append(float(row.metric_values[6].value))

    zipped_list = list(zip(date, active_users, new_users, scrolled_users, eng_duration, wau_per_mau, sessions, sessions_per_user))

    df = pd.DataFrame(zipped_list, columns=['date', 'active_users', 'new_users', 'scrolled_users', 'eng_duration', 'wau_per_mau', 'sessions', 'sessions_per_user']).sort_values(by=['date'], ascending=False)

    df[['date']] =  df[['date']].apply(pd.to_datetime)

    filtered_analytics = df_filter('Datetime Filter (Move slider to filter)', df)
    col_1, col_2 = st.columns(2)

    with col_1:
      st.header('New users')
      st.line_chart(filtered_analytics, x = 'date', y = 'new_users')

      st.header('Active users')
      st.line_chart(filtered_analytics, x = 'date', y = 'active_users')

    with col_2:
      st.header('Duration of engagement')
      st.bar_chart(filtered_analytics, x = 'date', y = 'eng_duration')

  # with tab2:
    # property_id = st.secrets["m_property_id"]
    # client = BetaAnalyticsDataClient.from_service_account_info(json.loads(st.secrets["google_man"]))

    # manager_request = RunReportRequest(
    # property=f"properties/{property_id}",
    # dimensions=[Dimension(name="date")],
    # metrics=[Metric(name="activeUsers"), Metric(name="newUsers"), Metric(name="scrolledUsers"), Metric(name="userEngagementDuration"), Metric(name="wauPerMau"), Metric(name="sessions"), Metric(name="sessionsPerUser"), Metric(name='averageSessionDuration'), Metric(name='engagedSessions')],
    # date_ranges=[DateRange(start_date="2020-03-31", end_date="today")],
    # )
    # manager_response = client.run_report(manager_request)

    # m_date = []
    # m_active_users = []
    # m_new_users = []
    # m_scrolled_users = []
    # m_eng_duration = []
    # m_wau_per_mau = []
    # m_sessions = []
    # m_sessions_per_user = []

    # for row in manager_response.rows:
    #     m_date.append(row.dimension_values[0].value)
    #     m_active_users.append(int(row.metric_values[0].value))
    #     m_new_users.append(int(row.metric_values[1].value))
    #     m_scrolled_users.append(int(row.metric_values[2].value))
    #     m_eng_duration.append(int(row.metric_values[3].value))
    #     m_wau_per_mau.append(float(row.metric_values[4].value))
    #     m_sessions.append(float(row.metric_values[5].value))
    #     m_sessions_per_user.append(float(row.metric_values[6].value))

    # m_zipped_list = list(zip(m_date, m_active_users, m_new_users, m_scrolled_users, m_eng_duration, m_wau_per_mau, m_sessions, m_sessions_per_user))

    # m_df = pd.DataFrame(m_zipped_list, columns=['date', 'active_users', 'new_users', 'scrolled_users', 'eng_duration', 'wau_per_mau', 'sessions', 'sessions_per_user']).sort_values(by=['date'], ascending=False)

    # m_df[['date']] =  m_df[['date']].apply(pd.to_datetime)
    # print(m_df.head())

    # m_filtered_analytics = df_filter('Datetime Filter (Move slider to filter)', m_df)
    # m_col_1, m_col_2 = st.columns(2)

    # with m_col_1:
    #   st.header('New users')
    #   st.line_chart(m_filtered_analytics, x = 'date', y = 'new_users')

    #   st.header('Active users')
    #   st.line_chart(m_filtered_analytics, x = 'date', y = 'active_users')

    # with m_col_2:
    #   st.header('Duration of engagement')
    #   st.bar_chart(m_filtered_analytics, x = 'date', y = 'eng_duration')

  with tab3:
    property_id = st.secrets["b_property_id"]
    client = BetaAnalyticsDataClient.from_service_account_info(json.loads(st.secrets["google_man"]))
    
    builder_request = RunReportRequest(
    property=f"properties/{property_id}",
    dimensions=[Dimension(name="date")],
    metrics=[Metric(name="activeUsers"), Metric(name="newUsers"), Metric(name="scrolledUsers"), Metric(name="userEngagementDuration"), Metric(name="wauPerMau"), Metric(name="sessions"), Metric(name="sessionsPerUser"), Metric(name='averageSessionDuration'), Metric(name='engagedSessions')],
    date_ranges=[DateRange(start_date="2020-03-31", end_date="today")],
    )
    builder_response = client.run_report(builder_request)

    b_date = []
    b_active_users = []
    b_new_users = []
    b_scrolled_users = []
    b_eng_duration = []
    b_wau_per_mau = []
    b_sessions = []
    b_sessions_per_user = []

    for row in builder_response.rows:
        b_date.append(row.dimension_values[0].value)
        b_active_users.append(int(row.metric_values[0].value))
        b_new_users.append(int(row.metric_values[1].value))
        b_scrolled_users.append(int(row.metric_values[2].value))
        b_eng_duration.append(int(row.metric_values[3].value))
        b_wau_per_mau.append(float(row.metric_values[4].value))
        b_sessions.append(float(row.metric_values[5].value))
        b_sessions_per_user.append(float(row.metric_values[6].value))

    b_zipped_list = list(zip(b_date, b_active_users, b_new_users, b_scrolled_users, b_eng_duration, b_wau_per_mau, b_sessions, b_sessions_per_user))

    b_df = pd.DataFrame(b_zipped_list, columns=['date', 'active_users', 'new_users', 'scrolled_users', 'eng_duration', 'wau_per_mau', 'sessions', 'sessions_per_user']).sort_values(by=['date'], ascending=False)

    b_df[['date']] =  b_df[['date']].apply(pd.to_datetime) 

    # b_filtered_analytics = df_filter('Datetime Filter (Move slider to filter)', b_df)
    b_col_1, b_col_2 = st.columns(2)

    with b_col_1:
      st.header('New users')
      st.line_chart(b_df, x = 'date', y = 'new_users')

      st.header('Active users')
      st.line_chart(b_df, x = 'date', y = 'active_users')

    with b_col_2:
      st.header('Duration of engagement')
      st.bar_chart(b_df, x = 'date', y = 'eng_duration')



  