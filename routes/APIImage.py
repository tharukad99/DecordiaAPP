import os
import requests
from flask import Blueprint, request, jsonify
from routes.auth import token_required, get_db_connection
from config import OPENAI_URL, OPENAI_GENERATE_URL

api_image_bp = Blueprint("api_image", __name__)


@api_image_bp.route('/api/generate-image', methods=['POST'])
@token_required
def generate_image(current_user_id):
    try:
        # Fetch user's custom API Key from database
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT ApiKey FROM UserApiKeys WHERE UserId = ?", (current_user_id,))
        row = cursor.fetchone()
        
        try:
            cursor.close()
            conn.close()
        except:
            pass

        if not row or not row.ApiKey:
            return jsonify({"error": "Please add your API Key in Settings to generate images."}), 400
        
        USER_API_KEY = row.ApiKey

        data = request.get_json()
        if not data:
            data = request.form

        prompt = data.get('prompt')
        if not prompt:
            return jsonify({"error": "Missing 'prompt' in request"}), 400

        headers = {
            "Authorization": f"Bearer {USER_API_KEY}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "dall-e-3",
            "prompt": prompt,
            "n": 1,
            "size": "1024x1024",
            "response_format": "b64_json"
        }

        print(f"Generating background image with DALL-E 3 for user {current_user_id}...")
        response = requests.post(OPENAI_GENERATE_URL, headers=headers, json=payload, timeout=180)
        
        try:
            return jsonify(response.json()), response.status_code
        except ValueError:
            return response.text, response.status_code

    except Exception as e:
        print("Error in generate_image:", str(e))
        return jsonify({"error": "Internal Server Error", "details": str(e)}), 500


@api_image_bp.route('/api/edit-image', methods=['POST'])
@token_required
def edit_image(current_user_id):
    try:
        # Fetch user's custom API Key from database
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT ApiKey FROM UserApiKeys WHERE UserId = ?", (current_user_id,))
        row = cursor.fetchone()
        
        try:
            cursor.close()
            conn.close()
        except:
            pass

        if not row or not row.ApiKey:
            return jsonify({"error": "Please add your API Key in Settings to generate images."}), 400
        
        USER_API_KEY = row.ApiKey

        # 1. Get prompt & quality from Postman's form-data
        prompt = request.form.get('prompt')
        quality = request.form.get('quality', 'low') # defaults to low if not passed
        
        if not prompt:
            return jsonify({"error": "Missing 'prompt' in form-data"}), 400

        # 2. Get ONLY images from Postman's form-data (Ensure exactly 2)
        images = request.files.getlist('image[]')
        if not images:
            images = request.files.getlist('image')
            
        if len(images) != 2:
            return jsonify({"error": f"You must upload exactly 2 images. You uploaded {len(images)}."}), 400

        # 3. Setup the headers for OpenAI API using the USER's API Key
        headers = {
            "Authorization": f"Bearer {USER_API_KEY}"
        }
        
        # 4. Use dynamic quality in the data payload
        data = {
            "model": "gpt-image-1",  # Hardcoded model here!
            "prompt": prompt,
            "quality": quality,      # Dynamic quality mapped to dropdown!
            "size": "1024x1024"      # Hardcoded size here!
        }
            
        # 5. Read files into format 'requests' understands
        files_payload = []
        for img in images:
            img_bytes = img.read()
            files_payload.append(('image[]', (img.filename, img_bytes, img.mimetype)))

        print(f"Forwarding {len(images)} images and prompt to OpenAI with hardcoded model details...")

        # 6. Forward the request to OpenAI
        response = requests.post(OPENAI_URL, headers=headers, data=data, files=files_payload, timeout=180)
        
        # 7. Return OpenAI's JSON response to Postman
        try:
            return jsonify(response.json()), response.status_code
        except ValueError:
            return response.text, response.status_code

    except Exception as e:
        print("Error:", str(e))
        return jsonify({"error": "Internal Server Error", "details": str(e)}), 500
