import os
import uuid

from werkzeug.utils import secure_filename


def upload_cover_to_supabase(file_storage) -> str | None:
    """
    Uploads a Werkzeug FileStorage to Supabase Storage and returns a public URL.
    Requires env vars:
      SUPABASE_URL
      SUPABASE_SERVICE_ROLE_KEY
      SUPABASE_STORAGE_BUCKET (default: "covers")
    """
    if not file_storage or not getattr(file_storage, "filename", ""):
        return None

    supabase_url = (os.environ.get("SUPABASE_URL") or "").strip()
    service_key = (os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or "").strip()
    bucket = (os.environ.get("SUPABASE_STORAGE_BUCKET") or "covers").strip()

    if not supabase_url or not service_key:
        return None

    # Lazy import so local dev without Supabase is ok
    from supabase import create_client  # type: ignore

    client = create_client(supabase_url, service_key)

    original = secure_filename(file_storage.filename)
    ext = ""
    if "." in original:
        ext = "." + original.rsplit(".", 1)[-1].lower()
    object_name = f"covers/{uuid.uuid4().hex}{ext}"

    content_type = getattr(file_storage, "mimetype", None) or "application/octet-stream"
    data = file_storage.read()
    file_storage.stream.seek(0)

    client.storage.from_(bucket).upload(
        object_name,
        data,
        file_options={
            "content-type": content_type,
            "upsert": "true",
        },
    )

    # Public URL (bucket must be public)
    return f"{supabase_url.rstrip('/')}/storage/v1/object/public/{bucket}/{object_name}"


def upload_pmc_pdf_to_supabase(file_storage) -> str | None:
    """
    Uploads a PDF to Supabase Storage (same bucket as covers by default).
    Returns None if no file, invalid type, or Supabase not configured.
    """
    if not file_storage or not getattr(file_storage, "filename", ""):
        return None

    original = secure_filename(file_storage.filename)
    if not original.lower().endswith(".pdf"):
        return None

    supabase_url = (os.environ.get("SUPABASE_URL") or "").strip()
    service_key = (os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or "").strip()
    bucket = (os.environ.get("SUPABASE_STORAGE_BUCKET") or "covers").strip()

    if not supabase_url or not service_key:
        return None

    from supabase import create_client  # type: ignore

    client = create_client(supabase_url, service_key)

    object_name = f"pmc-pdfs/{uuid.uuid4().hex}.pdf"
    content_type = "application/pdf"
    data = file_storage.read()
    file_storage.stream.seek(0)

    client.storage.from_(bucket).upload(
        object_name,
        data,
        file_options={
            "content-type": content_type,
            "upsert": "true",
        },
    )

    return f"{supabase_url.rstrip('/')}/storage/v1/object/public/{bucket}/{object_name}"

