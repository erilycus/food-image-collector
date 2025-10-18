import os
import streamlit as st
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Environment variables
_SUPABASE_URL: str = os.getenv("SUPABASE_URL")
_SUPABASE_SERVICE_ROLE_KEY: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
_SUPABASE_ANON_KEY: str = os.getenv("SUPABASE_ANON_KEY")
_SUPABASE_SCHEMA: str = os.getenv("SUPABASE_SCHEMA", "public")

_client: Client | None = None


@st.cache_resource(show_spinner=False)
def get_client() -> Client:
    """
    Returns a singleton Supabase client instance.
    Automatically prefers the service role key if available,
    falling back to anon key for read-only operations.
    """
    global _client
    if _client is None:
        if not _SUPABASE_URL:
            raise ValueError("SUPABASE_URL not set in environment variables.")

        # Prefer service role key for backend/server operations
        key_to_use = _SUPABASE_SERVICE_ROLE_KEY or _SUPABASE_ANON_KEY
        if not key_to_use:
            raise ValueError("No Supabase key found. Set SUPABASE_SERVICE_ROLE_KEY or SUPABASE_ANON_KEY.")

        _client = create_client(
            supabase_url=_SUPABASE_URL,
            supabase_key=key_to_use
        )
    return _client
