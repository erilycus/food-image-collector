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
st.title("Fit Freak Food Image Collector 🍕")
st.write("Upload a photo of what you eat, along with some metadata to build a massive food dataset that powers FitFreak's Food Engine! 🚀")

st.subheader("Upload your food image 📤")
uploaded_file: UploadedFile = st.file_uploader(
    label="Upload a food image",
    type=["jpg", "jpeg", "png"]
)

if uploaded_file is not None:
    st.markdown("Preview of Uploaded Image 🖼:")
    uploaded_image: Image.Image = display_image(
        uploaded_file,
        caption=str(uploaded_file.name.strip()) if uploaded_file else "No image uploaded yet.",
        width='stretch'
    )

    unique_image_id = create_unique_filename()
    current_time = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")

    st.subheader("Please provide some additional information about the image 📝")
    labels = st.text_input("What food is in the image? (e.g., 'pizza', 'salad', etc.)")
    region = st.text_input("Where is this food from? (e.g., 'US', 'EU', etc.)", "US")

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
    # When no image is uploaded
    st.markdown("### No image uploaded yet.😶")

# UI: FAQ Section
st.write("## FAQ")
with st.expander("What happens to my image?"):
    st.write(
        """
    When you click "upload image", your image gets stored on FitFreak servers\
    Here's a pretty picture which describes it in more detail:
    """
    )
    st.image("https://diurvyoemqqvltfqpbmc.supabase.co/storage/v1/object/public/public_images/image-uploading-workflow-with-background.png", caption="Image Uploading Workflow", width="content")
    st.write(
        "Later on, images in the database will be used to train a computer \
            vision model to power FitFreak Food Engine."
    )
with st.expander("Why do we need images of food?"):
    st.write(
        """
    Machine learning models learn by looking at many different examples \
        of things.\n
    Food included.\n
    Eventually, FitFreak wants to be an app you can use to *take a photo of \
        food and learn about it*.\n
    To do so, we'll need many different examples of foods to build a \
        computer vision model capable of identifying almost anything you can eat.\n
    And the more images of food you upload, the better the models will get.
    Your contributions will help make FitFreak better for everyone! 🙏\n
    """
    )
# UI: Source Code Link
st.markdown(
    "View the source code for this page on \
        [GitHub](https://github.com/erilycus/food-image-collector)."
)
st.markdown("---")

