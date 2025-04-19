document.addEventListener('DOMContentLoaded', function() {
    // Get form elements
    const queryForm = document.getElementById('queryForm');
    const queryInput = document.getElementById('queryInput');
    const apiKeyInput = document.getElementById('apiKeyInput');
    const toggleApiKey = document.getElementById('toggleApiKey');
    const topkSelector = document.getElementById('topkSelector');
    
    // Get results elements
    const resultsCard = document.getElementById('resultsCard');
    const loadingIndicator = document.getElementById('loadingIndicator');
    const resultsContent = document.getElementById('resultsContent');
    const answerText = document.getElementById('answerText');
    const sourcesList = document.getElementById('sourcesList');
    const errorDisplay = document.getElementById('errorDisplay');
    
    // Toggle API key visibility
    if (toggleApiKey) {
        toggleApiKey.addEventListener('click', function() {
            const type = apiKeyInput.getAttribute('type');
            if (type === 'password') {
                apiKeyInput.setAttribute('type', 'text');
                toggleApiKey.innerHTML = '<i data-feather="eye-off"></i>';
            } else {
                apiKeyInput.setAttribute('type', 'password');
                toggleApiKey.innerHTML = '<i data-feather="eye"></i>';
            }
            feather.replace();
        });
    }
    
    // Add event listener to form submission
    queryForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        // Get the query text
        const queryText = queryInput.value.trim();
        
        // Validate query
        if (!queryText) {
            showError('Please enter a question.');
            return;
        }
        
        // Get the API key (if provided)
        const apiKey = apiKeyInput ? apiKeyInput.value.trim() : '';
        
        // Get number of chunks to retrieve
        const topK = parseInt(topkSelector.value, 10);
        
        // Show loading state
        showLoading(true);
        
        // Prepare request data
        const requestData = {
            query: queryText,
            top_k: topK
        };
        
        // Add API key if provided
        if (apiKey) {
            requestData.api_key = apiKey;
        }
        
        // Make API request
        fetch('/query', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestData),
        })
        .then(response => {
            if (!response.ok) {
                // Handle HTTP errors
                return response.json().then(data => {
                    throw new Error(data.error || `HTTP error! Status: ${response.status}`);
                });
            }
            return response.json();
        })
        .then(data => {
            // Display results
            displayResults(data);
        })
        .catch(error => {
            // Handle errors
            showError(error.message);
        })
        .finally(() => {
            // Hide loading indicator
            showLoading(false);
        });
    });
    
    // Function to display results
    function displayResults(data) {
        // Show the results card
        resultsCard.classList.remove('d-none');
        errorDisplay.classList.add('d-none');
        resultsContent.classList.remove('d-none');
        
        // Display the answer with Markdown formatting
        answerText.innerHTML = formatText(data.answer);
        
        // Display sources
        sourcesList.innerHTML = '';
        if (data.sources && data.sources.length > 0) {
            data.sources.forEach(source => {
                const sourceItem = document.createElement('a');
                sourceItem.href = source;
                sourceItem.target = '_blank';
                sourceItem.className = 'list-group-item list-group-item-action d-flex justify-content-between align-items-center';
                sourceItem.innerHTML = `
                    ${source}
                    <span><i data-feather="external-link"></i></span>
                `;
                sourcesList.appendChild(sourceItem);
            });
            // Re-initialize Feather icons
            feather.replace();
        } else {
            sourcesList.innerHTML = '<div class="list-group-item text-muted">No sources found</div>';
        }
        
        // Scroll to results
        resultsCard.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
    
    // Function to show error message
    function showError(message) {
        resultsCard.classList.remove('d-none');
        resultsContent.classList.add('d-none');
        errorDisplay.classList.remove('d-none');
        errorDisplay.textContent = message;
        
        // Scroll to error
        resultsCard.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
    
    // Function to toggle loading state
    function showLoading(isLoading) {
        if (isLoading) {
            loadingIndicator.classList.remove('d-none');
            resultsContent.classList.add('d-none');
            errorDisplay.classList.add('d-none');
            resultsCard.classList.remove('d-none');
        } else {
            loadingIndicator.classList.add('d-none');
        }
    }
    
    // Function to format text with basic markdown-like features
    function formatText(text) {
        // Handle line breaks
        let formattedText = text.replace(/\n\n/g, '</p><p>').replace(/\n/g, '<br>');
        
        // Wrap in paragraph
        formattedText = `<p>${formattedText}</p>`;
        
        // Handle bold text (between ** or __)
        formattedText = formattedText.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        formattedText = formattedText.replace(/__(.*?)__/g, '<strong>$1</strong>');
        
        // Handle italic text (between * or _)
        formattedText = formattedText.replace(/\*(.*?)\*/g, '<em>$1</em>');
        formattedText = formattedText.replace(/_(.*?)_/g, '<em>$1</em>');
        
        // Handle links (not handling full markdown link syntax)
        formattedText = formattedText.replace(/(https?:\/\/[^\s]+)/g, '<a href="$1" target="_blank">$1</a>');
        
        return formattedText;
    }
});
