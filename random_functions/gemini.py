from google import genai

client = genai.Client(api_key="AIzaSyAeVKhK5vPnP2oYF683wfqdWjKS_6nrNI0")
response = client.models.generate_content(
    model="gemini-2.0-flash", contents="Give me the basic structure of a jsonfile"
)
print(response.text)