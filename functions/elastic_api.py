from elasticsearch import Elasticsearch

position_list = [10,20,30,40]

def get_elastic(query="Blackholes", max_results=5):
    ES_URL = "https://my-elasticsearch-project-bd33e8.es.us-east-1.aws.elastic.cloud:443"
    ES_API_KEY = "Q2tic0M1VUItTF9NN0J0cjhuaW86TE5lYjBOUEZlQTBSWHdaZk1xeEVzdw=="  

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

def token_search(source, keyPhrase, charPosition):
    for pos in charPosition

