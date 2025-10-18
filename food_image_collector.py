import os
import io
import logging
from datetime import datetime
from rich.logging import RichHandler
from rich import pretty, traceback
from dotenv import load_dotenv

import streamlit as st
from PIL import Image

from storage import ImageStore, MetadataStore
from streamlit.runtime.uploaded_file_manager import UploadedFile 
from utils import create_unique_filename, display_image, ensure_image

# === Setup Pretty Errors and Debugging ===
pretty.install()
traceback.install()

# === Load Environment Variables ===
load_dotenv()
if not os.getenv("SUPABASE_URL") or not (os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")):
    raise EnvironmentError("Supabase environment variables are not set properly. Please check your .env file.")

# === Configure Logging ===
LOG_DIR = os.path.join(os.path.dirname(__file__), "logs")
os.makedirs(LOG_DIR, exist_ok=True)

log_file = os.path.join(LOG_DIR, f"upload_{datetime.now().strftime('%Y-%m-%d')}.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="[%Y-%m-%d %H:%M:%S]",
    handlers=[
        RichHandler(markup=True, rich_tracebacks=True),
        # Add a file handler for logging to a file [FIXME: Add other service]
        logging.FileHandler(log_file, encoding="utf-8"),
    ],
)

logger = logging.getLogger("food_image_uploader")

# === Initialize Stores ===
image_store = ImageStore(os.getenv("SUPABASE_STORAGE_BUCKET", "food-images"))
metadata_store = MetadataStore(os.getenv("SUPABASE_METADATA_TABLE", "image_metadata"))


def upload_image_with_metadata(
    image: Image.Image,
    unique_id: str,
    labels: str,
    region: str
) -> str:
    """
    Upload an image and its metadata atomically.
    If metadata upload fails, the image is deleted to maintain consistency.
    """
    logger.info(f"Starting upload transaction for image '{unique_id}' (region={region})")

    try:
        # Step 1: Upload image
        public_url = image_store.upload_image(image, filename=unique_id, region=region)
        logger.info(f"[green]Image uploaded successfully:[/green] {public_url}")

        try:
            # Step 2: Upload metadata
            response = metadata_store.add_metadata(
                filename=unique_id,
                url=public_url,
                width=image.width,
                height=image.height,
                labels=labels,
                region=region,
            )
            logger.info(f"Metadata added for image '{unique_id}'")

        except Exception as meta_err:
            # Rollback image if metadata upload fails
            logger.error(f"[red]Metadata upload failed for {unique_id}:[/red] {meta_err}")
            image_store.delete_image(unique_id, region=region)
            logger.warning(f"Rolled back image '{unique_id}' from storage")
            raise Exception(f"Metadata upload failed: {meta_err}. Image deleted.")

        return public_url

    except Exception as e:
        logger.exception(f"[red]Upload failed for image '{unique_id}':[/red] {e}")
        raise Exception(f"Image upload failed: {e}")


# === Streamlit UI ===
st.title("🍕 Food Image Collector for Machine Learning")
st.write("Upload food images along with metadata to build a dataset for ML models.")

st.subheader("📤 Upload your food image")
uploaded_file: UploadedFile = st.file_uploader(
    label="Upload a food image",
    type=["jpg", "jpeg", "png"]
)

if uploaded_file is not None:
    st.markdown("Preview of Uploaded Image:")
    uploaded_image: Image.Image = display_image(
        uploaded_file,
        caption=str(uploaded_file.name.strip()) if uploaded_file else "No image uploaded yet.",
        width='stretch'
    )

    unique_image_id = create_unique_filename()
    current_time = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")

    st.subheader("📝 Please provide image metadata fields")
    labels = st.text_input("Enter labels for this image (e.g., 'pizza', 'salad', etc.)", "food_image")
    region = st.text_input("Enter region (e.g., 'US', 'EU', etc.)", "US")

    if st.button("📤 Upload"):
        with st.spinner("Uploading image..."):
            try:
                image = ensure_image(uploaded_image)
                public_url = upload_image_with_metadata(
                    image=image,
                    unique_id=unique_image_id,
                    labels=labels,
                    region=region
                )
                st.success(f"✅ Image and metadata uploaded successfully! Thanks for your contribution. 🙏")
                logger.info(f"[green]Upload completed successfully for {unique_image_id}[/green]")
            except Exception as e:
                st.error(f"❌ Upload failed: {e}")
                logger.error(f"[red]Upload failed for {unique_image_id}: {e}[/red]")

else:
    st.markdown("No image uploaded yet. Here's a sample image:")
    image_url = "https://diurvyoemqqvltfqpbmc.supabase.co/storage/v1/object/public/public_images/food_image_sample.jpg"
    display_image(image_url, caption="Default Sample Image", width='stretch')

st.markdown("---")
st.markdown("Developed by Dev Mukherjee. Powered by Supabase and Streamlit.")
