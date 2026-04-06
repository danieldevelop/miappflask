from datetime import datetime
from extensions import db
import json

class WebauthnCredential(db.Model):
    __tablename__ = "webauthn_credentials"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    credential_id = db.Column(db.String(255), unique=True, nullable=False, index=True)
    public_key = db.Column(db.Text, nullable=False)  # JSON encoded
    sign_count = db.Column(db.Integer, default=0, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    last_used = db.Column(db.DateTime, nullable=True)
    device_name = db.Column(db.String(255), nullable=True)  # ej: "Huella del iPhone"

    # Relación con User
    user = db.relationship('User', backref='webauthn_credentials')

    def to_dict(self):
        return {
            'id': self.id,
            'credential_id': self.credential_id,
            'device_name': self.device_name,
            'created_at': self.created_at.isoformat(),
            'last_used': self.last_used.isoformat() if self.last_used else None
        }
