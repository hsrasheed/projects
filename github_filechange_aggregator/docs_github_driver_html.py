from docs_github_wrapper_html import *
import calendar
import time

# Please create a Personal Access Token in GitHub
# https://help.github.com/en/articles/creating-a-personal-access-token-for-the-command-line

begin_date = "2019-10-01"
end_date = "2019-11-18"



###### Driver Code

public_repo = "azure-docs"
private_repo = "azure-docs-pr"
data_ai_svcs_prod =["analysis-services"
,"azure-analysis-services"
,"azure-databricks"
,"batch-ai"
,"cache"
,"cognitive-services"
,"consumer"
,"cosmos-db"
,"data-catalog"
,"data-explorer"
,"data-factory"
,"data-lake-analytics"
,"data-share"
,"dms"
,"enterprise-graph"
,"genomics"
,"hdinsight"
,"healthbot"
,"kusto"
,"machine-learning"
,"mariadb"
,"mysql"
,"mysql-database"
,"mysql-database-mc"
,"open-datasets"
,"postgresql"
,"powerbi"
,"power-bi-embedded"
,"powerquery"
,"search"
,"sql-database"
,"sql-data-warehouse"
,"sql-server-stretch-database"
,"sql-vms"
,"stream-analytics"
,"virtual-machines-sql"]

#data_ai_svcs_test = ["sql-database","sql-data-warehouse","sql-server-stretch-database"]

big_data_svcs =["hdinsight"]
#contributors_ignore_list=["hrasheed-msft","dagiro","JasonWHowell"]
contributors_ignore_list=[]

#data_svcs2 = ["postgresql"]
#"hdinsight","azure-databricks","cosmos-db",
#supp_svcs = ["hdinsight","azure-databricks","cosmos-db","data-factory"]

year = "2019"
month = "08"
end_day = calendar.monthrange(int(year), int(month))[1]

#begin_date = '{}-{}-01'.format(year,month)
#end_date = '{}-{}-{}'.format(year,month,str(end_day))

digest_modes = ['bodyText']

for digest_mode in digest_modes:

    print("Digest mode: "+digest_mode)

    for svc in big_data_svcs:
        print("Getting PRs for svc:{} between:{} and:{}".format(svc,begin_date,end_date))
        html_driver = docs_github_wrapper_html("31716b7f136b0a60495f5ccf7f8d1d266acd4525", begin_date, end_date, svc)
        html_driver.set_contributors_ignore(contributors_ignore_list)
        svc_private_prs = html_driver.get_label_query(private_repo)
        svc_public_prs = html_driver.get_label_query(public_repo)

        pr_numbers_in_range = html_driver.extract_pr_numbers(html_driver.call_github_api_iter([svc_private_prs]))
        public_pr_numbers_in_range = html_driver.extract_pr_numbers(html_driver.call_github_api_iter([svc_public_prs]))
        print("{} public PRs returned, {} private PRs returned".format(len(public_pr_numbers_in_range), len(pr_numbers_in_range)))
        all_pr_data = html_driver.get_pr_data_v4(pr_numbers_in_range, private_repo)
        all_pr_data += html_driver.get_pr_data_v4(public_pr_numbers_in_range, public_repo)

        print("Outputting to html...")
        html_driver.aggregate_sort_pr_data(all_pr_data,description_field=digest_mode)
        #html_driver.mysql_table(sorted_files, svc, digest_mode)
        html_driver.html_table(digest_mode)
