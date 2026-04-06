"""Utilidades de detección y reconocimiento facial con MediaPipe."""

import cv2
import numpy as np
from typing import Optional, Tuple
import base64
import hashlib
import json


class FacialDetector:
    """Detector de rostros y extractor de embeddings usando MediaPipe."""

    def __init__(self):
        import mediapipe as mp
        self.mp_face_detection = mp.solutions.face_detection
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_detector = self.mp_face_detection.FaceDetection(min_detection_confidence=0.7)
        self.face_mesh = self.mp_face_mesh.FaceMesh(min_detection_confidence=0.7)

    def detect_face(self, frame: np.ndarray) -> Optional[dict]:
        """
        Detecta rostro en un frame y retorna bounding box + landmarks.

        Args:
            frame: imagen en formato BGR (OpenCV)

        Returns:
            dict con rostro detectado o None si no hay rostro
        """
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_detector.process(rgb_frame)

        if results.detections:
            detection = results.detections[0]
            bbox = detection.location_data.relative_bounding_box
            h, w, _ = frame.shape

            x_min = int(bbox.xmin * w)
            y_min = int(bbox.ymin * h)
            width = int(bbox.width * w)
            height = int(bbox.height * h)

            confidence = detection.score[0]

            return {
                "bbox": (x_min, y_min, width, height),
                "confidence": float(confidence),
            }
        return None

    def extract_embedding(self, frame: np.ndarray) -> Optional[Tuple[np.ndarray, float]]:
        """
        Extrae embedding facial (vector 468 dimensiones de face mesh).

        Args:
            frame: imagen en formato BGR

        Returns:
            (embedding array, liveness_score) o (None, 0) si no hay rostro
        """
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(rgb_frame)

        if results.multi_face_landmarks:
            landmarks = results.multi_face_landmarks[0]
            embedding = np.array([
                [lm.x, lm.y, lm.z] for lm in landmarks.landmark
            ]).flatten()

            liveness = self._estimate_liveness(landmarks)
            return embedding, liveness
        return None, 0.0

    def _estimate_liveness(self, landmarks) -> float:
        """
        Estimación básica de liveness (detección de spoofing).
        Retorna 0.0-1.0 donde 1.0 es un rostro real.
        """
        if len(landmarks.landmark) < 468:
            return 0.0

        eye_left = [landmarks.landmark[33], landmarks.landmark[133]]
        eye_right = [landmarks.landmark[362], landmarks.landmark[263]]

        left_eye_ratio = abs(eye_left[0].y - eye_left[1].y) / max(abs(eye_left[0].x - eye_left[1].x), 0.001)
        right_eye_ratio = abs(eye_right[0].y - eye_right[1].y) / max(abs(eye_right[0].x - eye_right[1].x), 0.001)

        avg_eye_ratio = (left_eye_ratio + right_eye_ratio) / 2
        liveness_score = min(1.0, avg_eye_ratio * 2)
        return float(liveness_score)

    def frame_to_base64(self, frame: np.ndarray) -> str:
        """Convierte frame a base64 para enviar al frontend."""
        _, buffer = cv2.imencode('.jpg', frame)
        return base64.b64encode(buffer).decode('utf-8')

    def embedding_to_hash(self, embedding: np.ndarray) -> str:
        """Genera hash del embedding para detección de duplicados."""
        json_str = json.dumps(embedding.tolist())
        return hashlib.sha256(json_str.encode()).hexdigest()


def embedding_distance(emb1: np.ndarray, emb2: np.ndarray) -> float:
    """Calcula distancia euclidiana entre dos embeddings (normalizada 0-1)."""
    distance = np.linalg.norm(emb1 - emb2)
    return float(distance)


def embeddings_match(emb1: np.ndarray, emb2: np.ndarray, threshold: float = 0.5) -> bool:
    """Verifica si dos embeddings coinciden (similar > threshold)."""
    distance = embedding_distance(emb1, emb2)
    return distance < threshold

