# family_history

A tool to process handwritten letters and produce a more readable PDF, using Gemini-backed OCR.

**Input:** PDF scans that contain multiple cursive handwritten letters over a given time period. The PDF files are 20-70 pages long, and each letter is around 2-8 pages long. Some of the paper was thin and the ink bled through to the reverse side - a bit of a challenge for OCR. Plus, some of the handwriting is not the clearest.

**Output:** A PDF containing both the original and transcribed content. Realistically, I won't proofread all of the pages, and cursive went out of vogue in my elementary school years so I'm not qualified to do so anyway. Due to the potential challenges faced in the transcription, I want to make it easy for a reader to refer back to the original source if anything is confusing. I plan to interleave the original pages with the transcribed pages.

The optimal strategy would be to use the Google AI API with the flagship model, but I don't really want to pay for it. Just for the learning experience, I'm going to code this up with whatever lightweight model is available on the free tier. To get the prompt just right, I'll play around with the test file in regular Gemini chat, using Gemini 3 Pro. Once I'm happy with the performance, I'll likely go through the AI Studio UI to get the best transcriptions possible - over the course of a few days due to request limits.

General strategy:
* I'm going to do this as a python script - python should have all of the libraries required. I'll generate a test file with two letters, one long and one short.
* ~~As I understand it, I do not need to convert the PDFs to images first, so I will upload an entire PDF and then prompt the model to transcribe the content in batches, one prompt per batch.~~ Reading the chat model's "thinking", I discovered that it only has access to some preliminary OCR output, not the original PDF. Whether that's true or not of the API, I'll split the PDF into images just to be safe.
  * I'll start by using the entirety of each individual letter as a batch. This provides context for the model to guess at unclear words.
  * Batch page ranges will be saved as a text file alongside the images. (I expect to do some tweaking, or maybe I'll want to run the whole thing through again when a better model comes out, so I'll appreciate having the batches saved.)
  * Sleep for a bit between requests, depending on RPM. Handle "request limit exceeded" errors gracefully.
* Results will be saved as text files alongside the images, along with timestamps (or versioning?).
* In a separate script (because rate limiting will likely make the OCR a multi-step process), I will interleave the original scans with the processed text in a single large output PDF.

Potential improvements:
* For longer letters, experiment with using smaller batches to see if that improves results.
* Experiment with image pre-processing to improve contrast and clarity. Consider pillow?

Random notes:
* Chatting with AI about how to use AI inherently results in very out of date advice. The google AI API repo includes a prompt to use with Gemini with up to date instructions.
* Formatting has been the most difficult bit of this - the model uses both markdown and latex, and I cannot get it to stop using latex. The latex would in theory would work well with pandoc, but I've found that the latex processing trips over unusual character sequences too much. It also struggles to understand that markdown requires two newlines between paragraphs.
* Packages installed: `pip install google-genai fpdf2`; CLI tools used: mdtopdf, pdftoppm; consider pillow if images need cleaning
* I'll start with `gemini-2.5-flash-lite` for development, because it seems to have the highest RPD/RPM. If, after playing around with flash vs pro in chat, I determine that flash is good enough for my needs, I'll use `gemini-3-flash-preview`, with requests split over multiple days, for a final transcription. [Free tier availability found here.](https://ai.google.dev/gemini-api/docs/pricing)
* I've instructed the model to use a separator between pages, so I can interleave them properly later.
* In the prompt, play around with strategies to improve transcription. If there are specific characters that it gets wrong (a writer forms certain letters to look like others; maybe certain names or words appear frequently that can be used as an anchor), provide guidance to improve recognition.

The main prompt can be found in system_instruction.md.

