"""Private Supabase Storage integration for UBC media uploads."""
import uuid
from urllib.parse import quote
import requests
from flask import current_app

MAX_UPLOAD_BYTES = 8 * 1024 * 1024
MIME_EXTENSIONS = {
    b"\x89PNG\r\n\x1a\n": ("image/png", "png"),
    b"\xff\xd8\xff": ("image/jpeg", "jpg"),
    b"GIF87a": ("image/gif", "gif"),
    b"GIF89a": ("image/gif", "gif"),
}

class StorageError(RuntimeError):
    """The storage provider rejected or failed the operation."""

class StorageNotConfigured(StorageError):
    """Supabase credentials are missing from the server environment."""

def _settings():
    base_url=(current_app.config.get("SUPABASE_URL") or "").rstrip("/")
    service_key=current_app.config.get("SUPABASE_SERVICE_ROLE_KEY") or ""
    bucket=current_app.config.get("SUPABASE_STORAGE_BUCKET") or "ubc-media"
    if not base_url or not service_key:
        raise StorageNotConfigured("Supabase Storage is not configured.")
    return base_url,service_key,bucket

def is_storage_reference(value):
    return isinstance(value,str) and value.startswith("storage://")

def _file_type(data):
    for signature,result in MIME_EXTENSIONS.items():
        if data.startswith(signature):
            return result
    if len(data)>=12 and data[:4]==b"RIFF" and data[8:12]==b"WEBP":
        return "image/webp","webp"
    raise ValueError("Formato inválido. Envie PNG, JPG, WebP ou GIF.")

def upload_media(file_storage,kind="tournaments"):
    if kind not in ("tournaments","achievements"):
        raise ValueError("Categoria de mídia inválida.")
    data=file_storage.read(MAX_UPLOAD_BYTES+1)
    if not data:
        raise ValueError("O arquivo está vazio.")
    if len(data)>MAX_UPLOAD_BYTES:
        raise ValueError("O arquivo ultrapassa o limite de 8 MB.")
    mime_type,extension=_file_type(data)
    base_url,service_key,bucket=_settings()
    object_path=f"{kind}/{uuid.uuid4().hex}.{extension}"
    endpoint=f"{base_url}/storage/v1/object/{quote(bucket,safe='')}/{quote(object_path,safe='/')}"
    try:
        response=requests.post(endpoint,headers={"Authorization":f"Bearer {service_key}","apikey":service_key,"Content-Type":mime_type,"x-upsert":"false"},data=data,timeout=30)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise StorageError("Supabase upload failed.") from exc
    return f"storage://{object_path}"

def signed_media_url(reference):
    if not reference:
        return None
    if not is_storage_reference(reference):
        return reference
    base_url,service_key,bucket=_settings()
    object_path=reference[len("storage://"):]
    if not object_path or ".." in object_path.split("/") or object_path.startswith("/"):
        return None
    ttl=max(60,min(int(current_app.config.get("SUPABASE_STORAGE_SIGNED_URL_TTL",3600)),604800))
    endpoint=f"{base_url}/storage/v1/object/sign/{quote(bucket,safe='')}/{quote(object_path,safe='/')}"
    try:
        response=requests.post(endpoint,headers={"Authorization":f"Bearer {service_key}","apikey":service_key},json={"expiresIn":ttl},timeout=10)
        response.raise_for_status()
        signed_path=response.json().get("signedURL")
        if not signed_path:
            raise StorageError("Supabase did not return a signed URL.")
        if signed_path.startswith(("http://","https://")):
            return signed_path
        suffix=signed_path if signed_path.startswith("/") else "/"+signed_path
        return f"{base_url}/storage/v1{suffix}"
    except (requests.RequestException,ValueError,TypeError) as exc:
        raise StorageError("Could not create a signed media URL.") from exc
