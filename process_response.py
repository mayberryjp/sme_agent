import re

def extract_questions_from_content(content):
    """
    Extracts numbered or bulleted questions from a block of text.
    Returns a list of questions.
    """
    questions = []
    # Find lines that look like questions (start with number/bullet and end with '?')
    for line in content.splitlines():
        line = line.strip()
        # Numbered or bulleted questions
        match = re.match(r"^(?:\d+\.|\-|\*)\s*(.+\?)$", line)
        if match:
            questions.append(match.group(1).strip())
        # Sometimes questions are embedded in sentences
        elif line.endswith("?"):
            questions.append(line)
    return questions

def extract_questions_from_summary_table(content):
    """
    Extracts questions from a markdown-like summary table in the content.
    Returns a list of questions.
    """
    questions = []
    # Find table rows with a '|' and a question
    for line in content.splitlines():
        line = line.strip()
        # Table row with a question
        match = re.match(r"^\|.*\|\s*-\s*(.+\?)\s*\|", line)
        if match:
            questions.append(match.group(1).strip())
    # Also handle lines like: | **Category** | - Question? |
    match_lines = [line for line in content.splitlines() if "|" in line and "?" in line]
    for line in match_lines:
        # Extract after the dash
        parts = line.split("|")
        for part in parts:
            q = part.strip()
            if q.startswith("-") and "?" in q:
                questions.append(q.lstrip("-").strip())
    return questions

def extract_all_questions(api_response):
    """
    Given the API response (as a dict), extract all questions from the summary table
    and from the content parameter in chatHistory.messages.
    Returns a consolidated list of questions.
    """
    questions = []

    # Extract from summary table (last message, if present)
    messages = api_response.get("chatHistory", {}).get("messages", [])
    for msg in messages:
        content = msg.get("content", "")
        # If it looks like a summary table, extract from table
        if "| **Category**" in content or "|-" in content:
            questions += extract_questions_from_summary_table(content)
        # Otherwise, extract from content
        questions += extract_questions_from_content(content)

    # Deduplicate and clean
    questions = [q.strip() for q in questions if q.strip()]
    questions = list(dict.fromkeys(questions))  # Remove duplicates, preserve order
    return questions

# Example usage:
# api_response = ... # your API response dict
# all_questions = extract_all_questions(api_response)
# print(all_questions)