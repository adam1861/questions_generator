
import sys
import os
import json
import argparse
import requests
from pathlib import Path

CEREBRAS_API_ENDPOINT = "https://api.cerebras.ai/v1/"

def read_chunks_from_file(file_path):
    """Read chunks from a JSON file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data["chunks"]
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
        sys.exit(1)
    except (KeyError, json.JSONDecodeError) as e:
        print(f"Error reading chunks from file: {str(e)}")
        sys.exit(1)

def structure_chunks_with_llm(chunks, api_key, model="llama3.1-8b", timeout=300):
    print("Structuring chunks with LLM...")
    
    text_content = "\n\n".join([chunk["text"] for chunk in chunks])

    prompt = f"""
You are a content structuring utility. Your task is to analyze the following text and organize it into a hierarchical JSON structure.

**JSON Structure Rules:**
- The root should be a single JSON object.
- The levels of the hierarchy should be: `course` -> `modules` -> `mini_modules` -> `concepts` -> `mini_concepts`.
- You MUST output ONLY a single valid JSON object, enclosed in ```json ... ``` markdown fences.
- Do not include any conversational text, just the JSON block.

**Text to process:**
{text_content}
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

        # Final, most robust parsing logic
        json_content = None
        if '```json' in content:
            start = content.find('```json') + len('```json')
            end = content.find('```', start)
            json_content = content[start:end].strip()
        elif '```' in content:
            start = content.find('```') + len('```')
            end = content.find('```', start)
            json_content = content[start:end].strip()
        else:
            # Fallback for responses without markdown fences
            start_index = content.find('{')
            end_index = content.rfind('}')
            if start_index != -1 and end_index != -1:
                json_content = content[start_index:end_index+1]

        if not json_content:
            print("Error: Could not find a valid JSON block in the model's response.")
            print("Raw LLM output:")
            print(content)
            sys.exit(1)

        try:
            structure = json.loads(json_content)
        except json.JSONDecodeError as e:
            print("Error decoding model response as JSON:")
            print("Extracted content to parse:")
            print(json_content)
            print("\nJSON error:", str(e))
            sys.exit(1)

        return structure

    except requests.exceptions.RequestException as e:
        print(f"Network error: {str(e)}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        sys.exit(1)

def save_structure(structure, output_path):
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(structure, f, indent=2, ensure_ascii=False)
        print(f"\nStructure saved to: {output_path}")
    except Exception as e:
        print(f"Error saving file: {str(e)}")
        sys.exit(1)

def parse_args():
    parser = argparse.ArgumentParser(description="Structure text chunks using Cerebras LLM.")
    parser.add_argument("-i", "--input", default="hibernate_extracted_chunks.json")
    parser.add_argument("-o", "--output")
    parser.add_argument("-m", "--model", default="llama3.1-8b")
    parser.add_argument("--timeout", type=int, default=300)
    parser.add_argument(
        "--api-key",
        default=os.environ.get("CEREBRAS_API_KEY"),
        help="Cerebras API key (defaults to CEREBRAS_API_KEY env var).",
    )
    return parser.parse_args()

def main():
    args = parse_args()

    # WARNING: Hardcoding API keys is a security risk.
    api_key = "csk-2yw6jnr9y54k5f45jtxfwj4h2rhf6rr5v2ynye9t92wdhe9j"
    if not api_key:
        print(
            "Error: No Cerebras API key provided. "
            "Set the CEREBRAS_API_KEY environment variable or pass --api-key."
        )
        sys.exit(1)

    input_file = args.input
    output_file = args.output or (Path(input_file).stem + "_structure.json")

    print("Chunk Structuring (Cerebras Edition)")
    print("=" * 60)
    print(f"Input file: {input_file}")
    print(f"Output file: {output_file}")
    print(f"Model: {args.model}")
    print("=" * 60)

    chunks = read_chunks_from_file(input_file)
    
    structure = structure_chunks_with_llm(
        chunks=chunks,
        api_key=api_key,
        model=args.model,
        timeout=args.timeout,
    )

    save_structure(structure, output_file)
    print("\nStructuring complete.")

if __name__ == "__main__":
    main()
