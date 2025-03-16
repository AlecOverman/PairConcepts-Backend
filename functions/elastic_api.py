
import spacy
from elasticsearch import Elasticsearch, helpers
from .arxiv import fetch_arxiv_papers
import re
from pylatexenc.latex2text import LatexNodes2Text





# Connect to Elasticsearch
ES_URL = "https://da507f8d778a45289ccac8d865cfa1ff.us-east-2.aws.elastic-cloud.com:443"
ES_API_KEY = "RS1NdGpaVUJESFRfaUVHMHNiN3Q6U3JxbF9uLXlTbGlwQ2d2MEQ2MV9EQQ=="  

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

def turn_to_text():
    # Load spaCy model
    nlp = spacy.load("en_core_web_sm")

    # Fetch documents
    res = es.search(index=index_name, body={"query": {"match_all": {}}}, size=1000)
    docs = res["hits"]["hits"]

    print(f"Found {len(docs)} documents")

    bulk_actions_tokens = {}

    for doc in docs:
        try:
            doc_id = doc["_id"]

            # **Ensure that only documents in idd_list are processed**

            if "_source" in doc and "latex_source" in doc["_source"]:
                doc_spacy = nlp(doc["_source"]["latex_source"])

                # Tokenize using spaCy
                for token in doc_spacy:
                    if not token.is_punct and token.text.strip():
                        token_text = token.text.lower()

                        # Initialize the token entry if not exists
                        if token_text not in bulk_actions_tokens:
                            bulk_actions_tokens[token_text] = []

                        # Check if this document is already stored
                        found = False
                        for entry in bulk_actions_tokens[token_text]:
                            if entry["source"] == doc_id:
                                entry["positions"].append(token.idx)
                                found = True
                                break

                        # If this document is new for this token, add a new entry
                        if not found:
                            bulk_actions_tokens[token_text].append({
                                "source": doc_id,
                                "positions": [token.idx]
                            })

        except Exception as e:
            print(f"Error processing document {doc.get('_id', 'Unknown')}: {e}")

    # Convert bulk_actions_tokens to bulk API format
    bulk_actions = []
    for token_text, sources in bulk_actions_tokens.items():
        # Query Elasticsearch to check if the token already exists
        search_query = {
            "query": {
                "match": {  # Use term query for exact match
                    "token": token_text
                }
            }
        }
        res = es.search(index=token_index, body=search_query, size=1)
        
        # If the token exists in Elasticsearch (based on the search result)
        if res['hits']['total']['value'] > 0:
            print(f"Token '{token_text}' already exists in Elasticsearch.")
            
            # If the token exists, check if any new positions should be added
            for source in sources:
                print(f"Processing source '{source['source']}' for token '{token_text}'.")

                # Check if the source already exists in the 'sources' field for this token
                source_exists = False
                for existing_source in res['hits']['hits'][0]['_source'].get('sources', []):
                    if existing_source["source"] == source["source"]:
                        # If the source exists, we skip adding new positions
                        print(f"Source '{source['source']}' already exists for token '{token_text}'. Skipping new positions.")
                        source_exists = True
                        break

                if not source_exists:
                    # If source doesn't exist, then add it with new positions
                    print(f"Source '{source['source']}' does not exist for token '{token_text}'. Adding new positions.")
                    bulk_actions.append({
                        "_op_type": "update",
                        "_index": token_index,
                        "_id": token_text,
                        "script": {
                            "source": """
                                if (ctx._source.sources == null) {
                                    ctx._source.sources = params.sources;
                                } else {
                                    ctx._source.sources.add(params.source);
                                }
                            """,
                            "params": {
                                "source": source
                            }
                        }
                    })
        else:
            # If the token does not exist, index it as a new document
            print(f"Token '{token_text}' does not exist in Elasticsearch. Adding as new token.")
            bulk_actions.append({
                "_op_type": "index",
                "_index": token_index,
                "_id": token_text,
                "_source": {
                    "token": token_text,
                    "sources": sources  # List of papers containing this token with positions
                }
            })

    # Bulk insert or update into Elasticsearch
    # if bulk_actions:
    #     success, failed = helpers.bulk(es, bulk_actions)
    #     print(f"Successfully indexed {success} token documents. Failed: {failed}")
    return bulk_actions



def is_latex(content):
    """Check if the given content is a LaTeX document."""
    return isinstance(content, str) and ("\\documentclass" in content or "\\begin{document}" in content)

def latex_to_text():
    test = []
    # Fetch documents
    res = es.search(index=index_name, body={"query": {"match_all": {}}}, size=1000)  
    docs = res["hits"]["hits"]

    actions = []
    id_list = []
    for doc in docs:
        try:
            if "_source" in doc and "latex_source" in doc["_source"]:
                latex_content = doc["_source"]["latex_source"]

                # Check if content is LaTeX
                if is_latex(latex_content):
                    print("Valid LaTeX document detected.")

                    # Convert LaTeX to plain text
                    plain_text = LatexNodes2Text().latex_to_text(latex_content)
                    
                    # Prepare bulk update action
                    actions.append({
                        "_op_type": "update",
                        "_index": index_name,
                        "_id": doc["_id"],
                        "doc": {"latex_source": plain_text}
                    })
                    id_list.append(doc["_id"])
                else:
                    print(f"Skipping non-LaTeX document: {doc['_id']}")

        except Exception as e:
            print(f"Error processing document {doc['_id']}: {e}")
        # Perform bulk update
    if actions:
        success, failed = helpers.bulk(es, actions)
        print(f"Successfully updated {success} documents. Failed: {failed}")
        test = turn_to_text(id_list)

    return id_list



def check_duplicate_ids():
    """Checks for duplicate document IDs in the Elasticsearch index."""
    
    try:
        # Get all document IDs from Elasticsearch
        res = es.search(index=index_name, body={"query": {"match_all": {}}}, size=1000)  # Adjust size if needed
        docs = res["hits"]["hits"]

        id_counts = {}
        duplicates = []

        for doc in docs:
            doc_id = doc["_id"]
            if doc_id in id_counts:
                id_counts[doc_id] += 1
                duplicates.append(doc_id)  # Track duplicate ID
            else:
                id_counts[doc_id] = 1

        if duplicates:
            return {"duplicates": list(set(duplicates)), "count": len(duplicates)}
        else:
            return {"message": "No duplicate IDs found."}

    except Exception as e:
        return {"error": str(e)}
