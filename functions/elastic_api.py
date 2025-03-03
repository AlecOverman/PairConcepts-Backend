from elasticsearch import Elasticsearch, helpers
import re
from pylatexenc.latex2text import LatexNodes2Text
import spacy



# Connect to Elasticsearch
ES_URL = "https://my-elasticsearch-project-cdb29f.es.us-east-1.aws.elastic.cloud:443"
ES_API_KEY = "TWNNeEw1VUJVcEs4d3RkMDNzMlA6dldaUE5MbmlfNkxHbkcydW9Vd1g5Zw=="  

es = Elasticsearch(ES_URL, api_key=ES_API_KEY)
index_name = "arxiv_sources"
token_index = "tokens"


def get_elastic(query="Blackholes", max_results=5):

    if not es.indices.exists(index=index_name):
        es.indices.create(index=index_name)
        return {"message": "Index didn't exist but was created"}

    # Perform search query on Elasticsearch
    query_body = {
        "query": {
            "match": {
                "title": query  # Searching by paper title
            }
        },
        "size": max_results  # Limit results
    }

    try:
        response = es.search(index=index_name, body=query_body)
        hits = response['hits']['hits']
        results = [{"id": hit["_id"], "title": hit["_source"]["title"], "authors": hit["_source"]["authors"]} for hit in hits]
        return results
    except Exception as e:
        return {"error": str(e)}

def token_search():

    # Hardcoded test search params (a list of dictionaries)
    search_params = [
        {
            "id": "1312.1391v1",  # Example document ID
            "positions": [
                {"start": 10, "end": 50},  # Example character positions
                {"start": 2000, "end": 3000}
            ]
        }
    ]
    
    results = []

    for item in search_params:
        doc_id = item["id"]
        char_ranges = item["positions"]  # List of {"start": X, "end": Y}

        try:
            # Fetch the document using ID
            response = es.get(index=index_name, id=doc_id)
            latex_text = response["_source"].get("latex_source", "")

            extracted_sentences = []
            for pos in char_ranges:
                start, end = pos["start"], pos["end"]
                
                # Ensure positions are within range
                if start < 0 or end > len(latex_text):
                    continue
                
                # Extract full sentence instead of raw substring
                sentence = extract_full_sentence(latex_text, start, end)
                extracted_sentences.append(sentence)

            results.append({
                "id": doc_id,
                "extracted_sentences": extracted_sentences
            })

        except Exception as e:
            results.append({"id": doc_id, "error": str(e)})

    return results

# make a function that turns the latex into regular text
# this will allow me to tokenize the text

# By next week I want to be able to send to open ai to get text back from the given input, Ill send source summery and the sentences and see if they are related or just how the text is used

def turn_to_text():
    
    # Load spaCy model
    nlp = spacy.load("en_core_web_sm")

    # Fetch documents
    res = es.search(index=index_name, body={"query": {"match_all": {}}}, size=10000)
    docs = res["hits"]["hits"]

    print(f"Found {len(docs)} documents")

    processed_tokens = {}

    for doc in docs:
        try:
            if "_source" in doc and "latex_source" in doc["_source"]:
                doc_id = doc["_id"]
                doc_spacy = nlp(doc["_source"]["latex_source"])

                # Tokenize using spaCy
                for token in doc_spacy:
                    if not token.is_punct and token.text.strip():
                        token_text = token.text.lower()

                        # Initialize the token entry if not exists
                        if token_text not in processed_tokens:
                            processed_tokens[token_text] = []

                        # Check if this document is already stored
                        found = False
                        for entry in processed_tokens[token_text]:
                            if entry["source"] == doc_id:
                                entry["positions"].append(token.idx)
                                found = True
                                break

                        # If this document is new for this token, add a new entry
                        if not found:
                            processed_tokens[token_text].append({
                                "source": doc_id,
                                "positions": [token.idx]
                            })

        except Exception as e:
            print(f"Error processing document {doc.get('_id', 'Unknown')}: {e}")

    # Convert processed_tokens to bulk API format
    bulk_actions = []
    for token_text, sources in processed_tokens.items():
        bulk_actions.append({
            "_op_type": "index",
            "_index": token_index,
            "_id": token_text,  # Use token text as document ID to avoid duplicates
            "_source": {
                "token": token_text,
                "sources": sources  # List of documents containing this token with positions
            }
        })

    # Bulk insert into Elasticsearch
    if bulk_actions:
        success, failed = helpers.bulk(es, bulk_actions)
        print(f"Successfully indexed {success} token documents. Failed: {failed}")

def get_tokens(query="blackholes", max_results=1):

    if not es.indices.exists(index=token_index):
        return {"message": "Index didn't exist but was created"}

    # Perform search query on Elasticsearch
    query_body = {
        "query": {
            "match": {
                "token": query
            }
        },
        "size": max_results  # Limit results
    }

    try:
        response = es.search(index=token_index, body=query_body)
        hits = response['hits']['hits']
        results = [
            {
                "id": hit["_id"],
                "sources": [
                    {
                        "source": s["source"],
                        "positions": s["positions"]  # Keeps the full list of positions
                    }
                    for s in hit["_source"]["sources"]
                ],
                "token": hit["_source"].get("token", None)
            }
            for hit in hits
        ]


        return extract_full_sentence(results)
        # return results
    except Exception as e:
        return {"error": str(e)}


def extract_full_sentence(data):
    """
    Expands a substring to capture the full sentence using positions from JSON.
    Queries a specific index for the source text and metadata using the Elasticsearch client.
    Limits to 5 sentences per article.
    """
    # Define sentence-ending punctuation and sentence-starting characters
    sentence_endings = r"[.!?]"
    sentence_beginning = r"[.!?]"

    results = []  # To store the structured results

    for entry in data:
        keyword = entry["token"]
        for source in entry["sources"]:
            source_id = source["source"]
            positions = source["positions"]
        


            # Query to get both the source text and metadata using the source_id
            query_body = {
                "query": {
                    "match": {
                        "id": source_id
                    }
                }
            }

            # Send the query to Elasticsearch for a specific index
            response = es.search(index=index_name, body=query_body)

            # Check if there are hits in the response
            if response['hits']['total']['value'] > 0:
                # Get the source text from the result
                text = response['hits']['hits'][0]["_source"]["latex_source"]  # Assuming latex_source contains the full text

                # ✅ Initialize `article_data` here, so it resets for each source
                article_data = {
                    "sentences": [],  # List to store full sentences for this article
                    "published": response['hits']['hits'][0]["_source"].get("published", "N/A"),
                    "source_url": response['hits']['hits'][0]["_source"].get("source_url", "N/A"),
                    "summery": response['hits']['hits'][0]["_source"].get("summery", "N/A"),
                    "title": response['hits']['hits'][0]["_source"].get("title", "N/A"),
                    "authors": response['hits']['hits'][0]["_source"].get("authors", []),
                    "keyword": keyword
                }

                sentence_count = 0  # Counter for sentences

                for position in positions:
                    if sentence_count >= 5:  # Limit to 5 sentences
                        break

                    start = position  # Start position from the JSON
                    end = position  # Default end position is the same as start

                    # Expand start position to the beginning of the sentence
                    while start > 0 and not re.match(sentence_beginning, text[start - 1]):
                        start -= 1

                    # Expand end position to the end of the sentence
                    while end < len(text) and not re.match(sentence_endings, text[end]):
                        end += 1

                    # Capture the full sentence and strip unnecessary spaces
                    sentence = text[start:end].strip()
                    article_data["sentences"].append(sentence)
                    sentence_count += 1

                # ✅ Only append if sentences were found
                if article_data["sentences"]:
                    results.append(article_data)
            else:
                print(f"No results found for source: {source_id}")

    return results[1]
