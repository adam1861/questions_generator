
import json
import argparse
import os
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_LEFT, TA_CENTER

def create_pdf_quiz(json_path, pdf_path):
    """
    Generates a PDF quiz from a JSON file.
    """
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            quiz_data = json.load(f)
    except FileNotFoundError:
        print(f"Error: Input JSON file not found at '{json_path}'")
        return
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from '{json_path}'")
        return

    doc = SimpleDocTemplate(pdf_path)
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle('Title', parent=styles['h1'], alignment=TA_CENTER, spaceAfter=20)
    h1_style = ParagraphStyle('H1', parent=styles['h1'], spaceAfter=16)
    h2_style = ParagraphStyle('H2', parent=styles['h2'], spaceAfter=12)
    h3_style = ParagraphStyle('H3', parent=styles['h3'], spaceAfter=10)
    question_style = ParagraphStyle('Question', parent=styles['Normal'], spaceBefore=12, spaceAfter=6, leading=14)
    option_style = ParagraphStyle('Option', parent=styles['Normal'], leftIndent=20, spaceAfter=4)
    
    story = []
    answer_key = []

    def build_story(node, level=0):
        style_map = {0: title_style, 1: h1_style, 2: h2_style, 3: h3_style}
        
        if isinstance(node, dict):
            title = node.get('title', 'Quiz Section')
            style = style_map.get(level, h3_style)
            story.append(Paragraph(title, style))
            
            if 'questions' in node and node['questions']:
                for i, q_data in enumerate(node['questions']):
                    question_text = f"{i+1}. {q_data['question']}"
                    story.append(Paragraph(question_text, question_style))
                    
                    options = q_data.get('options', [])
                    for j, option in enumerate(options):
                        option_text = f"{chr(97+j)}) {option}"
                        story.append(Paragraph(option_text, option_style))
                    
                    # Add to answer key
                    answer_key.append({
                        "section": title,
                        "question_num": i + 1,
                        "answer": q_data.get('correct_answer', 'N/A')
                    })
                story.append(Spacer(1, 0.25 * inch))

            # Recursively process children
            for key, value in node.items():
                if key not in ['title', 'questions']:
                    build_story(value, level + 1)
                    
        elif isinstance(node, list):
            for item in node:
                build_story(item, level)

    # Build the main quiz part
    build_story(quiz_data)

    # Add the answer key
    story.append(PageBreak())
    story.append(Paragraph("Answer Key", title_style))
    
    last_section = ""
    for answer in answer_key:
        if answer["section"] != last_section:
            story.append(Paragraph(answer["section"], h2_style))
            last_section = answer["section"]
        answer_text = f"{answer['question_num']}: {answer['answer']}"
        story.append(Paragraph(answer_text, styles['Normal']))

    try:
        doc.build(story)
        print(f"Successfully generated PDF quiz: {pdf_path}")
    except Exception as e:
        print(f"Error building PDF: {e}")

def parse_args():
    parser = argparse.ArgumentParser(description="Convert a JSON quiz to a PDF file.")
    parser.add_argument("-i", "--input", default="hibernate_extracted_chunks_structure_quiz.json", help="Input JSON quiz file.")
    parser.add_argument("-o", "--output", help="Output PDF file path. Defaults to input name with .pdf extension.")
    return parser.parse_args()

def main():
    args = parse_args()
    
    input_path = args.input
    output_path = args.output or (os.path.splitext(input_path)[0] + ".pdf")
    
    create_pdf_quiz(input_path, output_path)

if __name__ == "__main__":
    main()
