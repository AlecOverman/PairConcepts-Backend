import requests
import feedparser

def fetch_arxiv_papers(query="Blackholes", max_results=5):
    """Fetches papers from arXiv API with source links."""
    base_url = "http://export.arxiv.org/api/query?"
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
        paper_id = paper["id"]
        source_url = f"https://arxiv.org/e-print/{paper_id}"
        response = requests.get(source_url, stream=True)

        # print(f"\n🔍 Debugging {paper_id} download:")
        # print(f"➡️ Status Code: {response.status_code}")
        # print(f"➡️ Content Type: {response.headers.get('Content-Type', 'Unknown')}")
        # print(f"➡️ First 500 bytes of content:\n{response.content[:500]}")

        if response.status_code == 200:
            try:
                # ✅ Check if response is a valid tar.gz file
                content_type = response.headers.get("Content-Type", "")
                if "application/x-tar" not in content_type and "application/gzip" not in content_type:
                    print(f"⚠️ No LaTeX source available for {paper_id} (Received non-tar file)")
                    continue  # Skip to the next paper

                # ✅ Read tar.gz file into memory
                tar_file = tarfile.open(fileobj=io.BytesIO(response.content), mode="r:gz")

                latex_content = ""

                # ✅ Extract only .tex files in memory
                for member in tar_file.getmembers():
                    if member.isfile() and member.name.endswith(".tex"):  # Only LaTeX files
                        latex_file = tar_file.extractfile(member)
                        if latex_file:
                            latex_content += latex_file.read().decode("utf-8") + "\n\n"

                if latex_content:
                    # ✅ Combine metadata with LaTeX content
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

    return all_docs
