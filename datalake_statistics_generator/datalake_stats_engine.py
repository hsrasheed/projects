from pyspark.shell import spark #this is necessary to run on the cluster
from pyspark import SparkContext 
from pyspark.sql.types import *
import azure.datalake.store
from azure.datalake.store import core, lib, multithread
from azure.storage.blob import BlockBlobService
from azure.storage.blob import AppendBlobService
import pandas as pd
import numpy as np
import sys
import threading
import re
import json
import traceback
from datetime import date


SAMPLE_PERC = .10
MAX_FILES_PER_FEED = 15
LOGGING = False
TENANT_ID = ""
CLIENT_ID = ""
CLIENT_SECRET = ""
BLOB_KEY = ''
BLOB_KEY_2 = ''
BLOB_CONTAINER = 'datacatalog/stats'
STORAGE_ACCT_NAME = 'STORAGE_ACCOUNT'
purge_config_path_short = "prod/configuration/purgeconfig.prod.csv"
purge_config_path = "adl://isrmanalyticsadlsdata01.azuredatalakestore.net/prod/configuration/purgeconfig.prod.csv"
ADLS_ACCOUNT = "isrmanalyticsadlsdata01"
current_date = date.today().isoformat()
STATS_FILE_NAME = 'stats_'+current_date+'.json'

def get_feed_list_from_config():
    "Returns a list of Data Platform feeds from the purgeconfig file."
    adlCreds = lib.auth(tenant_id=TENANT_ID, client_secret=CLIENT_SECRET,
                    client_id=CLIENT_ID, resource = 'https://datalake.azure.net/')
    adl = core.AzureDLFileSystem(adlCreds, store_name=ADLS_ACCOUNT)
    string = "adl://isrmanalyticsadlsdata01.azuredatalakestore.net/"
    re_string = re.escape(string)
    feed_list = []
    with adl.open(purge_config_path_short, 'rb') as purge_config_file:
        purge_config_file.readline()
        file_contents = purge_config_file.readlines()
        line_num = 0
        for line in file_contents:
            #if line_num >= 5: break
            if "wasbs" not in line.decode("utf-8"):
                clean_contents = re.sub(re_string,"",line.decode("utf-8").split(",")[0])
                feed_list.append(clean_contents)
                line_num += 1
    return feed_list

def parse_adls_path(path,level='file'):
    """Parse a feed path at the file level 
    (form: /prod/feeds/source_name/feed_name/etldate=2018-01-01/file_name.ext) 
    or at the etl level (/prod/feeds/source_name/feed_name/etldate=2018-01-01) 
    Returns a tuple of the various parts"""
    if level == 'file':
        path_parts = path.split("/")
        file_name = path_parts[-1]
        etl_stamp = extract_date(path_parts[-2])
        feed_name = path_parts[-3]
        source_name = path_parts[-4]
        return (file_name, etl_stamp, feed_name, source_name)
    elif level == 'etl':
        path_parts = path.split("/")
        etl_stamp = extract_date(path_parts[-1])
        feed_name = path_parts[-2]
        source_name = path_parts[-3]
        return (etl_stamp, feed_name, source_name)
    
def parse_path(path):
    """Parse a feed path of the form: /prod/feeds/source_name/feed_name/etldate=2018-01-01/file_name.ext. Returns a tuple of the various parts"""
    path_parts = path.split("/")
    file_name = path_parts[-1]
    etl_stamp = extract_date(path_parts[-2])
    feed_name = path_parts[-3]
    source_name = path_parts[-4]
    return (file_name, etl_stamp, feed_name, source_name)

def parse_etl_path(path):
    path_parts = path.split("/")
    etl_stamp = extract_date(path_parts[-1])
    feed_name = path_parts[-2]
    source_name = path_parts[-3]
    return (etl_stamp, feed_name, source_name)

def extract_date(etlstamp):
    try:
        return etlstamp.split("=")[1]
    except:
        #print("Could not extract date from etl time stamp")
        return "1970-01-01"

def get_adls_file_dataframe(beginning_path):
    """returns a data frame with detailed system information using a adls file system client"""
    adlCreds = lib.auth(tenant_id=TENANT_ID, client_secret=CLIENT_SECRET,
                    client_id=CLIENT_ID, resource = 'https://datalake.azure.net/')
    adl = core.AzureDLFileSystem(adlCreds, store_name=ADLS_ACCOUNT)
    return pd.DataFrame(adl.ls(beginning_path,detail=True))

def get_adls_file_list(beginning_path):
    """returns a data frame with detailed system information using a adls file system client"""
    adlCreds = lib.auth(tenant_id=TENANT_ID, client_secret=CLIENT_SECRET,
                    client_id=CLIENT_ID, resource = 'https://datalake.azure.net/')
    adl = core.AzureDLFileSystem(adlCreds, store_name=ADLS_ACCOUNT)
    return pd.DataFrame(adl.ls(beginning_path))

def open_stats_blob_json():
    append_blob_service = AppendBlobService(STORAGE_ACCT_NAME, BLOB_KEY)
    file_contents = "{"+"\"ProcessDate\": \"{}\",".format(current_date)
    #file_contents = "{"
    try:
        append_blob_service.create_blob(
            BLOB_CONTAINER,
            STATS_FILE_NAME,
            if_none_match='*'
        )
    except:
        print("Tried to Create Existing Blob")

    append_blob_service.append_blob_from_bytes(
        BLOB_CONTAINER,
        STATS_FILE_NAME,
        file_contents.encode()
    )
    
def close_stats_blob_json():
    append_blob_service = AppendBlobService(STORAGE_ACCT_NAME, BLOB_KEY)
    append_blob_service.append_blob_from_bytes(
        BLOB_CONTAINER,
        STATS_FILE_NAME,
        "}".encode()
    )

def output_stats_to_json_blob(feed_stats_dict):
    append_blob_service = AppendBlobService(STORAGE_ACCT_NAME, BLOB_KEY)
    json_string = '"'+feed_stats_dict['FeedName']+'":'+json.dumps(feed_stats_dict)+','
    if LOGGING: print("Writing to blob: {}".format(json_string))
    append_blob_service.append_blob_from_bytes(
        BLOB_CONTAINER,
        STATS_FILE_NAME,
        json_string.encode()
    )

def get_path_suffix(path):
    path_parts = path.split('/')
    last = path_parts[-1]
    return last

def get_feed_source(path):
    path_parts = path.split('/')
    last = path_parts[-2]
    return last

def process_feed_list_threaded(all_vdc_feeds):
    if len(all_vdc_feeds) == 0: return
    open_stats_blob_json()
    num_threads = 0
    threads = []
    for element in all_vdc_feeds:
        newThread = threadedCrawler(num_threads,element,num_threads)
        newThread.start()
        threads.append(newThread)
        num_threads = num_threads+1
    for t in threads:
        t.join()
    close_stats_blob_json()
    return

def process_feed_list(all_vdc_feeds):
    if len(all_vdc_feeds) == 0: return
    open_stats_blob_json()
    for element in all_vdc_feeds:
            process_feeds_agg(element)
    close_stats_blob_json()
    return    
      
def copy_latest_to_sampled_df(full_df, sampled_df):
    """This method tries to ensure that ETLs from the last 24 hours are present in the sampled DF
    (if present in the original) - if they are already present in the sample or not in the full
    the same sampled_df is returned. Otherwise the ETLs from the last 24hours are appended to the 
    sampled df"""
    current_time_ms = time.time()*1000
    minus_24hrs_ms = (time.time()*1000)-86400000
    
    cond1 = sampled_df.modificationTime < current_time_ms
    cond2 = sampled_df.modificationTime > minus_24hrs_ms
    num_latest_sampled = len(sampled_df[np.logical_and(cond1,cond2)]) 
    
    cond1 = full_df.modificationTime < current_time_ms
    cond2 = full_df.modificationTime > minus_24hrs_ms
    filtered_full_df = full_df[np.logical_and(cond1,cond2)]
    num_latest_full = len(filtered_full_df) 
    
    if(num_latest_full == 0 or num_latest_sampled > 0):
        return sampled_df
    else:
        sampled_df = sampled_df.append(filtered_full_df)
        return sampled_df
        
def get_total_bytes_latest_etl(df):
    """Todo: Add some windowing """
    df.sort_values(by='ETL', ascending=False, inplace=True)
    return df.iloc[0]['FileSize']

def get_total_bytes_today_etl(df):
    """Todo: Add some windowing """   
    if len(df[df['ETL'].str.contains(date.today().isoformat())]) == 0:
        return 0
    else:
        today_df = df[df['ETL'].str.contains(date.today().isoformat())]
        return today_df.iloc[0]['FileSize']
    
def get_total_bytes_24hrs(df):
    current_time_ms = time.time()*1000
    minus_24hrs_ms = (time.time()*1000)-86400000
    cond1 = df.ModificationTime < current_time_ms
    cond2 = df.ModificationTime > minus_24hrs_ms
    window_df = df[np.logical_and(cond1,cond2)]
    if len(window_df) == 0:
        return 0
    else:
        return window_df.iloc[0]['FileSize']
    
def process_feeds_agg(path):
    if LOGGING: print("Process Feed {}".format(path))
    try:
        current_element_name = get_path_suffix(path)
        sub_elements_df = get_adls_file_dataframe(path)
        #If this directory is empty -- just return
        if len(sub_elements_df) == 0: return
        # Get subdirectories for this one
        # Because we are in the feed directory, this gives a list of ETLs
        sampled_elements_df = sub_elements_df.sample(frac=SAMPLE_PERC)
        sampled_elements_df = copy_latest_to_sampled_df(sub_elements_df,sampled_elements_df)
        feed_file_stats_df = pd.DataFrame(columns=['ETL','FileSize','SourceName','FeedName','ModificationTime'])
        for element in sampled_elements_df['name']:
        #for element in sub_elements_df['name']:
            element_df = sub_elements_df[sub_elements_df['name'] == element]
            element_type = element_df['type'].values[0]
            #Ensure that a subelement to the feed directory is a directory type
            if element_type == 'DIRECTORY':
                etl_stats_dict = process_etls_agg(element)
                if len(etl_stats_dict) > 0:
                    feed_file_stats_df.loc[len(feed_file_stats_df)] = etl_stats_dict
        df_length = len(feed_file_stats_df)
        if df_length > 0:
            if LOGGING:
                print("*** Feed Stats *** Length: {}".format(df_length))
                print(feed_file_stats_df)
            feed_info_dict  = {'FeedName':current_element_name,
                               'SourceName': get_feed_source(path),
                               'SummaryStatistics':{
                                    'TotalETLsProcessed':len(feed_file_stats_df['FileSize']),
                                    'AvgETLBytes':feed_file_stats_df['FileSize'].mean(),
                                    'AvgETLMB':feed_file_stats_df['FileSize'].mean()/1000000,
                                    'StdDevETLMB':feed_file_stats_df['FileSize'].std()/1000000,
                                    'MaxETLMB':feed_file_stats_df['FileSize'].max()/1000000,
                                    'MinETLMB':feed_file_stats_df['FileSize'].min()/1000000,
                                    'LastUpdated': feed_file_stats_df['ETL'].max(),
                                    'LatestETLMB': get_total_bytes_latest_etl(feed_file_stats_df)/1000000,
                                    'Last24HrsETLMB': get_total_bytes_24hrs(feed_file_stats_df)/1000000,
                                    'ProcessDate': current_date
                                }
                              }
            if LOGGING:
                print('Finished Creating Dict in Feed')
                print(json.dumps(feed_info_dict))
            output_stats_to_json_blob(feed_info_dict)
    except:
        print("Unexpected error processing Feed: {} Error: {}".format(current_element_name,sys.exc_info()[0]))
        print(traceback.format_exc())
    return

def process_etls_agg(path):
    if LOGGING: print("Process ETL {}".format(path))
    current_element_name = get_path_suffix(path)
    sub_elements_df = get_adls_file_dataframe(path)
    etl_stats_df = pd.DataFrame(columns=['ETL','FileSize','FileName','SourceName','FeedName','ModificationTime'])
    if len(sub_elements_df) == 0: return etl_stats_df
    etl_stamp, feed_name, source_name = parse_adls_path(path,'etl')
    for element in sub_elements_df['name']:
        if LOGGING: print("Process File {}".format(element))
        file_name = get_path_suffix(element)
        element_df = sub_elements_df[sub_elements_df['name'] == element]
        element_type = element_df['type'].values[0]
        element_size = element_df['length'].values[0]
        if element_type == 'FILE' and element_size>200:         
            if LOGGING: print("Source: {}, Feed: {}, ETL: {}, File: {}".format(source_name,feed_name,etl_stamp,file_name))
            file_info_dict  = {'ETL':etl_stamp,
                               'FileSize':element_size,
                               'FileName':file_name,
                               'SourceName':source_name,
                               'FeedName':feed_name,
                               'ModificationTime':element_df['modificationTime'].values[0]
                              }
            etl_stats_df.loc[len(etl_stats_df)] = file_info_dict
            if LOGGING: print('Finished ETL Parsing') 
    etl_summ_dict = {'ETL':etl_stamp,'FileSize':etl_stats_df['FileSize'].sum(),'SourceName':source_name,'FeedName':feed_name,'ModificationTime':etl_stats_df['ModificationTime'].max()}
    #etl_summ_df = pd.DataFrame.from_dict(etl_summ_dict)
    return etl_summ_dict

class threadedCrawler(threading.Thread):
    def __init__(self, threadID, name, counter):
      threading.Thread.__init__(self)
      self.threadID = threadID
      self.name = name
      self.counter = counter
    def run(self):
      if LOGGING: print("Starting " + self.name)
      process_feeds_agg(self.name)
      if LOGGING: print("Exiting " + self.name)
            
import time

scheduler = sched.scheduler(time.time, time.sleep)
schedule_time_seconds = 60*60*24

def MAIN():
    start_time = time.time()
    process_feed_list_threaded(get_feed_list_from_config())
    print("--- %s seconds ---" % (time.time() - start_time))
    scheduler.enter(schedule_time_seconds, 1, MAIN,"")

scheduler.enter(2, 1, MAIN,"")
scheduler.run()
