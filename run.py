import os
import re
import time
from PIL import Image
from google import genai
from google.genai import types

"""
# TODO how do you represent the optional arg, conventionally
RUN: python run.py original_pdf_file_to_transcribe.pdf [pages_file.txt]
optional pages_file arg (if doing a retry run with only certain pages; default is the pages{pdf_name}.txt file)
"""

MODEL = 'gemini-2.5-flash-lite'
COOLDOWN = 5
USER_PROMPT = "Transcribe these letter pages, in the following order: {}"
SYSTEM_INSTRUCTION_FILE = "./system_instruction.txt"

client = genai.Client() # No API key needed for free tier

def parse_range(range_str):
    """
    Takes a page range, and converts it to an array
    This flexible formats handle pages scanned out of order
    E.g. '2-5,10,7-9' -> [2, 3, 4, 5, 10, 7, 8, 9]
    """
    pages = []
    for part in range_str.split(','):
        if '-' in part:
            start, end = map(int, part.split('-'))
            pages.extend(range(start, end + 1))
        else:
            pages.append(int(part.strip()))
    return pages

def get_pdf_dir_and_name(pdf_path):
    pdf_name = os.path.splitext(os.path.basename(pdf_path))[0] # name without extension
    return os.path.abspath(pdf_path), pdf_name

# This is mostly AI output, just to have a scaffold; I've put TODOs in where I need to make changes
def transcribe_batch(pdf_path, pages_file=""):

    # TODO it's a little awkward to take the PDF path given that we do nothing with it
    # relying on the preprocessing script but we could add preprocessing here later I suppose
    pdf_dir, pdf_name = get_pdf_dir_and_name(pdf_path)
    image_dir = f"{pdf_dir}/temp_{pdf_name}"
    pages_file = f"{pdf_dir}/pages_{pdf_name}.txt" # making this configurable; e.g. if the thing fails midway through because file not found etc
    output_dir = image_dir

    if not (os.path.exists(image_dir) or os.path.exists(pages_file)):
        # The initialization could be theoretically done in this script,
        # but it's in a bash script for now for easier manual use
        print(f"Project not correctly initialized; {image_dir} and {pages_file} must both exist")

    with open(SYSTEM_INSTRUCTION_FILE, 'r') as f:
        system_instructions = f.read()

    # PARSE PAGE RANGES
    with open(pages_file, 'r') as f:
    # maybe use the word batches in here, it's confusing now
    # TODO can't I use f.readlines(), doesn't strip whitespace but that's fine I think
        range_strings = [line.strip() for line in f if line.strip()]
        pages_list = [parse_range(range_string) for range_string in range_strings]

    for i, pages in enumerate(pages_list):
        print(f"Processing letter {i} of {len(pages_list)}; pages {pages}")

        # BUILD REQUEST
        for num in pages:
            # Matches the 'page-01.png' format (zero-padded)
            file_name = f"page-{num:02d}.png"
            file_path = os.path.join(IMAGE_DIR, file_name)

            if os.path.exists(file_path):
                img = Image.open(file_path)
                content_items.append(img)
            else:
                print(f"Warning: File {file_name} not found. Exiting.")
                sys.exit(1)
        content_items.append(USER_PROMPT.format(pages))

        # TRANSCRIBE PAGES
        try:
            response = client.models.generate_content(
                model=MODEL,
                contents=content_items,
                config=types.GenerateContentConfig(
                    # TODO: any other config for fine tuning?
                    system_instruction=system_instructions
                )
            )

            safe_name = letter_range.replace(',', '_')
            output_path = os.path.join(OUTPUT_DIR, f"letter_{safe_name}.md")

            with open(output_path, 'w', encoding='utf-8') as out_f:
                out_f.write(response.text)
            print(f"Successfully saved transcribed letter {i} with pages {pages}")

        except Exception as e:
            print(f"Error transcribing letter {i} with pages {pages}. Exiting.")
            # we'll exit here so it's obvious that something was missed, but consider continuing
            # also could gracefully handle rate limit errors specifically by sleeping
            sys.exit(1)

        # RATE LIMIT AVOIDANCE
        time.sleep(COOLDOWN)

if __name__ == "__main__":
    # could upgrade to argparse someday, or make this implementation less awkward
    if len(sys.argv) < 1 or len(sys.argv) > 2:
        print("Error: must provide either 1 or 2 arguments")
        sys.exit(1)

    if len(sys.argv) = 1:
        transcribe_batch(sys.argv[1], pages_file=sys.argv[2])

    transcribe_batch(sys.argv[1])
