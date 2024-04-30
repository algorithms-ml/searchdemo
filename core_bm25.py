from pinecone_text.sparse import BM25Encoder
bm25 = BM25Encoder()

from pinecone_text.dense import OpenAIEncoder
import json
from rank_bm25 import BM25Okapi
import nltk
from nltk.tokenize import word_tokenize
nltk.download('punkt')

def bm25_ranker(data, query : str = None, top_n : int = None):
    #data = json.loads(data)
    # Extract chunk_text from each item
    texts = [item["metadata"]["chunk_text"] for item in data["matches"]]

    # Tokenize texts
    tokenized_texts = [word_tokenize(text.lower()) for text in texts]

    # Initialize BM25
    bm25 = BM25Okapi(tokenized_texts, b=0)

    # Calculate BM25 scores for each document against the corpus itself (self-query for demonstration)
    # In a real scenario, you would query with specific search terms
    
    doc_scores = bm25.get_scores(query.lower())
    print(doc_scores)
    
     # Calculate mean and max of doc_scores for normalization
    max_score = max(doc_scores)
    min_score = min(doc_scores)

    # Apply mean-max normalization (based on the second interpretation)
    normalized_scores = [(score - min_score) / (max_score - min_score) for score in doc_scores]
    print("")
    print(normalized_scores)

    # The `data` structure is now updated with BM25 scores as "score_reranked"
    for match, score in zip(data["matches"], normalized_scores):
        match["score_reranked"] = score
    
    # Sort the matches based on score_reranked in descending order
    #data["matches"] = sorted(data["matches"], key=lambda x: x["score_reranked"], reverse=True)

    
    # Here we print the updated structure
    #print(json.dumps(data, indent=4))
    return data

    # If you want to save the updated JSON data to a file
    # with open('updated_data.json', 'w') as f:
    #     json.dump(data, f, indent=4)
    