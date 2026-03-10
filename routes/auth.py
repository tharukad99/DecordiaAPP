import os
import pyodbc
import jwt
import datetime
from functools import wraps
from flask import Blueprint, request, jsonify, render_template

auth_bp = Blueprint("auth", __name__)

from config import DB_CONNECTION_STRING, JWT_SECRET_KEY

def get_db_connection():
    return pyodbc.connect(DB_CONNECTION_STRING)

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]

        if not token:
            return jsonify({'error': 'Token is missing!'}), 401
        
        try:
            data = jwt.decode(token, JWT_SECRET_KEY, algorithms=["HS256"])
            current_user_id = data['user_id']
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token has expired!'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Token is invalid!'}), 401

        return f(current_user_id, *args, **kwargs)
    return decorated

@auth_bp.route('/login', methods=['GET'])
def login_page():
    return render_template('login.html')

@auth_bp.route('/register', methods=['GET'])
def register_page():
    return render_template('register.html')

@auth_bp.route('/api/register', methods=['POST'])
def register():
    from werkzeug.security import generate_password_hash
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if not username or not email or not password:
        return jsonify({'error': 'Missing required fields'}), 400

    hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT Id FROM Users WHERE Username = ? OR Email = ?", (username, email))
        if cursor.fetchone():
            return jsonify({'error': 'User with this username or email already exists'}), 409

        cursor.execute(
            "INSERT INTO Users (Username, Email, PasswordHash) VALUES (?, ?, ?)",
            (username, email, hashed_password)
        )
        conn.commit()
    except Exception as e:
        return jsonify({'error': 'Database error', 'details': str(e)}), 500
    finally:
        try:
            cursor.close()
            conn.close()
        except:
            pass

    return jsonify({'message': 'User registered successfully!'}), 201

@auth_bp.route('/api/login', methods=['POST'])
def login():
    from werkzeug.security import check_password_hash
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'error': 'Missing username or password'}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT Id, PasswordHash FROM Users WHERE Username = ?", (username,))
        user = cursor.fetchone()
    except Exception as e:
        return jsonify({'error': 'Database error', 'details': str(e)}), 500
    finally:
        try:
            cursor.close()
            conn.close()
        except:
            pass

    if user and check_password_hash(user.PasswordHash, password):
        token = jwt.encode({
            'user_id': user.Id,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
        }, JWT_SECRET_KEY, algorithm="HS256")

        return jsonify({'token': token, 'message': 'Login successful'}), 200
    else:
        return jsonify({'error': 'Invalid username or password'}), 401


@auth_bp.route('/api/user/key', methods=['GET', 'POST'])
@token_required
def manage_api_key(current_user_id):
    if request.method == 'GET':
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT ApiKey FROM UserApiKeys WHERE UserId = ?", (current_user_id,))
            row = cursor.fetchone()
            if row:
                return jsonify({"api_key": row.ApiKey}), 200
            else:
                return jsonify({"api_key": None}), 200
        except Exception as e:
            return jsonify({'error': 'Database error', 'details': str(e)}), 500
        finally:
            try:
                cursor.close()
                conn.close()
            except:
                pass

    if request.method == 'POST':
        data = request.get_json()
        new_key = data.get('api_key')
        
        if not new_key:
            return jsonify({'error': 'No API key provided'}), 400

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Check if key exists for user
            cursor.execute("SELECT Id FROM UserApiKeys WHERE UserId = ?", (current_user_id,))
            row = cursor.fetchone()
            
            if row:
                # Update existing
                cursor.execute(
                    "UPDATE UserApiKeys SET ApiKey = ?, UpdatedAt = GETDATE() WHERE UserId = ?", 
                    (new_key, current_user_id)
                )
            else:
                # Insert new
                cursor.execute(
                    "INSERT INTO UserApiKeys (UserId, ApiKey) VALUES (?, ?)", 
                    (current_user_id, new_key)
                )
            
            conn.commit()
            return jsonify({'message': 'API Key successfully updated'}), 200
        except Exception as e:
            return jsonify({'error': 'Database error', 'details': str(e)}), 500
        finally:
            try:
                cursor.close()
                conn.close()
            except:
                pass
