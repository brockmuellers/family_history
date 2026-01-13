#!/bin/bash
# Pre-processing for OCR of a PDF containing multiple handwritten letters
# Creates a new "temp" working directory, and copies the input PDF into it
# If there is not yet a text file defining the pages of each letter, make it
# Finally, split the PDF to a series of images for OCR
set -euo pipefail

# Extract the directory name from the input pdf's full path
PDF_PATH=$(readlink -f "$1")
PDF_DIR=$(dirname "$PDF_PATH")
PDF_FILE_NAME=$(basename "$PDF_PATH")
PDF_NAME="${PDF_FILE_NAME%.*}" # the filename without extension

# Make the working dir and copy the original PDF into it
# If the working dir already exists, we'll exit early with an error
TEMP_DIR="${PDF_DIR}/temp_${PDF_NAME}"
mkdir "$TEMP_DIR"
cp "$PDF_PATH" "${TEMP_DIR}/original.pdf"
echo "Created directory ${TEMP_DIR} and copied original PDF"

# The file defining letter pages may already exist, but create it if it doesn't
# If it is empty, warn the user that it must be filled in before processing
PAGES_FILE_PATH="${PDF_DIR}/pages_${PDF_NAME}.txt"
touch "$PAGES_FILE_PATH"
if [[ -s "$PAGES_FILE_PATH" ]]; then
    echo "File ${PAGES_FILE_PATH} exists and has been filled in."
else
    YELLOW='\e[33m'
    NORMAL='\e[0m' # Reset to normal text
    printf "${YELLOW}WARNING: You must define the page ranges of each individual letter in ${PAGES_FILE_PATH} before OCR processing.${NORMAL}"
fi

# Split to images, which will be written to the working dir
# Rely on this to crash if the input is not a pdf
echo "Generating images..."
pdftoppm -png "$PDF_PATH" "${TEMP_DIR}/page"
echo "Generated images from PDF\nSuccess: file ready for OCR processing!"
