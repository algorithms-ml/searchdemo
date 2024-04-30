
try:
    from typing import Annotated
except ImportError:
    from typing_extensions import Annotated
import os
from io import BytesIO
from starlette.responses import JSONResponse


from fastapi import Depends, FastAPI, Depends, File, UploadFile
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

import secrets
from typing import List
from pydantic import BaseModel

from core_index import upload_and_index
from core_search import retrieve_search_result
from utils_credentials import verify_credentials
from core_bm25 import bm25_ranker

app = FastAPI()

"""Middleware to allow webapi call"""
origins =   [
            "http://localhost",
            "http://localhost:3000",
            # Add more allowed origins here if needed
            ]

app.add_middleware( CORSMiddleware,
                    #allow_origins=origins,
                    #allow_credentials=True,
                    allow_origins=["*"],
                    allow_credentials=False,
                    allow_methods=["*"],
                    allow_headers=["*"],)

@app.get("/users/me")
def read_current_user(credentials: Annotated[HTTPBasicCredentials, Depends(verify_credentials)]):
    return {"username": credentials.username, "password": credentials.password}



@app.post("/uploadfiles/")
async def upload_file(knowledge_base: str, 
                      file: UploadFile = File(...), 
                      credentials:HTTPBasicCredentials = Depends(verify_credentials)):
    try:
        contents = await file.read()
        print(file.filename)
        print(type(contents))
        print("")
        print(knowledge_base)
        if contents is not None:
            filenm = os.path.join("./data/temp/", knowledge_base, file.filename)
            print(filenm)
            with open(filenm, "wb") as fp:
                fp.write(contents)
                upload_and_index(filenm = filenm, kb=knowledge_base)

            with open(file.filename, "wb") as fp:
                fp.write(contents)

        return JSONResponse(status_code=200, content={"message": f"File {file.filename} uploaded successfully"})
    except Exception as e:
        return JSONResponse(status_code=400, content={"message": f"Failed to upload file: {str(e)}"})
    
@app.get("/search")
def search(query:str, type: str, kb : str, credentials:HTTPBasicCredentials = Depends(verify_credentials)):
    # assuming search is a function that returns the search result

    search_type = type
    print(query)
    print(search_type)
    result = retrieve_search_result(query, search_type, kb)
    print(result)
    #apply bm25 reranking 
    result_reranked = bm25_ranker(data=result, query=query)
    return result_reranked


if __name__ == "__main__": 
    uvicorn.run("core_app:app", host="0.0.0.0", port=8000, reload=True)
