from datetime import datetime
from extensions import db
import json


class FacialEmbedding(db.Model):
    """Almacena embeddings faciales (vectores) para reconocimiento facial."""
    __tablename__ = "facial_embeddings"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    embedding = db.Column(db.Text, nullable=False)  # JSON encoded numpy array
    embedding_hash = db.Column(db.String(64), unique=True, nullable=False)  # SHA256 para detección de duplicados
    device_name = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    last_used = db.Column(db.DateTime, nullable=True)
    liveness_score = db.Column(db.Float, nullable=True)  # 0.0-1.0 para detectar spoofing

    user = db.relationship("User", backref="facial_embeddings")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "device_name": self.device_name,
            "liveness_score": self.liveness_score,
            "created_at": self.created_at.isoformat(),
            "last_used": self.last_used.isoformat() if self.last_used else None,
        }

