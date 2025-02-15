import json

# Your data
data = {
    "name": "Alec Overman",
    "age": 25,
    "skills": ["Python", "JavaScript", "Data Analysis"],
    "project": {
        "name": "PDF to Database",
        "status": "In Progress"
    }
}

# Save to a file
with open("data.json", "w") as json_file:
    json.dump(data, json_file, indent=4)
