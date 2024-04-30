"""-----------------------------------------------------------------------
1.0: Read liraries and dependencies
-----------------------------------------------------------------------"""

import requests
import json

"""-----------------------------------------------------------------------
2.0: API call to get sparse embedding
-----------------------------------------------------------------------"""

def initiate_sparse_embed(text):
	
  # assign dummy (needed for embedding)
  file_id        = 0     #dummy
  chunk_id       = 0     #dummy
  page_num       = 0     #dummy
  text_source    = 'na'  #dummy

  payload ={  "file_id"   : file_id,
              "data"  : [{"chunk_id"      : chunk_id,
                          "page_num"      : page_num,
                          "text_source"   : text_source,
                          "chunk_text"    : text}]}
	
	#API_URL = "http://localhost:8000/sparse_embed"
	#API_URL = "http://sparse_embed_app:8000/sparse_embed"
	#API_URL	= "http://3.145.193.223:8000/sparse_embed"
  API_URL	= "http://3.140.50.59:8000/sparse_embed"
  headers = 	{
					"Content-Type": "application/json"
				}
	
  response = requests.post(API_URL, headers=headers, json=payload)
	
  if response.status_code==200 :

    sparse = response.json()["data"][0]["sparse_embeddings"]
    #json_file = json.dumps(response.json(), indent=4)

    #print(f"   Sparse embedding succeeded.")
    return sparse
  else:
    print(f"   Sparse embedding failed.")
    print(f"   Sparse response status:", str(response.status_code))
    print(f"   Sparse error message:".format(response.json()))
    return None
  
#test
# text ="Hello how are you?"
# sed = initiate_sparse_embed(text)
# print(sed)