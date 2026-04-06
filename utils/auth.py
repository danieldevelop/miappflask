from functools import wraps
from flask import session, jsonify

def login_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if not session.get("user_id"):
            return jsonify({"ok": False, "message": "No autenticado"}), 401
        return view_func(*args, **kwargs)
    return wrapper
