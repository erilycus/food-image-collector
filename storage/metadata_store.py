from datetime import datetime
from .supabase_client import get_client


class MetadataStore:
    def __init__(self, client=None):
        self.client = client or get_client()
        # self.ensure_table_exists() # Assume table exists for simplicity
        
    def ensure_table_exists(self):
        """Ensure the metadata table exists"""
        tables = self.client.rpc("pg_tables").execute().data
        if not any(t["tablename"] == "image_metadata" for t in tables):
            self.client.rpc("""
            CREATE TABLE image_metadata (
                id SERIAL PRIMARY KEY,
                filename TEXT NOT NULL,
                url TEXT NOT NULL,
                uploaded_at TIMESTAMP NOT NULL,
                source TEXT
            );
            """).execute()

    def add_metadata(self, filename: str, url: str, source: str = "unknown"):
        """Insert metadata for uploaded image"""
        data = {
            "filename": filename,
            "url": url,
            "uploaded_at": datetime.utcnow().isoformat(),
            "source": source,
        }
        self.client.table("image_metadata").insert(data).execute()

    def list_metadata(self):
        """Fetch all metadata records"""
        result = self.client.table("image_metadata").select("*").order("uploaded_at", desc=True).execute()
        return result.data or []