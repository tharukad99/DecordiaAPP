document.addEventListener('DOMContentLoaded', () => {
    // Auth Check
    const token = localStorage.getItem('authToken');
    if (!token) {
        window.location.href = '/login';
        return;
    }

    // User Menu Toggle
    const userMenuBtn = document.getElementById('user-menu-btn');
    const dropdownMenu = document.getElementById('dropdown-menu');

    if (userMenuBtn && dropdownMenu) {
        userMenuBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            dropdownMenu.style.display = dropdownMenu.style.display === 'none' ? 'flex' : 'none';
        });

        // Close dropdown when clicking outside
        document.addEventListener('click', () => {
            dropdownMenu.style.display = 'none';
        });
    }

    // Settings Modal Logic
    const settingsBtn = document.getElementById('settings-btn');
    const settingsModal = document.getElementById('settings-modal');
    const closeModalBtn = document.getElementById('close-modal-btn');
    const settingsForm = document.getElementById('settings-form');
    const userApiKeyInput = document.getElementById('user-api-key');
    const settingsMessage = document.getElementById('settings-message');

    if (settingsBtn && settingsModal) {
        settingsBtn.addEventListener('click', async () => {
            settingsModal.style.display = 'flex';
            settingsMessage.textContent = 'Loading your key...';
            settingsMessage.style.color = 'var(--text-color)';

            // Try fetching the existing key from backend
            try {
                const response = await fetch('/api/user/key', {
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                if (response.ok) {
                    const data = await response.json();
                    if (data.api_key) {
                        userApiKeyInput.value = data.api_key;
                        settingsMessage.textContent = 'Existing key loaded.';
                        settingsMessage.style.color = 'green';
                    } else {
                        userApiKeyInput.value = '';
                        settingsMessage.textContent = 'No key saved. Using default global key if available.';
                        settingsMessage.style.color = 'orange';
                    }
                } else {
                    settingsMessage.textContent = 'Could not load key.';
                    settingsMessage.style.color = 'red';
                }
            } catch (err) {
                console.error("Failed to load key", err);
                settingsMessage.textContent = 'Failed to load key.';
                settingsMessage.style.color = 'red';
            }
        });

        closeModalBtn.addEventListener('click', () => {
            settingsModal.style.display = 'none';
        });
    }

    if (settingsForm) {
        settingsForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const newKey = userApiKeyInput.value.trim();
            const submitBtn = settingsForm.querySelector('button');
            submitBtn.disabled = true;
            settingsMessage.textContent = 'Saving...';
            settingsMessage.style.color = 'var(--text-color)';

            try {
                const response = await fetch('/api/user/key', {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ api_key: newKey })
                });

                if (response.ok) {
                    settingsMessage.textContent = 'API Key saved successfully!';
                    settingsMessage.style.color = 'green';
                    setTimeout(() => { settingsModal.style.display = 'none'; }, 1500);
                } else {
                    const data = await response.json();
                    settingsMessage.textContent = data.error || 'Failed to save key.';
                    settingsMessage.style.color = 'red';
                }
            } catch (err) {
                settingsMessage.textContent = 'Network error saving key.';
                settingsMessage.style.color = 'red';
            } finally {
                submitBtn.disabled = false;
            }
        });
    }

    // Logout logic
    const logoutBtn = document.getElementById('logout-btn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', () => {
            localStorage.removeItem('authToken');
            window.location.href = '/login';
        });
    }

    let elementCount = 1;

    // 1. Setup Event Delegation for dynamic radio toggling
    document.body.addEventListener('change', (e) => {
        if (e.target.matches('input[type="radio"]')) {
            const groupWrapper = e.target.closest('.grid-col');
            // Check if it belongs to a specific element box or background
            const contextContainer = e.target.closest('.element-box') || groupWrapper;

            // Re-apply disabled state to all within the specific context
            const radiosInContext = contextContainer.querySelectorAll(`input[name="${e.target.name}"]`);

            radiosInContext.forEach(radio => {
                const optionGroup = radio.closest('.option-group');
                const fileInput = optionGroup.querySelector('input[type="file"]');
                const textInput = optionGroup.querySelector('textarea');

                if (radio.checked) {
                    if (radio.value === 'image') {
                        if (fileInput) fileInput.disabled = false;
                        if (textInput) textInput.disabled = true;
                    } else {
                        if (fileInput) fileInput.disabled = true;
                        if (textInput) textInput.disabled = false;
                    }
                }
            });
        }
    });

    // 2. Add New Element block logic
    const elementsList = document.getElementById('elements-list');
    document.getElementById('add-element-btn').addEventListener('click', () => {
        elementCount++;
        const newEl = document.createElement('div');
        newEl.className = 'element-box';
        newEl.dataset.id = elementCount;
        newEl.innerHTML = `
            <h4>#${elementCount}</h4>
            <div class="option-group">
                <label class="radio-label">
                    <input type="radio" name="el${elementCount}_choice" value="image" checked>
                    <span class="radio-custom"></span>
                    Image Upload
                </label>
                <div class="input-wrapper">
                    <input type="file" id="el${elementCount}-file" name="el${elementCount}_file" accept="image/*" class="styled-input">
                </div>
            </div>
            <div class="option-group">
                <label class="radio-label">
                    <input type="radio" name="el${elementCount}_choice" value="text">
                    <span class="radio-custom"></span>
                    Text description
                </label>
                <div class="input-wrapper">
                    <textarea id="el${elementCount}-text" name="el${elementCount}_text" rows="3" class="styled-input" placeholder="Element details" disabled></textarea>
                </div>
            </div>
        `;
        elementsList.appendChild(newEl);
    });

    // 3. Form Submission API Logic
    const form = document.getElementById('image-form');
    const btn = document.getElementById('generate-btn');
    const btnText = btn.querySelector('.btn-text');
    const loader = btn.querySelector('.loader');

    const emptyState = document.getElementById('empty-state');
    const resultImage = document.getElementById('result-image');
    const errorMessage = document.getElementById('error-message');
    const resultActions = document.getElementById('result-actions');
    const downloadBtn = document.getElementById('download-btn');

    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        // Loading states
        btn.disabled = true;
        btnText.textContent = 'Synthesizing...';
        loader.style.display = 'inline-block';

        emptyState.style.display = 'none';
        resultImage.style.display = 'none';
        errorMessage.style.display = 'none';
        resultActions.style.display = 'none';

        // Data Collection
        let prompts = [];
        const formObj = new FormData(form);

        // Capture texts
        const masterPrompt = formObj.get('master_prompt');
        if (masterPrompt && masterPrompt.trim()) prompts.push(masterPrompt.trim());

        const bgChoice = formObj.get('bg_choice');
        if (bgChoice === 'text') {
            const bgText = formObj.get('bg_text');
            if (bgText && bgText.trim()) prompts.push("Background: " + bgText.trim());
        }

        const timeOfDay = formObj.get('time_of_day');
        if (timeOfDay) prompts.push("time of day: " + timeOfDay);

        const lighting = formObj.get('lighting_effects');
        if (lighting) prompts.push("lighting: " + lighting);

        const dressing = formObj.get('other_dressings');
        if (dressing) prompts.push("scene dressing: " + dressing);

        // Elements text
        for (let i = 1; i <= elementCount; i++) {
            if (formObj.get(`el${i}_choice`) === 'text') {
                // Must un-disable text area to read it from FormData, or read it explicitly
                const elTextNode = document.getElementById(`el${i}-text`);
                if (elTextNode && elTextNode.value.trim()) {
                    prompts.push(elTextNode.value.trim());
                }
            }
        }

        const finalPrompt = prompts.join(", ") || "Create a cinematic scene";

        // Capture files
        let imageFiles = [];
        if (bgChoice === 'image') {
            const bgFile = document.getElementById('bg-file').files[0];
            if (bgFile) imageFiles.push(bgFile);
        } else if (bgChoice === 'text') {
            btnText.textContent = 'Generating Background...';
            const bgDesc = formObj.get('bg_text') || '';
            const genPrompt = `Background: ${bgDesc}. Global context: ${finalPrompt}`.trim();

            const token = localStorage.getItem('authToken');
            const genRes = await fetch('/api/generate-image', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ prompt: genPrompt || "Cinematic blank scene" })
            });

            const genData = await genRes.json();

            if (!genRes.ok) {
                let errObj = "Background generation failed";
                if (genData.details && genData.details.error && genData.details.error.message) {
                    errObj = genData.details.error.message;
                } else if (genData.error) {
                    errObj = typeof genData.error === 'string' ? genData.error : JSON.stringify(genData.error);
                }
                throw new Error("Generator API: " + errObj);
            }

            if (genData.data && genData.data[0] && genData.data[0].b64_json) {
                const b64Data = genData.data[0].b64_json;
                // Convert base64 to File object using a lightweight blob fetch
                const resBase64 = await fetch("data:image/png;base64," + b64Data);
                const blob = await resBase64.blob();
                const genFile = new File([blob], "generated_background.png", { type: "image/png" });

                imageFiles.push(genFile);
            } else {
                throw new Error("Generator API did not return a valid base64 image.");
            }

            btnText.textContent = 'Composing...';
        }

        for (let i = 1; i <= elementCount; i++) {
            const elChoice = document.querySelector(`input[name="el${i}_choice"]:checked`);
            if (elChoice && elChoice.value === 'image') {
                const elFile = document.getElementById(`el${i}-file`).files[0];
                if (elFile) imageFiles.push(elFile);
            } else if (elChoice && elChoice.value === 'text') {
                btnText.textContent = `Generating Element #${i}...`;
                const elTextNode = document.getElementById(`el${i}-text`);
                const elDesc = elTextNode ? elTextNode.value.trim() : '';
                const genPrompt = `Element: ${elDesc}. Global context: ${finalPrompt}`.trim();

                const token = localStorage.getItem('authToken');
                const genRes = await fetch('/api/generate-image', {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ prompt: genPrompt || "A solitary visual element on transparent background" })
                });

                const genData = await genRes.json();

                if (!genRes.ok) {
                    let errObj = `Element #${i} generation failed`;
                    if (genData.details && genData.details.error && genData.details.error.message) {
                        errObj = genData.details.error.message;
                    } else if (genData.error) {
                        errObj = typeof genData.error === 'string' ? genData.error : JSON.stringify(genData.error);
                    }
                    throw new Error("Generator API: " + errObj);
                }

                if (genData.data && genData.data[0] && genData.data[0].b64_json) {
                    const b64Data = genData.data[0].b64_json;
                    const resBase64 = await fetch("data:image/png;base64," + b64Data);
                    const blob = await resBase64.blob();
                    const genFile = new File([blob], `generated_element_${i}.png`, { type: "image/png" });

                    imageFiles.push(genFile);
                } else {
                    throw new Error(`Generator API did not return a valid base64 image for Element #${i}.`);
                }

                btnText.textContent = 'Composing...';
            }
        }

        // Validate strictly 2 files
        if (imageFiles.length !== 2) {
            errorMessage.textContent = `API requires exactly 2 images (You selected ${imageFiles.length}). Please upload exactly 1 Background image and 1 Element image.`;
            errorMessage.style.display = 'block';
            emptyState.style.display = 'flex';
            btn.disabled = false;
            btnText.textContent = 'Create';
            loader.style.display = 'none';
            return;
        }

        // Create the NEW form data exactly the way your API requires:
        const payload = new FormData();
        payload.append('prompt', finalPrompt);

        const resultQuality = formObj.get('result_quality') || 'low';
        payload.append('quality', resultQuality);

        imageFiles.forEach(img => {
            payload.append('image[]', img);
        });

        try {
            // Forward to the NEW mapped API Endpoint you requested!
            const token = localStorage.getItem('authToken');
            const response = await fetch('/api/edit-image', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`
                },
                body: payload
            });

            const data = await response.json();

            // Error Checking
            if (!response.ok) {
                let apiErrorObj = 'Unknown rendering error occurred';
                if (data.details && data.details.error && data.details.error.message) {
                    apiErrorObj = data.details.error.message;
                } else if (data.error) {
                    apiErrorObj = typeof data.error === 'string' ? data.error : JSON.stringify(data.error);
                }
                throw new Error(apiErrorObj);
            }

            // Success Mapping
            if (data.data && data.data[0]) {
                const imgData = data.data[0];
                let encodedSrc = imgData.b64_json ? 'data:image/png;base64,' + imgData.b64_json : imgData.url;

                resultImage.src = encodedSrc;
                resultImage.style.display = 'block';
                resultActions.style.display = 'block';

                downloadBtn.onclick = () => {
                    const tempAnchor = document.createElement('a');
                    tempAnchor.href = encodedSrc;
                    tempAnchor.download = `decordia-${Date.now()}.png`;
                    document.body.appendChild(tempAnchor);
                    tempAnchor.click();
                    document.body.removeChild(tempAnchor);
                };
            } else {
                throw new Error("Invalid output format received from API server");
            }

        } catch (error) {
            console.error("Task Failed:", error);
            errorMessage.textContent = error.message;
            errorMessage.style.display = 'block';
            emptyState.style.display = 'flex';
        } finally {
            // Restore UI Buttons
            btn.disabled = false;
            btnText.textContent = 'Create';
            loader.style.display = 'none';
        }
    });
});
