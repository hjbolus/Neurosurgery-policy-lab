from bs4 import BeautifulSoup
import time
import ast
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def collect_comments(text: str) -> list:
    commentlist = []

    comments = [ast.literal_eval(i.split('type="application/ld+json">')[1].split('<')[0]) for i in text.split('<div class="c-single-comment"')[1:]]

    for i in comments:
        comment = dict()
        review = i['review']
        comment['text'] = review['reviewBody']
        comment['date'] = review['datePublished']
        comment['author'] = review['author']['name']
        comment['rating'] = review['reviewRating']['ratingValue']

        commentlist.append(comment)
    return commentlist

def extract_from_responsetext(text: str) -> dict:
    soup = BeautifulSoup(text, "html.parser")
    script = [i for i in soup.find_all("script") if any(["pes" in j for j in i.children])]

    if len(script) == 2:
        script = str(script[0])
    else:
        print("len(script) is " + str(len(script)))

    step_one = '"pes"' + script.split('"pes"')[1]

    if ',"surveysSuppressed":false}}' in step_one:
        step_two = (
            step_one.split(',"surveysSuppressed":false}}')[0]
            + ',"surveysSuppressed":false}}'
        )
    else:
        assert ',"surveysSuppressed":true}}' in step_one
        step_two = (
            step_one.split(',"surveysSuppressed":true}}')[0]
            + ',"surveysSuppressed":true}}'
        )

    step_three = (
        "{"
        + step_two.replace(":true", ":True")
        .replace(":false", ":False")
        .replace(":null", ":None")
        + "}"
    )
    pes = ast.literal_eval(step_three)
    return pes

def collect_aggregates(pes):

    aggregate_data = dict()
    aggregate_data["total reviews"] = pes["pes"]["model"]["surveyDistribution"]["totalResponseCount"]
    aggregate_data["total comments"] = pes["pes"]["model"]["commentCount"]

    for num in range(1, 6):
        aggregate_data[str(num) + " star count"] = [i["count"] for i in pes["pes"]["model"]["surveyDistribution"]["aggregates"] if i["star"] == num][0]

    for i in pes["pes"]["model"]["cards"]:
        for j in i["aggregates"]:
            aggregate_data[j["title"] + " score"] = j["actualScore"]
            aggregate_data[j["title"] + " count"] = j["responseCount"]

    return aggregate_data


def collectlocationdata(text):
    str1 = [i.split('data-qa-target="suggest-an-edit-button">Suggest an edit')[0] for i in text.split('class="office-locations"')[1].split('class="office-location profile-subsection-bordered-container"')][1:]

    locations = []
    for i in str1:
        tempdict = dict()
        locationdict = ast.literal_eval(i.split('<script data-qa-target="markup-facility-location" type="application/ld+json">')[1].split("</script>")[0])
        location = locationdict["location"]["address"]

        tempdict["location name"] = (i.split('data-qa-target="qa-practice-link"')[1].split(">")[1].split("<")[0])
        tempdict["type"] = ("Clinic" if locationdict["@type"] == "Physician" else locationdict["@type"])
        tempdict["state"] = abbrev_to_us_state[location["addressRegion"]]
        tempdict["city"] = location["addressLocality"]
        tempdict["address"] = location["streetAddress"]
        locations.append(tempdict)
    return locations


def get_hospital_names(text):
    str1 = text.split(
        '<script data-qa-target="markup-hospital-affilitation" type="application/ld+json">')[1:]

    hospitals = []
    for i in str1:
        tempdict = dict()
        dict1 = ast.literal_eval(i.split("}}}")[0] + "}}}")

        tempdict["location name"] = dict1["hospitalAffiliation"]["name"]
        tempdict["type"] = dict1["hospitalAffiliation"]["@type"]
        tempdict["state"] = abbrev_to_us_state[dict1["hospitalAffiliation"]["address"]["addressRegion"]]
        tempdict["city"] = dict1["hospitalAffiliation"]["address"]["addressLocality"]
        tempdict["address"] = dict1["hospitalAffiliation"]["address"]["streetAddress"]
        hospitals.append(tempdict)
    return hospitals


def click_show_more(driver, url: str) -> str:
    driver.get(url)

    while True:
        try:
            show_more_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//a[@class="c-comment-list__show-more"]')))
            driver.execute_script("arguments[0].click();", show_more_button)
        except Exception as e:
            print(e)
            break
        time.sleep(2)
    return driver.page_source

abbrev_to_us_state = {
    "AL": "Alabama",
    "AK": "Alaska",
    "AZ": "Arizona",
    "AR": "Arkansas",
    "CA": "California",
    "CO": "Colorado",
    "CT": "Connecticut",
    "DE": "Delaware",
    "FL": "Florida",
    "GA": "Georgia",
    "HI": "Hawaii",
    "ID": "Idaho",
    "IL": "Illinois",
    "IN": "Indiana",
    "IA": "Iowa",
    "KS": "Kansas",
    "KY": "Kentucky",
    "LA": "Louisiana",
    "ME": "Maine",
    "MD": "Maryland",
    "MA": "Massachusetts",
    "MI": "Michigan",
    "MN": "Minnesota",
    "MS": "Mississippi",
    "MO": "Missouri",
    "MT": "Montana",
    "NE": "Nebraska",
    "NV": "Nevada",
    "NH": "New Hampshire",
    "NJ": "New Jersey",
    "NM": "New Mexico",
    "NY": "New York",
    "NC": "North Carolina",
    "ND": "North Dakota",
    "OH": "Ohio",
    "OK": "Oklahoma",
    "OR": "Oregon",
    "PA": "Pennsylvania",
    "RI": "Rhode Island",
    "SC": "South Carolina",
    "SD": "South Dakota",
    "TN": "Tennessee",
    "TX": "Texas",
    "UT": "Utah",
    "VT": "Vermont",
    "VA": "Virginia",
    "WA": "Washington",
    "WV": "West Virginia",
    "WI": "Wisconsin",
    "WY": "Wyoming",
    "DC": "District of Columbia",
    "AS": "American Samoa",
    "GU": "Guam",
    "MP": "Northern Mariana Islands",
    "PR": "Puerto Rico",
    "UM": "United States Minor Outlying Islands",
    "VI": "U.S. Virgin Islands",
}
