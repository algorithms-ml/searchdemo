import pandas as pd
from datasets import load_dataset

# Load the TREC-COVID dataset
dataset = load_dataset('BeIR/trec-covid', 'queries')

# Save the dataset as a JSON file
#dataset.save_to_disk("trec_covid.json")