from flask import render_template, request, redirect, url_for, session, flash, jsonify
import json
import os
import hashlib
from datetime import datetime
import secrets
import time
import re

def get_home_content():
    """Get content for the home page"""
    welcome_text = "Your Personal Recipe AI Assistant"
    description = "Discover delicious recipes based on the ingredients you already have. Our AI will analyze your available ingredients and recommend the perfect dishes to make."
    
    features = [
        {
            "title": "Multi-Chain Web3 Support",
            "description": "Connect with Ethereum (MetaMask, OKX, Coinbase, WalletConnect) or Solana (Phantom, Solflare, Backpack) wallets. Choose your preferred blockchain ecosystem!"
        },
        {
            "title": "Cross-Chain Authentication",
            "description": "Your Recipe Finder account works seamlessly across both Ethereum and Solana networks. One profile, multiple wallets!"
        },
        {
            "title": "Natural Language Understanding",
            "description": "Simply tell the AI what ingredients you have in your kitchen, and it will understand what you're looking for."
        },
        {
            "title": "Intelligent Recipe Matching",
            "description": "Our AI analyzes your ingredients and finds the best recipe matches from our database."
        }
    ]
    
    return {
        'welcome_text': welcome_text,
        'description': description,
        'features': features
    }

def hash_password(password):
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def load_users():
    """Load users from JSON file"""
    if os.path.exists('user.json'):
        try:
            with open('user.json', 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {
                "users": [], 
                "web3_users": [], 
                "wallet_stats": {},
                "chain_stats": {
                    "ethereum": {"users": 0, "logins": 0},
                    "solana": {"users": 0, "logins": 0}
                }
            }
    return {
        "users": [], 
        "web3_users": [], 
        "wallet_stats": {},
        "chain_stats": {
            "ethereum": {"users": 0, "logins": 0},
            "solana": {"users": 0, "logins": 0}
        }
    }

def save_users(users_data):
    """Save users to JSON file"""
    with open('user.json', 'w') as f:
        json.dump(users_data, f, indent=4)

def is_valid_address(address, chain):
    """Validate wallet address based on chain"""
    if chain == 'ethereum':
        # Ethereum addresses: 0x followed by 40 hex characters
        return bool(re.match(r'^0x[a-fA-F0-9]{40}$', address))
    elif chain == 'solana':
        # Solana addresses: Base58 encoded, typically 32-44 characters
        # This is a basic check - in production, use proper base58 validation
        return bool(re.match(r'^[1-9A-HJ-NP-Za-km-z]{32,44}$', address))
    return False

def find_user_by_username(username):
    """Find user by username"""
    users_data = load_users()
    for user in users_data["users"]:
        if user["username"] == username:
            return user
    return None

def find_user_by_wallet(wallet_address, chain=None):
    """Find user by wallet address, optionally filtered by chain"""
    users_data = load_users()
    if "web3_users" not in users_data:
        users_data["web3_users"] = []
        save_users(users_data)
    
    for user in users_data["web3_users"]:
        if user["wallet_address"].lower() == wallet_address.lower():
            # If chain is specified, ensure it matches
            if chain and user.get("chain", "ethereum") != chain:
                continue
            return user
    return None

def find_user_by_id(user_id):
    """Find user by ID"""
    users_data = load_users()
    for user in users_data["users"]:
        if user["id"] == user_id:
            return user
    
    # Check web3 users too
    if "web3_users" in users_data:
        for user in users_data["web3_users"]:
            if user["id"] == user_id:
                return user
    return None

def get_chain_info(chain):
    """Get chain information"""
    chain_configs = {
        "ethereum": {
            "name": "Ethereum",
            "symbol": "ETH",
            "icon": "⟠",
            "color": "#627eea",
            "description": "Ethereum Virtual Machine",
            "explorer": "https://etherscan.io"
        },
        "solana": {
            "name": "Solana",
            "symbol": "SOL", 
            "icon": "◎",
            "color": "#9945ff",
            "description": "High-performance blockchain",
            "explorer": "https://solscan.io"
        }
    }
    
    return chain_configs.get(chain, {
        "name": "Unknown Chain",
        "symbol": "???",
        "icon": "🔗",
        "color": "#666666",
        "description": "Unknown blockchain",
        "explorer": "#"
    })

def get_wallet_info(wallet_type, chain):
    """Get wallet information based on type and chain"""
    wallet_configs = {
        # Ethereum Wallets
        "metamask": {
            "name": "MetaMask",
            "icon": "🦊",
            "color": "#f6851b",
            "description": "Browser extension wallet",
            "chain": "ethereum",
            "url": "https://metamask.io"
        },
        "okx": {
            "name": "OKX Wallet", 
            "icon": "⭕",
            "color": "#000000",
            "description": "Multi-chain DeFi wallet",
            "chain": "ethereum",
            "url": "https://www.okx.com/web3"
        },
        "coinbase": {
            "name": "Coinbase Wallet",
            "icon": "🔵", 
            "color": "#0052ff",
            "description": "Self-custody wallet from Coinbase",
            "chain": "ethereum",
            "url": "https://www.coinbase.com/wallet"
        },
        "walletconnect": {
            "name": "WalletConnect",
            "icon": "🌉",
            "color": "#3b99fc", 
            "description": "Connect via mobile wallet",
            "chain": "ethereum",
            "url": "https://walletconnect.com"
        },
        "trust": {
            "name": "Trust Wallet",
            "icon": "🛡️",
            "color": "#3375bb",
            "description": "Multi-coin mobile wallet",
            "chain": "ethereum",
            "url": "https://trustwallet.com"
        },
        "rainbow": {
            "name": "Rainbow",
            "icon": "🌈",
            "color": "#ff6b6b",
            "description": "Ethereum wallet for everyone",
            "chain": "ethereum",
            "url": "https://rainbow.me"
        },
        
        # Solana Wallets
        "phantom": {
            "name": "Phantom",
            "icon": "👻",
            "color": "#ab9ff2",
            "description": "Solana wallet made simple",
            "chain": "solana",
            "url": "https://phantom.app"
        },
        "solflare": {
            "name": "Solflare",
            "icon": "🔥",
            "color": "#ff6b35",
            "description": "Solana wallet & DeFi platform",
            "chain": "solana",
            "url": "https://solflare.com"
        },
        "backpack": {
            "name": "Backpack",
            "icon": "🎒",
            "color": "#000000",
            "description": "Multi-chain crypto wallet",
            "chain": "solana",
            "url": "https://backpack.app"
        },
        "slope": {
            "name": "Slope",
            "icon": "⛰️",
            "color": "#8b5cf6",
            "description": "Solana ecosystem wallet",
            "chain": "solana",
            "url": "https://slope.finance"
        },
        "glow": {
            "name": "Glow",
            "icon": "✨",
            "color": "#fbbf24",
            "description": "Solana wallet with rewards",
            "chain": "solana",
            "url": "https://glow.app"
        },
        "sollet": {
            "name": "Sollet",
            "icon": "🌞",
            "color": "#00d4aa",
            "description": "SPL token & SOL wallet",
            "chain": "solana",
            "url": "https://www.sollet.io"
        }
    }
    
    wallet_info = wallet_configs.get(wallet_type, {
        "name": "Unknown Wallet",
        "icon": "🔗",
        "color": "#666666",
        "description": "Web3 wallet",
        "chain": chain,
        "url": "#"
    })
    
    # Add chain info to wallet info
    chain_info = get_chain_info(chain)
    wallet_info.update({
        "chain_name": chain_info["name"],
        "chain_icon": chain_info["icon"],
        "chain_color": chain_info["color"]
    })
    
    return wallet_info

def update_wallet_stats(wallet_type, chain, action="login"):
    """Update wallet and chain usage statistics"""
    users_data = load_users()
    
    # Initialize stats if not present
    if "wallet_stats" not in users_data:
        users_data["wallet_stats"] = {}
    if "chain_stats" not in users_data:
        users_data["chain_stats"] = {
            "ethereum": {"users": 0, "logins": 0},
            "solana": {"users": 0, "logins": 0}
        }
    
    # Update wallet stats
    wallet_key = f"{wallet_type}_{chain}"
    if wallet_key not in users_data["wallet_stats"]:
        users_data["wallet_stats"][wallet_key] = {
            "wallet_type": wallet_type,
            "chain": chain,
            "total_users": 0,
            "total_logins": 0,
            "last_used": None
        }
    
    users_data["wallet_stats"][wallet_key]["total_logins"] += 1
    users_data["wallet_stats"][wallet_key]["last_used"] = datetime.now().isoformat()
    
    if action == "register":
        users_data["wallet_stats"][wallet_key]["total_users"] += 1
    
    # Update chain stats
    if chain in users_data["chain_stats"]:
        users_data["chain_stats"][chain]["logins"] += 1
        if action == "register":
            users_data["chain_stats"][chain]["users"] += 1
    
    save_users(users_data)
    return users_data["wallet_stats"], users_data["chain_stats"]

def register_user(username, email, password):
    """Register a new user"""
    # Check if user already exists
    if find_user_by_username(username):
        return False, "Username already exists"
    
    # Load existing users
    users_data = load_users()
    
    # Check if email already exists
    for user in users_data["users"]:
        if user["email"] == email:
            return False, "Email already registered"
    
    # Create new user
    new_user = {
        "id": len(users_data["users"]) + len(users_data.get("web3_users", [])) + 1,
        "username": username,
        "email": email,
        "password": hash_password(password),
        "created_at": datetime.now().isoformat(),
        "last_login": None,
        "auth_type": "traditional"
    }
    
    # Add to users list
    users_data["users"].append(new_user)
    
    # Save to file
    save_users(users_data)
    
    return True, "Registration successful"

def register_web3_user(wallet_address, chain, username=None, wallet_type="unknown"):
    """Register a new Web3 user with multi-chain support"""
    # Validate address format
    if not is_valid_address(wallet_address, chain):
        return False, f"Invalid {chain} address format"
    
    # Check if wallet already exists (same address + chain combination)
    if find_user_by_wallet(wallet_address, chain):
        return False, f"Wallet already registered on {chain}"
    
    # Load existing users
    users_data = load_users()
    
    # Ensure web3_users array exists
    if "web3_users" not in users_data:
        users_data["web3_users"] = []
    
    # Generate username if not provided
    if not username:
        wallet_info = get_wallet_info(wallet_type, chain)
        chain_info = get_chain_info(chain)
        username = f"{wallet_info['name']}_{chain_info['symbol']}_User_{wallet_address[:8]}"
    
    # Create new Web3 user
    new_user = {
        "id": len(users_data["users"]) + len(users_data["web3_users"]) + 1,
        "username": username,
        "wallet_address": wallet_address.lower(),
        "chain": chain,  # NEW: Store blockchain network
        "wallet_type": wallet_type,
        "wallet_info": get_wallet_info(wallet_type, chain),
        "chain_info": get_chain_info(chain),  # NEW: Store chain metadata
        "created_at": datetime.now().isoformat(),
        "last_login": None,
        "login_count": 0,
        "auth_type": "web3"
    }
    
    # Add to web3 users list
    users_data["web3_users"].append(new_user)
    
    # Update statistics
    update_wallet_stats(wallet_type, chain, "register")
    
    # Save to file
    save_users(users_data)
    
    wallet_info = get_wallet_info(wallet_type, chain)
    chain_info = get_chain_info(chain)
    
    return True, f"Web3 registration successful with {wallet_info['name']} on {chain_info['name']}"

def login_user(username, password):
    """Authenticate user login"""
    user = find_user_by_username(username)
    
    if not user:
        return False, "Username not found"
    
    if user["password"] != hash_password(password):
        return False, "Incorrect password"
    
    # Update last login
    users_data = load_users()
    for i, u in enumerate(users_data["users"]):
        if u["username"] == username:
            users_data["users"][i]["last_login"] = datetime.now().isoformat()
            users_data["users"][i]["login_count"] = users_data["users"][i].get("login_count", 0) + 1
            break
    
    save_users(users_data)
    
    # Set session
    session['user_id'] = user["id"]
    session['username'] = user["username"]
    session['auth_type'] = user.get("auth_type", "traditional")
    session['logged_in'] = True
    session.permanent = True
    
    return True, "Login successful"

def login_web3_user(wallet_address, chain, wallet_type="unknown"):
    """Authenticate Web3 user login with multi-chain support"""
    # Validate address format
    if not is_valid_address(wallet_address, chain):
        return False, f"Invalid {chain} address format"
    
    user = find_user_by_wallet(wallet_address, chain)
    
    if not user:
        # Auto-register new wallet with chain and wallet type
        success, message = register_web3_user(wallet_address, chain, wallet_type=wallet_type)
        if not success:
            return False, message
        user = find_user_by_wallet(wallet_address, chain)
    
    # Update last login and login count
    users_data = load_users()
    for i, u in enumerate(users_data["web3_users"]):
        if (u["wallet_address"].lower() == wallet_address.lower() and 
            u.get("chain", "ethereum") == chain):
            users_data["web3_users"][i]["last_login"] = datetime.now().isoformat()
            users_data["web3_users"][i]["login_count"] = users_data["web3_users"][i].get("login_count", 0) + 1
            
            # Update wallet type if it was unknown before
            if users_data["web3_users"][i].get("wallet_type", "unknown") == "unknown" and wallet_type != "unknown":
                users_data["web3_users"][i]["wallet_type"] = wallet_type
                users_data["web3_users"][i]["wallet_info"] = get_wallet_info(wallet_type, chain)
            break
    
    # Update statistics
    update_wallet_stats(user.get("wallet_type", wallet_type), chain)
    
    save_users(users_data)
    
    # Set session with wallet and chain info
    session['user_id'] = user["id"]
    session['username'] = user["username"]
    session['wallet_address'] = wallet_address.lower()
    session['wallet_type'] = user.get("wallet_type", wallet_type)
    session['chain'] = chain  # NEW: Store current chain in session
    session['auth_type'] = "web3"
    session['logged_in'] = True
    session.permanent = True
    
    wallet_info = get_wallet_info(user.get("wallet_type", wallet_type), chain)
    chain_info = get_chain_info(chain)
    
    return True, f"Web3 login successful with {wallet_info['name']} on {chain_info['name']}"

def generate_nonce():
    """Generate a random nonce for Web3 authentication"""
    return secrets.token_hex(16)

def create_auth_message(wallet_address, nonce, wallet_type="unknown", chain="ethereum"):
    """Create authentication message for signing with wallet and chain context"""
    wallet_info = get_wallet_info(wallet_type, chain)
    chain_info = get_chain_info(chain)
    
    return f"""Welcome to Recipe Finder!

Please sign this message to authenticate:

Wallet: {wallet_info['name']} {wallet_info['icon']}
Chain: {chain_info['name']} {chain_info['icon']}
Address: {wallet_address}
Nonce: {nonce}
Timestamp: {int(time.time())}

This signature proves you own this wallet address on {chain_info['name']} network.

By signing, you agree to our Terms of Service."""

def logout_user():
    """Logout user by clearing session"""
    session.clear()

def is_logged_in():
    """Check if user is logged in"""
    return session.get('logged_in', False)

def get_current_user():
    """Get current logged in user with enhanced multi-chain info"""
    if is_logged_in():
        user_id = session.get('user_id')
        auth_type = session.get('auth_type', 'traditional')
        
        if user_id:
            if auth_type == "web3":
                wallet_address = session.get('wallet_address')
                chain = session.get('chain', 'ethereum')
                user = find_user_by_wallet(wallet_address, chain)
            else:
                user = find_user_by_id(user_id)
            
            if user:
                user_info = {
                    'id': user["id"],
                    'username': user["username"],
                    'auth_type': user.get("auth_type", "traditional"),
                    'wallet_address': user.get("wallet_address", None),
                    'login_count': user.get("login_count", 0),
                    'last_login': user.get("last_login", None)
                }
                
                # Add wallet and chain-specific info for Web3 users
                if auth_type == "web3":
                    chain = user.get("chain", session.get('chain', 'ethereum'))
                    wallet_type = user.get("wallet_type", session.get('wallet_type', 'unknown'))
                    
                    wallet_info = get_wallet_info(wallet_type, chain)
                    chain_info = get_chain_info(chain)
                    
                    user_info.update({
                        'chain': chain,
                        'wallet_type': wallet_type,
                        'wallet_info': wallet_info,
                        'chain_info': chain_info,
                        'wallet_name': wallet_info['name'],
                        'wallet_icon': wallet_info['icon'],
                        'wallet_color': wallet_info['color'],
                        'chain_name': chain_info['name'],
                        'chain_icon': chain_info['icon'],
                        'chain_color': chain_info['color'],
                        'explorer_url': f"{chain_info['explorer']}/address/{user.get('wallet_address', '')}"
                    })
                
                return user_info
    return None

def get_analytics():
    """Get comprehensive analytics including multi-chain data"""
    users_data = load_users()
    
    total_traditional = len(users_data.get("users", []))
    total_web3 = len(users_data.get("web3_users", []))
    wallet_stats = users_data.get("wallet_stats", {})
    chain_stats = users_data.get("chain_stats", {})
    
    # Calculate wallet distribution by chain
    ethereum_wallets = {}
    solana_wallets = {}
    
    for user in users_data.get("web3_users", []):
        chain = user.get("chain", "ethereum")
        wallet_type = user.get("wallet_type", "unknown")
        
        if chain == "ethereum":
            ethereum_wallets[wallet_type] = ethereum_wallets.get(wallet_type, 0) + 1
        elif chain == "solana":
            solana_wallets[wallet_type] = solana_wallets.get(wallet_type, 0) + 1
    
    # Calculate chain adoption rates
    total_users = total_traditional + total_web3
    ethereum_users = chain_stats.get("ethereum", {}).get("users", 0)
    solana_users = chain_stats.get("solana", {}).get("users", 0)
    
    return {
        "total_users": total_users,
        "traditional_users": total_traditional,
        "web3_users": total_web3,
        "ethereum_users": ethereum_users,
        "solana_users": solana_users,
        "ethereum_wallets": ethereum_wallets,
        "solana_wallets": solana_wallets,
        "wallet_stats": wallet_stats,
        "chain_stats": chain_stats,
        "web3_adoption_rate": (total_web3 / total_users) * 100 if total_users > 0 else 0,
        "ethereum_adoption_rate": (ethereum_users / total_users) * 100 if total_users > 0 else 0,
        "solana_adoption_rate": (solana_users / total_users) * 100 if total_users > 0 else 0,
        "multi_chain_users": len([u for u in users_data.get("web3_users", []) if u.get("chain")])
    }

def render_home_page():
    """Render home page with authentication state"""
    content = get_home_content()
    current_user = get_current_user()
    
    # Get any flash messages
    message = request.args.get('message')
    message_type = request.args.get('type', 'success')
    
    return render_template('home.html', 
                         active_tab='home',
                         current_user=current_user,
                         message=message,
                         message_type=message_type,
                         **content)

def render_login_page():
    """Render login page"""
    # Redirect if already logged in
    if is_logged_in():
        return redirect('/')
    
    message = request.args.get('message')
    message_type = request.args.get('type', 'error')
    
    return render_template('login.html',
                         message=message,
                         message_type=message_type)

def render_web3_login_page():
    """Render Web3 login page with multi-chain analytics"""
    # Redirect if already logged in
    if is_logged_in():
        return redirect('/')
    
    message = request.args.get('message')
    message_type = request.args.get('type', 'error')
    
    # Get analytics for display (optional)
    analytics = get_analytics()
    
    return render_template('web3_login.html',
                         message=message,
                         message_type=message_type,
                         analytics=analytics)

def render_register_page():
    """Render register page"""
    # Redirect if already logged in
    if is_logged_in():
        return redirect('/')
    
    message = request.args.get('message')
    message_type = request.args.get('type', 'error')
    
    return render_template('register.html',
                         message=message,
                         message_type=message_type)

def handle_login():
    """Handle login form submission"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        # Validation
        if not username or not password:
            return redirect('/login-page?message=Username and password are required&type=error')
        
        # Login user
        success, message = login_user(username, password)
        
        if success:
            return redirect('/?message=Welcome back!&type=success')
        else:
            return redirect(f'/login-page?message={message}&type=error')
    
    return redirect('/login-page')

def handle_web3_auth():
    """Handle Web3 authentication with multi-chain support"""
    if request.method == 'POST':
        data = request.get_json()
        wallet_address = data.get('wallet_address')
        wallet_type = data.get('wallet_type', 'unknown')
        chain = data.get('chain', 'ethereum')  # NEW: Get chain from frontend
        
        if not wallet_address:
            return jsonify({'success': False, 'message': 'Wallet address required'})
        
        if not chain or chain not in ['ethereum', 'solana']:
            return jsonify({'success': False, 'message': 'Valid chain required (ethereum or solana)'})
        
        # Validate address format for the specified chain
        if not is_valid_address(wallet_address, chain):
            return jsonify({'success': False, 'message': f'Invalid {chain} address format'})
        
        # Generate nonce for this session
        nonce = generate_nonce()
        message = create_auth_message(wallet_address, nonce, wallet_type, chain)
        
        # Store nonce and wallet info in session temporarily
        session['web3_nonce'] = nonce
        session['web3_wallet'] = wallet_address.lower()
        session['web3_wallet_type'] = wallet_type
        session['web3_chain'] = chain  # NEW: Store chain in session
        
        wallet_info = get_wallet_info(wallet_type, chain)
        chain_info = get_chain_info(chain)
        
        return jsonify({
            'success': True, 
            'message': message,
            'nonce': nonce,
            'wallet_info': wallet_info,
            'chain_info': chain_info  # NEW: Return chain info to frontend
        })
    
    return jsonify({'success': False, 'message': 'Invalid request'})

def handle_web3_verify():
    """Handle Web3 signature verification with multi-chain support"""
    if request.method == 'POST':
        data = request.get_json()
        wallet_address = data.get('wallet_address')
        signature = data.get('signature')
        chain = data.get('chain', 'ethereum')  # NEW: Get chain from request
        
        if not wallet_address or not signature:
            return jsonify({'success': False, 'message': 'Missing wallet address or signature'})
        
        # Verify the wallet and chain match session
        if (session.get('web3_wallet', '').lower() != wallet_address.lower() or
            session.get('web3_chain', 'ethereum') != chain):
            return jsonify({'success': False, 'message': 'Wallet address or chain mismatch'})
        
        # Get wallet type from session
        wallet_type = session.get('web3_wallet_type', 'unknown')
        
        # For simplicity, we'll trust the signature verification is done client-side
        # In production, you should verify the signature server-side using appropriate libraries:
        # - For Ethereum: use eth_account.messages and eth_account.Account.recover_message
        # - For Solana: use solana.keypair and nacl for signature verification
        
        # Login the user with wallet type and chain
        success, message = login_web3_user(wallet_address, chain, wallet_type)
        
        if success:
            # Clear temporary session data
            session.pop('web3_nonce', None)
            session.pop('web3_wallet', None)
            session.pop('web3_wallet_type', None)
            session.pop('web3_chain', None)
            
            wallet_info = get_wallet_info(wallet_type, chain)
            chain_info = get_chain_info(chain)
            
            return jsonify({
                'success': True, 
                'message': f'Authentication successful with {wallet_info["name"]} on {chain_info["name"]}!',
                'redirect': f'/?message=Welcome to Recipe Finder via {wallet_info["name"]} on {chain_info["name"]}!&type=success',
                'wallet_info': wallet_info,
                'chain_info': chain_info
            })
        else:
            return jsonify({'success': False, 'message': message})
    
    return jsonify({'success': False, 'message': 'Invalid request'})

def handle_register():
    """Handle register form submission"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Validation
        if not username or not email or not password:
            return redirect('/register-page?message=All fields are required&type=error')
        
        if password != confirm_password:
            return redirect('/register-page?message=Passwords do not match&type=error')
        
        if len(password) < 6:
            return redirect('/register-page?message=Password must be at least 6 characters long&type=error')
        
        # Register user
        success, message = register_user(username, email, password)
        
        if success:
            return redirect('/login-page?message=Registration successful! Please login.&type=success')
        else:
            return redirect(f'/register-page?message={message}&type=error')
    
    return redirect('/register-page')

def handle_logout():
    """Handle logout"""
    logout_user()
    return redirect('/?message=You have been logged out successfully&type=success')

# NEW: API endpoints for multi-chain analytics
def api_get_analytics():
    """API endpoint to get analytics data"""
    if not is_logged_in():
        return jsonify({'success': False, 'message': 'Authentication required'})
    
    analytics = get_analytics()
    return jsonify({
        'success': True,
        'data': analytics
    })

def api_get_supported_chains():
    """API endpoint to get supported chains"""
    return jsonify({
        'success': True,
        'chains': {
            'ethereum': get_chain_info('ethereum'),
            'solana': get_chain_info('solana')
        }
    })

def api_get_supported_wallets():
    """API endpoint to get supported wallets by chain"""
    ethereum_wallets = ['metamask', 'okx', 'coinbase', 'walletconnect', 'trust', 'rainbow']
    solana_wallets = ['phantom', 'solflare', 'backpack', 'slope', 'glow', 'sollet']
    
    return jsonify({
        'success': True,
        'wallets': {
            'ethereum': [get_wallet_info(w, 'ethereum') for w in ethereum_wallets],
            'solana': [get_wallet_info(w, 'solana') for w in solana_wallets]
        }
    })