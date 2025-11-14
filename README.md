# ICodex Model – PDF to Quiz Pipeline

Turn any PDF into a structured, multi-choice quiz.  
This repository strings together a small set of CLI utilities that extract raw text, chunk it with a Cerebras-hosted LLM, build a hierarchical outline, ask the LLM for quiz questions, and finally render everything as a printable PDF.

## Features
- **End-to-end workflow** from `something.pdf` to `something_quiz.pdf`.
- **Semantic chunking + outlining** powered by Cerebras chat completions.
- **Multiple-choice generation** with JSON outputs you can reuse elsewhere.
- **ReportLab PDF export** with an auto-generated answer key.

## Repository Layout
| File | Description |
| --- | --- |
| `pdf_to_text.py` | Extracts raw text from a PDF into `<pdf>_extracted.txt`. |
| `text_to_chunks.Py` | Calls the LLM to break the text into semantic chunks and stores metadata in JSON. |
| `chunks_to_structure.py` | Builds a hierarchical course → module → concept structure from the chunks. |
| `structure_to_questions.Py` | Generates five QCM questions per node and appends them to the structure JSON. |
| `quiz_to_pdf.py` | Converts the quiz JSON into a formatted PDF with an answer key. |
| `requirements.txt` | Minimal runtime dependencies (`PyPDF2`, `requests`, `reportlab`). |

## Prerequisites
- Python 3.10+ is recommended (anything with `venv` and `pip` support should work).
- A Cerebras inference API key with access to the models you reference (default scripts use `llama3.1-8b`).
- C compiler is **not** required; everything installs via `pip`.

### Environment
```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```
> On macOS/Linux use `source .venv/bin/activate`.

### Configure your Cerebras key
Never keep production API keys in source control. All scripts accept `--api-key`, but the cleanest approach is the environment variable:
```powershell
$Env:CEREBRAS_API_KEY = "csk-your-key"
```
Linux/macOS:
```bash
export CEREBRAS_API_KEY="csk-your-key"
```
Remove the placeholder keys in the source files before making the repository public.

## Typical Workflow
Every script can be run independently, but they are designed to be chained. Replace `hibernate` with your own filename stem.

1. **PDF → text**
   ```powershell
   python pdf_to_text.py reports\hibernate.pdf -o hibernate_extracted.txt
   ```
2. **Text → semantic chunks**
   ```powershell
   python text_to_chunks.Py -i hibernate_extracted.txt -o hibernate_extracted_chunks.json --chunk-size 2000 --model llama3.1-8b
   ```
3. **Chunks → hierarchical structure**
   ```powershell
   python chunks_to_structure.py -i hibernate_extracted_chunks.json -o hibernate_extracted_chunks_structure.json
   ```
4. **Structure → MCQ quiz**
   ```powershell
   python structure_to_questions.Py -i hibernate_extracted_chunks_structure.json -o hibernate_extracted_chunks_structure_quiz.json
   ```
5. **Quiz JSON → printable PDF**
   ```powershell
   python quiz_to_pdf.py -i hibernate_extracted_chunks_structure_quiz.json -o hibernate_extracted_chunks_structure_quiz.pdf
   ```

> Each script prints progress information (page counts, chunk stats, section names, etc.) so you can monitor the run without additional logging.

## Command Reference

### `pdf_to_text.py`
- **Required:** path to a PDF (defaults to `hibernate.pdf`).
- **Flags:** `-o/--output` for the destination text file.

### `text_to_chunks.Py`
- **Flags:** `-i/--input`, `-o/--output`, `-s/--chunk-size` (default 2000 chars), `-m/--model`, `--timeout`, `--api-key`.
- Produces a JSON blob with metadata for each chunk plus summary statistics printed to the console.

### `chunks_to_structure.py`
- **Flags:** same pattern (`-i`, `-o`, `-m`, `--timeout`, `--api-key`).
- Returns a nested JSON object (`course → modules → mini_modules → concepts → mini_concepts`) with any additional keys the LLM emits.

### `structure_to_questions.Py`
- **Flags:** `-i`, `-o`, `-m`, `--timeout`, `--api-key`.
- Each node containing a `title` gets a `questions` array appended. Questions follow the `{question, options[4], correct_answer}` schema.

### `quiz_to_pdf.py`
- **Flags:** `-i/--input` JSON quiz path, `-o/--output` PDF path.
- Builds a PDF with styled headings plus an answer key appended at the end.

## Working With Your Own Content
1. Drop your PDF into the repository (or provide an absolute path).
2. Run the pipeline shown above, adjusting chunk size or model per your needs.
3. Inspect intermediate artifacts (`*_chunks.json`, `*_structure.json`, etc.) before moving to the next phase. Because each step emits JSON, you can also plug those files into other systems or perform QA checks.

### Tuning Tips
- **Chunk size:** Decrease for more granular outlines; increase to reduce API calls.
- **Model choice:** Any Cerebras model ID works as long as the account has access. For knowledge-dense PDFs, try more capable models (e.g., `llama3.1-70b`).
- **Rate limiting:** The scripts include small sleeps but you may need longer delays or batching if processing huge trees.
- **Retries:** If an API call fails, rerun the relevant step; artifacts from previous steps remain unchanged.

## Troubleshooting
- *LLM response is not valid JSON:* The scripts already try to strip Markdown fences; check the console output, adjust the prompt, or re-run the step.
- *Requests timeout:* Increase `--timeout`, ensure your network allows outbound HTTPS to `api.cerebras.ai`.
- *PDF text extraction looks noisy:* PDFs with complicated layout may need preprocessing. Consider exporting as text first or experimenting with another extractor.
- *Fonts missing in PDF output:* Install system fonts that ReportLab can see or edit `quiz_to_pdf.py` to register custom fonts.

## Roadmap / Ideas
- Add automated tests around parsing utilities.
- Support streaming + retries for Cerebras calls.
- Parameterize the quiz length (different number of questions per topic).
- Build a simple CLI wrapper that runs every step sequentially.

## License
Add a license file (MIT, Apache, etc.) before publishing. Until then, the code is “all rights reserved” by default.

---
Questions or improvements? Feel free to open an issue or PR once the repository is public.
