import os
import asyncio
import re
from lightrag import LightRAG, QueryParam
from lightrag.llm import azure_openai_complete, azure_openai_embedding
from dataclasses import field
from dsrag.document_parsing import extract_text_from_pdf, extract_text_from_docx

WORKING_DIR = "./ankers_hus_docs"
#WORKING_DIR = "./test"

if not os.path.exists(WORKING_DIR):
    os.mkdir(WORKING_DIR)

rag = LightRAG(
    working_dir=WORKING_DIR,
    llm_model_func=azure_openai_complete,
embedding_func=azure_openai_embedding
)


def separate_entities_and_sources(input_data):
    # Using regular expressions to split the input string by "Entities" and "Sources"
    entities = re.search(r"-----Entities-----(.*?)-----Sources-----", input_data, re.DOTALL)
    sources = re.search(r"-----Sources-----(.*)", input_data, re.DOTALL)

    # Extract and strip the matches, if found
    graph = entities.group(1).strip() if entities else ""
    context = sources.group(1).strip() if sources else ""

    return graph, context

def insert_file_into_rag(rag):
    # Open and read the file synchronously
    #with open("/Users/abylikhsanov/Documents/volve/rag_eval_data/supreme_court/out/output.txt", mode='r') as f:
    #    content = f.read()  # Read the file content synchronously
    directory = "/Users/abylikhsanov/Documents/jupyter/notebooks/data/ankers_hus"
    for root, dirs, files in os.walk(directory):
        for file_name in files:
            if file_name.endswith(('.docx', '.md', '.txt', '.pdf')):
                try:
                    file_path = os.path.join(root, file_name)
                    clean_file_path = file_path.replace(directory, "")
                    print(f'inserting document: {file_name}')

                    if file_name.endswith('.docx'):
                        text, _ = extract_text_from_docx(file_path)
                        rag.insert(text, original_doc_id=f"{file_name}")
                    elif file_name.endswith('.pdf'):
                        text, _ = extract_text_from_pdf(file_path)
                        rag.insert(text, original_doc_id=f"{file_name}")
                except Exception as e:
                    print(f"Error reading {str(e)}")
                    continue
            else:
                print(f"Unsupported file type: {file_name}")
                continue
        break

    # Now, await the async insert method
    #await rag.ainsert(content)

#asyncio.run(insert_file_into_rag(rag))
insert_file_into_rag(rag)

# Perform local search
#print(
#    rag.query("Which bidder is suited most given we look for the total cost, compliance against our proposal and based on timeline", param=QueryParam(mode="local"))
#)

# Perform global search
#print(
#    rag.query("Which bidder is suited most given we look for the total cost, compliance against our proposal and based on timeline", param=QueryParam(mode="global"))
#)

# Perform hybrid search
result = rag.query("Identify statements related to contract options or their prices", param=QueryParam(mode="hybrid", only_need_context=True))
graph, context = separate_entities_and_sources(result)

print("\n\n\n\n\n\n\n")
print(f"Graph: {graph}\n\n\n\nsource: {context}")
print("\n\n\n\n\n\n\n")
