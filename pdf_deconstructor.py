import pytesseract
from PIL import Image
import pdf2image
import os
import spacy
import pandas as pd
import json


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
        return tokenize_tag(text, pdf_filename)
    else:
        raise FileNotFoundError(f"PDF file {pdf_filename} not found in the project directory.")

import json

def tokenize_tag(extracted_text, title):
    nlp = spacy.load("en_core_web_sm")
    doc = nlp(extracted_text)

    # Store categorized entities with positions grouped by their text
    categorized_entities = {}

    for ent in doc.ents:
        if ent.label_ not in categorized_entities:
            categorized_entities[ent.label_] = {}

        if ent.text not in categorized_entities[ent.label_]:
            categorized_entities[ent.label_][ent.text] = []

        # Append the start and end positions for the entity
        categorized_entities[ent.label_][ent.text].append({
            "title": title,
            "start_pos": ent.start_char,
            "end_pos": ent.end_char
        })

    # Convert categorized entities into JSON format
    categorized_entities_json = json.dumps(categorized_entities, indent=4)

    return extracted_text, categorized_entities_json



def get_substring_at_positions(text, start_pos, end_pos):
    if start_pos < 0 or end_pos > len(text) or start_pos > end_pos:
        raise ValueError("Start or end position is out of bounds.")
    return text[start_pos:end_pos]

# def ent_return(doc, test_value):


# test_string = "Hello my name is Alec and im a student at UCR. i HAVE  a friend who use to go to UCR, his name is Michael. Michael is a cool dude. His name is Michael"
pdf_filename = 'Blackholes-test00.pdf'
extracted_text = process_pdf(pdf_filename)

#this will be able to retireve the char at a position
print(get_substring_at_positions(extracted_text[0], 50181, 50184))
# print(extracted_text[1])

