import requests
import torch
import warnings
from transformers import GPT2Tokenizer, GPT2LMHeadModel
from urllib.parse import urlparse

def preprocess_repository_names(repository_names):
    for repo in repository_names:
        repo = repo.strip().lower()  # Convert to lowercase and remove leading/trailing whitespaces
        if repo:  # Skip empty names
            yield repo

def process_repository(repository_name, tokenizer, model):
    # Generate a prompt or template based on the repository name
    prompt = f"Evaluate the technical complexity of the repository: {repository_name}. Analyze the code and provide insights on its complexity."
    
    # Tokenize the prompt
    input_ids = tokenizer.encode(prompt, add_special_tokens=False, truncation=True, max_length=100, return_tensors="pt")
    
    # Generate attention mask
    attention_mask = torch.ones_like(input_ids)

    # Generate output using the model
    with torch.no_grad():
        output = model.generate(input_ids=input_ids, attention_mask=attention_mask, max_new_tokens=200, pad_token_id=tokenizer.eos_token_id)

    # Decode the output
    processed_repo = tokenizer.decode(output[0], skip_special_tokens=True)

    return processed_repo

def fetch_github_repositories():
    warnings.filterwarnings("ignore")
    
    user_url = input("GitHub User URL: ")
    
    # Extracting the GitHub username from the user URL
    parsed_url = urlparse(user_url)
    username = parsed_url.path.strip("/")
    
    # Ensure the username is not empty
    if not username:
        print("Invalid GitHub user URL.")
        return
    
    # API endpoint to fetch user repositories
    api_url = f"https://api.github.com/users/{username}/repos"
    
    try:
        response = requests.get(api_url)
        response.raise_for_status()  # Raise exception if request was unsuccessful
        
        repositories = response.json()
        
        if not repositories:
            print("No repositories found for the user.")
            return
        
        # Extracting repository names
        repository_names = [repo['name'] for repo in repositories]
        
        # Initialize tokenizer and model
        tokenizer = GPT2Tokenizer.from_pretrained("gpt2")
        model = GPT2LMHeadModel.from_pretrained("gpt2")
        
        preprocessed_names_generator = preprocess_repository_names(repository_names)
        
        # Process and score the preprocessed names
        repository_scores = {}
        for preprocessed_name in preprocessed_names_generator:
            processed_repo = process_repository(preprocessed_name, tokenizer, model)
    
            # The complexity score is based on the length of the processed repository which in turn is based on output of the model.
            complexity_score = len(processed_repo)
            repository_scores[preprocessed_name] = complexity_score
        
        # Identify the repository with the highest complexity score
        most_complex_repo = max(repository_scores, key=repository_scores.get)
        
        # Justify the selection using GPT
        justification_prompt = f"Justification for selecting the most technically complex repository: {most_complex_repo}."
        justification_input_ids = tokenizer.encode(justification_prompt, add_special_tokens=False, truncation=True, max_length=100, return_tensors="pt")
        
        attention_mask = torch.ones_like(justification_input_ids)
        
        with torch.no_grad():
            justification_output = model.generate(input_ids=justification_input_ids, attention_mask=attention_mask, max_new_tokens=200, pad_token_id=tokenizer.eos_token_id)
        
        justification_text = tokenizer.decode(justification_output[0], skip_special_tokens=True)
        
        print("Most Complex Repository:", most_complex_repo)
        print("Justification:", justification_text)
        
    except requests.exceptions.HTTPError as err:
        print(f"An HTTP error occurred: {err}")
    except requests.exceptions.RequestException as err:
        print(f"An error occurred: {err}")
    finally:
        # Clean up resources if necessary
        del tokenizer
        del model

fetch_github_repositories()
