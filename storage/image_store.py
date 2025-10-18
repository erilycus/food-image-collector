import io
import re
from datetime import datetime
from PIL import Image
from .supabase_client import get_client

def sanitize_filename(filename: str) -> str:
    """Sanitize filename for Supabase Storage"""
    filename = filename.replace(" ", "_")
    filename = re.sub(r"[^A-Za-z0-9_\-\.]", "", filename)
    return f"{int(datetime.now().timestamp())}_{filename}"

class ImageStore:
    def __init__(self, bucket_name="food-images", client=None):
        self.client = client or get_client()
        self.bucket_name = bucket_name
        # self._ensure_bucket_exists() # Assume bucket exists for simplicity

    def _ensure_bucket_exists(self):
        """Ensure the storage bucket exists"""
        buckets = self.client.storage.list_buckets()
        if not any(b.name == self.bucket_name for b in buckets):
            self.client.storage.create_bucket(self.bucket_name)

    def upload_image(self, image: Image.Image, filename: str = None) -> str:
        """Upload a PIL image to Supabase Storage and return its public URL"""
        if filename is None:
            filename = f"image_{int(datetime.now().timestamp())}.png"
        elif not filename.endswith((".png", ".jpg", ".jpeg")):
            raise ValueError("Filename must end with .png, .jpg, or .jpeg")
        else:
            filename = sanitize_filename(filename)        
        
        img_bytes = io.BytesIO()
        image.save(img_bytes, format="PNG")
        img_bytes = img_bytes.getvalue()

        self.client.storage.from_(self.bucket_name).upload(filename, img_bytes, {"content-type": "image/png"})
        public_url = self.client.storage.from_(self.bucket_name).get_public_url(filename)
        return public_url
    
    def preview_image(self, filename: str) -> Image.Image:
        """Download and return an image as a PIL Image object"""
        response = self.client.storage.from_(self.bucket_name).download(filename)
        img_bytes = io.BytesIO(response)
        image = Image.open(img_bytes)
        return image
