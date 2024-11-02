import os
import asyncio
from lightrag import LightRAG, QueryParam
from lightrag.llm import gpt_4o_mini_complete
from dsrag.document_parsing import extract_text_from_pdf, extract_text_from_docx

WORKING_DIR = "./ankers_hus"
#WORKING_DIR = "./test"

if not os.path.exists(WORKING_DIR):
    os.mkdir(WORKING_DIR)

rag = LightRAG(
    working_dir=WORKING_DIR,
    #llm_model_func=gpt_4o_mini_complete,
    # llm_model_func=gpt_4o_complete
)

async def insert_file_into_rag(rag):
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
                        await rag.ainsert(text)
                    elif file_name.endswith('.pdf'):
                        text, _ = extract_text_from_pdf(file_path)
                        await rag.ainsert(text)
                except:
                    print(f"Error reading {file_name}")
                    continue
            else:
                print(f"Unsupported file type: {file_name}")
                continue
        break

    # Now, await the async insert method
    #await rag.ainsert(content)

#asyncio.run(insert_file_into_rag(rag))


# Perform local search
#print(
#    rag.query("Which bidder is suited most given we look for the total cost, compliance against our proposal and based on timeline", param=QueryParam(mode="local"))
#)

# Perform global search
#print(
#    rag.query("Which bidder is suited most given we look for the total cost, compliance against our proposal and based on timeline", param=QueryParam(mode="global"))
#)

# Perform hybrid search
print("\n\n\n\n\n\n\n")
print(
    rag.query("Identify any inconsistencies across the documents", param=QueryParam(mode="hybrid", only_need_context=False))
)
print("\n\n\n\n\n\n\n")
