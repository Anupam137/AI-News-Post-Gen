import asyncio
import httpx
from crawl4ai import *

# Replace this with your actual Groq API key
GROQ_API_KEY = "key here danny"
GROQ_MODEL = "gemma2-9b-it"

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


async def main():
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url="https://www.nbcnews.com/business",
        )
        print("[INFO] Fetched and scraped NBC Business page.")

        try:
            parsed = await parse_headlines_with_groq(result.markdown)
            print("\n📰 Parsed Headlines:\n")
            print(parsed)

        except httpx.HTTPStatusError as e:
            print(f"\n❌ HTTP Error {e.response.status_code}")
            print(f"Response: {e.response.text}")
        except Exception as ex:
            print(f"\n❌ Unexpected error: {str(ex)}")


if __name__ == "__main__":
    asyncio.run(main())
