import requests
import os
import glob
from sentence_transformers import SentenceTransformer
import subprocess
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Dict, Any

MODELFILE = """
FROM qwen2.5:0.5b

PARAMETER temperature 0.1

#System prompt
SYSTEM \"""You are a helpful assistant that answers questions based on the provided context.
Always prioritize information from the context when answering.
If the context doesn't contain relevant information to answer the question, acknowledge this limitation.
Do not make up information that isn't supported by the context.
Always cite the source file when providing information.\"""
"""

class RAGapp:
    def __init__(self, base_model='qwen2.5:0.5b', custom_model_name='ipn-assistant', embedding_model='all-MiniLM-L6-v2', texts_dir='./texts/'):
        self.base_model = base_model
        self.custom_model_name = custom_model_name
        self.texts_dir = texts_dir
        self.embedding_model = SentenceTransformer(embedding_model)

        self.document_store ={}
        self.embeddings = {}

        self.create_custom_model()
        self.load_texts()

    def create_custom_model(self):
        print(f'Creating custom model in Ollama: {self.custom_model_name}...')

        print(MODELFILE)
        with open('modelfile', 'w') as f:
            f.write(MODELFILE)

        try:
            response = requests.get(f"http://localhost:11434/api/tags")
            if response.status_code == 200:
                existing_models = [model["name"] for model in response.json().get("models", [])]
                if self.custom_model_name in existing_models:
                    print(f"Model '{self.custom_model_name}' already exists, skipping creation.")
                    return

            result = subprocess.run(
                ['ollama', 'create', self.custom_model_name, '-f', './modelfile'],
                text=True,
            )

            if result.returncode == 0:
                print(f"Model '{self.custom_model_name}' created successfully.")
            else:
                print(f"Error creating model '{self.custom_model_name}'")
                self.custom_model_name = self.base_model

        except Exception as e:
            print(f"Error creating model '{self.custom_model_name}': {e}")
            self.custom_model_name = self.base_model

        if os.path.exists('modelfile'):
            os.remove('modelfile')

    def load_texts(self):
        text_files = glob.glob(os.path.join(self.texts_dir, "*.txt"))

        if not text_files:
            print(f"No text files found in '{self.texts_dir}'.")
            return

        print(f"Loading {len(text_files)} text files...")

        for file_path in text_files:
            file_name = os.path.basename(file_path)

            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            chunks = [chunk.strip() for chunk in content.split('\n\n') if chunk.strip()]

            self.document_store[file_name] = chunks

            chunk_embeddings = self.embedding_model.encode(chunks)
            self.embeddings[file_name] = chunk_embeddings

        print(f"Loaded {sum(len(chunks) for chunks in self.document_store.values())} text chunks from {len(text_files)} files")

    def retrieve(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Retrieve the most relevant text chunks for a query.

        Args:
            query: The user query
            top_k: Number of top results to return

        Returns:
            List of dictionaries containing retrieved chunks and metadata
        """
        if not self.document_store:
            return []

        query_embedding = self.embedding_model.encode([query])[0]

        results = []

        for file_name, chunk_embeddings in self.embeddings.items():
            chunks = self.document_store[file_name]
            for i, chunk_embedding in enumerate(chunk_embeddings):
                similarity = cosine_similarity([query_embedding], [chunk_embedding])[0][0]
                results.append({
                    "file": file_name,
                    "chunk": chunks[i],
                    "similarity": similarity
                })
        results.sort(key=lambda x: x["similarity"], reverse=True)
        return results[:top_k]

    def generate(self, prompt: str) -> str:
        """
        Generate a response using Ollama.

        Args:
            prompt: The prompt to send to Ollama

        Returns:
            Generated response from Ollama
        """
        try:
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": self.custom_model_name,
                    "prompt": prompt,
                    "stream": False
                }
            )

            if response.status_code == 200:
                return response.json().get("response", "")
            else:
                return f"Error: Failed to generate response. Status code: {response.status_code}"

        except Exception as e:
            return f"Error: {str(e)}"

    def query(self, user_question: str) -> str:
        """
        Process a user query through the RAG pipeline.

        Args:
            user_question: The user's question

        Returns:
            Final response from the model
        """
        retrieved_chunks = self.retrieve(user_question)
        if not retrieved_chunks:
            return self.generate(user_question)

        context = "\n\n".join([f"From {chunk['file']}:\n{chunk['chunk']}" for chunk in retrieved_chunks])
        augmented_prompt = f"""Answer the question based on the following context:

Context:
{context}

Question: {user_question}

Answer:"""

        response = self.generate(augmented_prompt)
        return response