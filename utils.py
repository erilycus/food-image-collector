from io import BytesIO
from typing import Union
from PIL import Image, UnidentifiedImageError
import streamlit as st
from rich import print

def create_unique_filename() -> str:
    """Generate a unique filename using UUID4."""
    from uuid import uuid4
    return str(uuid4())

def current_timestamp() -> str:
    """Generate a formatted current timestamp string."""
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d-%H-%M-%S")

@st.cache_data(ttl=600, show_spinner=False, max_entries=10)
def display_image(_img: Union[Image.Image, str, BytesIO, bytes], caption: str = "", width: Union[int, str] = 300) -> Image.Image:
    """
    Display an image in Streamlit with caching.

    Args:
        img: The image to display (can be a PIL Image, file path/URL string, or bytes/BytesIO object).
        caption: Optional caption for the image.
    """
    if _img is not None:
        # Ensure we have a PIL Image
        try:
            image = ensure_image(_img)
        except ValueError as e:
            print(f"[bold red]Error:[/bold red] {e}")
            return _img
        # Format caption with metadata
        formatted_caption = format_image_caption(caption)
        # Log metadata to console
        print(f"[bold green]Displaying image with caption:[/bold green]\n{formatted_caption}")
        print(f"[bold green]Dimensions:[/bold green] : {image.width}x{image.height}")
        # Display image in Streamlit
        st.image(image, caption=formatted_caption, width=width, clamp=True, output_format="PNG",)
    return image


def format_image_caption(base_caption: str = "") -> str:
    """
    Format the caption for an image with its metadata.

    Args:
        image: The PIL Image object.
        base_caption: The base caption string.

    Returns:
        Formatted caption string with image metadata.
    """
    if base_caption not in (None, ""):
        caption = base_caption.strip().replace("\n", " ")
    else:
        caption = "Food Image"

    return caption

def ensure_image(img: Union[Image.Image, str, BytesIO, bytes]) -> Image.Image:
    """
    Ensures that the given input is converted into a valid PIL Image.

    Args:
        img: PIL Image, URL/path string, BytesIO, or bytes.

    Returns:
        PIL Image object.
    """
    try:
        # Case 1: Already a PIL Image
        if isinstance(img, Image.Image):
            return img

        # Case 2: If path or URL string
        if isinstance(img, str):
            if img.startswith("http"):
                try:
                    import requests
                    response = requests.get(img, stream=True)
                    response.raise_for_status()
                    return Image.open(response.raw)
                except requests.RequestException as e:
                    raise ValueError(f"Unable to fetch image from URL: {e}")
            else:
                return Image.open(img)

        # Case 3: Bytes or BytesIO
        if isinstance(img, (bytes, bytearray)):
            img = BytesIO(img)

        if isinstance(img, BytesIO):
            im = Image.open(img)
            im.load()  # force-load into memory
            return im

        raise ValueError("Unsupported image input type.")

    except UnidentifiedImageError:
        raise ValueError("Provided input is not a valid image.")
