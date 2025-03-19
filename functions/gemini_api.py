
import json
import google.generativeai as genai
import re
import os
from google import genai
from elastic_api import tokenize_input
import urllib.parse

api_key = os.getenv("gen_client")

client = genai.Client(api_key=api_key)
model_name = "gemini-2.0-flash"

def user_input(input=""):
    # Decode the input and fix potential issues like extra characters
    input = "=" + input
    
    # Improve the prompt to make the instructions clear and focus on pair-concepts
    prompt = f"""
    Using the following input: "{input}",
    Extract the exact phrase or sequence of words from the input that represents the primary concept or subject. Return this phrase as the value of the 'pair-concept' and make it singular not plural key in the following JSON format:
    
    [
        {{
            "pair-concept": "concept1"
        }},
        {{
            "pair-concept": "concept2"
        }}
    ]
    
    If no pair-concept exists in the input, return the following JSON:
    
    {{
        "error": "no pair-concept found"
    }}
    """

    try:
        # Generate the response using the model
        response = client.models.generate_content(model=model_name, contents=prompt)

        # print(response)
        
        # Access the first candidate's response text
        candidate = response.candidates[0]
        text = candidate.content.parts[0].text.strip()

        # Clean the response by removing markdown formatting
        cleaned_text = re.sub(r'```json\n|\n```', '', text)

        # Parse the cleaned text as JSON
        pair_concepts = json.loads(cleaned_text)

        # If no pair-concepts are found, return an error response
        if isinstance(pair_concepts, dict) and "error" in pair_concepts:
                    return []  # Return empty array if there's an error
        
        if isinstance(pair_concepts, list):
            # Ensure the response is a list of pair-concept objects
            updated_pair_concepts = []
            for pair in pair_concepts:
                if "and" in pair.get("pair-concept", ""):
                    # Split pair-concept if "and" exists to handle multiple concepts
                    parts = pair["pair-concept"].split(" and ")
                    for part in parts:
                        updated_pair_concepts.append({"pair-concept": part.strip()})
                else:
                    updated_pair_concepts.append(pair)
            
            # If pair-concepts exist, send them off to the next function for further processing
            tokenized_concepts = tokenize_input(updated_pair_concepts)  # Tokenizing the concepts
            # print(tokenized_concepts)
            data_new = analyze_sentences_from_documents(tokenized_concepts, "analysis_results(duhduh).json")
            # print(data_new)
            return data_new

        else:
            return {"error": "Invalid response format received from the model."}

    except (AttributeError, KeyError, json.JSONDecodeError) as e:
        # Handle errors gracefully
        print(f"Error processing response: {e}")
        return []  # Return an empty array in case of any error

def analyze_sentences_from_documents(documents, output_file):
    # print(documents)
    try:
        if not isinstance(documents, list):
            raise ValueError("Input should be a list of document objects.")
        
        all_results = []
        for document in documents:
            if not isinstance(document, dict) or "sentences" not in document:
                raise ValueError("Each item in the input list should be a document object with a 'sentences' key.")
            
            # Continue processing and collect results
            sentences = document["sentences"]
            keyword = document.get("keyword", "N/A")

            prompt = f"""
            You are given a JSON document. Your task is to modify the document in the following way:

            1. **Combine Duplicates**: If multiple entries have the same title and authors, combine them into a single entry.
            2. **Summarize Usage**: Replace the contents inthe 'sentences' section with a single, concise sentence (or multiple lines if needed) that clearly summarizes how the '{keyword}' is being used in the sentence keep the same data structure.
            3. **Focus on Conceptual Usage**: The new sentence should clearly describe the pair concept '{keyword}' and its conceptual role in the document.
            4. **Highlight Significance**: Ensure the response highlights the significance of the keyword in the context of the article and provides a clear explanation of its role.

            Here is the original JSON document:

            {json.dumps(document, indent=4)}

            The resulting sentence should look like: "The pair concept '{keyword}' is being used in this document to represent [explanation of usage]."
            """
            
            response = client.models.generate_content(model=model_name, contents=prompt)
            
            # Make sure the response is a list before appending
            try:
                json_start = response.text.find('{')
                json_end = response.text.rfind('}') + 1
                json_string = response.text[json_start:json_end]
                analysis = json.loads(json_string)
                all_results.append(analysis)
            except (json.JSONDecodeError, ValueError) as e:
                title = document.get('title', 'Unknown Title')
                all_results.append({"error": f"Failed to parse Gemini response: {str(e)}", "original_title": title})

        # Ensure the results are always returned as a list
        return all_results if isinstance(all_results, list) else []

    except Exception as e:
        print(f"An error occurred: {e}")
        return [{"ERROR": "Can not find results. If this is a mistake, report this issue:)"}]  # Return an empty list if there's an error
    

