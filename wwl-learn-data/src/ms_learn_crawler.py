import requests
import json
from lxml import html
import datetime
from datetime import datetime
import calendar
import sys
import codecs
from datetime import timedelta
import traceback

from azure.kusto.data.exceptions import KustoServiceError
from azure.kusto.data.helpers import dataframe_from_result_table
from azure.kusto.data import KustoClient, KustoConnectionStringBuilder, ClientRequestProperties

class ms_learn_crawler:

    cert_urls = []
    learn_path_uids = []
    learn_path_urls = []
    module_urls = []

    def __init__(self):
        return
    
    def get_learn_paths(self):
        for url in self.cert_urls:
            print("Getting Learn IDs for Cert: {}".format(url.strip()))
            page = requests.get(url.strip())
            if page.status_code == requests.codes.ok:
                tree = html.fromstring(page.content)
                learn_uids = tree.xpath('//article[@aria-label="Learning Paths"]/@data-learn-uid')
                self.learn_path_uids.append(learn_uids)
                #print(learn_uids)
                for uid in learn_uids:
                    last_period = uid.rfind(".")
                    id_stub = uid[last_period+1:]
                    self.learn_path_urls.append(id_stub)
            else:
                print("Did not receive OK status in return")
                print(page.status_code)
                print(page)
        print(self.learn_path_uids)
        #print(self.learn_path_urls)
        return
        
    def get_learn_paths_for_cert(self, cert_url):
        print("Getting Learn IDs for Cert: {}".format(cert_url.strip()))
        page = requests.get(cert_url.strip())
        if page.status_code == requests.codes.ok:
            tree = html.fromstring(page.content)
            learn_uids = tree.xpath('//article[@aria-label="Learning Paths"]/@data-learn-uid')
        else:
            print("Did not receive OK status in return")
            print(page.status_code)
            print(page)
        #print(self.learn_path_uids)
        #print(self.learn_path_urls)
        return learn_uids
        
    def get_learn_path_modules(self, learn_path_url):
        print("Getting Module IDs for Learning path: {}".format(learn_path_url.strip()))
        page = requests.get(learn_path_url.strip())
        if page.status_code == requests.codes.ok:
            tree = html.fromstring(page.content)
            module_uids = tree.xpath('//div/@data-progress-uid')
            return module_uids
        else:
            print("Did not receive OK status in return")
        return
        
    def get_learn_path_metadata(self, learn_uids):
        #Note: these queries are taken from the DevRel library of sample queries: https://review.docs.microsoft.com/en-us/new-hope/analytics/microsoft_learn/learn%20sample%20query?branch=master 
        cluster = "https://cgadatamall.westus.kusto.windows.net"
        
        kcsb = KustoConnectionStringBuilder.with_az_cli_authentication(cluster)

        # The authentication method will be taken from the chosen KustoConnectionStringBuilder.
        client = KustoClient(kcsb)
        
        db = "WebAnalytics"
        query = """TopicMetadata
        |where Site=="docs.microsoft.com"
        |where Pagetype=="learn"
        |where PageKind=="path"
        |where Locale=="en-us"
        |where IsLive==1
        |where FromHistoryData==0
        |extend Title1=iif(indexof(Title, "learning path - Learn | Microsoft Docs",0)>0,substring(Title,0, indexof(Title, "learning path - Learn | Microsoft Docs",0)) ,substring(Title,0, indexof(Title, "| Microsoft Docs",0)))
        |extend Title=iif(indexof(Title1, "- Learn",0)>0,substring(Title1,0, indexof(Title1, "- Learn",0)) ,Title1)
        |project Uid,Units,LastPublished,Products,Roles,Levels, Title,FirstPublishDateTime, Modules, LiveUrl
        |sort by Uid, LastPublished
        |extend rank=row_number(1, prev(Uid)!=Uid)
        |where rank==1
        |mvexpand ModuleUid=todynamic(Modules)
        |extend Products=strcat_array(todynamic(Products),";"), Roles=strcat_array(todynamic(Roles),";"), Levels=strcat_array(todynamic(Levels),";")
        |summarize TotalModules= count()
        by LearningPathUid=Uid,LiveUrl
        | where LearningPathUid in ("""
        for i in range(len(learn_uids)):
            query = query+"'"+learn_uids[i]+"'"
            if i<len(learn_uids)-1:
                query = query+','
        query = query + ")"

        try:
            response = client.execute(db, query)
        except Exception: 
            print("An error occured getting LP metadata")
            print(query)
            traceback.print_exc()
            
        # we also support dataframes:
        dataframe = dataframe_from_result_table(response.primary_results[0])
        return dataframe
        
    def get_module_metadata(self, learn_uids):
        #Note: these queries are taken from the DevRel library of sample queries: https://review.docs.microsoft.com/en-us/new-hope/analytics/microsoft_learn/learn%20sample%20query?branch=master 
        cluster = "https://cgadatamall.westus.kusto.windows.net"
        
        kcsb = KustoConnectionStringBuilder.with_az_cli_authentication(cluster)

        # The authentication method will be taken from the chosen KustoConnectionStringBuilder.
        client = KustoClient(kcsb)
        
        db = "WebAnalytics"
        query = """TopicMetadata
        |where Site=="docs.microsoft.com"
        |where Pagetype=="learn"
        |where PageKind=="module"
        |where Locale=="en-us"
        |where IsLive ==1
        |where FromHistoryData==0
        |project LiveUrl,Uid,Title,Products,Roles,Levels,Units, FirstPublishDateTime,LastPublished
        |sort by Uid, LastPublished
        |extend rank=row_number(1, prev(Uid)!=Uid)
        |where rank==1
        |mvexpand todynamic(Units)
        |extend Products=strcat_array(todynamic(Products),";"), Roles=strcat_array(todynamic(Roles),";"), Levels=strcat_array(todynamic(Levels),";")
        |extend Title1=iif(indexof(Title, "learning path - Learn | Microsoft Docs",0)>0,substring(Title,0, indexof(Title, "learning path - Learn | Microsoft Docs",0)) ,substring(Title,0, indexof(Title, "| Microsoft Docs",0)))
        |extend Title=iif(indexof(Title1, "- Learn",0)>0,substring(Title1,0, indexof(Title1, "- Learn",0)) ,Title1)
        |extend Url= iif(indexof(LiveUrl,"/learn/wwl-mba/")>0,strcat("/learn/modules/",substring(LiveUrl,indexof(LiveUrl,"/learn/wwl-mba/")+15,strlen(LiveUrl))),substring(LiveUrl,indexof(LiveUrl,"/learn/modules"),strlen(LiveUrl))) 
        |project LiveUrl,Uid,Title,Products,Roles,Levels,Units, FirstPublishDateTime,LastPublished, Url,UnitUid=tostring(Units)
        |join kind=inner (database('WebAnalytics').TopicMetadata
            |where Site=="docs.microsoft.com"
            |where Pagetype=="learn" 
            |where PageKind=="unit"
            |where Locale=="en-us"
            |where IsLive==1
            |where FromHistoryData==0
            |extend Duration=toint(substring(UnitDurations,2,strlen(UnitDurations)-4))
            |project UnitUid=Uid, Duration,LastPublished
            |sort by UnitUid,LastPublished
            |extend rank=row_number(1, prev(UnitUid)!=UnitUid)
            |where rank==1
        ) on UnitUid 
        |summarize Duration=sum(Duration),TotalUnits=dcount(UnitUid)
        by LiveUrl,Uid,Url
        | where Uid in ("""
        for i in range(len(learn_uids)):
            query = query+"'"+learn_uids[i]+"'"
            if i<len(learn_uids)-1:
                query = query+','
        query = query + ")"

        try:
            response = client.execute(db, query)
            # we also support dataframes:
            dataframe = dataframe_from_result_table(response.primary_results[0])
            return dataframe
        except Exception: 
            print("An error occured getting module metadata")
            print(query)
            traceback.print_exc()


        
    def get_module_ratings(self, module_urls):
        cluster = "https://cgadatamall.westus.kusto.windows.net"
        
        kcsb = KustoConnectionStringBuilder.with_az_cli_authentication(cluster)

        # The authentication method will be taken from the chosen KustoConnectionStringBuilder.
        client = KustoClient(kcsb)
        
        db = "WebAnalytics"
        query = """PageView
        |where StartDateTime >= datetime(2021-06-01) and StartDateTime < datetime(2021-07-01)
        |where Site=="docs.microsoft.com"
        |where Url matches regex ("https?://docs.microsoft.com/([^/]*)/learn/")
        |where isnotempty(LearnRatingStarEventsJson)
        |extend ModuleUrl= strcat("/learn/modules/",extract(@"/learn/modules/([^/]*)/",1,Url),"/")
        |mvexpand LearnRatingStarEventsJson 
        |extend RatingTime=todatetime(LearnRatingStarEventsJson.EventDateTime), Verbatim=tostring(LearnRatingStarEventsJson.verbatim),
          Rating=toint(LearnRatingStarEventsJson.score), Reason=tostring(LearnRatingStarEventsJson.reasons),
                isNew=tobool(LearnRatingStarEventsJson.isNew)
        |project ModuleUrl,RatingTime,Verbatim,Rating,Reason,isNew, VisitorId
        |sort by ModuleUrl, VisitorId, RatingTime desc 
        |extend rank=row_number(1, prev(VisitorId)!=VisitorId), Date=startofmonth(RatingTime)
        |where rank==1 
        |summarize AverageRating=avg(Rating) by ModuleUrl
        | where ModuleUrl in ("""
        for i in range(len(module_urls)):
            query = query+"'"+module_urls[i]+"'"
            if i<len(module_urls)-1:
                query = query+','
        query = query + ")"

        try:
            response = client.execute(db, query)
        except Exception: 
            print("An error occured getting module ratings")
            print(query)
            traceback.print_exc()

        # we also support dataframes:
        dataframe = dataframe_from_result_table(response.primary_results[0])
        return dataframe