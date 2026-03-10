document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.getElementById('login-form');
    const registerForm = document.getElementById('register-form');

    if (loginForm) {
        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;
            const errorDiv = document.getElementById('login-error');
            const submitBtn = loginForm.querySelector('button');

            submitBtn.disabled = true;
            submitBtn.textContent = 'Logging in...';
            errorDiv.style.display = 'none';

            try {
                const response = await fetch('/api/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ username, password })
                });

                const data = await response.json();

                if (response.ok && data.token) {
                    localStorage.setItem('authToken', data.token);
                    window.location.href = '/';
                } else {
                    errorDiv.textContent = data.error || 'Login failed';
                    errorDiv.style.display = 'block';
                }
            } catch (error) {
                errorDiv.textContent = 'Network error. Please try again.';
                errorDiv.style.display = 'block';
            } finally {
                submitBtn.disabled = false;
                submitBtn.textContent = 'Login';
            }
        });
    }

    if (registerForm) {
        registerForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const username = document.getElementById('username').value;
            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;
            const errorDiv = document.getElementById('register-error');
            const successDiv = document.getElementById('register-success');
            const submitBtn = registerForm.querySelector('button');

            submitBtn.disabled = true;
            submitBtn.textContent = 'Registering...';
            errorDiv.style.display = 'none';
            successDiv.style.display = 'none';

            let response;
            try {
                response = await fetch('/api/register', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ username, email, password })
                });

                const data = await response.json();

                if (response.ok) {
                    successDiv.textContent = 'Registration successful! Redirecting to login...';
                    successDiv.style.display = 'block';
                    setTimeout(() => {
                        window.location.href = '/login';
                    }, 2000);
                } else {
                    errorDiv.textContent = data.error || 'Registration failed';
                    errorDiv.style.display = 'block';
                }
            } catch (error) {
                errorDiv.textContent = 'Network error. Please try again.';
                errorDiv.style.display = 'block';
            } finally {
                if (!response || !response.ok) {
                    submitBtn.disabled = false;
                    submitBtn.textContent = 'Register';
                }
            }
        });
    }
});
