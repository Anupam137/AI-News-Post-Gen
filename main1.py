import asyncio
import httpx
import json
from datetime import datetime
from crawl4ai import *
from PIL import Image, ImageDraw, ImageFont
import os
from instagrapi import Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Keys
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = "gemma2-9b-it"
INSTAGRAM_USERNAME = os.getenv("INSTAGRAM_USERNAME")
INSTAGRAM_PASSWORD = os.getenv("INSTAGRAM_PASSWORD")

# News sources to scrape
NEWS_SOURCES = [
    "https://www.nbcnews.com/business",
    "https://www.bbc.com/news/business",
    "https://www.reuters.com/business/"
]

async def parse_headlines_with_groq(content):
    # Truncate content if it's too long
    if len(content) > 12000:
        content = content[:12000]

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    messages = [
        {
            "role": "system",
            "content": "You are a helpful assistant that extracts news headlines from webpage content. Format them as a JSON list with title, category, and URL."
        },
        {
            "role": "user",
            "content": f"""Extract all the news headlines from this scraped content:

\"\"\"{content}\"\"\"

Return them in this format:
[
  {{
    "title": "Example headline",
    "category": "Business",
    "url": "https://example.com/story"
  }},
  ...
]
"""
        }
    ]

    body = {
        "model": GROQ_MODEL,
        "messages": messages,
        "temperature": 0.2
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=body
        )

        # Debugging logs
        print("[DEBUG] Status:", response.status_code)
        print("[DEBUG] Text:", response.text)

        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]

async def generate_news_image(headlines):
    # Create a new image with a white background
    width, height = 1080, 1080  # Instagram square format
    image = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(image)
    
    # Add a title
    title = "Daily News Digest"
    font = ImageFont.truetype("arial.ttf", 60)
    draw.text((width/2, 50), title, fill='black', font=font, anchor="mm")
    
    # Add headlines
    y_position = 150
    for headline in headlines[:5]:  # Show top 5 headlines
        draw.text((50, y_position), f"• {headline['title']}", fill='black', font=ImageFont.truetype("arial.ttf", 30))
        y_position += 60
    
    # Save the image
    image_path = f"news_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
    image.save(image_path)
    return image_path

async def post_to_instagram(image_path, headlines):
    # Initialize Instagram client
    cl = Client()
    cl.login(INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD)
    
    # Create caption from headlines
    caption = "📰 Daily News Digest\n\n"
    for headline in headlines[:5]:
        caption += f"• {headline['title']}\n"
    caption += "\n#news #dailynews #businessnews"
    
    # Upload the image
    cl.photo_upload(image_path, caption)
    
    # Clean up
    os.remove(image_path)

async def main():
    all_headlines = []
    
    async with AsyncWebCrawler() as crawler:
        for source in NEWS_SOURCES:
            try:
                result = await crawler.arun(url=source)
                print(f"[INFO] Fetched and scraped {source}")
                
                parsed = await parse_headlines_with_groq(result.markdown)
                headlines = json.loads(parsed)
                all_headlines.extend(headlines)
                
            except Exception as e:
                print(f"[ERROR] Failed to scrape {source}: {str(e)}")
    
    if all_headlines:
        # Generate and post image
        image_path = await generate_news_image(all_headlines)
        await post_to_instagram(image_path, all_headlines)
        print("[INFO] Successfully posted to Instagram")
    else:
        print("[ERROR] No headlines were scraped")

if __name__ == "__main__":
    asyncio.run(main())
