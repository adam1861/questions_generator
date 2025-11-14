# PDF Text Extractor
# Extracts text content from PDF files and saves it to a text file.

import argparse
import PyPDF2
from pathlib import Path


def extract_text_from_pdf(pdf_path):
    """
    Extract text from a PDF file.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        Extracted text as a string
    """
    text_content = []
    
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            num_pages = len(pdf_reader.pages)
            
            print(f"Processing {num_pages} pages...")
            
            for page_num in range(num_pages):
                page = pdf_reader.pages[page_num]
                text = page.extract_text()
                text_content.append(f"--- Page {page_num + 1} ---\n{text}\n")
                print(f"Extracted page {page_num + 1}/{num_pages}")
            
            return "\n".join(text_content)
    
    except FileNotFoundError:
        print(f"Error: File '{pdf_path}' not found.")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)


def save_text_to_file(text, output_path):
    """
    Save extracted text to a file.
    
    Args:
        text: Text content to save
        output_path: Path for the output file
    """
    try:
        with open(output_path, 'w', encoding='utf-8') as file:
            file.write(text)
        print(f"\nText saved to: {output_path}")
    except Exception as e:
        print(f"Error saving file: {str(e)}")
        sys.exit(1)


def parse_args():
    parser = argparse.ArgumentParser(description="Extract text from a PDF into a text file.")
    parser.add_argument(
        "pdf_path",
        nargs="?",
        default="hibernate.pdf",
        help="Path to the PDF to process (defaults to hibernate.pdf).",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Destination text file (defaults to <pdf_stem>_extracted.txt).",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    pdf_path = args.pdf_path

    output_path = args.output or (Path(pdf_path).stem + "_extracted.txt")
    
    print(f"Extracting text from: {pdf_path}")
    
    # Extract text
    extracted_text = extract_text_from_pdf(pdf_path)
    
    # Save to file
    save_text_to_file(extracted_text, output_path)
    
    # Display statistics
    char_count = len(extracted_text)
    word_count = len(extracted_text.split())
    print(f"\nStatistics:")
    print(f"  Characters: {char_count:,}")
    print(f"  Words: {word_count:,}")


if __name__ == "__main__":
    main()
