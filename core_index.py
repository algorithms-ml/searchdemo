from utilities_core import helper_setup_env
from utilities_core import doc_parse, doc_chunk
from utilities_core import embed_connection, apply_embedding_doc
from utilities_core import setup_pinecone, doc_index

#0.0: AI model set up and vector DB set up
embeddings_model = embed_connection()
setup_pinecone("searchdemo")

# core upload and index function
def upload_and_index(filenm, kb):
    print("Parsing initiated")
    #1.0 apply parsing
    _text, metadata = doc_parse(filenm)
    print("Parsing successful")
          
    
    #2.0: apply chunking
    print("Chunking initiated")
    doc_obj = doc_chunk(_text, metadata)
    print("Chunking successful")

    #3.0: apply sense emedding
    embed_doc = apply_embedding_doc(embeddings_model, doc_obj, kb)
    print("Embedding initiated")


    #5.0: indexing
    doc_index(embed_doc, "searchdemo", namespace=kb)
    print("Embedding successful")



