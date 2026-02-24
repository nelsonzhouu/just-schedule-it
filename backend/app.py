from flask import Flask, request, jsonify
from flask_cors import CORS
from config import Config

# Initialize Flask app
app = Flask(__name__)

# Load configuration
app.config.from_object(Config)

# Enable CORS for cross-origin requests from frontend
CORS(app, origins=Config.CORS_ORIGINS)

@app.route('/api/message', methods=['POST'])
def handle_message():
    """
    Handle incoming messages from the frontend.
    For Phase 1, this simply echoes back the message.

    Expected JSON payload:
    {
        "message": "user's message here"
    }

    Returns:
    {
        "success": true,
        "response": "Echo: user's message here"
    }
    """
    try:
        # Get JSON data from request
        data = request.get_json()

        # Validate that message field exists
        if not data or 'message' not in data:
            return jsonify({
                'success': False,
                'error': 'Message field is required'
            }), 400

        user_message = data['message']

        # Phase 1: Simple echo response
        # Future: This is where we'll integrate Groq API and Google Calendar
        response_message = f"Echo: {user_message}"

        return jsonify({
            'success': True,
            'response': response_message
        }), 200

    except Exception as e:
        # Log error (in production, use proper logging)
        print(f"Error processing message: {str(e)}")

        return jsonify({
            'success': False,
            'error': 'An error occurred processing your message'
        }), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'message': 'JustScheduleIt backend is running'
    }), 200

if __name__ == '__main__':
    print(f"Starting Flask server on port {Config.PORT}...")
    print(f"Environment: {Config.FLASK_ENV}")
    print(f"CORS enabled for: {Config.CORS_ORIGINS}")

    app.run(
        host='0.0.0.0',
        port=Config.PORT,
        debug=Config.DEBUG
    )
