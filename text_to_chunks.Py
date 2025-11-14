# Smart Text Chunker with Cerebras API (API key included)
# Uses a Cerebras-hosted LLM (e.g., qwen2.5-72b) to intelligently chunk text
#"csk-2yw6jnr9y54k5f45jtxfwj4h2rhf6rr5v2ynye9t92wdhe9j"

# Smart Text Chunker with Cerebras API
# Uses a Cerebras-hosted LLM (e.g., llama3.1-8b) to intelligently chunk text

import sys
import os
import json
import argparse
import requests
from pathlib import Path

CEREBRAS_API_ENDPOINT = "https://api.cerebras.ai/v1/"


# ====== READ FILE ======

def read_text_file(file_path: str) -> str:
    """Read text from a file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading file: {str(e)}")
        sys.exit(1)


# ====== CHUNKING WITH CEREBRAS ======

def chunk_text_with_llm(
    text: str,
    api_key: str,
    model: str = "llama3.1-8b",
    max_chunk_size: int = 2000,
    timeout: int = 300,
):
    print("Analyzing text structure with LLM...")
    print(f"Text length: {len(text)} characters\n")

    num_chunks = max(1, len(text) // max_chunk_size + 1)
    delimiter = "|||---|||"

    prompt = f"""
You are a text processing utility. Your task is to divide the following text into {num_chunks} semantic chunks of about ~{max_chunk_size} characters.

**Rules:**
- Separate each chunk with the delimiter: {delimiter}
- You MUST ONLY output the text chunks and the delimiter.
- Do NOT output any other text, conversation, or any JSON.
- Split the text at natural paragraph or topic boundaries.
- NEVER cut sentences in half.
- Preserve the original order of the text.
- Do NOT summarize or rewrite the text.

**Text to process:**
{text}
"""

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0,
        "stream": False,
    }

    try:
        response = requests.post(
            f"{CEREBRAS_API_ENDPOINT}chat/completions",
            headers=headers,
            json=payload,
            timeout=timeout,
        )

        if response.status_code != 200:
            print(f"API Error: {response.status_code}")
            print(response.text)
            sys.exit(1)

        data = response.json()
        content = data["choices"][0]["message"]["content"].strip()

        # Split the response by the delimiter
        chunks = [chunk.strip() for chunk in content.split(delimiter) if chunk.strip()]

        if not chunks:
            print("Error: Model did not return any valid chunks.")
            print("Raw LLM output:")
            print(content)
            sys.exit(1)

        return chunks

    except requests.exceptions.RequestException as e:
        print(f"Network error: {str(e)}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        sys.exit(1)


# ====== SAVE RESULTS ======

def save_chunks(chunks, output_path: str):
    try:
        output_data = {
            "total_chunks": len(chunks),
            "chunks": [
                {
                    "id": i + 1,
                    "text": chunk,
                    "char_count": len(chunk),
                    "word_count": len(chunk.split()),
                }
                for i, chunk in enumerate(chunks)
            ],
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)

        print(f"\nChunks saved to: {output_path}")
        return output_data

    except Exception as e:
        print(f"Error saving file: {str(e)}")
        sys.exit(1)


# ====== STATS ======

def display_statistics(chunks_data):
    print("\n" + "=" * 60)
    print("CHUNKING STATISTICS")
    print("=" * 60)

    total = chunks_data["total_chunks"]
    print(f"Total chunks: {total}")

    char_counts = [c["char_count"] for c in chunks_data["chunks"]]
    word_counts = [c["word_count"] for c in chunks_data["chunks"]]

    print("\nCharacter counts:")
    print(f"  Avg: {sum(char_counts) / total:.0f}")
    print(f"  Min: {min(char_counts)}")
    print(f"  Max: {max(char_counts)}")

    print("\nWord counts:")
    print(f"  Avg: {sum(word_counts) / total:.0f}")
    print(f"  Min: {min(word_counts)}")
    print(f"  Max: {max(word_counts)}")

    print("\nPreview of first chunk:")
    first_chunk = chunks_data["chunks"][0]["text"]
    print("  " + first_chunk[:200].replace("\n", " ") + "...")


# ====== ARGUMENTS ======

def parse_args():
    parser = argparse.ArgumentParser(
        description="Smart text chunker using Cerebras LLM."
    )
    parser.add_argument("-i", "--input", default="hibernate_extracted.txt")
    parser.add_argument("-o", "--output")
    parser.add_argument("-s", "--chunk-size", type=int, default=2000)
    parser.add_argument("-m", "--model", default="llama3.1-8b")
    parser.add_argument("--timeout", type=int, default=300)
    parser.add_argument(
        "--api-key",
        default=os.environ.get("CEREBRAS_API_KEY"),
        help="Cerebras API key (defaults to CEREBRAS_API_KEY env var).",
    )
    return parser.parse_args()


# ====== MAIN ======

def main():
    args = parse_args()

    # If you REALLY want to hardcode: put your key here instead of None
    HARDCODED_API_KEY = "csk-2yw6jnr9y54k5f45jtxfwj4h2rhf6rr5v2ynye9t92wdhe9j"  # e.g. "csk-XXXX..."

    api_key = HARDCODED_API_KEY or args.api_key
    if not api_key:
        print(
            "Error: No Cerebras API key provided.\n"
            "Set the CEREBRAS_API_KEY environment variable, "
            "use --api-key, or hardcode it in HARDCODED_API_KEY."
        )
        sys.exit(1)

    if args.chunk_size <= 0:
        print("Error: Chunk size must be a positive integer.")
        sys.exit(1)

    input_file = args.input
    output_file = args.output or (Path(input_file).stem + "_chunks.json")

    print("Smart Text Chunker (Cerebras Edition)")
    print("=" * 60)
    print(f"Input file: {input_file}")
    print(f"Output file: {output_file}")
    print(f"Chunk size: {args.chunk_size}")
    print(f"Model: {args.model}")
    print("=" * 60)

    text = read_text_file(input_file)

    chunks = chunk_text_with_llm(
        text=text,
        api_key=api_key,
        model=args.model,
        max_chunk_size=args.chunk_size,
        timeout=args.timeout,
    )

    print(f"\nSuccessfully created {len(chunks)} semantic chunks.")

    chunks_data = save_chunks(chunks, output_file)
    display_statistics(chunks_data)


if __name__ == "__main__":
    main()
