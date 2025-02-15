import pytesseract
from PIL import Image
import pdf2image
import os
import spacy
import pandas as pd
import json
from elasticsearch import Elasticsearch, helpers


# # Convert PDF to images (one per page)
def pdf_to_images(pdf_path):
    # Convert the entire PDF to images (one per page)
    return pdf2image.convert_from_path(pdf_path)

# # Perform OCR on each page image
def ocr_on_pdf(pdf_path):
    # Convert the PDF pages to images
    pages = pdf_to_images(pdf_path)
    text = ""
    for page in pages:
        # Extract text from each page image
        text += pytesseract.image_to_string(page)
    return text

# # Process a specific PDF file from the project directory
def process_pdf(pdf_filename):
    # Make sure the file exists in the current project directory
    pdf_path = os.path.join(os.getcwd(), pdf_filename)
    if os.path.exists(pdf_path):
        text = ocr_on_pdf(pdf_path)
        return process_and_send_tokens(text,pdf_filename)
    else:
        raise FileNotFoundError(f"PDF file {pdf_filename} not found in the project directory.")



# def process_and_send_tokens(extracted_text, title):
#     nlp = spacy.load("en_core_web_sm")
#     doc = nlp(extracted_text)

#     # Store categorized entities with positions grouped by their text
#     categorized_entities = {}

#     for ent in doc.ents:
#         if ent.label_ not in categorized_entities:
#             categorized_entities[ent.label_] = {}

#         if ent.text not in categorized_entities[ent.label_]:
#             categorized_entities[ent.label_][ent.text] = []

#         # Append the start and end positions for the entity
#         categorized_entities[ent.label_][ent.text].append({
#             "title": title,
#             "start_pos": ent.start_char,
#             "end_pos": ent.end_char
#         })


#     return extracted_text, categorized_entities

def process_and_send_tokens(extracted_text, title):
    nlp = spacy.load("en_core_web_sm")
    doc = nlp(extracted_text)

    # Initialize the list of docs
    docs = []

    # Iterate through the entities and format the output
    for ent in doc.ents:
        # Check if the entity already exists in the docs list
        token_exists = False
        for doc_item in docs:
            if doc_item["token"] == ent.text:
                # If it exists, append the item
                doc_item["items"].append({
                    "source": title,
                    "start_pos": ent.start_char,
                    "end_pos": ent.end_char
                })
                token_exists = True
                break
        
        # If the entity is not found in docs, create a new entry
        if not token_exists:
            docs.append({
                "items": [{
                    "source": title,
                    "start_pos": ent.start_char,
                    "end_pos": ent.end_char
                }],
                "token": ent.text
            })

    return extracted_text, docs
    
def get_substring_at_positions(text, start_pos, end_pos):
    if start_pos < 0 or end_pos > len(text) or start_pos > end_pos:
        raise ValueError("Start or end position is out of bounds.")
    return text[start_pos:end_pos]


# test_string = "Hello my name is Alec and im a student at UCR. i HAVE  a friend who use to go to UCR, his name is Michael. Michael is a cool dude. His name is Michael"
pdf_filename = 'Blackholes-test00.pdf'

process_pdf_results = process_pdf(pdf_filename)

token_list = process_pdf_results[1]
extracted_text = process_pdf_results[0]




# ************************************ #
# This will be for Elastic [Important] #
# ************************************ #
client = Elasticsearch(
    "https://my-elasticsearch-project-bd33e8.es.us-east-1.aws.elastic.cloud:443",
    api_key="RVVXcTU1UUJBU0VQOE1LbkFrYUY6ek5hMFNxd3hTZkdUaGRNQWszYU9oQQ=="
)

# index_name = "search-backend"
token_index_name = "tokens"

# Define the mapping
mappings = {
  "properties": {
    "token": {
      "type": "text"
    },
    "items": {  # Define 'items' as a field in the root properties
      "type": "nested",
      "properties": {
        "source": { "type": "text" },
        "start_pos": { "type": "integer" },
        "end_pos": { "type": "integer" }
      }
    }
  }
}

mapping_response = client.indices.put_mapping(index=token_index_name, body=mappings)
print(mapping_response)



