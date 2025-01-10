import pandas as pd
import uuid
import datetime
from astrapy import DataAPIClient
from openai import OpenAI
import json
import os
api_key = os.environ.get("OPENAI_API_KEY")
client = DataAPIClient(os.environ.get("ASTRA_DB_TOKEN"))
database = client.get_database("https://8b9db7c0-9835-419e-a7d0-96c0396c3672-us-east-2.apps.astra.datastax.com", keyspace="posts")
collection = database.data

# Initialize OpenAI
client = OpenAI(api_key=api_key)

collection.delete_many({})
# Read CSV
csv_file = "data.csv"
data = pd.read_csv(csv_file)

# Debug column names
print("Columns in CSV:", data.columns)

def get_openai_embedding(text):
    response = client.embeddings.create(
        input=text,
        model="text-embedding-3-small"
    )
    return response.data[0].embedding

# Insert documents with content as JSON key-value pairs
for _, row in data.iterrows():
    # Prepare content
    content = {
        "post_id": row['post_id'],  # Post ID
        "post_type": row['post_type'],  # Type of post
        "likes": row['likes'],  # Number of likes
        "comments": row['comments'],  # Number of comments
        "shares": row['shares'],  # Number of shares
    }
    content_text = json.dumps(content)
    # Generate OpenAI embeddings
    # content_text = f"{row['post_type']} {row['post_id']} {row['likes']} likes {row['comments']} comments {row['shares']} shares"
    response = client.embeddings.create(
        input=content_text,
        model="text-embedding-3-small"
    )
    embedding = response.data[0].embedding
    
    # Prepare record with embedding
    record = {
        "_id": str(uuid.uuid4()),  # Unique identifier
        "$vector": embedding,  # Vector field for search
        "content": content_text,
        "metadata": {
            "post_id": row['post_id'],
            "post_type": row['post_type'],
            "likes": row['likes'],
            "comments": row['comments'],
            "shares": row['shares'],
            "created_at": datetime.datetime.now().isoformat(),
        },
    }
    
    # Insert record into MongoDB
    collection.insert_one(record)
