import asyncio
import aiohttp
import asyncpg
from PIL import Image
from io import BytesIO
from bs4 import BeautifulSoup
import base64


# Fetch images from Google
async def fetch_images(query, max_images):
    async with aiohttp.ClientSession() as session:
        url = f"https://www.google.com/search?q={query}&tbm=isch"
        headers = {"User-Agent": "Mozilla/5.0"}
        async with session.get(url, headers=headers) as response:
            html = await response.text()

        soup = BeautifulSoup(html, "html.parser")
        image_elements = soup.find_all("img", limit=max_images)
        image_urls = [img['src'] for img in image_elements if 'src' in img.attrs]

        return image_urls


# Download and resize images
async def download_and_resize(url, session, resize_to=(256, 256)):
    try:
        async with session.get(url) as response:
            if response.status == 200:
                image_data = await response.read()
                image = Image.open(BytesIO(image_data)).convert("RGB")
                image = image.resize(resize_to)
                buffer = BytesIO()
                image.save(buffer, format="JPEG")
                return base64.b64encode(buffer.getvalue()).decode("utf-8")
    except Exception as e:
        print(f"Error processing image {url}: {e}")
    return None


# Save images to PostgreSQL
async def save_to_postgres(image_data, db_config):
    try:
        conn = await asyncpg.connect(**db_config)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS images (
                id SERIAL PRIMARY KEY,
                data BYTEA NOT NULL
            )
        """)
        for image in image_data:
            await conn.execute("INSERT INTO images (data) VALUES ($1)", image)
        await conn.close()
    except Exception as e:
        print(f"Database error: {e}")


# Main function
async def main(query, max_images, db_config):
    image_data = []
    async with aiohttp.ClientSession() as session:
        image_urls = await fetch_images(query, max_images)
        tasks = [download_and_resize(url, session) for url in image_urls]
        results = await asyncio.gather(*tasks)
        image_data = [img for img in results if img]

    await save_to_postgres(image_data, db_config)

# PostgreSQL configuration
db_config = {
    "user": "your_user",
    "password": "your_password",
    "database": "your_database",
    "host": "localhost",
    "port": 5432,
}

# Inputs
query = "cute kittens"
max_images = 5

# Run the script
if __name__ == "__main__":
    asyncio.run(main(query, max_images, db_config))