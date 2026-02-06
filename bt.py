import streamlit as st
from Bio import Entrez
import xml.etree.ElementTree as ET
from datetime import datetime
import requests
import feedparser

# Set your email address for Entrez
Entrez.email = "<email>"

def format_date(raw_date):
    """
    Formats a date string into DD-MM-YYYY format.
    """
    try:
        formatted_date = datetime.strptime(raw_date, "%Y%b%d").strftime("%d-%m-%Y")
        return formatted_date
    except ValueError:
        return "N/A"

def fetch_from_pubmed(keyword, max_results=10):
    """
    Fetches articles from PubMed based on the provided keyword.
    """
    search_results = Entrez.esearch(
        db="pubmed", term=[keyword.lower()], retmax=max_results, usehistory="y"
    )
    record = Entrez.read(search_results)

    id_list = record["IdList"]
    if not id_list:
        return []

    handle = Entrez.efetch(db="pubmed", id=",".join(id_list), rettype="xml", retmode="text")
    records = handle.read()
    handle.close()

    root = ET.fromstring(records)
    articles = []
    for article in root.findall(".//PubmedArticle"):
        title = article.find(".//ArticleTitle")
        title_text = ET.tostring(title, encoding="unicode", method="text").strip() if title is not None else "N/A"

        abstract_sections = article.findall(".//AbstractText")
        abstract_text = " ".join(ET.tostring(section, encoding="unicode", method="text").strip() for section in abstract_sections) if abstract_sections else "Abstract not available"

        date_elements = article.find(".//PubDate")
        raw_date = ET.tostring(date_elements, encoding="unicode", method="text").strip() if date_elements is not None else "N/A"
        formatted_date = format_date(raw_date)

        doi = article.find(".//ELocationID[@EIdType='doi']")
        doi_text = doi.text.strip() if doi is not None else "N/A"
        doi_url = f"https://doi.org/{doi_text}" if doi_text != "N/A" else "N/A"

        articles.append({
            "Title": title_text,
            "Abstract": abstract_text,
            "PubDate": formatted_date,
            "DOI": doi_text,
            "DOI_URL": doi_url,
        })
    return articles

def fetch_from_arxiv(keyword, max_results=10):
    """
    Fetches articles from arXiv based on the provided keyword.
    """
    base_url = "http://export.arxiv.org/api/query"
    params = {
        "search_query": f"all:{keyword.lower()}",
        "start": 0,
        "max_results": max_results,
        "sortBy": "relevance",
    }
    response = requests.get(base_url, params=params)
    if response.status_code != 200:
        return []

    feed = feedparser.parse(response.text)
    articles = []
    for entry in feed.entries:
        title = entry.get("title", "N/A").strip()
        abstract = entry.get("summary", "Abstract not available").strip()
        pub_date = datetime.strptime(entry.get("published", "N/A")[:10], "%Y-%m-%d").strftime("%d-%m-%Y") if entry.get("published") else "N/A"
        doi_url = entry.get("id", "N/A")

        articles.append({
            "Title": title,
            "Abstract": abstract,
            "PubDate": pub_date,
            "DOI": "N/A",
            "DOI_URL": doi_url,
        })
    return articles

def main():
    st.title("Multi-Source Article Fetcher")
    st.write("Search for research articles from multiple sources, including PubMed and arXiv.")

    source = st.selectbox("Select the source to fetch articles from:", ["PubMed", "arXiv"])
    keyword = st.text_input("Enter a keyword to search for research papers:")

    if keyword:
        st.write(f"Searching for articles with the keyword: '{keyword}' in {source}...")

        if source == "PubMed":
            results = fetch_from_pubmed(keyword)
        elif source == "arXiv":
            results = fetch_from_arxiv(keyword)

        if not results:
            st.write(f"No articles found for keyword: '{keyword}' in {source}.")
            return

        st.subheader("Articles Found:")
        for idx, article in enumerate(results, start=1):
            st.write(f"### Article {idx}")
            st.write(f"**Title**: {article['Title']}")
            st.write(f"**Abstract**: {article['Abstract']}")
            st.write(f"**Publication Date**: {article['PubDate']}")
            st.write(f"**DOI URL**: [Link]({article['DOI_URL']})" if article['DOI_URL'] != "N/A" else "DOI: N/A")
            st.write("-" * 50)

if __name__ == "__main__":
    main()
