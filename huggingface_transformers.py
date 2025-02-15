from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
import numpy as np
from scipy.spatial.distance import cosine

model_id = "meta-llama/Llama-3.2-1B"

print("Step 1: Starting script")
tokenizer = AutoTokenizer.from_pretrained(model_id)
print("Step 2: Tokenizer loaded")

# Assign eos_token to pad_token if not already set
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

print("Step 3: Starting model loading...")
model = AutoModelForCausalLM.from_pretrained(model_id)
print("Step 4: Model loaded successfully")

print("Step 3: Model loaded")

model.eval()  # Set the model to evaluation mode

# Example input texts
input_text1 = "I like blackholes"
input_text2 = "look at the cakes"

# Tokenize the input texts
inputs1 = tokenizer(input_text1, return_tensors='pt', padding=True, truncation=False)
inputs2 = tokenizer(input_text2, return_tensors='pt', padding=True, truncation=False)

# Get model outputs (hidden states or embeddings)
with torch.no_grad():
    outputs1 = model(**inputs1)
    outputs2 = model(**inputs2)

# Extract the last hidden state (embedding of [CLS] token)
embedding1 = outputs1.logits.mean(dim=1).squeeze().cpu().numpy()
embedding2 = outputs2.logits.mean(dim=1).squeeze().cpu().numpy()

# Compute the cosine similarity between the two embeddings
cosine_sim = 1 - cosine(embedding1, embedding2)

print(f"Cosine Similarity: {cosine_sim}")
