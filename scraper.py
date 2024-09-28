import requests
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin


def get_help_center_links(base_url):
    response = requests.get(base_url)
    soup = BeautifulSoup(response.text, 'html.parser')

    links = []
    for a_tag in soup.find_all('a', href=True):
        link = a_tag['href']
        full_link = urljoin(base_url, link)
        if '/help/' in full_link:
            links.append(full_link)

    return links

def extract_and_chunk_article(url, max_length=750):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    chunks = []
    current_chunk = []
    current_length = 0

    def add_to_chunk(text):
        nonlocal current_length, current_chunk, chunks
        if current_length + len(text) > max_length:
            chunks.append(' '.join(current_chunk))
            current_chunk = []
            current_length = 0
        current_chunk.append(text)
        current_length += len(text)

    for element in soup.find_all(['h2', 'h3', 'p', 'ul', 'li']):
        if element.name in ['h2', 'h3']:
            header_text = element.get_text().strip()
            if header_text:
                add_to_chunk("\n\n" + header_text + "\n\n")
        elif element.name == 'p':
            para_text = element.get_text().strip()
            if para_text:
                add_to_chunk(para_text + "\n")
        elif element.name == 'ul':
            list_items = element.find_all('li')
            for li in list_items:
                li_text = li.get_text().strip()
                if li_text:
                    add_to_chunk("• " + li_text + "\n")
    
    if current_chunk:
        chunks.append(' '.join(current_chunk))

    return chunks

def clean_and_format_chunk(chunk):
    cleaned_chunk = chunk.strip()
    cleaned_chunk = re.sub(r'•\s*', '\n• ', cleaned_chunk)
    cleaned_chunk = re.sub(r'\s*\n+', '\n', cleaned_chunk)
    cleaned_chunk = re.sub(r'([a-z])([A-Z])', r'\1 \2', cleaned_chunk)
    cleaned_chunk = re.sub(r'(\n• [\w\s]+){2,}', r'\1', cleaned_chunk)
    cleaned_chunk = re.sub(r'\n+', '\n', cleaned_chunk).strip()
    
    return cleaned_chunk

def clean_chunks(nested_chunks):
    cleaned_chunks = []
    for chunk in flatten_chunks(nested_chunks):
        cleaned_chunk = clean_and_format_chunk(chunk)
        cleaned_chunks.append(cleaned_chunk)
    return cleaned_chunks

def flatten_chunks(nested_chunks):
    flat_chunks = []
    for chunk in nested_chunks:
        if isinstance(chunk, list):
            flat_chunks.extend(flatten_chunks(chunk))
        else:
            flat_chunks.append(chunk)
    return flat_chunks

if __name__ == "__main__":
    base_url = 'https://www.notion.so/help'
    article_links = get_help_center_links(base_url)

    all_articles_content = []
    for link in article_links:
        article_content = extract_and_chunk_article(link)
        all_articles_content.append(article_content)

    cleaned_chunks = clean_chunks(all_articles_content)

    output_file_path = 'help_center_articles.txt'

    with open(output_file_path, 'w', encoding='utf-8') as file:
        for idx, chunk in enumerate(cleaned_chunks):
            file.write(f"Chunk {idx + 1}:\n{chunk}\n\n")
