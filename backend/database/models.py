"""
AgriVersion - Relational Database Schema & SQLAlchemy Models
Models: User, Farm, Field, Prediction, Conversation, Message, MessageImage, DiseaseInfo, AdminLog
"""

from datetime import datetime
import json
from backend.database.db import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(20), nullable=True)
    location = db.Column(db.String(120), nullable=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default="user")  # 'user' or 'admin'
    preferred_lang = db.Column(db.String(10), default="en")
    voice_pref = db.Column(db.String(50), default="default")
    avatar = db.Column(db.String(255), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    farms = db.relationship("Farm", backref="owner", lazy=True, cascade="all, delete-orphan")
    predictions = db.relationship("Prediction", backref="user", lazy=True, cascade="all, delete-orphan")
    conversations = db.relationship("Conversation", backref="user", lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "full_name": self.full_name,
            "username": self.username,
            "email": self.email,
            "phone": self.phone,
            "location": self.location,
            "role": self.role,
            "preferred_lang": self.preferred_lang,
            "voice_pref": self.voice_pref,
            "avatar": self.avatar,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S")
        }


class Farm(db.Model):
    __tablename__ = "farms"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    location = db.Column(db.String(120), nullable=False)
    total_area = db.Column(db.Float, default=1.0)  # in acres
    soil_type = db.Column(db.String(80), default="Alluvial / Clayey Loam")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    fields = db.relationship("Field", backref="farm", lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "location": self.location,
            "total_area": self.total_area,
            "soil_type": self.soil_type,
            "fields_count": len(self.fields),
            "created_at": self.created_at.strftime("%Y-%m-%d")
        }


class Field(db.Model):
    __tablename__ = "fields"

    id = db.Column(db.Integer, primary_key=True)
    farm_id = db.Column(db.Integer, db.ForeignKey("farms.id"), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    crop_variety = db.Column(db.String(100), default="IR64 / Sona Masoori")
    sowing_date = db.Column(db.String(50), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship
    predictions = db.relationship("Prediction", backref="field", lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "farm_id": self.farm_id,
            "farm_name": self.farm.name if self.farm else "",
            "name": self.name,
            "crop_variety": self.crop_variety,
            "sowing_date": self.sowing_date,
            "notes": self.notes,
            "scans_count": len(self.predictions),
            "created_at": self.created_at.strftime("%Y-%m-%d")
        }


class Prediction(db.Model):
    __tablename__ = "predictions"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    field_id = db.Column(db.Integer, db.ForeignKey("fields.id"), nullable=True)
    
    # Image file paths
    image_filename = db.Column(db.String(255), nullable=False)
    gradcam_filename = db.Column(db.String(255), nullable=True)
    severity_mask_filename = db.Column(db.String(255), nullable=True)
    report_pdf_filename = db.Column(db.String(255), nullable=True)

    # Diagnostic results
    disease_name = db.Column(db.String(100), nullable=False)
    confidence = db.Column(db.Float, nullable=False)
    severity_level = db.Column(db.String(50), default="Healthy")
    healthy_area_pct = db.Column(db.Float, default=100.0)
    affected_area_pct = db.Column(db.Float, default=0.0)
    lesion_count = db.Column(db.Integer, default=0)
    top_predictions_json = db.Column(db.Text, nullable=True)
    is_low_confidence = db.Column(db.Boolean, default=False)
    # Image upload location & geolocation
    location_name = db.Column(db.String(150), nullable=True)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    location_source = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        top_preds = []
        if self.top_predictions_json:
            try:
                top_preds = json.loads(self.top_predictions_json)
            except Exception:
                top_preds = []

        return {
            "id": self.id,
            "user_id": self.user_id,
            "field_id": self.field_id,
            "field_name": self.field.name if self.field else None,
            "farm_name": self.field.farm.name if (self.field and self.field.farm) else None,
            "image_url": f"/uploads/{self.image_filename}" if self.image_filename else None,
            "gradcam_url": f"/uploads/{self.gradcam_filename}" if self.gradcam_filename else None,
            "severity_mask_url": f"/uploads/{self.severity_mask_filename}" if self.severity_mask_filename else None,
            "report_pdf_url": f"/static_reports/{self.report_pdf_filename}" if self.report_pdf_filename else None,
            "disease_name": self.disease_name,
            "confidence": self.confidence,
            "severity_level": self.severity_level,
            "healthy_area_pct": self.healthy_area_pct,
            "affected_area_pct": self.affected_area_pct,
            "lesion_count": self.lesion_count,
            "top_predictions": top_preds,
            "is_low_confidence": self.is_low_confidence,
            "location_name": self.location_name,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "location_source": self.location_source,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S")
        }


class Conversation(db.Model):
    __tablename__ = "conversations"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    title = db.Column(db.String(200), default="Rice Leaf Consultation")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    messages = db.relationship("Message", backref="conversation", lazy=True, cascade="all, delete-orphan", order_by="Message.created_at")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "title": self.title,
            "messages_count": len(self.messages),
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "updated_at": self.updated_at.strftime("%Y-%m-%d %H:%M:%S")
        }


class Message(db.Model):
    __tablename__ = "messages"

    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey("conversations.id"), nullable=False)
    sender = db.Column(db.String(20), nullable=False)  # 'user' or 'assistant'
    text_content = db.Column(db.Text, nullable=False)
    audio_url = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship for multi-image uploads
    images = db.relationship("MessageImage", backref="message", lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "conversation_id": self.conversation_id,
            "sender": self.sender,
            "text_content": self.text_content,
            "audio_url": self.audio_url,
            "images": [img.to_dict() for img in self.images],
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S")
        }


class MessageImage(db.Model):
    __tablename__ = "message_images"

    id = db.Column(db.Integer, primary_key=True)
    message_id = db.Column(db.Integer, db.ForeignKey("messages.id"), nullable=False)
    image_filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "image_url": f"/uploads/{self.image_filename}",
            "original_filename": self.original_filename
        }


class DiseaseInfo(db.Model):
    __tablename__ = "disease_info"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(80), unique=True, nullable=False)
    name_en = db.Column(db.String(120), nullable=False)
    scientific_name = db.Column(db.String(150), nullable=True)
    pathogen_type = db.Column(db.String(80), nullable=True)
    description = db.Column(db.Text, nullable=True)
    symptoms = db.Column(db.Text, nullable=True)
    causes = db.Column(db.Text, nullable=True)
    prevention = db.Column(db.Text, nullable=True)
    management = db.Column(db.Text, nullable=True)
    severity_info = db.Column(db.Text, nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "code": self.code,
            "name_en": self.name_en,
            "scientific_name": self.scientific_name,
            "pathogen_type": self.pathogen_type,
            "description": self.description,
            "symptoms": self.symptoms,
            "causes": self.causes,
            "prevention": self.prevention,
            "management": self.management,
            "severity_info": self.severity_info
        }


class AdminLog(db.Model):
    __tablename__ = "admin_logs"

    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, nullable=True)
    action = db.Column(db.String(100), nullable=False)
    target = db.Column(db.String(255), nullable=True)
    details = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "admin_id": self.admin_id,
            "action": self.action,
            "target": self.target,
            "details": self.details,
            "timestamp": self.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        }


def format_relative_time(dt):
    """Generates human-readable relative time strings (e.g. '18 minutes ago')."""
    if not dt:
        return "Unknown"
    now = datetime.utcnow()
    diff = now - dt
    seconds = int(diff.total_seconds())

    if seconds < 0:
        return "Just now"
    if seconds < 60:
        return "Just now"
    if seconds < 3600:
        mins = seconds // 60
        return f"{mins} minute{'s' if mins > 1 else ''} ago"
    if seconds < 86400:
        hours = seconds // 3600
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    if seconds < 172800:
        return "Yesterday"
    days = seconds // 86400
    if days < 30:
        return f"{days} days ago"
    months = days // 30
    return f"{months} month{'s' if months > 1 else ''} ago"


class Store(db.Model):
    __tablename__ = "stores"

    id = db.Column(db.Integer, primary_key=True)
    store_name = db.Column(db.String(150), nullable=False, index=True)
    owner_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    owner_name = db.Column(db.String(120), nullable=True)
    phone = db.Column(db.String(30), nullable=False)
    email = db.Column(db.String(120), nullable=True)
    whatsapp = db.Column(db.String(30), nullable=True)
    website = db.Column(db.String(255), nullable=True)
    address = db.Column(db.Text, nullable=False)
    city = db.Column(db.String(100), nullable=False, index=True)
    district = db.Column(db.String(100), nullable=False, index=True)
    state = db.Column(db.String(100), default="Karnataka")
    pincode = db.Column(db.String(20), nullable=False, index=True)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    opening_hours = db.Column(db.String(120), default="08:00 AM - 08:00 PM (Mon-Sat)")
    is_open_now = db.Column(db.Boolean, default=True)
    verification_status = db.Column(db.String(30), default="verified")  # 'verified', 'pending', 'rejected', 'suspended'
    license_number = db.Column(db.String(100), nullable=True)
    rating = db.Column(db.Float, default=4.8)
    reviews_count = db.Column(db.Integer, default=0)
    categories_json = db.Column(db.Text, nullable=True)  # JSON array of category names
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    products = db.relationship("Product", backref="store", lazy=True, cascade="all, delete-orphan", order_by="Product.product_name")
    reviews = db.relationship("StoreReview", backref="store", lazy=True, cascade="all, delete-orphan", order_by="StoreReview.created_at.desc()")
    requests = db.relationship("StoreRequest", backref="store", lazy=True, cascade="all, delete-orphan")

    def get_categories(self):
        if not self.categories_json:
            return ["Fungicides", "Bactericides", "Fertilizers & Micronutrients", "Bio-control"]
        try:
            return json.loads(self.categories_json)
        except Exception:
            return ["Fungicides", "Bactericides", "Fertilizers"]

    def to_dict(self, include_products=False, user_lat=None, user_lng=None):
        categories = self.get_categories()
        products_list = [p.to_dict() for p in self.products] if include_products else []

        # Find latest inventory update timestamp
        latest_inv_time = None
        for p in self.products:
            if not latest_inv_time or (p.last_updated and p.last_updated > latest_inv_time):
                latest_inv_time = p.last_updated

        # Summary of availability
        in_stock_count = sum(1 for p in self.products if p.stock_status == "in_stock")
        limited_count = sum(1 for p in self.products if p.stock_status == "limited_stock")
        out_count = sum(1 for p in self.products if p.stock_status == "out_of_stock")

        if in_stock_count > 0:
            overall_stock = "in_stock"
        elif limited_count > 0:
            overall_stock = "limited_stock"
        elif len(self.products) > 0 and out_count == len(self.products):
            overall_stock = "out_of_stock"
        else:
            overall_stock = "unknown"

        # Check freshness (stale if older than 3 days)
        is_fresh = True
        if latest_inv_time:
            diff_days = (datetime.utcnow() - latest_inv_time).total_seconds() / 86400.0
            if diff_days > 3.0:
                is_fresh = False
        else:
            is_fresh = False

        data = {
            "id": self.id,
            "store_name": self.store_name,
            "owner_id": self.owner_id,
            "owner_name": self.owner_name,
            "phone": self.phone,
            "email": self.email,
            "whatsapp": self.whatsapp,
            "website": self.website,
            "address": self.address,
            "city": self.city,
            "district": self.district,
            "state": self.state,
            "pincode": self.pincode,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "opening_hours": self.opening_hours,
            "is_open_now": self.is_open_now,
            "verification_status": self.verification_status,
            "is_verified": self.verification_status == "verified",
            "license_number": self.license_number,
            "rating": round(self.rating, 1),
            "reviews_count": len(self.reviews) if self.reviews else self.reviews_count,
            "categories": categories,
            "total_products": len(self.products),
            "in_stock_count": in_stock_count,
            "limited_count": limited_count,
            "overall_stock": overall_stock,
            "latest_inventory_update": latest_inv_time.strftime("%Y-%m-%d %H:%M:%S") if latest_inv_time else None,
            "inventory_freshness_text": format_relative_time(latest_inv_time),
            "is_inventory_fresh": is_fresh,
            "created_at": self.created_at.strftime("%Y-%m-%d")
        }

        if include_products:
            data["products"] = products_list
            data["reviews"] = [r.to_dict() for r in self.reviews[:10]]

        return data


class Product(db.Model):
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    store_id = db.Column(db.Integer, db.ForeignKey("stores.id"), nullable=False, index=True)
    product_name = db.Column(db.String(150), nullable=False)
    category = db.Column(db.String(80), nullable=False, index=True)  # 'Fungicide', 'Bactericide', 'Insecticide', 'Bio-control', 'Fertilizer & Micronutrient', 'Seed Treatment', 'Farming Tool'
    active_ingredient = db.Column(db.String(200), nullable=False)
    manufacturer = db.Column(db.String(120), nullable=False)
    pack_size = db.Column(db.String(50), nullable=False)
    price = db.Column(db.Float, nullable=True)  # Published price in INR
    stock_status = db.Column(db.String(30), default="in_stock")  # 'in_stock', 'limited_stock', 'out_of_stock', 'unknown'
    target_diseases_json = db.Column(db.Text, nullable=True)  # JSON array of diseases
    dosage_label_info = db.Column(db.Text, nullable=True)
    safety_guidelines = db.Column(db.Text, nullable=True)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = db.Column(db.String(80), default="Retail Store Manager")

    def get_target_diseases(self):
        if not self.target_diseases_json:
            return []
        try:
            return json.loads(self.target_diseases_json)
        except Exception:
            return []

    def to_dict(self):
        diff_days = (datetime.utcnow() - (self.last_updated or datetime.utcnow())).total_seconds() / 86400.0
        return {
            "id": self.id,
            "store_id": self.store_id,
            "store_name": self.store.store_name if self.store else None,
            "product_name": self.product_name,
            "category": self.category,
            "active_ingredient": self.active_ingredient,
            "manufacturer": self.manufacturer,
            "pack_size": self.pack_size,
            "price": self.price,
            "stock_status": self.stock_status,
            "target_diseases": self.get_target_diseases(),
            "dosage_label_info": self.dosage_label_info,
            "safety_guidelines": self.safety_guidelines,
            "last_updated": self.last_updated.strftime("%Y-%m-%d %H:%M:%S") if self.last_updated else None,
            "last_updated_relative": format_relative_time(self.last_updated),
            "is_fresh": diff_days <= 3.0,
            "updated_by": self.updated_by
        }


class StoreRequest(db.Model):
    __tablename__ = "store_requests"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    store_id = db.Column(db.Integer, db.ForeignKey("stores.id"), nullable=True)
    product_category = db.Column(db.String(80), nullable=False)
    disease_name = db.Column(db.String(100), nullable=True)
    product_name_query = db.Column(db.String(150), nullable=True)
    user_name = db.Column(db.String(120), nullable=True)
    user_phone = db.Column(db.String(30), nullable=True)
    user_email = db.Column(db.String(120), nullable=True)
    location = db.Column(db.String(150), nullable=True)
    status = db.Column(db.String(30), default="pending")  # 'pending', 'notified', 'fulfilled'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "store_id": self.store_id,
            "store_name": self.store.store_name if self.store else "Any Nearby Store",
            "product_category": self.product_category,
            "disease_name": self.disease_name,
            "product_name_query": self.product_name_query,
            "user_name": self.user_name,
            "user_phone": self.user_phone,
            "user_email": self.user_email,
            "location": self.location,
            "status": self.status,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S")
        }


class StoreReview(db.Model):
    __tablename__ = "store_reviews"

    id = db.Column(db.Integer, primary_key=True)
    store_id = db.Column(db.Integer, db.ForeignKey("stores.id"), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    user_name = db.Column(db.String(120), default="Local Farmer")
    rating = db.Column(db.Integer, default=5)
    comment = db.Column(db.Text, nullable=False)
    is_moderated = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "store_id": self.store_id,
            "user_id": self.user_id,
            "user_name": self.user_name,
            "rating": self.rating,
            "comment": self.comment,
            "is_moderated": self.is_moderated,
            "created_at": self.created_at.strftime("%Y-%m-%d")
        }

