

def get_elastic():
        # ✅ Load Elasticsearch credentials from environment variables
        ES_URL = os.getenv("http_elastic")  # Set this in Render
        ES_API_KEY = os.getenv("key_elastic")  # Set this in Render

        # ✅ Initialize Elasticsearch client securely
        es = Elasticsearch(ES_URL, api_key=ES_API_KEY)

        index_name = "arxiv_sources"

        # Ensure index exists before inserting documents
        if not es.indices.exists(index=index_name):
            es.indices.create(index=index_name)
        else: print("Hello Word")