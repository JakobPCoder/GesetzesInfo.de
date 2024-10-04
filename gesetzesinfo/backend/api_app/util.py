
import os
import re

from dotenv import dotenv_values
import tiktoken

# Get the directory of the current script
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
env_path = os.path.join(parent_dir, '.env')

# Load the environment variables
env_vars = dotenv_values(env_path)

def clear_text(query: str):
    # Strip whitespace and newlines from start and end
    query = query.strip()
    
    # Replace multiple newlines with two newlines
    query = re.sub(r'\n{4,}', '\n\n\n', query)
    
    # Replace multiple whitespaces with a single space
    query = re.sub(r' {2,}', ' ', query)
    
    return query

def clamp_text_to_tokens(text: str, max_tokens: int):
    if len(text) > max_tokens:
        encoding = tiktoken.encoding_for_model(env_vars.get('EMBEDDING_MODEL'))
        encoded_text = encoding.encode(text)
        num_tokens = len(encoded_text)
        if num_tokens > max_tokens:
            text = encoding.decode(encoded_text[:max_tokens])
        return text
    else:
        return text


def main():
    # Example badly formatted multi-line text string
    example_text = """
    This   is  a   badly    formatted
    
    text   string  with    multiple
    
        lines   and   extra    spaces.
    
    It also has   some empty  lines.
    """
    
    print("Original text:")
    print(example_text)
    
    cleaned_text = clear_text(example_text)
    
    print("\nCleaned text:")
    print(cleaned_text)

if __name__ == "__main__":
    main()



