"""
Conference Notes Tool
Fetches transcripts from Fireflies.ai, summarizes with Claude, and saves to Google Docs.
"""

import os
import json
from datetime import datetime
from flask import Flask, render_template, jsonify, request
import requests

app = Flask(__name__)

# Import anthropic only when needed to avoid startup errors
anthropic = None
def get_anthropic_client():
    global anthropic
    if anthropic is None:
        import anthropic as anth
        anthropic = anth
    return anthropic

# Configuration from environment variables
FIREFLIES_API_KEY = os.environ.get("FIREFLIES_API_KEY")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
GOOGLE_SCRIPT_URL = os.environ.get("GOOGLE_SCRIPT_URL")  # Optional: for Google Docs integration

# Fireflies GraphQL endpoint
FIREFLIES_API_URL = "https://api.fireflies.ai/graphql"

# Summary prompt template
SUMMARY_PROMPT = """You are an expert at extracting insights from meeting transcripts and voice notes.

Analyze the following transcript and provide a structured summary with these sections:

## Key Takeaways
- List the 3-5 most important insights or learnings
- Focus on unique ideas, announcements, or valuable information

## Action Items
- List specific tasks or follow-ups mentioned or implied
- Format as actionable items (e.g., "Research X", "Contact Y about Z")

## Follow-up Questions
- Suggest 2-3 questions worth exploring further
- These could be clarifications or deeper dives into topics mentioned

## Notable Quotes
- Include 1-2 particularly insightful or memorable quotes (if any)
- Include speaker attribution if available

Keep the summary concise but comprehensive. Use bullet points for clarity.

---

TRANSCRIPT:
{transcript}
"""


def fetch_fireflies_transcripts(limit=5):
    """Fetch recent transcripts from Fireflies.ai"""
    if not FIREFLIES_API_KEY:
        return None, "Fireflies API key not configured"

    query = """
    query {
        transcripts(limit: %d) {
            id
            title
            date
            duration
            organizer_email
            sentences {
                speaker_name
                text
            }
        }
    }
    """ % limit

    headers = {
        "Authorization": f"Bearer {FIREFLIES_API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(
            FIREFLIES_API_URL,
            json={"query": query},
            headers=headers,
            timeout=30
        )
        response.raise_for_status()
        data = response.json()

        if "errors" in data:
            return None, f"Fireflies API error: {data['errors']}"

        return data.get("data", {}).get("transcripts", []), None
    except requests.exceptions.RequestException as e:
        return None, f"Failed to fetch transcripts: {str(e)}"


def get_transcript_by_id(transcript_id):
    """Fetch a specific transcript by ID"""
    if not FIREFLIES_API_KEY:
        return None, "Fireflies API key not configured"

    query = """
    query GetTranscript($id: String!) {
        transcript(id: $id) {
            id
            title
            date
            duration
            sentences {
                speaker_name
                text
            }
        }
    }
    """

    headers = {
        "Authorization": f"Bearer {FIREFLIES_API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(
            FIREFLIES_API_URL,
            json={"query": query, "variables": {"id": transcript_id}},
            headers=headers,
            timeout=30
        )
        response.raise_for_status()
        data = response.json()

        if "errors" in data:
            return None, f"Fireflies API error: {data['errors']}"

        return data.get("data", {}).get("transcript"), None
    except requests.exceptions.RequestException as e:
        return None, f"Failed to fetch transcript: {str(e)}"


def format_transcript(transcript):
    """Convert Fireflies transcript to readable text"""
    if not transcript or not transcript.get("sentences"):
        return ""

    lines = []
    for sentence in transcript["sentences"]:
        speaker = sentence.get("speaker_name", "Unknown")
        text = sentence.get("text", "")
        lines.append(f"{speaker}: {text}")

    return "\n".join(lines)


def summarize_with_claude(transcript_text, title=""):
    """Send transcript to Claude for summarization"""
    if not ANTHROPIC_API_KEY:
        return None, "Anthropic API key not configured"

    if not transcript_text.strip():
        return None, "Empty transcript"

    anth = get_anthropic_client()
    client = anth.Anthropic(api_key=ANTHROPIC_API_KEY)

    prompt = SUMMARY_PROMPT.format(transcript=transcript_text)

    try:
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        summary = message.content[0].text
        return summary, None
    except Exception as e:
        return None, f"Claude API error: {str(e)}"


def append_to_google_doc(title, summary, date):
    """Send summary to Google Apps Script for appending to Google Doc"""
    if not GOOGLE_SCRIPT_URL:
        return False, "Google Script URL not configured"

    payload = {
        "title": title,
        "summary": summary,
        "date": date,
        "timestamp": datetime.now().isoformat()
    }

    try:
        response = requests.post(
            GOOGLE_SCRIPT_URL,
            json=payload,
            timeout=30
        )
        response.raise_for_status()
        return True, None
    except requests.exceptions.RequestException as e:
        return False, f"Failed to append to Google Doc: {str(e)}"


@app.route("/")
def index():
    """Main page"""
    return render_template("index.html")


@app.route("/api/transcripts")
def list_transcripts():
    """List recent transcripts from Fireflies"""
    transcripts, error = fetch_fireflies_transcripts(limit=10)

    if error:
        return jsonify({"error": error}), 500

    # Simplify the response
    simplified = []
    for t in transcripts:
        simplified.append({
            "id": t.get("id"),
            "title": t.get("title", "Untitled"),
            "date": t.get("date"),
            "duration": t.get("duration", 0),
            "organizer_email": t.get("organizer_email", "")
        })

    return jsonify({"transcripts": simplified})


@app.route("/api/process/<transcript_id>")
def process_transcript(transcript_id):
    """Process a specific transcript: fetch, summarize, and optionally save"""
    try:
        # Fetch the transcript
        transcript, error = get_transcript_by_id(transcript_id)
        if error:
            return jsonify({"error": f"Failed to fetch transcript: {error}"}), 500

        if not transcript:
            return jsonify({"error": "Transcript not found"}), 404

        # Format the transcript
        transcript_text = format_transcript(transcript)
        title = transcript.get("title", "Untitled")
        date = transcript.get("date", "")

        if not transcript_text.strip():
            return jsonify({"error": "Transcript is empty - it may still be processing in Fireflies"}), 400

        # Summarize with Claude
        summary, error = summarize_with_claude(transcript_text, title)
        if error:
            return jsonify({"error": f"Failed to summarize: {error}"}), 500

        # Try to append to Google Doc (optional)
        google_saved = False
        google_error = None
        if GOOGLE_SCRIPT_URL:
            google_saved, google_error = append_to_google_doc(title, summary, date)

        return jsonify({
            "title": title,
            "date": date,
            "summary": summary,
            "google_saved": google_saved,
            "google_error": google_error
        })
    except Exception as e:
        return jsonify({"error": f"Processing failed: {str(e)}"}), 500


@app.route("/api/process-latest")
def process_latest():
    """Process the most recent transcript"""
    transcripts, error = fetch_fireflies_transcripts(limit=1)

    if error:
        return jsonify({"error": error}), 500

    if not transcripts:
        return jsonify({"error": "No transcripts found"}), 404

    latest = transcripts[0]
    return process_transcript(latest["id"])


@app.route("/health")
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "ok",
        "fireflies_configured": bool(FIREFLIES_API_KEY),
        "anthropic_configured": bool(ANTHROPIC_API_KEY),
        "google_configured": bool(GOOGLE_SCRIPT_URL)
    })


@app.route("/api/debug/<transcript_id>")
def debug_transcript(transcript_id):
    """Debug endpoint to see raw transcript data"""
    transcript, error = get_transcript_by_id(transcript_id)
    if error:
        return jsonify({"error": error}), 500

    if not transcript:
        return jsonify({"error": "Transcript not found"}), 404

    sentences = transcript.get("sentences", [])
    return jsonify({
        "id": transcript.get("id"),
        "title": transcript.get("title"),
        "date": transcript.get("date"),
        "duration": transcript.get("duration"),
        "sentence_count": len(sentences) if sentences else 0,
        "first_sentences": sentences[:3] if sentences else [],
        "has_content": bool(sentences)
    })


@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        "error": "Internal server error",
        "details": str(error)
    }), 500


@app.errorhandler(Exception)
def handle_exception(e):
    return jsonify({
        "error": "An error occurred",
        "details": str(e)
    }), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
