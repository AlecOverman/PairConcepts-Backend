from elasticsearch import Elasticsearch, helpers
import re
from pylatexenc.latex2text import LatexNodes2Text
import spacy


def get_elastic(query="Blackholes", max_results=5):
    ES_URL = "https://my-elasticsearch-project-cdb29f.es.us-east-1.aws.elastic.cloud:443"
    ES_API_KEY = "https://my-elasticsearch-project-cdb29f.es.us-east-1.aws.elastic.cloud:443"  

    es = Elasticsearch(ES_URL, api_key=ES_API_KEY)
    index_name = "arxiv_sources"

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


def extract_full_sentence(text, start, end):
    """
    Expands a substring to capture the full sentence.
    """
    # Define sentence-ending punctuation
    sentence_endings = r"[.!?]"
    
    # Expand start position to the beginning of the sentence
    while start > 0 and not re.match(sentence_endings, text[start - 1]):
        start -= 1

    # Expand end position to the end of the sentence
    while end < len(text) and not re.match(sentence_endings, text[end - 1]):
        end += 1

    # Ensure we capture the full sentence
    return text[start:end].strip()


def token_search():
    ES_URL = "https://my-elasticsearch-project-cdb29f.es.us-east-1.aws.elastic.cloud:443"
    ES_API_KEY = "https://my-elasticsearch-project-cdb29f.es.us-east-1.aws.elastic.cloud:443"    
    index_name = "arxiv_sources"

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
    
    es = Elasticsearch(ES_URL, api_key=ES_API_KEY)
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
    # Connect to Elasticsearch
    ES_URL = "https://my-elasticsearch-project-cdb29f.es.us-east-1.aws.elastic.cloud:443"
    ES_API_KEY = "https://my-elasticsearch-project-cdb29f.es.us-east-1.aws.elastic.cloud:443"  

    es = Elasticsearch(ES_URL, api_key=ES_API_KEY)
    index_name = "arxiv_sources"
    token_index = "tokens"
    
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



def latex_to_text():
    # Connect to Elasticsearch
    ES_URL = "https://my-elasticsearch-project-cdb29f.es.us-east-1.aws.elastic.cloud:443"
    ES_API_KEY = "https://my-elasticsearch-project-cdb29f.es.us-east-1.aws.elastic.cloud:443"  

    es = Elasticsearch(ES_URL, api_key=ES_API_KEY)
    index_name = "arxiv_sources"

    # Fetch documents
    res = es.search(index=index_name, body={"query": {"match_all": {}}}, size=1000)  # Fetch up to 1000 documents
    docs = res["hits"]["hits"]

    actions = []
    for doc in docs:
        try:
            if "_source" in doc and "latex_source" in doc["_source"]:
                # Convert LaTeX to plain text
                plain_text = LatexNodes2Text().latex_to_text(doc["_source"]["latex_source"])
                
                # Prepare bulk update action
                actions.append({
                    "_op_type": "update",
                    "_index": index_name,
                    "_id": doc["_id"],
                    "doc": {"latex_source": plain_text}
                })
        except Exception as e:
            print(f"Error processing document {doc['_id']}: {e}")

    # Perform bulk update
    if actions:
        success, failed = helpers.bulk(es, actions)
        print(f"Successfully updated {success} documents. Failed: {failed}")

# You have the tokens and you have the full text and meta data. Now first extract the tokens use their source to go to the source and 

