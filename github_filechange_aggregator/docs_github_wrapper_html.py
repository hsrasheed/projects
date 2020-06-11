import requests
import json
from lxml import html
import datetime
from datetime import datetime
import calendar
import sys

class docs_github_wrapper_html:

    patoken = "12345"
    public_repo = "azure-docs"
    private_repo = "azure-docs-pr"
    begin_date = ""
    end_date = ""
    service = ""
    aggregate_stats = {}
    top_contributors = {}
    contributors_ignore = {}
    sorted_update_list = []
    sorted_new_list = []
    sorted_contributor_list = []

    def __init__(self,newtoken,begindate,enddate,svc):
        self.patoken = newtoken
        self.begin_date = begindate
        self.end_date = enddate
        self.service = svc
        self.top_contributors = {}
    
    def set_contributors_ignore(self,contrib_ignore):
        self.contributors_ignore = contrib_ignore
    
    def call_github_api_iter(self, api_urls):
        
        headers1 = {'Authorization': 'token ' + self.patoken, 'Accept': 'application/vnd.github.symmetra-preview+json'}
        json_data_array = []
        
        for api_url in api_urls:  
        
            current_response = requests.get(url=api_url, headers=headers1)

            json_data_array.append(current_response.json())

            if len(json_data_array) > 10:
                return (json_data_array)

            while 'next' in current_response.links.keys():
                current_response = requests.get(url=current_response.links['next']['url'], headers=headers1)
                json_data_array.append(current_response.json())
        
        return (json_data_array)

    def get_doc_title_path(self, file_path):
        shortened_path = file_path[file_path.find("articles/")+9:file_path.find(".md")]
        url = "https://docs.microsoft.com/en-us/azure/"+shortened_path
        page = requests.get(url, allow_redirects=False)
        if page.status_code == requests.codes.ok:
            tree = html.fromstring(page.content)
            doc_title = tree.xpath('//h1/text()')
            return doc_title[0].replace("'","")
        elif page.status_code == requests.codes.moved_permanently:
            doc_title = "[PERMANENTLY REDIRECTING] " + url
            return doc_title
        elif page.status_code == requests.codes.not_found:
            doc_title = "[PERMANENTLY REDIRECTING] " + url
            return doc_title   

    def get_doc_title_url(self, url):
        page = requests.get(url, allow_redirects=False)
        if page.status_code == requests.codes.ok:
            tree = html.fromstring(page.content)
            doc_title = tree.xpath('//h1/text()')
            return doc_title[0].replace("'","")
        elif page.status_code == requests.codes.moved_permanently:
            doc_title = "[PERMANENTLY REDIRECTING] " + url
            return doc_title
        elif page.status_code == requests.codes.not_found:
            doc_title = "[PERMANENTLY REDIRECTING] " + url
            return doc_title   

    def output_docs_link(self, file_path):
        shortened_path = file_path[file_path.find("articles/")+9:file_path.find(".md")]
        url = "https://docs.microsoft.com/en-us/azure/"+shortened_path
        return('<a href="{}">{}</a>'.format(url, self.get_doc_title_url(url)))
        
    def output_docs_url(self, file_path):
        shortened_path = file_path[file_path.find("articles/")+9:file_path.find(".md")]
        return "https://docs.microsoft.com/en-us/azure/"+shortened_path
            
    def get_author_query(self, repo, author):
        author_prs = 'https://api.github.com/search/issues?q=repo:MicrosoftDocs/{} type:pr author:{} is:merged merged:{}..{}'.format(repo, author, self.begin_date, self.end_date)
        return author_prs
        
    def get_label_query(self, repo):
        svc_prs = 'https://api.github.com/search/issues?q=repo:MicrosoftDocs/{} type:pr label:{}/svc is:merged merged:{}..{}'.format(repo, self.service, self.begin_date, self.end_date)
        return svc_prs

    def detect_newly_added(self, file_path):
        headers1 = {'Authorization': 'token ' + self.patoken, 'Accept': 'application/vnd.github.symmetra-preview+json'}
        json_data_array = []

        file_commits_query = 'https://api.github.com/repos/MicrosoftDocs/azure-docs-pr/commits?path={}'.format(file_path)
        current_response = requests.get(url=file_commits_query, headers=headers1)

        json_data_array.append(current_response.json())

        if len(json_data_array) > 10:
            print("json array larger than 10")
            return (json_data_array)

        while 'next' in current_response.links.keys():
            current_response = requests.get(url=current_response.links['next']['url'], headers=headers1)
            json_data_array.append(current_response.json())

        try:
            #print("Size of json array: "+str(len(json_data_array)))
            if len(json_data_array)>0:
                #print("Size of last json array: "+str(len(json_data_array[-1])))
                if len(json_data_array[-1]) > 0:
                    #print("Size of last last json array: "+str(len(json_data_array[-1][-1])))
                    if len(json_data_array[-1][-1]) > 0:
                        earliest_commit = json_data_array[-1][-1]                 
                    elif len(json_data_array[-1][-2]) > 0:
                        earliest_commit = json_data_array[-1][-2]
                    else:
                        print("Couldn't get last commit")
                        return 0
                    json_obj = json.loads(json.dumps(earliest_commit))
                    earliest_date = json_obj['commit']['committer']['date']
                    earliest_date_obj = datetime.strptime(earliest_date,'%Y-%m-%dT%H:%M:%SZ') 
                    if(earliest_date_obj>=datetime.strptime(self.begin_date,'%Y-%m-%d') and earliest_date_obj<=datetime.strptime(self.end_date,'%Y-%m-%d')):
                        #print("File: "+file_path+" - Newly Added")
                        return 1
                    else:
                        #print("File: "+file_path+" - Updated")
                        return 0      
                else:
                    print("File: "+file_path)
                    print("Size of last json array is zero")
                    #print(json_data_array)
            else:
                print("File: "+file_path)
                print("Size of json response is zero")
                #print(json_data_array)
            return 0
        except Exception as e:
            print("File: "+file_path+" - Could not get earliest commit")
            print(e)
            return 0


        
    def extract_pr_numbers(self, json_response_array):
        pr_list = []
        try:
            for json_response in json_response_array:  
                json_obj = json.loads(json.dumps(json_response))
                if len(json_obj) == 0:
                    sys.exit("No json content returned from search")
                    return 0
                #if not 'items' in json_obj or len(json_obj['items']) == 0:
                #    print(json.dumps(json_obj['items']))
                #    print("Expected array 'items' is json object was empty. Please verify repo details and permissions.")
                #    #return 0
                for pr in json_obj['items']:
                    number = json.dumps(pr['number'])
                    #title = json.dumps(pr['title'])
                    pr_list.append(number)        
            return(pr_list)
        except Exception as e:
            print(e)
            sys.exit("Error extracting PR numbers from GitHub search query")
            return 0
            
    def get_pr_data_v4(self, pr_number_array, repo):

        url = 'https://api.github.com/graphql' 
        headers = {'Authorization': 'token ' + self.patoken}
        
        all_pr_data = []
        
        for pr_number in pr_number_array:
            pr_files_query = """{repository(owner:"MicrosoftDocs", name: "%s") {
                pullRequest(number: %d){
                    author{login}
                    url
                    title
                    bodyText
                    createdAt
                    additions
                    changedFiles
                    state
                    publishedAt
                    number
                    files(first: 20){
                    edges{
                      node{
                        path
                        additions
                        deletions
                      }
                    }
                    }
                }
              }
            }
            """ % (repo, int(pr_number))
            json1 = {'query' : '%s' % pr_files_query}
            r = requests.post(url=url, json=json1, headers=headers)
            json_string = r.json()        
            all_pr_data.append(json_string)
        
        return(all_pr_data)
        
    def aggregate_sort_pr_data(self, pr_data_array,description_field='title'):
        file_info = {}
        updated_file_info_list = []
        new_file_info_list = []
        contributor_info_list = []
        
        for pr in pr_data_array:
            try:
                pr_url = json.dumps(pr['data']['repository']['pullRequest']['url'])
                number = json.dumps(pr['data']['repository']['pullRequest']['number'])
                author = json.dumps(pr['data']['repository']['pullRequest']['author']['login']).replace("\"","")
                published_date = json.dumps(pr['data']['repository']['pullRequest']['publishedAt'])
                title = json.dumps(pr['data']['repository']['pullRequest']['title'])
                bodyText = json.dumps(pr['data']['repository']['pullRequest']['bodyText'])
            except:
                print("Error processing pr: "+str(pr))
                continue
                   
            for file in pr['data']['repository']['pullRequest']['files']['edges']:
                file_name = json.dumps(file['node']['path']).replace("\"","")
                
                if ".md" not in file_name:
                    continue
                if "includes" in file_name:
                    continue
                
                pr_additions = json.dumps(file['node']['additions'])
                pr_deletions = json.dumps(file['node']['deletions'])

                current_file_info = file_info.get(file_name,{})
                current_file_info["total_modifications"] = current_file_info.get("total_modifications",0) + int(pr_additions) + int(pr_deletions)
                current_file_info["times_modified"] = current_file_info.get("times_modified",0) + 1
                
                if author not in self.contributors_ignore:
                    if author not in self.top_contributors:
                        self.top_contributors[author] = 1
                    else:
                        self.top_contributors[author] = self.top_contributors.get(author) + 1

                if 'doc_title' not in current_file_info:
                    current_file_info["doc_title"] = self.get_doc_title_path(file_name)
                
                if description_field == "title":
                    if len(title) > 2:
                            if 'description' in current_file_info:
                                current_file_info["description_html"] = str(current_file_info.get("description_html","")) + " <br> " + 'PR: <a href={}>{}</a> <strong>Author:</strong> {} <strong>Description:</strong> {}'.format(pr_url,number,author,title)
                                current_file_info["description"] = str(current_file_info.get("description","")) + " | " + 'PR: {} Author: {} Description: {}\n'.format(number,author,title)
                            else:
                                current_file_info["description_html"] = 'PR: <a href={}>{}</a> <strong>Author:</strong> {} <strong>Description:</strong> {}'.format(pr_url,number,author,title)
                                current_file_info["description"] = 'PR: {} Author: {} Description: {}'.format(number,author,title)
                else:
                    if len(bodyText) > 2:
                        if 'description' in current_file_info:
                            current_file_info["description_html"] = str(current_file_info.get("description_html","")) + " <br> " + 'PR: <a href={}>{}</a> <strong>Author:</strong> {} <strong>Description:</strong> {}'.format(pr_url,number,author,bodyText)
                            current_file_info["description"] = str(current_file_info.get("description","")) + " | " + 'PR: {} Author: {} Description: {}\n'.format(number,author,bodyText)
                        else:
                            current_file_info["description_html"] = 'PR: <a href={}>{}</a> <strong>Author:</strong> {} <strong>Description:</strong> {}'.format(pr_url,number,author,bodyText)
                            current_file_info["description"] = 'PR: {} Author: {} Description: {}\n'.format(number,author,bodyText)
                
                file_info[file_name] = current_file_info
        
        for key in file_info.keys():
            
            if "description" not in file_info[key]:
                file_info[key]["description"] = "None"
                file_info[key]["description_html"] = "None"
            
            new_article = self.detect_newly_added(key)
            
            if new_article:
                new_file_info_list.append({"file_name": key,
                                       "total_modifications": file_info[key]["total_modifications"],
                                       "times_modified":file_info[key]["times_modified"],
                                       "description":file_info[key]["description"],
                                       "description_html":file_info[key]["description_html"],
                                       "doc_title":file_info[key]["doc_title"],
                                       "newly_added":new_article})
            else:
                updated_file_info_list.append({"file_name": key,
                                       "total_modifications": file_info[key]["total_modifications"],
                                       "times_modified":file_info[key]["times_modified"],
                                       "description":file_info[key]["description"],
                                       "description_html":file_info[key]["description_html"],
                                       "doc_title":file_info[key]["doc_title"],
                                       "newly_added":new_article})
        
        #get a list of all new files sorted by total modifications
        sorted_list = sorted(updated_file_info_list, key=lambda k: k['total_modifications'], reverse=True) 
        self.sorted_update_list = sorted_list
        
        #get a list of all UPDATED files sorted by total modifications
        sorted_list2 = sorted(new_file_info_list, key=lambda k: k['total_modifications'], reverse=True) 
        self.sorted_new_list = sorted_list2  
        
        for key in self.top_contributors.keys():
            contributor_info_list.append({"contributor_name":key,"total_prs":self.top_contributors[key]})
        
        #get a list of all contributors sorted by total PRs
        sorted_list3 = sorted(contributor_info_list, key=lambda k: k['total_prs'], reverse=True) 
        self.sorted_contributor_list = sorted_list3  
           
    def html_table(self, digest_mode):
        final_string = '''
        <html>
            <head>
                <style type="text/css">
                #docupdates {
                font-family: "Trebuchet MS", Arial, Helvetica, sans-serif;
                border-collapse: collapse;
                width: 100%;
                }

                #docupdates td, #docupdates th {
                border: 1px solid #ddd;
                padding: 8px;
                }

                #docupdates tr:nth-child(even){background-color: #f2f2f2;}

                #docupdates tr:hover {background-color: #ddd;}

                #docupdates th {
                padding-top: 12px;
                padding-bottom: 12px;
                text-align: left;
                background-color: #000000;
                color: white;
                }
                </style>
            </head>
        '''
        #calculate aggregates
        total_newly_added = 0
        total_updated = 0
        total_lines_modified = 0
        
        total_newly_added = len(self.sorted_new_list)
        total_updated = len(self.sorted_update_list)
        
        for file_dict in self.sorted_new_list:      
            total_lines_modified += file_dict["total_modifications"]
            
        for file_dict in self.sorted_update_list:      
            total_lines_modified += file_dict["total_modifications"]
        
        final_string += '<body><h1>PR Report for {} from {} to {}</h1>'.format(self.service, self.begin_date, self.end_date)
        final_string += '<table id="docupdates"><tr><th>Total Docs Added</th><th>Total Docs Updated</th><th>Total Lines Modified</th></tr><tr><td>{}</td><td>{}</td><td>{}</td></tr></table></br></br>'.format(total_newly_added,total_updated,total_lines_modified)
        
        final_string += '<table id="docupdates"><tr><th>Contributor</th><th>PRs authored</th></tr>'
        for contributor in self.top_contributors:
            final_string += '<tr><td>{}</td><td>{}</td></tr>'.format(contributor,self.top_contributors[contributor])
        final_string += '</table></br></br>'
        
        #comment = """        
        final_string += '<table id="docupdates">'
        final_string += '<tr><th>Doc Title</th><th>Added</th><th>Total Lines Modified</th><th>Number of Pull Requests</th><th>Description of Changes</th></tr>'
        for file_dict in self.sorted_new_list:
            if len(file_dict)>0:
                final_string += '<tr><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{}</td></tr>'.format(self.output_docs_link(file_dict["file_name"]),
                                                                                                            "A" if file_dict["newly_added"] == 1 else "U",
                                                                                                            file_dict["total_modifications"],
                                                                                                            file_dict["times_modified"],
                                                                                                            file_dict["description_html"])
        for file_dict in self.sorted_update_list:
            if len(file_dict)>0:
                final_string += '<tr><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{}</td></tr>'.format(self.output_docs_link(file_dict["file_name"]),
                                                                                                            "A" if file_dict["newly_added"] == 1 else "U",
                                                                                                            file_dict["total_modifications"],
                                                                                                            file_dict["times_modified"],
                                                                                                            file_dict["description_html"])
        final_string += '</table></body></html>'
        #"""
        #cur_dt1 = datetime.datetime.today()
        #dt_str = '{:%m_%d_%y_%H_%M}'.format(cur_dt1)
        file_name = "GitHub_PR_Query_Data_"+self.service+"_"+self.begin_date.replace("-","")+"_"+self.end_date.replace("-","")+".html"
        with open(file_name, "w") as text_file:
            print(final_string, file=text_file)