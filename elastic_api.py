from elasticsearch import Elasticsearch, helpers
client = Elasticsearch(
    "https://backend-cbc16a.es.us-east-1.aws.elastic.cloud:443",
    api_key="cnNscWdKUUJUYU9HemY3UTJ5aG86UXl6VGNpWmRUTXVKSXB6c1poVUNvQQ=="
)


index_name = "search-backend"

docs = [
    {
        "text": "Yellowstone National Park is known for its geothermal features, especially the Old Faithful Geyser, which erupts regularly."
    },
]

bulk_response = helpers.bulk(client, docs, index=index_name)
print(bulk_response)

# response = client.search(
#     index = index_name,
#     body = {
#         "query": {
#             "match": {
#                 "text":  "Yellowstone"
#             }
#         }

#     }
# )

# print(response['hits']['hits'])  # Print the documents found