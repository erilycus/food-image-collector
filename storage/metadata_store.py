from datetime import datetime
from typing import Optional

from .supabase_client import get_client
from supabase import Client as SupabaseClient

from rich import print

class MetadataStore:
    def __init__(self, table_name: str , client: Optional[SupabaseClient] = None):
        self.client = client or get_client()
        self.table_name = table_name or "image_metadata"
        # Assume table exists for simplicity while using anon key
        # self.ensure_table_exists()
        
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

    def add_metadata(self, filename: str, url: str, width: int, height: int, labels: str, region: str) -> None:
        """Insert metadata for uploaded image"""
        data = {
            "_id": filename,
            "image_url": url,
            "image_width": width,
            "image_height": height,
            "image_ext": url.split('.')[-1],  # Optional: extract from URL if needed
            "uploaded_at": datetime.utcnow().isoformat(),
            "image_source": "streamlit_public_app",
            "upload_region": region, 
            "labels": labels,
        }
        # Execute insert Query
        self.client.table(self.table_name).insert(data).execute()
        print(f"[bold green]Success:[/bold green] Metadata for {filename} added to {self.table_name}")
        return True