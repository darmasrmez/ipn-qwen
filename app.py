from RAG import RAGapp
from flask import Flask, request, jsonify, render_template, send_from_directory
import os

app = Flask(__name__, static_folder='static')
rag_app = RAGapp()


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/query', methods=['POST'])
def api_query():
    data = request.json
    question = data.get('question', '')

    if not question:
        return jsonify({"error": "No question provided"}), 400

    result = rag_app.query(question)
    return jsonify(result)

if __name__ == "__main__":

    print("Starting the RAG Web Application...")
    print("Make sure Ollama is running on http://localhost:11434")
    print("Place your text files in the 'texts' directory or upload them through the UI")
    app.run(debug=True, host='0.0.0.0', port=5000)