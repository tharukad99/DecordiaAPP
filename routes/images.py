import os
import requests
from flask import Blueprint, request, jsonify
from PIL import Image
from io import BytesIO

images_bp = Blueprint("images", __name__)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

@images_bp.route("/api/images/edit", methods=["POST"])
def edit_image():

    size = request.form.get("size", "1024x1024")
    dim = int(size.split("x")[0])

    # ---------- Build Prompt ----------
    prompts = []

    master_prompt = request.form.get("master_prompt", "").strip()
    if master_prompt:
        prompts.append(master_prompt)

    bg_text = request.form.get("bg_text", "").strip()
    if bg_text:
        prompts.append(f"Background: {bg_text}")

    time_of_day = request.form.get("time_of_day")
    lighting = request.form.get("lighting_effects")
    dressing = request.form.get("other_dressings")

    if time_of_day:
        prompts.append(f"time of day: {time_of_day}")

    if lighting:
        prompts.append(f"lighting: {lighting}")

    if dressing:
        prompts.append(f"scene dressing: {dressing}")

    num_elements = int(request.form.get("num_elements", 0))

    for i in range(1, num_elements + 1):
        txt = request.form.get(f"el{i}_text", "").strip()
        if txt:
            prompts.append(txt)

    prompt = ", ".join(prompts)

    if not prompt:
        prompt = "Create a cinematic scene"

    # ---------- Collect Uploaded Images ----------
    uploaded_images = []

    if "bg_file" in request.files and request.files["bg_file"].filename:
        uploaded_images.append(request.files["bg_file"])

    for i in range(1, num_elements + 1):
        key = f"el{i}_file"
        if key in request.files and request.files[key].filename:
            uploaded_images.append(request.files[key])

    # ---------- Create Base Canvas ----------
    base = Image.new("RGBA", (dim, dim), (255, 255, 255, 255))

    for index, file in enumerate(uploaded_images):

        img = Image.open(file.stream).convert("RGBA")

        if index == 0:
            img = img.resize((dim, dim))
            base.paste(img, (0, 0))
        else:
            img.thumbnail((dim // 2, dim // 2))

            x = (dim - img.width) // 2
            y = (dim - img.height) // 2

            base.paste(img, (x, y), img)

    # ---------- Convert to Bytes ----------
    buf_image = BytesIO()
    base.save(buf_image, format="PNG")
    buf_image.seek(0)

    # ---------- Transparent Mask ----------
    mask = Image.new("RGBA", (dim, dim), (0, 0, 0, 0))
    buf_mask = BytesIO()
    mask.save(buf_mask, format="PNG")
    buf_mask.seek(0)

    # ---------- Files for API ----------
    files = {
        "image": ("image.png", buf_image, "image/png"),
        "mask": ("mask.png", buf_mask, "image/png")
    }

    data = {
        "model": "dall-e-2",
        "prompt": prompt,
        "size": size,
        "response_format": "b64_json"
    }

    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}"
    }

    # --- DEBUGGING PRINT STATEMENTS ---
    print("\n[DEBUG] --- SENDING TO OPENAI ---")
    print(f"[DEBUG] URL: https://api.openai.com/v1/images/edits")
    print(f"[DEBUG] Prompt: {data.get('prompt')}")
    print(f"[DEBUG] Model: {data.get('model')}")
    print(f"[DEBUG] Total Image Files Attached: {len(files)}")
    print("[DEBUG] ---------------------------------\n")

    try:
        response = requests.post(
            "https://api.openai.com/v1/images/edits",
            headers=headers,
            data=data,
            files=files,
            timeout=120
        )
        
        # In case the response is not valid JSON
        try:
            resp_data = response.json()
        except Exception:
            return jsonify({"error": "Received an invalid response from OpenAI."}), 502

        return jsonify(resp_data), response.status_code
    
    except Exception as e:
        # Prevent HTML stack trace, return proper JSON error readable by Javascript
        return jsonify({"error": f"Backend processing error: {str(e)}"}), 500