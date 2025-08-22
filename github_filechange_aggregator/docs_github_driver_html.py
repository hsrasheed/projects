from docs_github_wrapper_html import *
import calendar
import time

# Please create a Personal Access Token in GitHub
# https://help.github.com/en/articles/creating-a-personal-access-token-for-the-command-line

begin_date = "2020-05-01"
end_date = "2020-06-01"

###### Driver Code

public_repo = "azure-docs"
private_repo = "azure-docs-pr"

svcs =["hdinsight"]

f = open("access_token.config", "r")
access_token = f.readline().strip()

digest_modes = ['bodyText']

for digest_mode in digest_modes:

    print("Digest mode: "+digest_mode)

    for svc in svcs:
        print("Getting PRs for svc:{} between:{} and:{}".format(svc,begin_date,end_date))
        html_driver = docs_github_wrapper_html(access_token, begin_date, end_date, svc)
        #html_driver.set_contributors_ignore(contributors_ignore_list)
        svc_private_prs = html_driver.get_label_query(private_repo)
        svc_public_prs = html_driver.get_label_query(public_repo)

        pr_numbers_in_range = html_driver.extract_pr_numbers(html_driver.call_github_api_iter([svc_private_prs]))
        public_pr_numbers_in_range = html_driver.extract_pr_numbers(html_driver.call_github_api_iter([svc_public_prs]))
        print("{} public PRs returned, {} private PRs returned".format(len(public_pr_numbers_in_range), len(pr_numbers_in_range)))
        all_pr_data = html_driver.get_pr_data_v4(pr_numbers_in_range, private_repo)
        all_pr_data += html_driver.get_pr_data_v4(public_pr_numbers_in_range, public_repo)

        print("Outputting to html...")
        html_driver.aggregate_sort_pr_data(all_pr_data,description_field=digest_mode)
        html_driver.html_table(digest_mode)
