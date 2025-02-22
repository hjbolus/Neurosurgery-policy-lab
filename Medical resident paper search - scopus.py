import pandas as pd
import requests
import time
from datetime import datetime
from dateutil.relativedelta import relativedelta
import numpy as np
from statistics import mean
import ast


# ------------------------ Parameters ------------------------------------------------------------------------------------------------
# Enter your API keys here
apiKeys = [
            "...", 
            "...", 
            "..."
]

# Put the name of the excel file and sheet containing resident names and scopus IDs here.
# Either save this .py file to the same folder as your excel file, or enter the entire file path as the name.
# For example:     data_file = '/Users/harrisbolus/Desktop/Research/H-index project/residents.xlsx'
# Make sure resident names are in column 1 and scopus IDs are in column 2.
file_list = [
            ["... .xlsx", "..."], 
            ["... .xlsx", "..."]
]

# Do you want a subject-specific breakdown? If so, change subject_specific to True and provide a name: term list pair
# ex: term_list = {'subject1': {'term1', 'term2'}, 'subject2': {'term3', 'term4'}}
subject_specific = False
term_list = {}

# Do you want to backdate citation indices? If no, set to 0.
pgy = 1

# What date in the year should the backdating use as a cutoff?
latest_cycle = datetime.strptime("2023-07-01", "%Y-%m-%d")

# -------------------------------------------------------------------------------------------------------------------------------------


def api_keys_test():
    global apiKeys
    global apiKey
    time.sleep(0.01)
    headers = {"Accept": "application/json", "X-ELS-APIKey": apiKey}
    base_url = f'https://api.elsevier.com/content/abstract/doi/{"10.1227/ons.0000000000000809"}'
    response = requests.get(base_url, headers=headers)
    if response.status_code != 200:
        apiKey = apiKeys.pop(0)
        api_keys_test()

    elif (
        "X-RateLimit-Remaining" in response.headers
        and response.headers["X-RateLimit-Remaining"] == 0
    ):
        apiKey = apiKeys.pop(0)
        api_keys_test()
    print(
        "your first working api key is ",
        apiKey,
        f' and it has {response.headers["X-RateLimit-Remaining"]} queries remaining',
    )


def scopus_search_author_id(author_id, start=0):
    global apiKey
    time.sleep(0.01)

    # each paper should be a dict with the following keys: {'abs_uri', 'paper_title', 'journal_name', 'date', 'senior_author', 'senior_author_uri'}
    params = {"start": str(start)}
    headers = {"Accept": "application/json", "X-ELS-APIKey": apiKey}
    base_url = f"http://api.elsevier.com/content/search/scopus?query=au-id%28{author_id}%29&view=COMPLETE"
    response = requests.get(base_url, headers=headers, params=params)
    # print(response.headers)
    if (
        "X-RateLimit-Remaining" in response.headers
        and response.headers["X-RateLimit-Remaining"] == 0
    ):
        apiKey = apiKeys.pop(0)

    if response.status_code == 200:
        data = response.json()["search-results"]

        paper_list = []
        for i in data["entry"]:
            tempdict = {
                "doi": i["prism:doi"] if "prism:doi" in i.keys() else None,
                "paper_title": i["dc:title"],
                "journal_name": i["prism:publicationName"],
                "date": datetime.strptime(i["prism:coverDate"], "%Y-%m-%d"),
                "senior_author": i["author"][-1]["given-name"]
                + " "
                + i["author"][-1]["surname"]
                if i["author"][-1]["given-name"]
                else i["author"][-1]["surname"],
                "senior_author_uri": i["author"][-1]["author-url"],
                "citations": int(i["citedby-count"]),
                "type": i["subtypeDescription"],
            }
            if "pubmed-id" in i.keys():
                tempdict["pubmed id"] = i["pubmed-id"]
            paper_list.append(tempdict)

        total_pubs = int(data["opensearch:totalResults"])
        next_start = int(data["opensearch:startIndex"]) + int(
            data["opensearch:itemsPerPage"]
        )
        return (paper_list, total_pubs, next_start)
    else:
        print(response.status_code, "\n", response.text)


def author_retrieval_from_scopus_id(scopus_id):
    global apiKey
    time.sleep(0.01)
    uri = f"https://api.elsevier.com/content/author/author_id/{scopus_id}?view=ENHANCED"
    headers = {"Accept": "application/json", "X-ELS-APIKey": apiKey}
    response = requests.get(uri, headers=headers)

    if (
        "X-RateLimit-Remaining" in response.headers
        and response.headers["X-RateLimit-Remaining"] == 0
    ):
        apiKey = apiKeys.pop(0)

    if response.status_code == 200:
        data = response.json()["author-retrieval-response"][0]
        h_index = data["h-index"]
        return int(h_index)
    else:
        print(response.status_code, "\n", response.text)


def abstract_retrieval_from_doi(doi):
    global apiKey
    time.sleep(0.01)
    headers = {"Accept": "application/json", "X-ELS-APIKey": apiKey}
    base_url = f"https://api.elsevier.com/content/abstract/doi/{doi}"
    response = requests.get(base_url, headers=headers)

    if (
        "X-RateLimit-Remaining" in response.headers
        and response.headers["X-RateLimit-Remaining"] == 0
    ):
        apiKey = apiKeys.pop(0)

    if response.status_code == 200:
        dict1 = dict()
        data = response.json()["abstracts-retrieval-response"]
        dict1["subjects"] = ", ".join(
            [i["$"] for i in data["subject-areas"]["subject-area"]]
        )
        if "prism:issn" in data["coredata"].keys():
            dict1["issn"] = data["coredata"]["prism:issn"]
        else:
            dict1["issn"] = None

        first = None
        second = None

        if data["authors"]:
            authors = data["authors"]["author"]
            first = (
                authors[0]["ce:given-name"] + " " + authors[0]["ce:surname"]
                if "ce:given-name" in authors[0].keys()
                and "ce_surname" in authors[0].keys()
                else authors[0]["ce:indexed-name"]
            )
            if len(authors) > 1:
                second = (
                    authors[1]["ce:given-name"] + " " + authors[1]["ce:surname"]
                    if "ce:given-name" in authors[0].keys()
                    and "ce_surname" in authors[1].keys()
                    else authors[1]["ce:indexed-name"]
                )
        dict1["first"] = first
        dict1["second"] = second
        return dict1
    else:
        print(response.status_code, "\n", response.text)


def citation_metrics_from_issn(issn):
    global apiKey
    time.sleep(0.01)
    uri = f"https://api.elsevier.com/content/serial/title?issn={issn}"
    headers = {"Accept": "application/json", "X-ELS-APIKey": apiKey}
    response = requests.get(uri, headers=headers)

    if (
        "X-RateLimit-Remaining" in response.headers
        and response.headers["X-RateLimit-Remaining"] == 0
    ):
        apiKey = apiKeys.pop(0)

    if response.status_code == 200:
        data = ast.literal_eval(
            response.text.replace("false", "False")
            .replace("true", "True")
            .replace("null", "None")
        )
        if "entry" in data["serial-metadata-response"].keys():
            if "SNIPList" in data["serial-metadata-response"]["entry"][0].keys():
                snip = data["serial-metadata-response"]["entry"][0]["SNIPList"]["SNIP"][
                    -1
                ]["$"]
                snipyear = data["serial-metadata-response"]["entry"][0]["SNIPList"][
                    "SNIP"
                ][-1]["@year"]
            else:
                snip = None
                snipyear = None
            if "SJRList" in data["serial-metadata-response"]["entry"][0].keys():
                sjr = data["serial-metadata-response"]["entry"][0]["SJRList"]["SJR"][
                    -1
                ]["$"]
                sjryear = data["serial-metadata-response"]["entry"][0]["SJRList"][
                    "SJR"
                ][-1]["@year"]
            else:
                sjr = None
                sjryear = None
            if (
                "citeScoreYearInfoList"
                in data["serial-metadata-response"]["entry"][0].keys()
            ):
                citescore = data["serial-metadata-response"]["entry"][0][
                    "citeScoreYearInfoList"
                ]["citeScoreCurrentMetric"]
                citescoreyear = data["serial-metadata-response"]["entry"][0][
                    "citeScoreYearInfoList"
                ]["citeScoreCurrentMetricYear"]
            else:
                citescore = None
                citescoreyear = None
        else:
            snip = None
            snipyear = None
            sjr = None
            sjryear = None
            citescore = None
            citescoreyear = None
        return {
            "snip": snip,
            "snip year": snipyear,
            "sjr": sjr,
            "sjr year": sjryear,
            "citescore": citescore,
            "citescore year": citescoreyear,
        }
    else:
        print(response.status_code, "\n", response.text)


def author_retrieval_from_uri(uri):
    global apiKey
    time.sleep(0.01)
    uri = uri + "?view=ENHANCED"
    headers = {"Accept": "application/json", "X-ELS-APIKey": apiKey}
    response = requests.get(uri, headers=headers)

    if (
        "X-RateLimit-Remaining" in response.headers
        and response.headers["X-RateLimit-Remaining"] == 0
    ):
        apiKey = apiKeys.pop(0)

    if response.status_code == 200:
        data = response.json()["author-retrieval-response"][0]
        h_index = data["h-index"]
        try:
            if (
                type(data["author-profile"]["affiliation-current"]["affiliation"])
                == list
            ):
                affil = "; ".join(
                    [
                        i["ip-doc"]["afdispname"]
                        for i in data["author-profile"]["affiliation-current"][
                            "affiliation"
                        ]
                    ]
                )
            else:
                affil = data["author-profile"]["affiliation-current"]["affiliation"][
                    "ip-doc"
                ]["afdispname"]
        except KeyError:
            affil = None
        return (affil, int(h_index))
    else:
        print(response.status_code, "\n", response.text)


def find_backdated_h_index_from_papers(paper_list, pgy):  # consider adding number of pubs in this period
    interview_end_date = latest_cycle - relativedelta(years=pgy)

    pre_residency_citation_list = [
        paper["citations"] for paper in paper_list if paper["date"] < interview_end_date
    ]
    if pre_residency_citation_list:
        pre_residency_citations = sum(pre_residency_citation_list)
        citations = np.array(pre_residency_citation_list)
        n = citations.shape[0]
        array = np.arange(1, n + 1)
        citations = np.sort(citations)[::-1]
        pre_residency_h_index = np.max(np.minimum(citations, array))
    else:
        (pre_residency_h_index, pre_residency_citations) = (0, 0)

    return (pre_residency_h_index, pre_residency_citations)


def subject_test(paper):
    journalname = paper["journal_name"].lower()
    title = paper["paper_title"].lower()
    subjects = [i.lower() for i in paper["subjects"]]

    for term in term_list:
        if term in journalname:
            return True
        if term in title:
            return True
        for item in subjects:
            if term in item:
                return True
    return False


# --------------------------
if __name__ == "__main__":
    startTime = datetime.now()
    
    apiKey = apiKeys.pop(0)
    api_keys_test()
    for i in file_list:
        print("\n\n\n", i[0])
        data_file = i[0]
        data_sheet = i[1]
        output_file_name = (
            data_file.split("/")[-1].split(".")[0].split("_")[0] + " scopus data.xlsx"
        )
    
        df = pd.read_excel(data_file, sheet_name=data_sheet)
        resident_list = [
            {"resident name": resident[0], "scopus id": str(int(resident[1]))}
            for resident in df.values
            if len(str(resident[1])) > 10
        ]
    
        if subject_specific:
            subjects = list(term_list.keys())
    
        journals = {}
        data_list = []
        summary_list = []
        for resident in resident_list:
            print(resident["resident name"], resident["scopus id"])
            resident["resident current h index"] = author_retrieval_from_scopus_id(
                resident["scopus id"]
            )
            (paper_list, resident["total_pubs"], next_start) = scopus_search_author_id(
                resident["scopus id"]
            )
    
            while next_start < resident["total_pubs"]:
                (new_papers, resident["total_pubs"], next_start) = scopus_search_author_id(
                    resident["scopus id"], next_start
                )
                paper_list = paper_list + new_papers
    
            for paper in paper_list:
                if paper["doi"]:
                    paper.update(abstract_retrieval_from_doi(paper["doi"]))
                    if paper["issn"]:
                        if paper["issn"] in journals.keys():
                            paper.update(journals[paper["issn"]])
                        else:
                            citation_metrics = citation_metrics_from_issn(paper["issn"])
                            paper.update(citation_metrics)
                            journals[paper["issn"]] = citation_metrics
    
                (
                    paper["sr_author_affil"],
                    paper["sr_author_h_index"],
                ) = author_retrieval_from_uri(paper["senior_author_uri"])
    
                if subject_specific:
                    for subject in subjects:
                        paper[subject] = subject_test(paper)
    
                paper.update(resident)
    
                data_list.append(paper)
    
            resident["i-10 index"] = len(
                [paper for paper in paper_list if paper["citations"] >= 10]
            )
    
            sr_author_h_indices = [paper["sr_author_h_index"] for paper in paper_list]
            unique_sr_author_h_indices = [
                j[1]
                for j in set(
                    [(i["senior_author_uri"], i["sr_author_h_index"]) for i in paper_list]
                )
            ]
            resident["total citations"] = sum([paper["citations"] for paper in paper_list])
            if pgy:
                (
                    resident["pre_residency_h_index"],
                    resident["pre_residency_citations"],
                ) = find_backdated_h_index_from_papers(paper_list, pgy)
            resident["max_h_index"] = max(sr_author_h_indices)
            resident["weighted_avg_h_index"] = mean(sr_author_h_indices)
            resident["avg_h_index"] = mean(unique_sr_author_h_indices)
    
            if subject_specific:
                for subject in subjects:
                    subject_paper_list = [paper for paper in paper_list if paper[subject]]
                    subject_sr_author_h_indices = [
                        paper["sr_author_h_index"] for paper in subject_paper_list
                    ]
                    unique_subject_sr_author_h_indices = [
                        j[1]
                        for j in set(
                            [
                                (i["senior_author_uri"], i["sr_author_h_index"])
                                for i in paper_list
                            ]
                        )
                    ]
                    resident[f"total {subject} citations"] = sum(
                        [paper["citations"] for paper in subject_paper_list]
                    )
                    (
                        resident[f"{subject}_pre_residency_h_index"],
                        resident[f"{subject} pre residency citations"],
                    ) = find_backdated_h_index_from_papers(subject_paper_list, pgy)
                    resident[f"{subject}_max_h_index"] = max(subject_sr_author_h_indices)
                    resident[f"{subject}_weighted_avg_h_index"] = mean(
                        subject_sr_author_h_indices
                    )
                    resident[f"{subject}_avg_h_index"] = mean(
                        unique_subject_sr_author_h_indices
                    )
    
            summary_list.append(resident)
    
        resident_names = set([resident[0] for resident in df.values])
        attempted_names = set([i["resident name"] for i in resident_list])
        succeeded_names = set([i["resident name"] for i in summary_list])
    
        invalid_entries = resident_names - attempted_names
        failed_entries = attempted_names - succeeded_names
    
        with pd.ExcelWriter(output_file_name) as writer:
            pd.DataFrame(data_list).to_excel(writer, sheet_name="data")
            pd.DataFrame(summary_list).to_excel(writer, sheet_name="summary statistics")
    
            if invalid_entries:
                pd.merge(
                    pd.DataFrame(invalid_entries),
                    df,
                    how="left",
                    left_on=0,
                    right_on="Name",
                ).to_excel(writer, sheet_name="invalid")
            if failed_entries:
                pd.merge(
                    pd.DataFrame(failed_entries), df, how="left", left_on=0, right_on="Name"
                ).to_excel(writer, sheet_name="failed")
    
        print(datetime.now() - startTime)
