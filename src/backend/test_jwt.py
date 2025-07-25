#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from flask_jwt_extended import JWTManager, create_access_token, decode_token
from config import Config

def test_jwt():
    app = Flask(__name__)
    app.config.from_object(Config)
    jwt = JWTManager(app)
    
    with app.app_context():
        # Create a test token
        test_user_id = 1
        token = create_access_token(identity=test_user_id)
        print(f"Generated token: {token}")
        
        try:
            # Try to decode the token
            decoded = decode_token(token)
            print(f"Decoded token: {decoded}")
            print("JWT configuration is working correctly!")
            return True
        except Exception as e:
            print(f"Error decoding token: {e}")
            return False

if __name__ == "__main__":
    test_jwt()
