from RAG import RAGapp

def main():
    rag_app = RAGapp()
    print("RAG App with custom Ollama model initialized. Type 'exit' to quit.")

    while True:
        user_input = input("\nQuestion: ")

        if user_input.lower() == 'exit':
            print("Exiting...")
            break

        response = rag_app.query(user_input)
        print("\nAnswer:", response)

if __name__ == "__main__":
    main()