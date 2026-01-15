import argparse
import json
import os
import re
import time
from PIL import Image
from google import genai
from google.genai import types

"""
RUN: python run.py original_pdf_file_to_transcribe.pdf
"""

# Models mapped to a shorthand (used as args and appended to results files)
MODELS = {
    '25fl': 'gemini-2.5-flash-lite', # cheap and adequate at OCR but bad at following instructions, 10 RPM 20 RPD
    '25f': 'gemini-2.5-flash', # cheapish, a bit better than the lite, 5 RPM 20 RPD
    '25p': 'gemini-2.5-pro', # pricey, got a 429 so maybe I can't use it
    '3fp': 'gemini-3-flash-preview', # cheapish, 5 RPM 20 RPD
    #'3pp': 'gemini-3-pro-preview' # I don't get this in the free tier
    }
COOLDOWN = 5
USER_PROMPT = "Transcribe these letter pages, in the following order: {}"
SYSTEM_INSTRUCTION_FILE = "system_instruction.md"

client = genai.Client() # API key loaded from env

def parse_range(range_str):
    """
    Takes a page range, and converts it to an array
    This flexible format handles pages scanned out of order
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
    pdf_file_name = os.path.basename(pdf_path)
    pdf_name = os.path.splitext(pdf_file_name)[0] # name without extension
    return os.path.dirname(os.path.abspath(pdf_path)), pdf_name

def transcribe_batch(pdf_path, pages_file="", model="", skip_letters=[], verbose=False):
    model_name = MODELS[model]
    model_key = model

    if not os.path.exists(pdf_path):
        print(f"Cannot find input file {pdf_path}")
        return

    # TODO it's a little awkward to take the PDF path given that we do nothing with it
    # relying on the preprocessing script but we could add preprocessing here later I suppose
    pdf_dir, pdf_name = get_pdf_dir_and_name(pdf_path)
    image_dir = f"{pdf_dir}/temp_{pdf_name}"
    if pages_file == "" or pages_file is None:
        pages_file = f"{pdf_dir}/pages_{pdf_name}.txt"
    output_dir = image_dir

    if not (os.path.exists(image_dir) and os.path.exists(pages_file)):
        # The initialization could be theoretically done in this script,
        # but it's in a bash script for now for easier manual use
        print(f"Project not correctly initialized; {image_dir} and {pages_file} must both exist")
        return

    with open(SYSTEM_INSTRUCTION_FILE, 'r') as f:
        system_instructions = f.read()

    # PARSE PAGE RANGES
    with open(pages_file, 'r') as f:
    # maybe use the word batches in here, it's confusing now
    # TODO can't I use f.readlines(), doesn't strip whitespace but that's fine I think
        range_strings = [line.strip() for line in f if line.strip()]
        pages_list = [parse_range(range_string) for range_string in range_strings]

    for i, pages in enumerate(pages_list):
        if i in skip_letters:
            print(f"Skipping letter index {i} per user request")
            continue
        print(f"Processing letter index {i} of {len(pages_list)}; pages {pages}")
        start_time = time.time()

        # BUILD REQUEST
        content_items = []
        for num in pages:
            # Matches the 'page-01.png' format (zero-padded)
            file_name = f"page-{num:02d}.png"
            file_path = os.path.join(image_dir, file_name)

            if os.path.exists(file_path):
                img = Image.open(file_path) # Images are about 1.2 mb
                content_items.append(img)
            else:
                print(f"Warning: File {file_name} not found. Exiting.")
                return
        content_items.append(USER_PROMPT.format(pages))

        # TRANSCRIBE PAGES
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=content_items,
                config=types.GenerateContentConfig(
                    # TODO: any other config for fine tuning?
                    system_instruction=system_instructions
                )
            )

            # Log full response if there's an issue
            # Just checking candidates for now because that's one issue I had
            if not response.candidates:
                json_data = response.model_dump_json()
                pretty_json = json.dumps(json.loads(json_data), indent=2)
                if verbose:
                    print(f"FULL RESPONSE: {pretty_json}")
                print("Error: No candidates returned. The request may have been blocked or failed.")
                return

            # Write file (maybe should be done before the candidates check)
            safe_name = '_'.join([f"{num:02d}" for num in pages])
            output_path = os.path.join(output_dir, f"ocr_{model_key}_pages_{safe_name}.md")

            with open(output_path, 'w', encoding='utf-8') as out_f:
                out_f.write(response.text)
            end_time = time.time()
            print(f"Successfully saved transcribed letter {i} with pages {pages}. Total time: {end_time - start_time:.2f} seconds")

            # Some logging
            if verbose:
                # Accessing usage metadata
                usage = response.usage_metadata
                print(f"Prompt Tokens: {usage.prompt_token_count}")
                print(f"Candidates Tokens: {usage.candidates_token_count}")
                print(f"Total Tokens: {usage.total_token_count}")

                # Accessing the model's internal reasoning (if available)
                # (checked that candidates exists already above)
                for part in response.candidates[0].content.parts:
                    if part.thought:
                        # Could consider saving these to file
                        print(f"MODEL REASONING: {part.text}")
                # Check if the response was flagged
                if response.candidates[0].finish_reason == "SAFETY":
                    print("Warning: Content was blocked by safety filters.")


        except Exception as e:
            print(f"Exception: {e}")
            print(f"Error transcribing letter {i} with pages {pages}. Exiting.")
            # we'll exit here so it's obvious that something was missed, but consider continuing
            # also could gracefully handle rate limit errors (429) specifically by sleeping
            return

        # RATE LIMIT AVOIDANCE
        # TODO this should be variable by model
        time.sleep(COOLDOWN)

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="A script to process handwritten letter images with gen AI.")
    parser.add_argument("pdf_path",
        help="The name of the source PDF file to process (not in temp folder).")
    parser.add_argument("--pages_file",
        help="The name of the file containing letter page ranges, if not using the default pages{pdf_name}.txt")
    parser.add_argument("--skip_letters", nargs='+', type=int, default=[],
        help="Space separated list of letter numbers to skip (0-indexed lines in the pages file)")
    parser.add_argument("--model", default="25fl", help="LLM model to use (see map at beginning of file)")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    transcribe_batch(**vars(args))
