
import re


def clear_text(query: str):
    # Strip whitespace and newlines from start and end
    query = query.strip()
    
    # Replace multiple newlines with two newlines
    query = re.sub(r'\n{4,}', '\n\n\n', query)
    
    # Replace multiple whitespaces with a single space
    query = re.sub(r' {2,}', ' ', query)
    
    return query



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



