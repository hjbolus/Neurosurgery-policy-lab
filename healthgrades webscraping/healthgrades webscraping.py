import pandas as pd
from selenium import webdriver
from healthgrades_functions import *
import requests

# What should the output file be named?
output_file_name = ".../.../... .xlsx"

# Provide a list of HealthGrades physician profile URLs. I sourced them from an excel sheet, but you can change this accordingly (as long as urllist is a url list).
excel = '.../.../... .xlsx'
sheet = '...'
column = '...'

urllist = list(pd.read_excel(excel, sheet_name = sheet)[column])

driver = webdriver.Chrome()

comments = []
aggregate = []
locations = []
for url in urllist:
    time.sleep(0.5)
    name = " ".join(url.split("/")[-1].split("-")[0:-1]).replace("dr", "Dr.").title()
    print(name)

    response = requests.get(url).text

    pes = extract_from_responsetext(response)
    if pes['pes']['model']['commentCount'] > 20:
        response = click_show_more(driver, url)

    new_aggregate = collect_aggregates(pes)
    new_comments = collect_comments(response)
    for i in new_comments:
        i["physician"] = name
        comments.append(i)

    new_aggregate["physician"] = name
    new_aggregate["link"] = url
    new_aggregate["website"] = "HealthGrades"
    new_aggregate["average rating"] = response.split('data-qa-target="summaryStarReviewLink"')[1].split('>')[1].split(' ')[0]

    comment_ratings = [i['rating'] for i in new_comments]
    if len(comment_ratings):
        new_aggregate["average comment rating"] = sum(comment_ratings) / len(comment_ratings)
    else:
        new_aggregate["average comment rating"] = None
    aggregate.append(new_aggregate)

    for i in collectlocationdata(response):
        i["physician"] = name
        locations.append(i)

    for i in get_hospital_names(response):
        i["physician"] = name
        locations.append(i)

driver.quit()
with pd.ExcelWriter(output_file_name) as writer:
    pd.DataFrame(comments).to_excel(writer, sheet_name="comments")
    pd.DataFrame(aggregate).to_excel(writer, sheet_name="aggregate")
    pd.DataFrame(locations).to_excel(writer, sheet_name="locations")
