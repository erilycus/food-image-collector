import os
import streamlit as st
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env.development')
load_dotenv(dotenv_path)

_SUPABASE_URL: str = os.environ.get("SUPABASE_URL")
_SUPABASE_KEY: str = os.environ.get("SUPABASE_KEY")
_SUPABASE_SCHEMA: str = os.environ.get("SUPABASE_SCHEMA", "public")

# Global client instance (singleton)
_client: Client | None = None

@st.cache_resource(show_spinner=False)
def get_client() -> Client:
    """
    Returns a singleton Supabase client instance.
    Cached across Streamlit reruns for efficiency.
    """
    global _client
    if _client is None:
        if not _SUPABASE_URL or not _SUPABASE_KEY:
            raise ValueError("Supabase URL or Key not set in environment variables.")
        _client = create_client(
            supabase_url=_SUPABASE_URL,
            supabase_key=_SUPABASE_KEY
        )
    return _client
