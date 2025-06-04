# Email Summary

Simple Flask application that uses the OpenAI API (gpt-4o) to summarize an email chain.

## Features
1. Generates a summary of the chain.
2. Lists all people involved.
3. Displays action items.
4. Provides a reply template with blanks (``_____``).

## Usage
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Set the `OPENAI_API_KEY` environment variable with your OpenAI key.
3. Run the application:
   ```bash
   python app.py
   ```
4. Open `http://localhost:5000` in your browser and paste the email chain.
