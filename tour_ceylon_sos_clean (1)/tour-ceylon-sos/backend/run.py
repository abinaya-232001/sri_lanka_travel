"""Start the backend:  python run.py   (http://localhost:5000)"""
import os

from dotenv import load_dotenv

load_dotenv()

from app import create_app  # noqa: E402
from app.extensions import socketio  # noqa: E402

app = create_app()

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "5000")),
                 debug=os.getenv("FLASK_DEBUG") == "1", allow_unsafe_werkzeug=True)
