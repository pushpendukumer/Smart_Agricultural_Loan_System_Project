import base64
import hashlib
import json
import numpy as np
import os
from io import BytesIO
from PIL import Image
from django.conf import settings


try:
    from deepface import DeepFace

    DEEPFACE_AVAILABLE = True
except ImportError:
    DEEPFACE_AVAILABLE = False
    print("Warning: DeepFace not installed. Face verification will not work.")


FACE_MATCH_THRESHOLD = 0.90
DUPLICATE_FACE_THRESHOLD = 0.85
NID_STORAGE_DIR = os.path.join(settings.MEDIA_ROOT, "nid_cards")
FACE_ENCODING_DIR = os.path.join(settings.MEDIA_ROOT, "face_encodings")
os.makedirs(NID_STORAGE_DIR, exist_ok=True)
os.makedirs(FACE_ENCODING_DIR, exist_ok=True)


def decode_base64_image(base64_string):
    try:
        if "," in base64_string:
            base64_string = base64_string.split(",")[1]
        image_data = base64.b64decode(base64_string)
        image = Image.open(BytesIO(image_data))
        if image.mode != "RGB":
            image = image.convert("RGB")
        return image
    except Exception as e:
        print(f"Error decoding base64 image: {e}")
        return None


def validate_nid_format(nid_number):
    if not nid_number:
        return False, "NID number is required"

    if len(nid_number) < 10 or len(nid_number) > 20:
        return False, "NID number must be 10-20 digits"

    if not nid_number.isdigit():
        return False, "NID number must contain only digits"

    return True, "Valid"


def hash_sensitive_data(data):
    return hashlib.sha256(data.encode()).hexdigest()


def extract_face_embedding(image):
    if not DEEPFACE_AVAILABLE:
        return None

    try:
        temp_path = os.path.join(FACE_ENCODING_DIR, "temp_face.jpg")
        image.save(temp_path)

        embedding_obj = DeepFace.represent(
            temp_path,
            model_name="Facenet",
            detector_backend="opencv",
            enforce_detection=True,
        )

        if os.path.exists(temp_path):
            os.remove(temp_path)

        if embedding_obj and len(embedding_obj) > 0:
            return embedding_obj[0].get("embedding")

        return None
    except Exception as e:
        print(f"Error extracting face embedding: {e}")
        if os.path.exists(temp_path):
            os.remove(temp_path)
        return None


def compare_faces(img1_base64, img2_base64):
    if not DEEPFACE_AVAILABLE:
        return {"success": False, "error": "DeepFace not available", "confidence": 0}

    try:
        img1 = decode_base64_image(img1_base64)
        img2 = decode_base64_image(img2_base64)

        if img1 is None or img2 is None:
            return {"success": False, "error": "Invalid images", "confidence": 0}

        temp_path1 = os.path.join(FACE_ENCODING_DIR, "temp1.jpg")
        temp_path2 = os.path.join(FACE_ENCODING_DIR, "temp2.jpg")

        img1.save(temp_path1)
        img2.save(temp_path2)

        result = DeepFace.verify(
            temp_path1,
            temp_path2,
            model_name="Facenet",
            detector_backend="opencv",
            distance_metric="cosine",
            enforce_detection=True,
        )

        os.remove(temp_path1)
        os.remove(temp_path2)

        if result and "verified" in result:
            confidence = 1 - result.get("distance", 1)
            confidence = max(0, min(1, confidence))

            return {
                "success": result["verified"],
                "confidence": confidence,
                "threshold": FACE_MATCH_THRESHOLD,
                "is_match": confidence >= FACE_MATCH_THRESHOLD,
            }

        return {"success": False, "error": "Face comparison failed", "confidence": 0}

    except Exception as e:
        print(f"Error comparing faces: {e}")
        return {"success": False, "error": str(e), "confidence": 0}


def detect_face_in_image(image_base64):
    if not DEEPFACE_AVAILABLE:
        return {"success": False, "error": "DeepFace not available"}

    try:
        image = decode_base64_image(image_base64)

        if image is None:
            return {"success": False, "error": "Invalid image"}

        temp_path = os.path.join(FACE_ENCODING_DIR, "temp_detect.jpg")
        image.save(temp_path)

        embedding = DeepFace.represent(
            temp_path,
            model_name="Facenet",
            detector_backend="opencv",
            enforce_detection=True,
        )

        os.remove(temp_path)

        if embedding and len(embedding) > 0:
            return {
                "success": True,
                "has_face": True,
                "embedding": embedding[0].get("embedding"),
            }

        return {"success": True, "has_face": False}

    except Exception as e:
        error_msg = str(e).lower()
        if "face" in error_msg and "not detected" in error_msg:
            return {"success": True, "has_face": False}
        print(f"Error detecting face: {e}")
        return {"success": False, "error": str(e)}


def check_duplicate_face(new_embedding, exclude_user_id=None):
    if new_embedding is None:
        return {"is_duplicate": False, "matched_user": None}

    try:
        from loan_app.models import User

        users_with_face = User.objects.exclude(face_encoding__isnull=True).exclude(
            face_encoding=""
        )

        if exclude_user_id:
            users_with_face = users_with_face.exclude(id=exclude_user_id)

        for user in users_with_face:
            try:
                stored_encoding = json.loads(user.face_encoding)
                stored_embedding = np.array(stored_encoding)
                new_emb = np.array(new_embedding)

                cosine_similarity = np.dot(stored_embedding, new_emb) / (
                    np.linalg.norm(stored_embedding) * np.linalg.norm(new_emb)
                )

                if cosine_similarity >= DUPLICATE_FACE_THRESHOLD:
                    return {
                        "is_duplicate": True,
                        "matched_user": user.username,
                        "similarity": float(cosine_similarity),
                    }
            except (json.JSONDecodeError, ValueError) as e:
                print(f"Error parsing face encoding for user {user.id}: {e}")
                continue

        return {"is_duplicate": False, "matched_user": None}

    except Exception as e:
        print(f"Error checking duplicate face: {e}")
        return {"is_duplicate": False, "matched_user": None}


def detect_liveness(frames):
    if not frames or len(frames) < 3:
        return {"is_live": False, "reason": "Not enough frames"}

    try:
        embeddings = []

        for frame in frames:
            result = detect_face_in_image(frame)
            if result.get("success") and result.get("has_face"):
                embeddings.append(result.get("embedding"))

        if len(embeddings) < 3:
            return {"is_live": False, "reason": "Not enough valid face detections"}

        max_movement = 0
        for i in range(len(embeddings) - 1):
            emb1 = np.array(embeddings[i])
            emb2 = np.array(embeddings[i + 1])
            distance = np.linalg.norm(emb1 - emb2)
            max_movement = max(max_movement, distance)

        liveness_threshold = 0.3
        if max_movement > liveness_threshold:
            return {"is_live": True, "movement_score": float(max_movement)}
        else:
            return {
                "is_live": False,
                "reason": "No significant movement detected",
                "movement_score": float(max_movement),
            }

    except Exception as e:
        print(f"Error detecting liveness: {e}")
        return {"is_live": False, "reason": str(e)}
