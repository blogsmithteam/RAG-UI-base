import os
import logging
from flask import Flask, request, jsonify, render_template
from rag import retrieve_and_generate_answer

# Configure logging for debugging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create the Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")

@app.route('/')
def index():
    """Render the main webpage with the query interface."""
    return render_template('index.html')

@app.route("/query", methods=["POST"])
def query():
    """API endpoint to process RAG queries."""
    try:
        # Get JSON data from request
        data = request.get_json()
        
        # Extract query text
        query_text = data.get("query", "")
        if not query_text:
            return jsonify({"error": "Missing query parameter"}), 400
            
        # Get the top_k parameter (default to 5 if not provided)
        top_k = data.get("top_k", 5)
        
        # Process the query through the RAG system
        answer, sources = retrieve_and_generate_answer(query_text, top_k)
        
        # Return the answer and sources
        return jsonify({
            "answer": answer,
            "sources": list(sources)
        })
        
    except Exception as e:
        logger.exception("Error processing query")
        return jsonify({"error": str(e)}), 500

# Health check endpoint
@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint for monitoring."""
    return jsonify({"status": "healthy"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
