import json
import google.generativeai as genai
import re
import os
from google import genai


client = genai.Client(api_key = "AIzaSyAeVKhK5vPnP2oYF683wfqdWjKS_6nrNI0")
model_name="gemini-2.0-flash"



def user_input(input):
    prompt = f"""
    Using this input: {input},
    give me either a JSON response structured like this which only gives me the pair concept present in tthe input if a pair-concept exists or if multiple exist:

    [
        {{
            "pair-concept": "concept1"
        }},
        {{
            "pair-concept": "concept2"
        }}
    ]

    If a pair-concept does not exist, return this:

    {{
        "error": "no pair-concept found"
    }}
    """

    # Generate the response using the model
    response = client.models.generate_content(model=model_name, contents=prompt)
    # print(response)

    try:
        # Access the 'candidates' list from the response
        candidate = response.candidates[0]  # Access the first candidate
        text = candidate.content.parts[0].text.strip()  # Extract the text from the first part

        # Remove the markdown formatting (triple backticks)
        cleaned_text = re.sub(r'```json\n|\n```', '', text)

        # Directly parse the cleaned text content as JSON
        pair_concepts = json.loads(cleaned_text)  # Assuming the model response is directly valid JSON

        # Check if the response contains a list of pair-concept items
        if isinstance(pair_concepts, list):
            # Check if there's a single pair-concept that needs splitting
            updated_pair_concepts = []
            for pair in pair_concepts:
                if "and" in pair.get("pair-concept", ""):  # Check for "and" indicating multiple concepts
                    parts = pair["pair-concept"].split(" and ")
                    for part in parts:
                        updated_pair_concepts.append({"pair-concept": part.strip()})
                else:
                    updated_pair_concepts.append(pair)
            
            print(updated_pair_concepts)
            return updated_pair_concepts
        else:
            print("Error: Expected a list of pair-concept items.")
            return {"error": "Expected a list of pair-concept items."}

    except (AttributeError, KeyError, json.JSONDecodeError) as e:
        # Handle cases where the expected attributes or data are not available
        print(f"Error extracting pair-concepts: {e}")
        return {"error": "Failed to extract pair-concept"}

def analyze_sentences_from_documents(input_file, output_file):
    """
    Analyzes sentences from a JSON file with document metadata using the Gemini API,
    including keyword definition based on sentence usage.
    """
    try:
        with open(input_file, 'r') as f:
            documents = json.load(f)

        if not isinstance(documents, list):
            raise ValueError("Input JSON should contain a list of document objects.")

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
            
            # Print the raw response for debugging
            print("Response Text:", response.text)

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

    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    # Replace with your actual API key
  # Hardcoded API key here

    # Path to the JSON file in the parent directory (project folder)
    # json_path = os.path.join('.', 'articles_data_blackholes_updated.json')  # '..' goes up one directory
    json_path = os.path.join('.', 'breaking_the_ice.json')  # '..' goes up one directory
    # Replace with your actual file paths
    input_file = json_path  # Hardcoded input file path here.
    output_file = "analysis_results(breaking_the_ice).json"  # Hardcoded output file path here.

    # analyze_sentences_from_documents(input_file, output_file)
    input = user_input("search up this pair concept: Politcal anarchy")

