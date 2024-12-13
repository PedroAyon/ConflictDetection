import os
import sqlite3
import time
from threading import Thread
from typing import List, Tuple

from dotenv import load_dotenv
from flask import Flask, request, jsonify, abort, send_from_directory
from conflict_detection import ConflictDetector
from file_convertion import convert_m4a_to_wav
from speech_recognition.speech_to_text_service import SpeechToTextService

# Load environment variables
load_dotenv()

# Constants
DB_PATH = "database.db"
CHECK_INTERVAL = 5  # Time in seconds to check for new files

# Initialize services
speech_service = SpeechToTextService(
    os.getenv("SPEECH_KEY"),
    os.getenv("SERVICE_REGION")
)
conflict_detector = ConflictDetector()

# Initialize Flask app
app = Flask(__name__)


class Database:
    def __init__(self, db_path: str):
        """Initializes the Database instance with the specified database path."""
        self.db_path = db_path

    def init_db(self):
        """Initializes the SQLite database with the required schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS processed_files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_path TEXT NOT NULL,
                    text_extracted TEXT,
                    conflictive BOOLEAN,
                    agent_id INTEGER,
                    agent_name TEXT,
                    date TEXT
                )
                """
            )

    def add_file(self, file_path, agent_id, agent_name, date):
        """Adds a file record to the database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO processed_files (file_path, agent_id, agent_name, date) VALUES (?, ?, ?, ?)",
                (file_path, agent_id, agent_name, date)
            )

    def get_processed_files(self) -> List[Tuple[int, str, str, bool, int, str, str]]:
        """Fetches files where text_extracted and conflictive are NOT NULL."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, file_path, text_extracted, conflictive, agent_id, agent_name, date 
                FROM processed_files 
                WHERE text_extracted IS NOT NULL AND conflictive IS NOT NULL
                """
            )
            return cursor.fetchall()


# Initialize the database instance
db = Database(DB_PATH)


@app.route("/")
def home():
    return jsonify({"message": "Hello, Flask!"})


@app.route("/process", methods=["POST"])
def process():
    file = request.files.get("file")
    agent_id = request.form.get("agent_id")
    agent_name = request.form.get("agent_name")
    date = request.form.get("date")

    if not file or not file.filename.endswith(".m4a"):
        return jsonify({"error": "Only M4A files are supported."}), 400

    if not agent_id or not agent_name or not date:
        return jsonify({"error": "Missing agent information."}), 400

    try:
        temp_input_path = f"temp_{time.time_ns()}.m4a"
        file.save(temp_input_path)

        output_path = convert_m4a_to_wav(temp_input_path)
        os.remove(temp_input_path)

        db.add_file(output_path, agent_id, agent_name, date)

        return jsonify({
            "message": "File converted successfully.",
            "output_file": output_path
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/processed_files", methods=["GET"])
def get_processed_files():
    """Endpoint to retrieve all processed files with text extracted and conflictive not null."""
    try:
        files = db.get_processed_files()
        return jsonify({
            "processed_files": [
                {
                    "id": file[0],
                    "file_path": file[1],
                    "text_extracted": file[2],
                    "conflictive": file[3],
                    "agent_id": file[4],
                    "agent_name": file[5],
                    "date": file[6]
                } for file in files
            ]
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

AUDIO_DIRECTORY = './'

@app.route('/audio/<filename>')
def serve_audio(filename):
    try:
        # Ensure the file has a .wav extension and exists in the directory
        if not filename.endswith('.wav'):
            abort(400, description="Only .wav files are allowed")

        # Safely join the directory and filename to avoid path traversal issues
        file_path = os.path.join(AUDIO_DIRECTORY, filename)

        # Check if the file exists
        if os.path.exists(file_path):
            return send_from_directory(AUDIO_DIRECTORY, filename)
        else:
            abort(404, description="File not found")

    except Exception as e:
        return str(e), 500

def process_files():
    """
    Checks the database for new files, processes them with speech recognition,
    then determines if the extracted text represents a conflictive conversation
    and updates the database with results.
    """
    while True:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, file_path, text_extracted FROM processed_files WHERE text_extracted IS NULL OR conflictive IS NULL"
            )
            files_to_process = cursor.fetchall()

        for file_id, file_path, text_extracted in files_to_process:
            try:
                if text_extracted is None:
                    extracted_text, _ = speech_service.speech_to_text_from_file(file_path)
                else:
                    extracted_text = text_extracted

                conflictive = conflict_detector.detect_conflict(extracted_text or "")

                with sqlite3.connect(DB_PATH) as conn:
                    conn.execute(
                        """
                        UPDATE processed_files
                        SET text_extracted = ?, conflictive = ?
                        WHERE id = ?
                        """,
                        (extracted_text, conflictive, file_id)
                    )

            except Exception as e:
                print(f"Error processing file {file_path}: {str(e)}")

        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    db.init_db()
    Thread(target=process_files, daemon=True).start()
    app.run(debug=True, use_reloader=False)
