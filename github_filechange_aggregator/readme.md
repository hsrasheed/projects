# Automating reports on doc updates
A simple wrapper for the GitHub developer APIs (v3 and v4) that faciliates reporting aggregated file activity. This code is most suited for use with reporting on history of .md files hosted on GitHub, but it could be customized easily to extend to other use cases.

## The Need

The activity for our service had been minimal for an extended period of time and we had a big freshness problem.  When we finally started making updates regularly, we needed a way to inform our stakeholders about what articles had changed and how. We wanted a simple approach that would be easy to start using and have the fewest dependencies.

We decided to use the GitHub APIs (v3 and v4) because each of them provide some very useful unique features. We also decided to use basic python code for web requests because it would be simple for others to read and extend later for their own reporting use cases.

## Overview

Basically the code works in three phases:

1) Get a list of Pull Requests that meet your search criteria (using the version 3 REST API): repository, service label, dates, author, etc
2) Fetch detailed information about each of the Pull Requests including comments, and files  (using the version 4 GraphQL API)
3) Aggregate information for all of the files changed in the Pull Requests that you fetched: number of modifications and the summary of the changes made (by using the initial comment in each PR or the PR title)
4) Report out a list of all of the files modified in the period sorted by the total number of modifications and summarizing the changes.

The idea is that someone should be able to look at the report and see the files which had the greatest activity and understand what changes were made.

## Register a personal access token

Before getting started with the code, get a github personal access token at https://help.github.com/en/articles/creating-a-personal-access-token-for-the-command-line

## Understand GitHub APIs

### v3 REST API

The GitHub v3 API allows you to search a number of different objects, each with different parameters:

* repositories
* commits
* code
* issues and pull requests
* users
* topics
* labels

For more information, consult the [full documentation for the v3 GitHub developer API](https://developer.github.com/v3/).

#### Example queries for searching issues and pull requests:

Query the **azure-docs-pr** reposiroty for pull requests with a service label **hdinsight/svc**, status: "merged", and an updated date more recent than May 1, 2019. Note the name of the repository is specified in the format OWNER/REPOSITORY -- so in this case the owner is **MicrosoftDocs** and the repository is called **azure-docs-pr**.
```
https://api.github.com/search/issues?q=repo:MicrosoftDocs/azure-docs-pr type:pr label:hdinsight/svc is:merged updated:>2019-05-01
```

Query the "azure-docs" repo (public this time) for prs with a service label "hdinsight/svc", status: "merged", and an updated date more recent than May 1, 2019. 
```
https://api.github.com/search/issues?q=repo:MicrosoftDocs/azure-docs type:pr label:hdinsight/svc is:merged updated:>2019-05-01
```

Query the "azure-docs-pr" repository for prs with an author of "hrasheed-msft" or "dagiro", status: "merged", and an updated date more recent than May 1, 2019

```
https://api.github.com/search/issues?q=repo:MicrosoftDocs/azure-docs-pr type:pr author:hrasheed-msft author:dagiro is:merged updated:>2019-05-01
```

Query the "azure-docs-pr" repository for prs with a service label "hdinsight/svc", status: "merged", and a merged date between May 1, 2019 and June 1, 2019
```
https://api.github.com/search/issues?q=repo:MicrosoftDocs/azure-docs-pr type:pr label:hdinsight/svc is:merged merged:2019-05-01..2019-06-01
```

Getting file information:

[](https://api.github.com/search/code?q=repo:MicrosoftDocs/azure-docs+filename:hdinsight-hadoop-create-linux-clusters-adf.md)

Common parameters you might use when querying the REST API can be found in the following table:

| Parameter | Description | Possible Values |
|---|---|---|
| repo | GitHub repository | {azure-docs-pr, azure-docs,...} |
| type | the type of issue | {pr, issue} |
| label | a label attached to the pull request | {cosmos-db/svc, hdinsight/svc,...} |
| is | what type of issue it is | {pr, issue} |
| merged | the date when the pull request was merged | YYYY-MM-DD, Ex: 2019-05-01 |
| updated | the last updated date of the pull request | YYYY-MM-DD, Ex: 2019-05-01 |

For a full list of the qualifiers that you can use when querying issues, see [Searching issues and pull requests](https://help.github.com/en/articles/searching-issues-and-pull-requests)


### v4 GraphQL

The newer v4 GraphQL API allows you to specify the data that you want returned. Whereas the REST API may respond to a search query with a lot of extraneous information, the GraphQL API provides only the data you want (including connected objects) and thats it. You can often use just one query, rather than the multiple queries you would have to use with the v3 API.

However, [the v4 API doesnt allow you to filter PullRequest objects by date ](https://github.community/t5/GitHub-API-Development-and/GraphQL-Filtering-Pull-Request-on-CreatedDate/td-p/21402) -- so you will still have to run an initial search query to get a list of PRs and then follow up queries to get the details of the PRs with their subfields like commits, comments and files.

#### v4 Example queries equivalent to the previous examples

Query the **azure-docs-pr** repository for prs with a service label "hdinsight/svc", status: "merged", and an updated date more recent than May 1, 2019
```
{
  search(query: "repo:MicrosoftDocs/azure-docs-pr is:pr is:merged updated:>2019-05-01 label:hdinsight/svc", type: ISSUE) {
    edges {
      node {
        ... on PullRequest {
          url
          title
          createdAt
        }
      }
    }
  }
}
```

Query the **azure-docs** repository for prs with a service label "hdinsight/svc", status: "merged", and an updated date more recent than May 1, 2019
```
https://api.github.com/search/issues?q=repo:MicrosoftDocs/azure-docs type:pr label:hdinsight/svc is:merged updated:>2019-05-01
{
  search(query: "repo:MicrosoftDocs/azure-docs is:pr is:merged updated:>2019-05-01 label:hdinsight/svc", type: ISSUE) {
    edges {
      node {
        ... on PullRequest {
          url
          title
          createdAt
        }
      }
    }
  }
}
```

Query the **azure-docs-pr** repository for prs with an author of "hrasheed-msft" or "dagiro", status: "merged", and an updated date more recent than May 1, 2019

```
https://api.github.com/search/issues?q=repo:MicrosoftDocs/azure-docs-pr type:pr author:hrasheed-msft author:dagiro is:merged updated:>2019-05-01
{
  search(query: "repo:MicrosoftDocs/azure-docs-pr is:pr is:merged  author:hrasheed-msft author:dagiro updated:>2019-05-01", type: ISSUE) {
    edges {
      node {
        ... on PullRequest {
          url
          title
          createdAt
        }
      }
    }
  }
}
```

Query the **azure-docs-pr** repository for prs with a service label "hdinsight/svc", status: "merged", and a merged date between May 1, 2019 and June 1, 2019
```
{
  search(query: "repo:MicrosoftDocs/azure-docs-pr is:pr is:merged merged:2019-05-01..2019-06-01 label:hdinsight/svc", type: ISSUE) {
    edges {
      node {
        ... on PullRequest {
          url
          title
          createdAt
        }
      }
    }
  }
}
```

You can experiment with different GraphQL queries in the [API Explorer](https://developer.github.com/v4/explorer/)

For more information on search queries in the v4 API, see [Forming Calls with GraphQL \| GitHub Developer Guide](https://developer.github.com/v4/guides/forming-calls/#example-query).

[Repository \| GitHub Developer Guide](https://developer.github.com/v4/object/repository/)



## Python Code

### Create a query

#### V3 API Get

For searching with the v3 API we basically get a URL that contains all of the qualifiers we want, like the examples in the previous section. 

```python
def get_author_query(author, repo, begin_date, end_date):
    author_prs = 'https://api.github.com/search/issues?q=repo:MicrosoftDocs/{} type:pr author:{} is:merged merged:{}..{}'.format(repo, author, begin_date, end_date)
    return author_prs
```

```python
def get_label_query(svc_label, repo, begin_date, end_date):
    svc_prs = 'https://api.github.com/search/issues?q=repo:MicrosoftDocs/{} type:pr label:{} is:merged merged:{}..{}'.format(repo, svc_label, begin_date, end_date)
    return svc_prs
```

### Call the v3 API to get a list of PRs

Next we create a python HTTP request using the url as a parameter.

```python
def call_github_api_iter(api_urls, patoken):
    
    headers1 = {'Authorization': 'token ' + patoken, 'Accept': 'application/vnd.github.symmetra-preview+json'}
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
```

Important features of this code to note:

* Placing your personal access token in the request header
* Handling pagination is done using the following code: 

```
while 'next' in current_response.links.keys():
    current_response = requests.get(url=current_response.links['next']['url'], headers=headers1)
    json_data_array.append(current_response.json())
```

### Extract the PR numbers

```python
def extract_pr_numbers(json_response_array):
    pr_list = []
    for json_response in json_response_array:  
        json_obj = json.loads(json.dumps(json_response))
        for pr in json_obj['items']:
            number = json.dumps(pr['number'])
            #title = json.dumps(pr['title'])
            pr_list.append(number)        
    return(pr_list)
```

### Get detailed info on each PR using the v4 API



```python
def get_pr_data_v4(pr_number_array, patoken):

    url = 'https://api.github.com/graphql' 
    headers = {'Authorization': 'token ' + patoken}
    
    all_pr_data = []
    
    for pr_number in pr_number_array:
        pr_files_query = '''{repository(owner:"MicrosoftDocs", name:"azure-docs-pr") {
            pullRequest(number: '''+str(pr_number)+'''){
                  url
                  title
                  bodyText
                  createdAt
                  additions
                  changedFiles
                  state
                  publishedAt
                  number
                  commits(first: 10)
                  {
                    edges{
                      node{
                        id
                        commit
                        {
                          changedFiles
                        }
                      }
                    }
                  }
                  files(last: 100){
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
        '''
        json1 = {'query' : '%s' % pr_files_query}
        r = requests.post(url=url, json=json1, headers=headers)
        json_string = r.json()        
        all_pr_data.append(json_string)
    
    return(all_pr_data)
```

### Aggregating data at the file level and sorting

Now that we have obtained the detailed information for each of our pull requests, we iterate through this list and aggregate information about the files (or articles) we are interested in. 

1. Iterate through the list of pullRequests, obtaining basic information about each PR
1. Each pullRequest has a number of files. Iterate through the list of files and, using a hash that is keyed by the file path, keep track of all of the changes that have occurred on this file across the PR list: how many pullRequests modified the file, how many total lines were modified and what were the modifications.
2. Return a list of the files that is sorted by the total number of modifications across all PRs.

```python
def aggregate_sort_pr_data(pr_data_array,description_field='title'):
    file_info = {}
    file_info_list = []
    
    for pr in pr_data_array:
        #extract basic data about the PR from the json: url, number, author, date
        ...
        
        
        for file in pr['data']['repository']['pullRequest']['files']['edges']:
            file_name = json.dumps(file['node']['path']).replace("\"","")
            
            ...

            current_file_info = file_info.get(file_name,{})
            current_file_info["total_modifications"] = current_file_info.get("total_modifications",0) + int(pr_additions) + int(pr_deletions)
            current_file_info["times_modified"] = current_file_info.get("times_modified",0) + 1
            
            # create the description either using the PR title or the description (bodyText)
            if description_field == "title":
                if len(title) > 2:
                        if 'description' in current_file_info:
                            current_file_info["description"] = str(current_file_info.get("description","")) + " <br> " + 'PR: <a href={}>{}</a> <strong>Author:</strong> {} <strong>Description:</strong> {}'.format(pr_url,number,author,title)
                        else:
                            current_file_info["description"] = 'PR: <a href={}>{}</a> <strong>Author:</strong> {} <strong>Description:</strong> {}'.format(pr_url,number,author,title)
            else:
                if len(bodyText) > 2:
                    if 'description' in current_file_info:
                        current_file_info["description"] = str(current_file_info.get("description","")) + " <br> " + 'PR: <a href={}>{}</a> <strong>Author:</strong> {} <strong>Description:</strong> {}'.format(pr_url,number,author,bodyText)
                    else:
                        current_file_info["description"] = 'PR: <a href={}>{}</a> <strong>Author:</strong> {} <strong>Description:</strong> {}'.format(pr_url,number,author,bodyText)
            
            # add the aggregated data for the current
            file_info[file_name] = current_file_info
    
    # after iterating through all of the PRs, we have a hash map of all of the files modified in this group of PRs
    # we want to convert that hash map of hash maps to a list of hash maps so that the list can be sorted
    for key in file_info.keys():
        
        if "description" not in file_info[key]:
            file_info[key]["description"] = "None"
            
        file_info_list.append({"file_name": key,
                               "total_modifications": file_info[key]["total_modifications"],
                               "times_modified":file_info[key]["times_modified"],
                               "description":file_info[key]["description"]})
    
    # sort the list of files
    sorted_list = sorted(file_info_list, key=lambda k: k['total_modifications'], reverse=True) 
    return sorted_list  
```

### Generating output


The code below creates a HTML table with all of the different data aggregated in the previous methods, and then outputs to a file. 

I chose HTML output because its pretty ubiquitous and allowed for a reasonable amount of formatting like coloring alternating rows.  The code also uses a few simple methods to get the title of the document and detect if the URL is redirecting.

```python
def html_table(list_of_dicts):
    final_string = '''
    <html>
        <head>
          ...
        </head>
    '''
    final_string += '<table id="docupdates">'
    final_string += '<tr><th>Doc Title</th><th>Total Lines Modified</th><th>Number of Pull Requests</th><th>Description of Changes</th></tr>'
    for file_dict in list_of_dicts:
        if len(file_dict)>0:
            final_string += '<tr><td>{}</td><td>{}</td><td>{}</td><td>{}</td></tr>'.format(output_docs_link(file_dict["file_name"]),file_dict["total_modifications"],file_dict["times_modified"],file_dict["description"])
    final_string += '</table></html>'
    cur_dt1 = datetime.datetime.today()
    dt_str = '{:%m_%d_%y_%H_%M}'.format(cur_dt1)
    file_name = "GitHub_PR_Query_Data_"+dt_str+".html"
    with open(file_name, "w") as text_file:
        print(final_string, file=text_file)
```

## Pulling it all together

The following code snippet shows an example of using all of the different methods to create a report on documents in the Azure documentation repository labelled for the cosmos-db service between June 1, 2019 and June 31, 2019. It uses the PullRequest title as the description for the changes that occurred.

```python
patoken = "ABCD1234"

public_repo = "azure-docs"
private_repo = "azure-docs-pr"
svc = "cosmos-db/svc"
begin_date = "2019-06-01"
end_date = "2019-06-31"

svc_public_prs = get_label_query(svc,public_repo,begin_date,end_date)
svc_private_prs = get_label_query(svc,private_repo,begin_date,end_date)

private_pr_numbers_in_range = extract_pr_numbers(call_github_api_iter([svc_private_prs],patoken))
public_pr_numbers_in_range = extract_pr_numbers(call_github_api_iter([svc_public_prs],patoken))

all_pr_data = get_pr_data_v4(private_pr_numbers_in_range, patoken, private_repo)
all_pr_data += get_pr_data_v4(public_pr_numbers_in_range, patoken, public_repo)

html_table(aggregate_sort_pr_data(all_pr_data,description_field='title'))
```


