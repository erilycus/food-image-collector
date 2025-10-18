import os
import io
import requests
from datetime import datetime
from rich import pretty, print, traceback

import streamlit as st
from PIL import Image

from storage import ImageStore, MetadataStore
from streamlit.runtime.uploaded_file_manager import UploadedFile 
from utils import create_unique_filename, display_image, ensure_image

# Load for better error messages and debugging
pretty.install()
traceback.install()

# Initialize Storage and MetadataStore with environment variables
image_store = ImageStore(os.getenv("SUPABASE_STORAGE_BUCKET", "food-images"))
metadata_store = MetadataStore(os.getenv("SUPABASE_METADATA_TABLE", "image_metadata"))

# UI: Title and Description
st.title("🍕 Food Image Collector for Machine Learning")
st.write("Upload food images along with metadata to build a dataset for ML models.")

# UI: Image File Uploader
st.subheader("📤 Upload your food image")
uploaded_file: UploadedFile = st.file_uploader(
    label="Upload a food image",
    type=["jpg", "jpeg", "png"]
)


if uploaded_file is not None:
    # UI: Display uploaded image preview with caching
    st.markdown("Preview of Uploaded Image:")
    uploaded_image: Image.Image = display_image(
        uploaded_file,
        caption=str(uploaded_file.name.strip()) if uploaded_file else "No image uploaded yet.",
        width='stretch'
    )

    # Generate unique filename
    unique_image_id = create_unique_filename()
    
    # Make Timestamp
    current_time = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")

    # Ask for Metadata inputs
    st.subheader("📝 Please provide image metadata fields")
    labels = st.text_input("Enter labels for this image (e.g., 'pizza', 'salad', etc.)", "food_image")
    region = st.text_input("Enter region (e.g., 'US', 'EU', etc.)", "US")

    # Upload image object to Storage
    if st.button("📤 Upload"):
        with st.spinner("Uploading image..."):
            try:
                # Ensure we have a PIL Image
                image = ensure_image(uploaded_image)
                # Receive public URL after upload
                public_url = image_store.upload_image(image, filename=unique_image_id, region=region)

                # Save metadata to MetadataStore
                response = metadata_store.add_metadata(
                    filename=unique_image_id,
                    url=public_url,
                    width=image.width,
                    height=image.height,
                    labels=labels,
                    region=region,
                )

                if response:
                    print(f"[bold green]Success:[/bold green] \n Image uploaded from {region}!")
                    st.success("✅ Image and metadata uploaded successfully! Thanks for your contribution. 🙏")
                else:
                    st.error("❌ Failed to upload metadata.")
            except Exception as e:
                st.error(f"Error during upload: {e}")

else:
    # Display a default sample image when no file is uploaded
    st.markdown("No image uploaded yet. Here's a sample image:")
    image_url: str = "https://diurvyoemqqvltfqpbmc.supabase.co/storage/v1/object/public/public_images/food_image_sample.jpg"
    display_image(image_url, caption="Default Sample Image", width='stretch')

st.markdown("---")
st.markdown("Developed by Dev Mukherjee. Powered by Supabase and Streamlit.")

# Handle any errors gracefully
try:
    pass
except Exception as e:
    st.cache_resource.clear()
    st.error(f"An error occurred: {e}")
    st.stop()
