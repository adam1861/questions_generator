import sys
import os
import json
import argparse
import requests
from pathlib import Path
import time

CEREBRAS_API_ENDPOINT = "https://api.cerebras.ai/v1/"

def read_structure_from_file(file_path):
    """Read structure from a JSON file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error reading structure from file: {str(e)}")
        sys.exit(1)

def generate_questions_for_node(topic, api_key, model, timeout):
    """Generates 5 QCM questions for a single topic."""
    print(f"  Generating questions for: {topic}")
    prompt = f"""
You are a quiz generation utility. Your task is to create 5 multiple-choice questions (QCM) for the following topic.

**Rules:**
- You MUST output ONLY a single valid JSON array of question objects, enclosed in ```json ... ``` markdown fences.
- Each question object must have three fields:
    1. "question": The question text (string).
    2. "options": An array of 4 answer choices (strings). These choices should be similar to make the question challenging.
    3. "correct_answer": The correct answer from the "options" array (string).
- Do not include any conversational text, just the JSON block.

**Topic:**
{topic}
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
            print(f"    API Error: {response.status_code} - {response.text}")
            return None

        data = response.json()
        content = data["choices"][0]["message"]["content"].strip()

        # New, more robust parsing logic
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
            start_index = content.find('[')
            end_index = content.rfind(']')
            if start_index != -1 and end_index != -1:
                json_content = content[start_index:end_index+1]

        if not json_content:
            print(f"    Error: No JSON array found for topic: {topic}")
            print(f"    Raw output: {content}")
            return None

        try:
            return json.loads(json_content)
        except json.JSONDecodeError:
            print(f"    Error decoding JSON for topic: {topic}")
            print(f"    Raw output: {content}")
            return None

    except requests.exceptions.RequestException as e:
        print(f"    Network error for topic {topic}: {str(e)}")
        return None

def traverse_and_generate(node, api_key, model, timeout):
    """Recursively traverses the structure and generates questions for each node."""
    if isinstance(node, dict):
        # Generate questions for the current node's title
        if 'title' in node:
            questions = generate_questions_for_node(node['title'], api_key, model, timeout)
            if questions:
                node['questions'] = questions
            time.sleep(1) # Add a small delay to avoid hitting API rate limits

        # Recursively process child nodes
        for key, value in node.items():
            if key != 'questions': # Avoid processing the newly added questions
                traverse_and_generate(value, api_key, model, timeout)

    elif isinstance(node, list):
        for item in node:
            traverse_and_generate(item, api_key, model, timeout)

def save_quiz(quiz, output_path):
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(quiz, f, indent=2, ensure_ascii=False)
        print(f"\nQuiz saved to: {output_path}")
    except Exception as e:
        print(f"Error saving file: {str(e)}")
        sys.exit(1)

def parse_args():
    parser = argparse.ArgumentParser(description="Generate quiz from structured text using Cerebras LLM.")
    parser.add_argument("-i", "--input", default="hibernate_extracted_chunks_structure.json")
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
    output_file = args.output or (Path(input_file).stem + "_quiz.json")

    print("Quiz Generation (Cerebras Edition)")
    print("=" * 60)
    print(f"Input file: {input_file}")
    print(f"Output file: {output_file}")
    print(f"Model: {args.model}")
    print("=" * 60)

    structure = read_structure_from_file(input_file)
    
    print("Generating questions for each section...")
    traverse_and_generate(
        node=structure,
        api_key=api_key,
        model=args.model,
        timeout=args.timeout,
    )

    save_quiz(structure, output_file)
    print("\nQuiz generation complete.")

if __name__ == "__main__":
    main()