import io
import re
from datetime import datetime
from typing import Optional

from PIL import Image

from .supabase_client import get_client
from supabase import Client as SupabaseClient

from rich import print

class ImageStore:
    def __init__(self, bucket_name: str, client: Optional[SupabaseClient] = None):
        self.client = client or get_client()
        self.bucket_name = bucket_name or "food-images"
        # Assume bucket exists for simplicity while using anon key
        # self._ensure_bucket_exists()

    def _ensure_bucket_exists(self) -> None:
        """Ensure the storage bucket exists. If not, create it."""
        buckets = self.client.storage.list_buckets()
        if not any(b.name == self.bucket_name for b in buckets):
            self.client.storage.create_bucket(self.bucket_name)

    def upload_image(self, image: Image.Image, filename: str, region: str) -> str:
        """Upload a PIL image to Supabase Storage and return its public URL"""
        img_bytes = io.BytesIO()
        image.save(img_bytes, format='PNG')
        img_bytes = img_bytes.getvalue()

        # Construct path with region folder
        path = f"{region}/{filename}.png"

        # Save to Supabase Storage
        try:
            resp = self.client.storage.from_(self.bucket_name).upload(
                path=path,
                file=img_bytes,
                file_options={
                    "content-type": "image/png",
                    "cacheControl": "3600",
                    "upsert": False
                }
            )
            public_url = self.client.storage.from_(self.bucket_name).get_public_url(path)
            print(f"[bold green]Success:[/bold green] Image uploaded to {public_url}")
        except Exception as e:
            raise RuntimeError(f"Failed to upload image: {e}")
        
        return public_url

