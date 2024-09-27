
import re


def clear_query(query: str):
    # Strip whitespace and newlines from start and end
    query = query.strip()
    
    # Replace multiple whitespaces with a single space, but keep other newlines intact

    query = re.sub(r'[^\S\n]+', ' ', query)
    
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
    
    cleaned_text = clear_query(example_text)
    
    print("\nCleaned text:")
    print(cleaned_text)

if __name__ == "__main__":
    main()



