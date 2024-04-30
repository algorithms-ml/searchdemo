import os
import time
from dotenv import load_dotenv
from langchain_community.document_loaders import PDFMinerLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from pinecone import Pinecone, ServerlessSpec
from tqdm.auto import tqdm

from core_splade import initiate_sparse_embed
from pinecone_text.hybrid import hybrid_convex_scale

#0.0: Read env variables
def helper_setup_env():
    load_dotenv()
    env_vars = {"OPENAI_API_KEY"   : os.getenv("OPENAI_API_KEY"),
                "PINECONE_API_KEY" : os.getenv("PINECONE_API_KEY"),
                "PINECONE_CLOUD"   : os.getenv("PINECONE_CLOUD"),              
                "PINECONE_REGION" : os.getenv("PINECONE_REGION"),
                "VECTOR_DIMENSION" : os.getenv("VECTOR_DIMENSION")}
    return env_vars

PINECONE_API_KEY = helper_setup_env().get("PINECONE_API_KEY") 
PINECONE_CLOUD   = helper_setup_env().get("PINECONE_CLOUD") 
PINECONE_REGION  = helper_setup_env().get("PINECONE_REGION")
OPENAI_API_KEY   = helper_setup_env().get("OPENAI_API_KEY")  
VECTOR_DIMENSION = int(helper_setup_env().get("VECTOR_DIMENSION"))


#1.0: Parsing
def doc_parse(filenm : str, filetype='pdf'):
    print(filenm)
    loader = PDFMinerLoader(filenm)
    data = loader.load()
    _text = data[0].page_content
    _text = str(_text.encode(encoding = 'UTF-8', errors = 'replace'))
    #print(_text)
    metadata = data[0].metadata
    return _text, metadata
    
#_text, metadata = doc_parse("./data/SMC2358.pdf")


#2.0: Cunking
def doc_chunk(text : str, metadata : str, chunk_size : int = 512, chunk_overlap : int = 20):
    text_splitter = CharacterTextSplitter(
        separator =  " ",
        chunk_size = chunk_size,
        chunk_overlap  = chunk_overlap
    )
    text = text.replace("\\n",'')
    docs = text_splitter.create_documents([text], metadatas=[metadata])
    #print(docs)
    return docs

#doc_obj = doc_chunk(_text, metadata)
#print(doc_obj)



#3.0: embedding model set up
def embed_connection(api=OPENAI_API_KEY):
    embeddings_model = OpenAIEmbeddings(disallowed_special=(), openai_api_key=api)
    print("Connection to Embedding model is successful.")
    return embeddings_model

#embeddings_model = embed_connection()

#4.0: apply embedding
def apply_embedding_doc(model : object, doc_obj, kb : str):
    embed_doc = []
    for i,val in enumerate(doc_obj):
        chunk_dict = {"id": doc_obj[i].metadata["source"]+"_" + str(i), 
                      "metadata": dict(**doc_obj[i].metadata,
                                       **{"chunk_num": i}, 
                                       **{"chunk_text": doc_obj[i].page_content},
                                       **{"kb" : kb}), 
                        "values"    : model.embed_query(doc_obj[i].page_content),
                         "sparse_values" : initiate_sparse_embed(doc_obj[i].page_content)}
        embed_doc.append(chunk_dict)
        time.sleep(0.05)

    return embed_doc


#embed_doc = apply_embedding_doc(embeddings_model,doc_obj)
#print(embed_doc)

def apply_embedding_query(model : object, query : str):
    embeddings = model.embed_query(query)
    return embeddings
#embed_query = apply_embedding_query(embeddings_model, "Hello ji, how are you?")

#5.0: vector db set up
def setup_pinecone(index_name : str, 
                   api_key=PINECONE_API_KEY, 
                   api_region=PINECONE_REGION ,
                   api_cloud = PINECONE_CLOUD,  
                   dim : int = VECTOR_DIMENSION):
  # Instantiate Pinecone
  pinecone = Pinecone(api_key=api_key)
  
  # Create an index
  if index_name in pinecone.list_indexes().names():
    print(f"Index '{index_name}' already exists.")
    return False

  else:
    pinecone.create_index(name=index_name, 
                          metric='dotproduct', 
                          dimension=dim,
                          spec=ServerlessSpec(cloud=api_cloud, region=api_region) 
                        )
    print(f"Created index '{index_name}' was successful.")
    return True
#setup_pinecone("healthcare")


#6.0: vector db indexing:
def doc_index(  input_data    : list,
                index_name    : str, 
                api_key       : str = PINECONE_API_KEY,
                batch_size    : int = 100,
                namespace     : str = None):
    
    # Initialize connection to Pinecone
    pinecone = Pinecone(api_key=api_key)

    # Connect to the index and view index stats
    index = pinecone.Index(index_name)

    for i_start in tqdm(range(0, len(input_data), batch_size)):
        i_end = min(len(input_data), i_start+batch_size)
        print("")
        print(f"processing from index {i_start} to {i_end}")

        if namespace is not None:
            index.upsert(vectors=input_data[i_start: i_end], async_req=True, namespace = namespace)
        else:
            index.upsert(vectors=input_data[i_start: i_end], async_req=True, namespace = None)

#doc_index(embed_doc, "healthcare")

#7.0: retrieval


def doc_search( query           : str,
                index_name      : str,
                model           : object,
                api_key         : str = PINECONE_API_KEY,
                num_retievals   : int = 5,
                namespace       : str = None,
                search_type     : str = None):
    
    # Initialize connection to Pinecone
    pinecone = Pinecone(api_key=api_key)

    # Connect to the index and view index stats
    index = pinecone.Index(index_name)

    #apply embeddings
    embd_query_dense = apply_embedding_query(model, query)
    embd_query_sparse= initiate_sparse_embed(query)

    if search_type in ['semantic', 'lexical'] : alpha = 1.0
    elif search_type in ['hybrid'] : alpha = 0.7

    hybrid_dense, hybrid_sparse = hybrid_convex_scale(embd_query_dense, 
                                                      embd_query_sparse, 
                                                      alpha= alpha)

    print(query)
    print("")

    #retrieve search results
    results = index.query(  vector          =hybrid_dense,
                            sparse_vector   =hybrid_sparse, 
                            top_k           =num_retievals,
                            namespace       = namespace,
                            include_metadata=True,
                            include_values  =False,
                            )

    results = results.to_dict() #convert pinecone object to dict
    return results

# search_result = doc_search("What are the indcation for oncology and adult population", 
#                            'healthcare',
#                            embeddings_model)
# print(search_result)
