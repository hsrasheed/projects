from ms_learn_crawler import *
import calendar
import time
import pandas as pd
import pickle
import os

data_month = 1
data_year = 2022

f = open("portfolio.config", "r")
portfolio_urls = f.readlines()
cert_info = {}
all_cert_lp_info = pd.DataFrame()
all_cert_module_info = pd.DataFrame()
crawler = ms_learn_crawler()

## Get all the LP info for each cert
cert_lp_pickle_file_name = "../data/"+str(data_month)+"-"+str(data_year)+"-all_cert_lp_info.pkl"
if(os.path.exists(cert_lp_pickle_file_name)):
    #read from file to avoid reprocessing
    with open(cert_lp_pickle_file_name, 'rb') as file:
    # Call load method to deserialze
        all_cert_lp_info = pickle.load(file)
    
else:
    # do the processing
    for cert in portfolio_urls:

        learn_uids = crawler.get_learn_paths_for_cert(cert)
        if len(learn_uids)>0:
            lp_metadata = crawler.get_learn_path_metadata(learn_uids)
            df = pd.DataFrame(lp_metadata, columns = ['LearningPathUid', 'LiveUrl','TotalModules'])
            last_slash = cert.rfind("/")
            cert_name = cert[last_slash+1:]
            df['Certification'] = cert_name.strip()
            if all_cert_lp_info.size == 0:
                all_cert_lp_info = df
            else:
                all_cert_lp_info = pd.concat([all_cert_lp_info,df],sort=False)
    
    #print(all_cert_lp_info)
    # Open a file and use dump()
    with open(cert_lp_pickle_file_name, 'wb') as file:
          
        # A new file will be created
        pickle.dump(all_cert_lp_info, file)

print(all_cert_lp_info.describe())

input("Press Enter to continue...")

lp_data = pd.read_csv('../data/learning_path_stats-latest.csv', encoding = 'unicode_escape', engine ='python')
all_cert_lp_info = pd.merge(all_cert_lp_info, lp_data,on='LiveUrl')
all_cert_lp_info.rename(columns={'LiveUrl': 'LearningPathUrl'}, inplace=True)
all_cert_lp_info.columns.values[4] = "Title"
all_cert_lp_info['Month'] = data_month
all_cert_lp_info['Year'] = data_year

#Drop MSAuthor and GitHubAuthor columns, export w/o header
#all_cert_lp_info.drop(['MSAuthor', 'GitHubAuthor'], axis = 1)
print(all_cert_lp_info.columns)
all_cert_lp_info_final = all_cert_lp_info[["LearningPathUid_x","LearningPathUrl","TotalModules","Certification","Title","Total modules","Visitors","Page Views","LPCompletedRate","LPStarted","LPComplete","Trophies","Shared Trophies","Avg Minutes per Visitor","Bookmard Users","Duration(min)","LearningPathUid_y","Roles","Products","Levels","Month","Year"]]
all_cert_lp_info_final.to_csv('../processed_data/portfolio_cert_lp_info.csv',mode='w',header = False)

learn_path_urls = all_cert_lp_info['LearningPathUrl'].tolist()

all_cert_module_info_pickle_file_name = "../data/"+str(data_month)+"-"+str(data_year)+"-all_cert_module_info.pkl"
if(os.path.exists(all_cert_module_info_pickle_file_name)):
    #read from file to avoid reprocessing
    with open(all_cert_module_info_pickle_file_name, 'rb') as file:
    # Call load method to deserialze
        all_cert_module_info = pickle.load(file)
    
else:

    for learn_path_url in learn_path_urls:

        module_uids = crawler.get_learn_path_modules(learn_path_url)
        module_metadata = crawler.get_module_metadata(module_uids)
        df = pd.DataFrame(module_metadata, columns = ['LiveUrl','Uid','Url'])
        df['Certification'] = all_cert_lp_info.loc[all_cert_lp_info['LearningPathUrl'] == learn_path_url]['Certification'].values[0]
        df['LearningPathUrl'] = learn_path_url
        
        all_cert_module_info = pd.concat([all_cert_module_info,df],sort=False)

    # Open a file and use dump()
    with open(all_cert_module_info_pickle_file_name, 'wb') as file:
          
        # A new file will be created
        pickle.dump(all_cert_module_info, file)

input("Press Enter to continue...")

module_data = pd.read_csv('../data/module_stats-latest.csv', encoding = 'unicode_escape', engine ='python')
all_cert_module_info = pd.merge(all_cert_module_info, module_data,on='LiveUrl')
all_cert_module_info.rename(columns={'LiveUrl': 'ModuleUrl'}, inplace=True)
all_cert_module_info.columns.values[5] = "Title"
all_cert_module_info['Month'] = data_month
all_cert_module_info['Year'] = data_year

print(all_cert_module_info.columns)

#Drop MSAuthor and GitHubAuthor columns, export w/o header
#all_cert_module_info.drop(['MSAuthor', 'GitHubAuthor'], axis = 1)
all_cert_module_info_final = all_cert_module_info[["ModuleUrl","Uid","Url","Certification","LearningPathUrl","Title","Total Units","Visitors","Page Views","Module Completed Rate","Module Started","Module Completed","Badges","Shared Badges","Module Hours Viewed","Module Avg Minutes per UV","Duration","Average Star rating","Total Rater","Sandbox Activate(Clicks)","Sandbox Activate(Users)","Products","Roles","Levels","Month","Year"]]
all_cert_module_info_final.to_csv('../processed_data/portfolio_cert_module_info.csv',mode='w',header = False)

# This final part isn't necessary if we use the export from the dashboard that contains star rating data - 

#module_urls = all_cert_module_info['Url'].tolist()
#print(module_urls)
#module_ratings = pd.DataFrame(crawler.get_module_ratings(module_urls), columns = ['ModuleUrl','AverageRating'])
#print("Module Ratings DF")
#print(module_ratings.head())
#all_cert_module_info = pd.merge(all_cert_module_info, module_ratings.set_index('ModuleUrl'),left_on='Url',right_index=True)

#print(all_cert_lp_info)
#learn_urls2 = crawler.get_modules()
#print(all_cert_module_info.head())
