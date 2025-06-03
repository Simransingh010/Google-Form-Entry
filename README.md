# Google Form Auto-Submission Script

This script automates the submission of Google Forms using the Google Gemini AI API to generate realistic, diverse responses.

## Setup Instructions

1. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Get a Google Gemini API key:
   - Go to https://ai.google.dev/
   - Create or sign in to your Google account
   - Create an API key in the Google AI Studio
   - Copy your API key

3. Configure the script:
   - Open `entry.py`
   - Replace `YOUR_GEMINI_API_KEY` with your actual API key
   - Replace `YOUR_GOOGLE_FORM_URL` with your Google Form URL
   - Update the `form_fields` list to match your form structure (see below)

## Configuring Form Fields

You need to inspect your Google Form and update the `form_fields` list in `entry.py` accordingly. For each field in your form, add a dictionary with:

- `label`: The exact text label of the field as it appears in the form
- `type`: The type of field (`text`, `number`, `multiple_choice`, etc.)
- `options`: For multiple-choice fields, a list of the available options

Example:
```python
form_fields = [
    {
        "label": "Full Name",
        "type": "text"
    },
    {
        "label": "Age",
        "type": "number"
    },
    {
        "label": "Gender",
        "type": "multiple_choice",
        "options": ["Male", "Female", "Non-binary", "Prefer not to say"]
    },
    # Add more fields based on your form structure
]
```

## Running the Script

```
python entry.py
```

The script will:
1. Generate 100 realistic form responses using the Gemini AI API
2. Submit each response to your Google Form
3. Add random delays between submissions to appear more natural
4. Print progress and results to the console

## Notes

- Make sure you have Chrome installed as the script uses Chrome WebDriver
- Consider the ethical implications of form submission automation
- Respect website terms of service and avoid overwhelming form servers 