from src.RhythmRegistryApp import app
import os


if __name__ == "__main__":
    # Get port from environment variable (Render sets PORT env var)
    port = int(os.environ.get("PORT", 5002))
    # In production, debug should be False
    debug = os.environ.get("FLASK_ENV") == "development"
    # Bind to 0.0.0.0 to make the app accessible externally
    app.run(host="0.0.0.0", debug=debug, port=port)