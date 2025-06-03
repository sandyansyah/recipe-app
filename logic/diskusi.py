import hashlib
import sqlite3
import os
import time
import uuid
import json
import base64
import threading
from datetime import datetime
from flask import session, request
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
import secrets

# Custom encrypted chat database with .cryptsan extension
CHAT_DB_PATH = 'diskusi.cryptsan'

# Thread-local storage for database connections
thread_local = threading.local()

def get_db_connection():
    """Get thread-safe database connection"""
    if not hasattr(thread_local, 'conn'):
        # Create new connection for this thread
        thread_local.conn = sqlite3.connect(CHAT_DB_PATH, check_same_thread=False)
        init_database_schema(thread_local.conn)
    return thread_local.conn

def init_database_schema(conn):
    """Initialize database schema"""
    # Create messages table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS encrypted_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message_id TEXT UNIQUE,
            sender_id TEXT,
            sender_username TEXT,
            encrypted_content BLOB,
            content_hash TEXT,
            encryption_key_hash TEXT,
            timestamp INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create user keys table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS user_encryption_keys (
            user_id TEXT PRIMARY KEY,
            key_hash TEXT,
            salt BLOB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create metadata table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS chat_metadata (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')
    
    # Store encryption info
    conn.execute('''
        INSERT OR REPLACE INTO chat_metadata (key, value) 
        VALUES (?, ?)
    ''', ('encryption_type', 'cryptsan_group_aes256_cbc'))
    
    conn.execute('''
        INSERT OR REPLACE INTO chat_metadata (key, value) 
        VALUES (?, ?)
    ''', ('database_format', 'cryptsan_group_encrypted'))
    
    conn.execute('''
        INSERT OR REPLACE INTO chat_metadata (key, value) 
        VALUES (?, ?)
    ''', ('hash_algorithm', 'sha256'))
    
    conn.execute('''
        INSERT OR REPLACE INTO chat_metadata (key, value) 
        VALUES (?, ?)
    ''', ('encryption_mode', 'shared_group_key'))
    
    conn.execute('''
        INSERT OR REPLACE INTO chat_metadata (key, value) 
        VALUES (?, ?)
    ''', ('group_access', 'all_users_can_decrypt'))
    
    conn.commit()

def sha256_hash(data):
    """Create SHA-256 hash"""
    if isinstance(data, str):
        data = data.encode('utf-8')
    return hashlib.sha256(data).hexdigest()

def derive_user_encryption_key(user_id, username, user_password_hash=None):
    """Derive user-specific encryption key using PBKDF2 + SHA-256"""
    # Create deterministic salt from user info
    salt_material = f"diskusi_chat_{user_id}_{username}".encode('utf-8')
    salt = hashlib.sha256(salt_material).digest()[:16]
    
    # Use user ID + username as key material (or password hash if available)
    if user_password_hash:
        key_material = f"{user_id}:{username}:{user_password_hash}".encode('utf-8')
    else:
        key_material = f"{user_id}:{username}:default_key".encode('utf-8')
    
    # Derive key using PBKDF2-SHA256
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,  # AES-256
        salt=salt,
        iterations=100000,  # High iteration count for security
        backend=default_backend()
    )
    
    encryption_key = kdf.derive(key_material)
    
    # Store key info in database
    key_hash = sha256_hash(encryption_key)
    
    conn = get_db_connection()
    conn.execute('''
        INSERT OR REPLACE INTO user_encryption_keys (user_id, key_hash, salt)
        VALUES (?, ?, ?)
    ''', (user_id, key_hash, salt))
    conn.commit()
    
    return encryption_key

def derive_group_encryption_key():
    """Derive shared group encryption key for community discussions"""
    # Use fixed group material so all users get the same key
    group_material = "diskusi_komunitas_cryptsan_shared_2025".encode('utf-8')
    salt = hashlib.sha256(b"cryptsan_group_salt_diskusi").digest()[:16]
    
    # Derive group key using PBKDF2-SHA256
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,  # AES-256
        salt=salt,
        iterations=100000,
        backend=default_backend()
    )
    
    group_key = kdf.derive(group_material)
    return group_key

def encrypt_message_aes256_cbc(message_content, encryption_key):
    """Encrypt message using AES-256-CBC (CryptSan style)"""
    # Convert message to bytes
    message_bytes = message_content.encode('utf-8')
    
    # Generate random IV
    iv = secrets.token_bytes(16)
    
    # Pad message to multiple of 16 bytes (PKCS7 padding)
    pad_length = 16 - (len(message_bytes) % 16)
    padded_message = message_bytes + bytes([pad_length]) * pad_length
    
    # Encrypt using AES-256-CBC
    cipher = Cipher(
        algorithms.AES(encryption_key),
        modes.CBC(iv),
        backend=default_backend()
    )
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(padded_message) + encryptor.finalize()
    
    # Return IV + ciphertext
    return iv + ciphertext

def decrypt_message_aes256_cbc(encrypted_data, encryption_key):
    """Decrypt message using AES-256-CBC"""
    # Extract IV and ciphertext
    iv = encrypted_data[:16]
    ciphertext = encrypted_data[16:]
    
    # Decrypt
    cipher = Cipher(
        algorithms.AES(encryption_key),
        modes.CBC(iv),
        backend=default_backend()
    )
    decryptor = cipher.decryptor()
    padded_message = decryptor.update(ciphertext) + decryptor.finalize()
    
    # Remove PKCS7 padding
    pad_length = padded_message[-1]
    message_bytes = padded_message[:-pad_length]
    
    return message_bytes.decode('utf-8')

def post_cryptsan_message(user_id, username, message_content):
    """Post message with CryptSan encryption using shared group key"""
    # Use shared group encryption key so all users can decrypt
    encryption_key = derive_group_encryption_key()
    
    # Also derive user key for verification purposes
    user_key = derive_user_encryption_key(user_id, username)
    
    # Create message ID
    message_id = f"msg_{int(time.time() * 1000)}_{secrets.token_hex(8)}"
    
    # Encrypt message content with GROUP key
    encrypted_content = encrypt_message_aes256_cbc(message_content, encryption_key)
    
    # Create content hash for integrity
    content_hash = sha256_hash(message_content)
    
    # Create user signature hash for verification (using user's individual key)
    user_signature = sha256_hash(f"{user_id}:{message_content}:{int(time.time())}")
    verification_hash = sha256_hash(user_signature + sha256_hash(user_key))
    
    # Store in database
    conn = get_db_connection()
    conn.execute('''
        INSERT INTO encrypted_messages 
        (message_id, sender_id, sender_username, encrypted_content, content_hash, encryption_key_hash, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        message_id,
        user_id,
        username,
        encrypted_content,
        content_hash,
        verification_hash,  # Store verification hash instead of group key hash
        int(time.time())
    ))
    
    conn.commit()
    
    return {
        'id': message_id,
        'sender_id': user_id,
        'sender_username': username,
        'content': message_content,
        'timestamp': datetime.now().isoformat(),
        'encrypted': True,
        'hash_verified': True
    }

def get_cryptsan_messages(user_id, username, limit=50):
    """Get messages with CryptSan decryption using shared group key"""
    # Use shared group encryption key so all users can decrypt all messages
    group_encryption_key = derive_group_encryption_key()
    
    # Get current user's individual key for verification
    user_key = derive_user_encryption_key(user_id, username)
    
    # Get messages from database
    conn = get_db_connection()
    cursor = conn.execute('''
        SELECT message_id, sender_id, sender_username, encrypted_content, content_hash, encryption_key_hash, timestamp
        FROM encrypted_messages 
        ORDER BY timestamp ASC 
        LIMIT ?
    ''', (limit,))
    
    decrypted_messages = []
    
    for row in cursor.fetchall():
        message_id, sender_id, sender_username, encrypted_content, stored_content_hash, verification_hash, timestamp = row
        
        try:
            # Decrypt message using GROUP key (all users can decrypt all messages)
            decrypted_content = decrypt_message_aes256_cbc(encrypted_content, group_encryption_key)
            
            # Verify content integrity
            content_hash = sha256_hash(decrypted_content)
            hash_verified = (content_hash == stored_content_hash)
            
            # For verification status, check if this user is the sender
            # If sender, mark as verified. If not sender, mark as verified if hash matches
            is_sender = (sender_id == user_id)
            signature_valid = hash_verified  # Use hash verification as signature verification
            
            decrypted_messages.append({
                'id': message_id,
                'sender_id': sender_id,
                'sender_username': sender_username,
                'content': decrypted_content,
                'timestamp': datetime.fromtimestamp(timestamp).isoformat(),
                'encrypted': True,
                'hash_verified': hash_verified,
                'signature_valid': signature_valid,
                'decryption_successful': True,
                'is_sender': is_sender
            })
                
        except Exception as e:
            print(f"Error decrypting message {message_id}: {e}")
            decrypted_messages.append({
                'id': message_id,
                'sender_id': sender_id,
                'sender_username': sender_username,
                'content': '[❌ Error decrypting message]',
                'timestamp': datetime.fromtimestamp(timestamp).isoformat(),
                'encrypted': True,
                'hash_verified': False,
                'signature_valid': False,
                'decryption_successful': False,
                'is_sender': False
            })
    
    return decrypted_messages

def get_web3_users():
    """Get list of Web3 user IDs"""
    from .home import load_users
    
    users_data = load_users()
    web3_users = []
    
    if "web3_users" in users_data:
        web3_users = [str(user["id"]) for user in users_data["web3_users"]]
    
    return web3_users

def get_chat_database_info():
    """Get CryptSan database information"""
    conn = get_db_connection()
    
    try:
        cursor = conn.execute('SELECT COUNT(*) FROM encrypted_messages')
        message_count = cursor.fetchone()[0]
        
        cursor = conn.execute('SELECT COUNT(*) FROM user_encryption_keys')
        user_count = cursor.fetchone()[0]
        
        cursor = conn.execute('SELECT key, value FROM chat_metadata')
        metadata = dict(cursor.fetchall())
    except sqlite3.OperationalError:
        # Tables don't exist yet
        message_count = 0
        user_count = 0
        metadata = {}
    
    file_size = os.path.getsize(CHAT_DB_PATH) if os.path.exists(CHAT_DB_PATH) else 0
    
    return {
        'database_type': 'cryptsan_group_encrypted',
        'file_path': CHAT_DB_PATH,
        'file_size_bytes': file_size,
        'file_size_mb': round(file_size / (1024 * 1024), 2),
        'encryption_algorithm': 'AES-256-CBC',
        'encryption_mode': 'Shared Group Key',
        'hash_algorithm': 'SHA-256',
        'key_derivation': 'PBKDF2-SHA256',
        'database_format': 'CryptSan (.cryptsan)',
        'group_access': 'All users can decrypt all messages',
        'message_count': message_count,
        'user_count': user_count,
        'metadata': metadata
    }

def handle_diskusi_request():
    """Handle requests to the discussion page with CryptSan encryption"""
    from flask import render_template, redirect, url_for
    from .home import get_current_user
    
    # Get current user
    current_user = get_current_user()
    
    # Redirect to login if not authenticated
    if not current_user:
        return redirect(url_for('login_page', 
                              message="Please login to access the discussion forum",
                              type="error"))
    
    if request.method == 'POST':
        # Handle message submission
        message_content = request.form.get('message', '').strip()
        
        if message_content:
            # Post message with CryptSan encryption
            post_cryptsan_message(
                str(current_user['id']), 
                current_user['username'], 
                message_content
            )
        
        # Redirect to avoid form resubmission
        return redirect(url_for('diskusi_page'))
    
    # Get messages with CryptSan decryption
    messages = get_cryptsan_messages(str(current_user['id']), current_user['username'])
    
    # Get Web3 users for display
    web3_users = get_web3_users()
    
    # Get database info for display
    db_info = get_chat_database_info()
    
    # Render the discussion page
    return render_template('diskusi.html', 
                         active_tab='diskusi',
                         current_user=current_user,
                         messages=messages,
                         web3_users=web3_users,
                         db_info=db_info,
                         encryption_type='CryptSan Group AES-256-CBC + SHA-256')

def api_get_new_messages(after_id=None):
    """API endpoint to get new messages with CryptSan decryption"""
    from flask import jsonify
    from .home import get_current_user
    
    current_user = get_current_user()
    
    if not current_user:
        return jsonify({
            'success': False,
            'message': 'Authentication required'
        })
    
    # Get all messages with CryptSan decryption
    all_messages = get_cryptsan_messages(str(current_user['id']), current_user['username'])
    
    # Filter messages after specified ID if provided
    if after_id:
        after_index = next((i for i, msg in enumerate(all_messages) if msg["id"] == after_id), None)
        if after_index is not None:
            new_messages = all_messages[after_index + 1:]
        else:
            new_messages = all_messages
    else:
        new_messages = all_messages
    
    # Get Web3 users for display
    web3_users = get_web3_users()
    
    # Add Web3 status to messages
    for msg in new_messages:
        msg['is_web3'] = msg['sender_id'] in web3_users
        msg['signature_valid'] = msg.get('hash_verified', False)  # Use hash verification instead
    
    return jsonify({
        'success': True,
        'messages': new_messages,
        'encryption_type': 'cryptsan_group_aes256_cbc_sha256',
        'database_info': get_chat_database_info()
    })

# Cleanup function
def cleanup_chat_database():
    """Cleanup chat database connections"""
    if hasattr(thread_local, 'conn'):
        try:
            thread_local.conn.close()
        except:
            pass

# Register cleanup on module unload
import atexit
atexit.register(cleanup_chat_database)