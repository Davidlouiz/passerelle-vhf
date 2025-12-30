"""
Modèles SQLAlchemy pour Passerelle VHF.

Schéma de base de données complet avec toutes les tables nécessaires.
"""
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Text, Float,
    ForeignKey, UniqueConstraint, Index, JSON
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class User(Base):
    """Comptes administrateurs."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    must_change_password = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_login_at = Column(DateTime, nullable=True)


class ProviderCredential(Base):
    """Identifiants des providers (FFVL, OpenWindMap, etc.)."""
    __tablename__ = "provider_credentials"

    id = Column(Integer, primary_key=True)
    provider_id = Column(String(50), unique=True, nullable=False, index=True)
    credentials_json = Column(JSON, nullable=False)  # Ex: {"ffvl_key": "..."}
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class Channel(Base):
    """Configuration d'un canal (balise + voix + planning)."""
    __tablename__ = "channels"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    enabled = Column(Boolean, default=False, nullable=False)
    
    # Provider et station
    provider_id = Column(String(50), nullable=False, index=True)
    station_id = Column(String(50), nullable=False)
    station_name_cache = Column(String(200), nullable=True)
    station_visual_url_cache = Column(String(500), nullable=True)
    
    # Planification
    measurement_period_seconds = Column(Integer, nullable=False)  # Aussi utilisé pour péremption
    offsets_seconds_json = Column(JSON, nullable=False)  # Ex: [0, 1200, 2400]
    offset_policy = Column(String(20), default="cancel_on_new", nullable=False)
    min_interval_between_tx_seconds = Column(Integer, default=300, nullable=False)
    
    # Template et voix
    template_text = Column(Text, nullable=False)
    voice_engine_id = Column(String(50), nullable=False)
    voice_id = Column(String(100), nullable=False)
    voice_params_json = Column(JSON, nullable=True)  # Paramètres spécifiques au moteur
    
    # Audio
    audio_device = Column(String(100), nullable=True)  # Device ALSA/PulseAudio
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relations
    runtime = relationship("ChannelRuntime", back_populates="channel", uselist=False, cascade="all, delete-orphan")
    tx_history = relationship("TxHistory", back_populates="channel", cascade="all, delete-orphan")


class ChannelRuntime(Base):
    """État runtime d'un canal (dernière mesure, prochaine TX, etc.)."""
    __tablename__ = "channel_runtime"

    channel_id = Column(Integer, ForeignKey("channels.id", ondelete="CASCADE"), primary_key=True)
    last_measurement_at = Column(DateTime, nullable=True)
    last_measurement_hash = Column(String(64), nullable=True)  # Hash pour détecter changements
    last_tx_at = Column(DateTime, nullable=True)
    next_tx_at = Column(DateTime, nullable=True)
    last_error = Column(Text, nullable=True)
    
    # Relation
    channel = relationship("Channel", back_populates="runtime")


class SystemSettings(Base):
    """Paramètres globaux du système (row unique id=1)."""
    __tablename__ = "system_settings"

    id = Column(Integer, primary_key=True, default=1)
    master_enabled = Column(Boolean, default=False, nullable=False)
    poll_interval_seconds = Column(Integer, default=60, nullable=False)
    inter_announcement_pause_seconds = Column(Integer, default=10, nullable=False)
    
    # PTT
    ptt_gpio_pin = Column(Integer, nullable=True)
    ptt_active_level = Column(Integer, default=1, nullable=False)  # 1=HIGH, 0=LOW
    ptt_lead_ms = Column(Integer, default=500, nullable=False)
    ptt_tail_ms = Column(Integer, default=500, nullable=False)
    tx_timeout_seconds = Column(Integer, default=30, nullable=False)  # Verrouillé à 30


class TxHistory(Base):
    """Historique des transmissions (scheduled + manual tests)."""
    __tablename__ = "tx_history"

    id = Column(Integer, primary_key=True)
    tx_id = Column(String(64), unique=True, nullable=False, index=True)  # Hash pour idempotence
    
    channel_id = Column(Integer, ForeignKey("channels.id", ondelete="CASCADE"), nullable=False, index=True)
    mode = Column(String(20), nullable=False)  # SCHEDULED | MANUAL_TEST
    status = Column(String(20), nullable=False, index=True)  # PENDING | SENT | FAILED | ABORTED
    
    # Détails de la transmission
    station_id = Column(String(50), nullable=False)
    measurement_at = Column(DateTime, nullable=False, index=True)
    offset_seconds = Column(Integer, nullable=False)
    planned_at = Column(DateTime, nullable=False)
    sent_at = Column(DateTime, nullable=True)
    
    # Contenu
    rendered_text = Column(Text, nullable=False)
    audio_path = Column(String(500), nullable=True)
    error_message = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relation
    channel = relationship("Channel", back_populates="tx_history")
    
    __table_args__ = (
        Index("idx_tx_history_status_planned", "status", "planned_at"),
    )


class AudioCache(Base):
    """Cache des fichiers audio synthétisés."""
    __tablename__ = "audio_cache"

    id = Column(Integer, primary_key=True)
    tts_cache_key = Column(String(64), unique=True, nullable=False, index=True)
    audio_path = Column(String(500), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_used_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    size_bytes = Column(Integer, nullable=False)
    meta_json = Column(JSON, nullable=True)  # engine_id, voice_id, text preview, etc.


class AuditLog(Base):
    """Journal d'audit des actions administrateur."""
    __tablename__ = "audit_log"

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action = Column(String(100), nullable=False)
    details_json = Column(JSON, nullable=True)
    ip_address = Column(String(45), nullable=True)
