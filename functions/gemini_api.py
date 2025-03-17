
import json
import google.generativeai as genai
import re
import os
from google import genai
from elastic_api import tokenize_input
import urllib.parse

client = genai.Client(api_key="AIzaSyAeVKhK5vPnP2oYF683wfqdWjKS_6nrNI0")
model_name = "gemini-2.0-flash"

def user_input(input=""):
    # Decode the input and fix potential issues like extra characters
    input = "=" + input
    
    # Improve the prompt to make the instructions clear and focus on pair-concepts
    prompt = f"""
    Using the following input: "{input}",
    Please return a JSON response that contains a list of pair-concepts, like so:
    
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

        print(response)
        
        # Access the first candidate's response text
        candidate = response.candidates[0]
        text = candidate.content.parts[0].text.strip()

        # Clean the response by removing markdown formatting
        cleaned_text = re.sub(r'```json\n|\n```', '', text)

        # Parse the cleaned text as JSON
        pair_concepts = json.loads(cleaned_text)

        # If no pair-concepts are found, return an error response
        if isinstance(pair_concepts, dict) and "error" in pair_concepts:
            return pair_concepts  # Return the error message if no pair-concepts are found
        
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
            return analyze_sentences_from_documents(tokenized_concepts, "analysis_results(duhduh).json")

        else:
            return {"error": "Invalid response format received from the model."}

    except (AttributeError, KeyError, json.JSONDecodeError) as e:
        # Handle errors in the response processing
        print(f"Error processing response: {e}")
        return {"error": "Failed to extract pair-concept"}

def analyze_sentences_from_documents(documents, output_file):
    print(f"Type of documents input: {type(documents)}")  # Debugging line
    """
    Analyzes sentences from a list of document objects (JSON) using the Gemini API,
    including keyword definition based on sentence usage.
    """
    try:
        if not isinstance(documents, list):
            raise ValueError("Input should be a list of document objects.")

        all_results = []
        for document in documents:
            if not isinstance(document, dict) or "sentences" not in document:
                raise ValueError("Each item in the input list should be a document object with a 'sentences' key.")

            sentences = document["sentences"]
            keyword = document.get("keyword", "N/A")  # Get the keyword, or set to "N/A" if not present.

            # Prepare the prompt for the Gemini API
            prompt = f"""
            You are given a JSON document. Your task is to modify the document in the following way:

            1. Replace the 'sentences' section with a single, concise sentence (or multiple lines if needed) that clearly summarizes how the keyword '{keyword}' is used in the context of the document.
            2. The new sentence should clearly describe the pair concept '{keyword}' and its usage in this document. It should be structured like a short paragraph, but focus on summarizing how '{keyword}' is represented throughout the document.
            3. Ensure the response highlights the significance of the keyword in the context of the article, and provides a clear explanation of its role.

            Here is the original JSON document:

            {json.dumps(document, indent=4)}

            The resulting sentence should look like: "The pair concept '{keyword}' is being used in this document to represent [explanation of usage]."
            """

            # Call to Gemini API
            response = client.models.generate_content(model=model_name, contents=prompt)
            
            try:
                # Parsing the response to extract JSON
                json_start = response.text.find('{')
                json_end = response.text.rfind('}') + 1
                json_string = response.text[json_start:json_end]

                # Try loading the JSON from the string
                analysis = json.loads(json_string)

                # Append the analysis result directly to the all_results
                all_results.append(analysis)

            except (json.JSONDecodeError, ValueError) as e:
                title = document.get('title', 'Unknown Title')  # Default to 'Unknown Title' if key is missing
                print(f"Error processing response for document: '{title}': {e}")
                all_results.append({"error": f"Failed to parse Gemini response: {str(e)}", "original_title": title})
                print(response.text)  # Print the raw response for debugging

        # Save the results to the output file
        with open(output_file, 'w') as f:
            json.dump(all_results, f, indent=4)

        return all_results
    except Exception as e:
        print(f"An error occurred: {e}")
        return str(e)
