import streamlit as st
import pandas as pd
import numpy as np

st.title('Pool Check Ins')

uploaded_daily_check_in = st.file_uploader("Upload Daily Check Ins")
if uploaded_daily_check_in is not None:

    # Can be used wherever a "file-like" object is accepted:
    df_daily_check_in = pd.read_excel(uploaded_daily_check_in, skiprows=4, skipfooter=3)
    #st.write(df_daily_check_in)
    
uploaded_pool_sign_ups = st.file_uploader("Upload Pool Sign Ins")
if uploaded_pool_sign_ups is not None:

    # Can be used wherever a "file-like" object is accepted:
    df_pool_sign_up = pd.read_excel(uploaded_pool_sign_ups)
    #st.write(df_pool_sign_up)
    
def analysis(df_check_in, df_pool):
    
    #Only pull needed columns and exclude anyone that unregistered from their reservation
    df_pool_needed = df_pool[['Name', 'Start', 'End', 'Duration', 'Capacity','First', 'Last', 'Department', 'Status', 'Registration', 'Unregistered']]
    df_pool_needed = df_pool_needed[df_pool_needed['Status']== 'Registered']
    df_pool_needed['Full Name'] = df_pool_needed['First'].str.lower() + ' ' + df_pool_needed['Last'].str.lower()

    df_check_in_needed = df_check_in[['\nLast Name','\nFirst Name', '\nCheck-In Date/Time']]
    df_check_in_needed = df_check_in_needed.rename(columns={'\nLast Name': 'Last Name','\nFirst Name': 'First Name', '\nCheck-In Date/Time': 'Check-In Date/Time'})
    df_check_in_needed['Full Name'] = df_check_in_needed['First Name'].str.lower() + ' ' + df_check_in_needed['Last Name'].str.lower()
    
    #find date
    pool_min = df_pool_needed['Start'].min().date()
    pool_max = df_pool_needed['Start'].max().date()
    check_min = pd.to_datetime(df_check_in_needed['Check-In Date/Time']).min().date()
    check_max = pd.to_datetime(df_check_in_needed['Check-In Date/Time']).max().date()
    if pool_min==pool_max==check_min==check_max:
        date = check_max
    else:
        print('Not all days are the same')
        date = None
        return None, None

    df_comb = pd.merge(df_pool_needed, df_check_in_needed, how='outer', on='Full Name', indicator=True)

    signed_up_pool = df_pool_needed['Full Name'].tolist()

    names_only_in_pool = df_comb[df_comb['_merge'] == 'left_only']

    names_only_in_pool = names_only_in_pool[['Name', 'Start', 'End', 'First', 'Last', 'Full Name', 'Check-In Date/Time']]
    names_only_in_pool['Pool Check'] = 'Name not found in check ins'

    inner_join_df = df_comb[df_comb['_merge'] == 'both']
    
    # Calculate time differences
    print(inner_join_df.dtypes)
    inner_join_df['Check-In Date/Time'] = pd.to_datetime(inner_join_df['Check-In Date/Time'])
    delta_start = inner_join_df['Start'] - inner_join_df['Check-In Date/Time']


    # check_in_before_end = inner_join_df[inner_join_df['End']>=inner_join_df['Check-In Date/Time']]
    # check_in_before_end = check_in_before_end[['Name', 'Start', 'End', 'First', 'Last', 'Full Name', 'Check-In Date/Time']]
    # check_in_before_end['Pool Check'] = 'Member checked in before end of registration'

    # check_in_after_reg = inner_join_df[inner_join_df['End']<inner_join_df['Check-In Date/Time']]
    # check_in_after_reg = check_in_after_reg[['Name', 'Start', 'End', 'First', 'Last', 'Full Name', 'Check-In Date/Time']]
    # check_in_after_reg['Pool Check'] = 'Member checked after end of registration'
    
    conditions = [
    delta_start > pd.Timedelta(hours=2), # More than two before Start
    (delta_start <= pd.Timedelta(hours=2)) & (delta_start >= pd.Timedelta(0)), # Within two hours of Start
    (inner_join_df['Check-In Date/Time'] >= inner_join_df['Start']) & (inner_join_df['Check-In Date/Time'] <= inner_join_df['End']), # After start but before or at end
    inner_join_df['Check-In Date/Time'] > inner_join_df['End'] # After end
    ]
    choices = [
        'Member checked in MORE THAN two hours before start of registration',
        'Member checked in WITHIN tow hours before start of registration',
        'Member checked in AFTER registration started BUT before end',
        'Member checked in AFTER registration ended'
    ]
    
    choice_ids = [1, 2, 3, 4]
    
    inner_join_df['Pool Check'] = np.select(conditions, choices, default='Unknown Check-in Status')
    inner_join_df['Pool Check ID'] = np.select(conditions, choice_ids, default=-1)
    
    issue_check_ins = inner_join_df[inner_join_df['Pool Check ID'].isin([1, 4])]
    issue_check_ins = issue_check_ins[['Name', 'Start', 'End', 'First', 'Last', 'Full Name', 'Check-In Date/Time', 'Pool Check']]

    output = pd.concat([names_only_in_pool, issue_check_ins])

    #find date
    pool_min = df_pool_needed['Start'].min().date()
    pool_max = df_pool_needed['Start'].max().date()
    check_min = pd.to_datetime(df_check_in_needed['Check-In Date/Time']).min().date()
    check_max = pd.to_datetime(df_check_in_needed['Check-In Date/Time']).max().date()
        
    return output, date
    
if uploaded_pool_sign_ups is not None and uploaded_daily_check_in is not None:
    
    df, date = analysis(df_daily_check_in, df_pool_sign_up)
    date_str = str(date)
    print(date_str, ' Date')
    if df is None:
        st.subheader("Not all the days in both files are the same")
    else:
        st.subheader("Pool Usage Descrepencies")
        st.dataframe(df)
        df = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            "Download Pool Usage Descrepencies as CSV",
            data=df,
            file_name=f"pool_usage_descrepencies_{date_str}.csv"
            #mime="text/csv"
        )