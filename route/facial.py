"""Endpoints para captura y detección facial (Fase 2.2A)."""

from flask import Blueprint, request, jsonify, session
from datetime import datetime
from extensions import db
from models.user import User
from models.facial_embedding import FacialEmbedding
from utils.auth import api_login_required, page_login_required
from utils.facial_detection import FacialDetector
from utils.facial_detection import embeddings_match
import cv2
import numpy as np
import base64
import json

facial_bp = Blueprint('facial', __name__, url_prefix='/facial')
detector = None
MIN_LIVENESS_SCORE = 0.20


@facial_bp.route('/embeddings', methods=['GET'])
@api_login_required
def list_embeddings():
    """Lista los embeddings faciales del usuario autenticado."""
    user = db.session.get(User, session["user_id"])
    if not user:
        return jsonify({"ok": False, "message": "Sesión inválida"}), 401

    embeddings = FacialEmbedding.query.filter_by(user_id=user.id).all()
    return jsonify({
        "ok": True,
        "embeddings": [emb.to_dict() for emb in embeddings]
    }), 200


@facial_bp.route('/embeddings/<int:embedding_id>', methods=['DELETE'])
@api_login_required
def delete_embedding(embedding_id):
    """Elimina un embedding facial del usuario autenticado."""
    user = db.session.get(User, session["user_id"])
    if not user:
        return jsonify({"ok": False, "message": "Sesión inválida"}), 401

    embedding = FacialEmbedding.query.filter_by(
        id=embedding_id,
        user_id=user.id
    ).first()

    if not embedding:
        return jsonify({"ok": False, "message": "Embedding no encontrado"}), 404

    db.session.delete(embedding)
    db.session.commit()

    return jsonify({
        "ok": True,
        "message": "Embedding facial eliminado"
    }), 200
def get_detector():
    global detector
    if detector is None:
        detector = FacialDetector()
    return detector


@facial_bp.route('/detect-frame', methods=['POST'])
def detect_frame():
    detector = get_detector()
    """
    Procesa un frame de la cámara y detecta rostro.
    Retorna: bbox, confidence, face_detected
    """
    try:
        data = request.get_json(silent=True) or {}
        frame_b64 = data.get('frame', '')

        if not frame_b64:
            return jsonify({"ok": False, "message": "Frame vacío"}), 400

        frame_data = base64.b64decode(frame_b64.split(',')[1] if ',' in frame_b64 else frame_b64)
        nparr = np.frombuffer(frame_data, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if frame is None:
            return jsonify({"ok": False, "message": "Frame inválido"}), 400

        detection = detector.detect_face(frame)

        if detection:
            embedding, liveness = detector.extract_embedding(frame)
            can_proceed = embedding is not None and liveness >= MIN_LIVENESS_SCORE
            return jsonify({
                "ok": True,
                "face_detected": True,
                "confidence": detection["confidence"],
                "liveness_score": liveness,
                "bbox": detection["bbox"],
                "can_register": can_proceed,
                "can_authenticate": can_proceed,
                "min_liveness_required": MIN_LIVENESS_SCORE,
            }), 200
        else:
            return jsonify({
                "ok": True,
                "face_detected": False,
                "confidence": 0.0,
                "liveness_score": 0.0,
                "can_register": False,
                "can_authenticate": False,
                "min_liveness_required": MIN_LIVENESS_SCORE,
            }), 200

    except Exception as e:
        return jsonify({"ok": False, "message": str(e)}), 400


@facial_bp.route('/register-embedding', methods=['POST'])
@api_login_required
def register_embedding():
    detector = get_detector()
    """
    Registra un embedding facial después de captura en tiempo real.
    Guarda en BD para login futuro.
    """
    user = db.session.get(User, session["user_id"])
    if not user:
        return jsonify({"ok": False, "message": "Sesión inválida"}), 401

    try:
        data = request.get_json(silent=True) or {}
        frame_b64 = data.get('frame', '')
        device_name = (data.get('device_name') or 'Mi rostro').strip()

        if not frame_b64 or len(frame_b64) < 100:
            return jsonify({
                "ok": False,
                "message": f"Frame inválido o vacío (tamaño: {len(frame_b64)} bytes)"
            }), 400

        frame_data = base64.b64decode(frame_b64.split(',')[1] if ',' in frame_b64 else frame_b64)
        nparr = np.frombuffer(frame_data, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if frame is None:
            return jsonify({"ok": False, "message": "Frame inválido"}), 400

        embedding, liveness = detector.extract_embedding(frame)

        if embedding is None or liveness < MIN_LIVENESS_SCORE:
            return jsonify({
                "ok": False,
                "message": (
                    f"Rostro no detectado o liveness insuficiente "
                    f"({liveness:.2f}). Mínimo requerido: {MIN_LIVENESS_SCORE:.2f}"
                )
            }), 400

        embedding_hash = detector.embedding_to_hash(embedding)

        existing = FacialEmbedding.query.filter_by(embedding_hash=embedding_hash).first()
        if existing:
            return jsonify({"ok": False, "message": "Este embedding ya está registrado"}), 400

        facial_emb = FacialEmbedding(
            user_id=user.id,
            embedding=json.dumps(embedding.tolist()),
            embedding_hash=embedding_hash,
            device_name=device_name,
            liveness_score=liveness,
        )

        db.session.add(facial_emb)
        db.session.commit()

        return jsonify({
            "ok": True,
            "message": "Embedding facial registrado",
            "embedding": facial_emb.to_dict(),
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"ok": False, "message": str(e)}), 400


@facial_bp.route('/authenticate-frame', methods=['POST'])
def authenticate_frame():
    """
    Autentica un usuario comparando embedding facial capturado con los guardados.
    """
    detector = get_detector()

    try:
        data = request.get_json(silent=True) or {}
        frame_b64 = data.get('frame', '')
        username = (data.get('username') or '').strip()

        if not frame_b64 or not username:
            return jsonify({"ok": False, "message": "Frame o usuario vacío"}), 400

        frame_data = base64.b64decode(frame_b64.split(',')[1] if ',' in frame_b64 else frame_b64)
        nparr = np.frombuffer(frame_data, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if frame is None:
            return jsonify({"ok": False, "message": "Frame inválido"}), 400

        user = User.query.filter_by(username=username, is_active=True).first()
        if not user:
            return jsonify({"ok": False, "message": "Usuario no encontrado"}), 401

        embedding, liveness = detector.extract_embedding(frame)

        if embedding is None or liveness < MIN_LIVENESS_SCORE:
            return jsonify({
                "ok": False,
                "message": (
                    f"Rostro no detectado o liveness insuficiente "
                    f"({liveness:.2f}). Mínimo requerido: {MIN_LIVENESS_SCORE:.2f}"
                )
            }), 400

        stored_embeddings = FacialEmbedding.query.filter_by(user_id=user.id).all()

        if not stored_embeddings:
            return jsonify({"ok": False, "message": "Usuario no tiene embeddings faciales registrados"}), 400

        best_match = None
        best_distance = float('inf')
        threshold = 0.6

        for stored in stored_embeddings:
            stored_emb = np.array(json.loads(stored.embedding))
            distance = np.linalg.norm(embedding - stored_emb)

            if distance < best_distance:
                best_distance = distance
                best_match = stored

        if best_distance < threshold and best_match:
            session["user_id"] = user.id
            session["username"] = user.username
            session.modified = True

            best_match.last_used = datetime.utcnow()
            db.session.commit()

            return jsonify({
                "ok": True,
                "message": "Autenticación facial exitosa",
                "redirect": "/dashboard",
                "distance": float(best_distance),
                "confidence": max(0, 1.0 - best_distance),
            }), 200
        else:
            return jsonify({
                "ok": False,
                "message": f"Rostro no coincide (distancia: {best_distance:.2f}, umbral: {threshold})",
                "distance": float(best_distance),
            }), 401

    except Exception as e:
        return jsonify({"ok": False, "message": str(e)}), 400


