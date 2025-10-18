import requests
import streamlit as st
from PIL import Image
from storage import ImageStore, MetadataStore

st.title("🍕 Food Image Collector with Supabase")
st.write("Upload and store food images along with metadata in Supabase!")

image_store = ImageStore()
metadata_store = MetadataStore()

uploaded_file = st.file_uploader("Upload a food image", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption="Uploaded Image", width='stretch')
    # Upload button
    if st.button("📤 Upload"):
        with st.spinner("Uploading image..."):
            public_url = image_store.upload_image(image, filename=uploaded_file.name)
            metadata_store.add_metadata(filename=uploaded_file.name, url=public_url, source="user_upload")
        st.success("Image uploaded successfully!")
        st.markdown(f"**Public URL:** {public_url}")
else:
    image = Image.open(requests.get("https://picsum.photos/300/200", stream=True).raw)
    st.image(image, caption="Default Sample Image", width='stretch')

st.markdown("---")
st.subheader("📦 Stored Images")
data = metadata_store.list_metadata()

if not data:
    st.info("No images stored yet.")
else:
    for item in data:
        st.image(item["url"], caption=item["filename"], width=200)
        st.caption(f"🕓 {item['uploaded_at']} | 📍 Source: {item['source']}")

# Handle any errors gracefully
try:
    # Main logic here
    pass
except Exception as e:
    st.cache_resource.clear()
    st.error(f"An error occurred: {e}")
    st.stop()
