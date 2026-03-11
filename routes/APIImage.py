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

import base64
import uuid

ALLOWED_QUALITIES = {"low", "medium", "high", "auto"}
ALLOWED_SIZES = {"1024x1024", "1024x1536", "1536x1024", "auto"}
ALLOWED_MIME_TYPES = {"image/png", "image/jpeg", "image/jpg", "image/webp"}


@api_image_bp.route("/api/edit-image-multiple", methods=["POST"])
@token_required
def edit_image_multiple(current_user_id):
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
            return jsonify({
                "success": False,
                "error": "Please add your API Key in Settings to generate images."
            }), 400
        
        api_key = row.ApiKey

        # 1. Read form-data text fields
        prompt = request.form.get("prompt", "").strip()
        model = request.form.get("model", "gpt-image-1").strip()
        quality = request.form.get("quality", "low").strip().lower()
        size = request.form.get("size", "1024x1024").strip().lower()

        if not prompt:
            return jsonify({
                "success": False,
                "error": "Missing 'prompt'"
            }), 400

        if quality not in ALLOWED_QUALITIES:
            return jsonify({
                "success": False,
                "error": f"Invalid quality: {quality}"
            }), 400

        if size not in ALLOWED_SIZES:
            return jsonify({
                "success": False,
                "error": f"Invalid size: {size}"
            }), 400

        # 2. Read uploaded files
        images = request.files.getlist("image[]")
        if not images:
            images = request.files.getlist("image")

        images = [img for img in images if img and img.filename]

        if len(images) < 1 or len(images) > 10:
            return jsonify({
                "success": False,
                "error": f"You must upload between 1 and 10 images. Received: {len(images)}"
            }), 400

        for img in images:
            if img.mimetype not in ALLOWED_MIME_TYPES:
                return jsonify({
                    "success": False,
                    "error": f"Unsupported file type: {img.filename} ({img.mimetype})"
                }), 400

        # 3. Prepare OpenAI request
        headers = {
            "Authorization": f"Bearer {api_key}"
        }

        data = {
            "model": model,
            "prompt": prompt,
            "quality": quality,
            "size": size,
            "n": "1"
        }

        files = []
        for img in images:
            img.stream.seek(0)
            files.append(
                (
                    "image[]",
                    (
                        img.filename,
                        img.stream,
                        img.mimetype
                    )
                )
            )

        # 4. Send request to OpenAI
        response = requests.post(
            OPENAI_URL,
            headers=headers,
            data=data,
            files=files,
            timeout=180
        )

        # 5. Parse response
        try:
            result_json = response.json()
        except Exception:
            return jsonify({
                "success": False,
                "status_code": response.status_code,
                "error": "OpenAI returned non-JSON response",
                "raw_response": response.text
            }), response.status_code

        if response.status_code != 200:
            return jsonify({
                "success": False,
                "status_code": response.status_code,
                "openai_error": result_json
            }), response.status_code

        output = {
            "success": True,
            "status_code": response.status_code,
            "input_image_count": len(images),
            "openai_response": result_json
        }

        # 6. Parse and return final response
        if "data" in result_json and len(result_json["data"]) > 0:
            first = result_json["data"][0]

            if "b64_json" in first:
                output["image_base64"] = first["b64_json"]

            if "url" in first:
                output["image_url"] = first["url"]

            if "revised_prompt" in first:
                output["revised_prompt"] = first["revised_prompt"]

        return jsonify(output), 200

    except requests.exceptions.Timeout:
        return jsonify({
            "success": False,
            "error": "OpenAI request timed out"
        }), 504

    except Exception as e:
        return jsonify({
            "success": False,
            "error": "Internal server error",
            "details": str(e)
        }), 500

















