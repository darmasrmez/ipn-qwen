document.addEventListener('DOMContentLoaded', function() {
    // Elements
    const chatContainer = document.getElementById('chat-container');
    const questionInput = document.getElementById('question-input');
    const askButton = document.getElementById('ask-button');
    const uploadForm = document.getElementById('upload-form');
    const documentsList = document.getElementById('documents-list');
    const showSourcesSwitch = document.getElementById('show-sources-switch');
    
    // Load available documents
    fetchDocuments();
    
    // Event listeners
    askButton.addEventListener('click', askQuestion);
    questionInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            askQuestion();
        }
    });

    // Functions
    function askQuestion() {
        const question = questionInput.value.trim();
        if (!question) return;
        
        // Add user message to chat
        addMessage(question, 'user');
        
        // Clear input
        questionInput.value = '';
        
        // Show loading indicator
        const loadingMsgId = addMessage('Thinking...', 'system');
        
        // Send to API
        fetch('/api/query', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                question: question,
                show_sources: showSourcesSwitch.checked
            })
        })
        .then(response => response.json())
        .then(data => {
            // Remove loading message
            document.getElementById(loadingMsgId).remove();
            
            // Add AI response to chat
            const answer = data.answer || 'Sorry, I could not find an answer.';
            
            // Format the response with markdown
            const formattedAnswer = marked.parse(answer);
            
            // Create AI message element
            const messageElement = document.createElement('div');
            messageElement.className = 'ai-message';
            
            // Add the answer with markdown formatting
            const answerElement = document.createElement('div');
            answerElement.className = 'answer-content';
            answerElement.innerHTML = formattedAnswer;
            messageElement.appendChild(answerElement);
            
            // Add sources if available
            if (data.sources && data.sources.length > 0 && showSourcesSwitch.checked) {
                const sourcesElement = document.createElement('div');
                sourcesElement.className = 'source-reference';
                
                const sourcesTitle = document.createElement('div');
                sourcesTitle.innerText = 'Sources:';
                sourcesTitle.style.fontWeight = 'bold';
                sourcesTitle.style.marginBottom = '5px';
                sourcesElement.appendChild(sourcesTitle);
                
                data.sources.forEach(source => {
                    const sourceItem = document.createElement('div');
                    sourceItem.className = 'source-item';
                    
                    const sourceFile = document.createElement('div');
                    sourceFile.className = 'source-file';
                    sourceFile.innerText = source.file;
                    
                    const similarity = document.createElement('span');
                    similarity.className = 'similarity';
                    similarity.innerText = `Similarity: ${source.similarity}`;
                    
                    sourceFile.appendChild(similarity);
                    sourceItem.appendChild(sourceFile);
                    
                    const sourceText = document.createElement('div');
                    sourceText.className = 'source-text';
                    sourceText.innerText = source.text;
                    sourceItem.appendChild(sourceText);
                    
                    sourcesElement.appendChild(sourceItem);
                });
                
                messageElement.appendChild(sourcesElement);
            }
            
            chatContainer.appendChild(messageElement);
            scrollToBottom();
        })
        .catch(error => {
            // Remove loading message
            document.getElementById(loadingMsgId).remove();
            
            // Show error
            addMessage('Error: Could not get a response. Please make sure Ollama is running.', 'system');
            console.error('Error:', error);
        });
    }
    
    function addMessage(text, type) {
        const messageId = 'msg-' + Date.now();
        const messageElement = document.createElement('div');
        messageElement.className = type + '-message';
        messageElement.id = messageId;
        messageElement.innerText = text;
        
        chatContainer.appendChild(messageElement);
        scrollToBottom();
        
        return messageId;
    }
    
    function scrollToBottom() {
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }
    
    function uploadDocument() {
        const fileInput = document.getElementById('document-file');
        const file = fileInput.files[0];
        
        if (!file) {
            alert('Please select a file to upload');
            return;
        }
        
        if (!file.name.endsWith('.txt')) {
            alert('Only .txt files are supported');
            return;
        }
        
        const formData = new FormData();
        formData.append('file', file);
        
        // Show loading message
        addMessage(`Uploading ${file.name}...`, 'system');
        
        fetch('/api/upload', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                addMessage(`Successfully uploaded ${file.name}!`, 'system');
                fileInput.value = ''; // Clear file input
                fetchDocuments(); // Refresh document list
            } else {
                addMessage(`Error: ${data.error}`, 'system');
            }
        })
        .catch(error => {
            addMessage('Error uploading file. Please try again.', 'system');
            console.error('Error:', error);
        });
    }

    function fetchDocuments() {
        fetch('/api/docs')
            .then(response => response.json())
            .then(data => {
                documentsList.innerHTML = ''; // Clear list

                if (data.documents && data.documents.length > 0) {
                    data.documents.forEach(doc => {
                        const listItem = document.createElement('li');
                        listItem.className = 'list-group-item';
                        listItem.innerText = doc;
                        documentsList.appendChild(listItem);
                    });
                } else {
                    const emptyItem = document.createElement('li');
                    emptyItem.className = 'list-group-item text-center text-muted';
                    emptyItem.innerText = 'No documents loaded';
                    documentsList.appendChild(emptyItem);
                }
            })
            .catch(error => {
                console.error('Error fetching documents:', error);
            });
    }
});