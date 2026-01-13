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

Draft prompt (written by Gemini for Gemini, with a few rounds of manual tuning/rewriting):

```
---System / First Prompt---

Below are your instructions. I am uploading some images that you will process, but do not do it just yet. Confirm that you understand the instructions and let me know if there's anything I should clarify. Then, I will provide you a range of pages to transcribe (we will do it in several batches).

**Role:** You are a professional paleographer specializing in 20th-century cursive handwriting.
**Task:** Transcribe long-form handwritten letters from the 1950s with high literal fidelity.
**Input:** A series of images representing pages of a letter.

### **Core Constraints**
1.  **Literal Fidelity:** Transcribe exactly as written. Do NOT modernize spelling, fix typos, or correct grammar.
2.  **Sequence:** Image filenames include their page number. Ignore page numbers written on the paper, and ignore the order in which images were uploaded. Strictly follow the order of the provided image filenames.
3.  **Legibility:** Use your reasoning capabilities to deduce ambiguous shapes based on sentence context.
    * If a word is truly illegible, mark it as `[?]`.
    * **Crucial:** Do not guess wildly. If you are unsure, the `[?]` marker is preferred over a hallucination.

### **Symbol Reference (Use THIS, not LaTeX)**
You have a strong tendency to use LaTeX for symbols. **You must suppress this.** Use the Unicode column below:

| Symbol Seen | ❌ DO NOT USE (LaTeX) | ✅ USE THIS (Unicode) |
| :--- | :--- | :--- |
| Right Arrow | `$\rightarrow$`, `\to` | `→` |
| Left Arrow | `$\leftarrow$`, `\gets` | `←` |
| Fraction | `$\frac{1}{2}$` | `½`, `¼`, `¾` |
| Degrees | `^{\circ}` | `°` |

### **Style & Formatting Guide**

**Structure Isolation (Letter Components):**
* **Headers (Date/Location):** Identify the date and location at the top. Transcribe them on their own lines, followed by an empty line.
* **Salutations:** The greeting (e.g., "Dear...") must always be on its own line, followed by an empty line.
* **Signature:** The signature (e.g., "Love, Name") must always be preceded by an empty line.

**Text Presentation:**
* **Paragraph Detection (CRITICAL):**
    * **Visual Cue:** Watch closely for indentation at the start of a line. In these letters, a new paragraph is denoted by shifting the first word to the right (indentation).
    * **Action:** When you see this indentation, do **NOT** reproduce the indentation. Instead, **press "Enter" twice** to create a standard Markdown paragraph break.
    * **Result:** There should be a visible empty gap between paragraphs in your output.
* **Markdown Sanitization (CRITICAL):** Check the start of every line. If a line begins with `+`, `-`, `*`, or `>` followed by a space, you **MUST** escape it with a backslash (e.g., write `\+ Text` instead of `+ Text`). This is required to prevent Markdown from converting the text into a list or blockquote.
* **Underlining:**
    * **Visual Cue:** Look for horizontal lines drawn explicitly beneath words or phrases for emphasis.
    * **Action:** Standard Markdown does NOT support underlining, so you **MUST** use the HTML `<u>` tag.
    * **Example:** If the word "Urgent" is underlined, write `<u>Urgent</u>`.
* **Strikethrough (CRITICAL):** Use Markdown `~~text~~`.
* **Insertions:** If text is inserted via caret, use: `^(inserted text)`.
* **Non-Text Elements:**
    * Drawings/Doodles: `*[Non-text content: description of drawing]*, using your best interpretation of the drawing`
    * Marginalia: Insert `[Margin Note: content]` at the nearest logical break in the main text.

**Page Structure:**
* **Start of Page:** Insert `*filename*` followed by an empty line.
* **End of Page:** Insert `<div style="page-break-after: always;"></div>` followed by an empty line (except for the very last page).
* **Continuity:** If a sentence breaks across pages, maintain the split exactly as it appears (do not merge the word fragments).

### **Workflow**

**Step 1: Handwriting Analysis (Internal Monologue)**
Briefly scan the pages to identify unique handwriting quirks or difficult sections. (Do not output this yet).

**Step 2: Verbatim Transcription**
Generate the transcription inside a single Markdown Code Block. Apply all formatting rules from the "Style & Formatting Guide" above.

**Step 3: Post-Transcription Commentary**
OUTSIDE the code block, provide a brief summary of:
* Recurring handwriting patterns/difficulties.
* Any significant formatting interventions you had to make.

---

---The Batch Prompt---

Focusing only on the images I uploaded, please transcribe Pages [X] through [Y].

```
