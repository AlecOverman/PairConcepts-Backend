import requests
import feedparser
import random
import time
import tarfile
import io
from elasticsearch import Elasticsearch, helpers

ES_URL = "https://da507f8d778a45289ccac8d865cfa1ff.us-east-2.aws.elastic-cloud.com:443"
ES_API_KEY = "RS1NdGpaVUJESFRfaUVHMHNiN3Q6U3JxbF9uLXlTbGlwQ2d2MEQ2MV9EQQ=="  

es = Elasticsearch(ES_URL, api_key=ES_API_KEY)
index_name = "arxiv_sources"
token_index = "tokens"

# Define a list of User-Agent strings
user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
    "Mozilla/5.0 (Linux; Android 9; SM-J260F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.77 Mobile Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:42.0) Gecko/20100101 Firefox/42.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36 Edge/74.0.2"
]

def fetch_arxiv_papers(query="CS", max_results=5, base_url="http://export.arxiv.org/api/query?"):
    """Fetches papers from arXiv API with source links."""
    search_query = f"search_query=all:{query}&max_results={max_results}"
    url = base_url + search_query

    response = requests.get(url)
    
    if response.status_code != 200:
        return {"error": f"Failed to fetch papers (Status {response.status_code})"}

    feed = feedparser.parse(response.text)
    papers = []

    for entry in feed.entries:
        paper_id = entry.id.split("/")[-1]
        paper = {
            "id": paper_id,
            "title": entry.title,
            "authors": ", ".join(author.name for author in entry.authors),
            "summary": entry.summary,
            "published": entry.published,
            "category": entry.tags[0]["term"] if entry.tags else "Unknown",
            "arxiv_url": entry.link,
            "source_url": f"https://arxiv.org/e-print/{paper_id}"
        }
        papers.append(paper)

    return stream_and_index_latex_source(papers)

def stream_and_index_latex_source(papers):
    """Downloads, extracts, and indexes LaTeX source from arXiv along with metadata for a list of papers."""
    all_docs = []  # List to store the final documents

    for paper in papers:
        # Adding a 1-second delay to be polite to the server
        time.sleep(1)

        paper_id = paper["id"]
        source_url = f"https://arxiv.org/e-print/{paper_id}"

        # Randomly select a User-Agent for each request
        headers = {
            "User-Agent": random.choice(user_agents)
        }

        # Request with headers
        response = requests.get(source_url, headers=headers, stream=True)

        if response.status_code == 200:
            try:
                content_type = response.headers.get("Content-Type", "")
                if "application/x-tar" not in content_type and "application/gzip" not in content_type:
                    print(f"⚠️ No LaTeX source available for {paper_id} (Received non-tar file)")
                    continue  # Skip to the next paper

                tar_file = tarfile.open(fileobj=io.BytesIO(response.content), mode="r:gz")
                latex_content = ""

                for member in tar_file.getmembers():
                    if member.isfile() and member.name.endswith(".tex"):
                        latex_file = tar_file.extractfile(member)
                        if latex_file:
                            latex_content += latex_file.read().decode("utf-8") + "\n\n"

                if latex_content:
                    doc = {
                        "id": paper_id,
                        "title": paper["title"],
                        "authors": paper["authors"],
                        "summary": paper["summary"],
                        "published": paper["published"],
                        "category": paper["category"],
                        "arxiv_url": paper["arxiv_url"],
                        "source_url": paper["source_url"],
                        "latex_source": latex_content,
                    }
                    all_docs.append(doc)
                    # ✅ Index the combined document into Elasticsearch
                    # es.index(index="arxiv_sources", id=paper_id, document=doc)
                    # print(f"✅ Indexed LaTeX source and metadata for {paper_id}")
                else:
                    print(f"⚠️ No LaTeX content found for {paper_id}")

            except Exception as e:
                print(f"❌ Error extracting LaTeX for {paper_id}: {e}")

        else:
            print(f"❌ Failed to download source for {paper_id} (Status {response.status_code})")

        # ✅ Bulk insert into Elasticsearch
    if all_docs:
        success, failed = helpers.bulk(es, [
            {
                "_op_type": "index",
                "_index": index_name,
                "_id": doc["id"],
                "_source": doc
            } for doc in all_docs
        ])
        print(f"✅ Successfully indexed {success} documents. Failed: {failed}")
    else:
        print("⚠️ No documents to index.")

    return all_docs
