import time
from google import genai
from google.genai import types

MODEL = 'gemini-2.5-flash-lite'
COOLDOWN = 15
ERRORSLEEP = 60

client = genai.Client()

# This is mostly AI output, just to have a scaffold; I've put TODOs in where I need to make changes
def transcribe_batch(pdf_path):
    print(f"Uploading {pdf_path}...")
    # TODO: each batch of images is uploaded separately
    # 1. Upload once (Free storage for 48 hours)
    myfile = client.files.upload(file=pdf_path)

    # TODO: chunks will be defined in the letter pages files
    # 2. Process in Large Chunks (10 pages per request)
    # This maximizes your Free Tier RPD (Requests Per Day)
    chunk_size = 10
    total_pages = 50

    for i in range(0, total_pages, chunk_size):
        start, end = i + 1, min(i + chunk_size, total_pages)
        print(f"Processing pages {start} to {end}...")

        try:
            # TODO: where to include system prompt? better to do with each individual prompt?
            # TODO: change prompts to assume that all provided images will be transcribed
            response = client.models.generate_content(
                model=MODEL,
                contents=[
                    myfile,
                    f"Transcribe pages {start} through {end} exactly. "
                    "Maintain original line breaks. Use [?] for unreadable words."
                ]
            )

            # TODO: wrong output
            with open("transcription.txt", "a") as f:
                f.write(f"\n--- PAGES {start}-{end} ---\n")
                f.write(response.text)

            # TODO: tune this
            # 3. Add a "Politeness Delay"
            # Free tier usually allows 2-15 RPM (Requests Per Minute).
            # Sleeping 10-20 seconds ensures you don't get 429 errors.
            print(f"Success. Cooling down for 15 seconds...")
            time.sleep(COOLDOWN)

        except Exception as e:
            print(f"Rate limit or error hit: {e}. Waiting 1 minute...")
            time.sleep(ERRORSLEEP)

if __name__ == "__main__":
    # TODO: file name should be an input arg
    transcribe_batch("letters.pdf")
