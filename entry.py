import requests
import time
import random
import csv
import os
import subprocess
import sys
import zipfile
import platform
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium_stealth import stealth
import google.generativeai as genai
import json
import re

# Configure the Gemini API
API_KEY = "AIzaSyClyzC7Auyy06NsOWJMwRxwiUfg1xBa-YQ"  # Replace with your actual API key
genai.configure(api_key=API_KEY)

# Google Form URL
FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSczvu694KWU4Lq9u34c0q1O4_eJFuFizHj7ZgJRYNV9zj7jYQ/viewform"  # Replace with your actual form URL

# Function to generate realistic form responses using Gemini
def generate_form_response(form_fields):
    """
    Generate realistic responses for form fields using Gemini AI
    
    Args:
        form_fields: List of dictionaries containing field info (type, label, options)
    
    Returns:
        Dictionary with field labels as keys and generated responses as values
    """
    # Create a prompt for Gemini
    prompt = """Generate a realistic response for an Indian medical student survey form with the following fields. 
Return the response as a JSON object with field labels as keys and responses as values.
Make the responses diverse, realistic, and human-like for an Indian medical student. Ensure they are consistent with each other.
The response should represent a single individual Indian medical student with consistent habits, study patterns, and health behaviors.

For email addresses:
- IMPORTANT: The email MUST be in EXACTLY this format: firstname@gmail.com (no dots, no underscores, no numbers)
- Use common Indian first names (e.g., Rahul, Priya, Amit, Neha, etc.)
- The email address should be short and simple
- DO NOT include last names in the email
- DO NOT include any special characters
- DO NOT duplicate any part of the email
- Examples of valid emails:
  * rahul@gmail.com
  * priya@gmail.com
  * amit@gmail.com
  * neha@gmail.com

For age, generate realistic ages for medical students (typically 18-30).
For percentages in tests, generate realistic scores (typically between 40-95%).

Here are the fields:
"""
    
    for field in form_fields:
        prompt += f"Field: {field['label']}\n"
        prompt += f"Type: {field['type']}\n"
        
        if field['type'] == 'multiple_choice' and 'options' in field:
            prompt += f"Options: {', '.join(field['options'])}\n"
        
        prompt += "\n"
    
    # Generate response using Gemini
    model = genai.GenerativeModel('gemini-2.0-flash')
    
    try:
        response = model.generate_content(prompt)
        
        # Check if response is None or has no text attribute
        if response is None or not hasattr(response, 'text') or response.text is None:
            print("Error: Received empty response from Gemini API")
            return create_fallback_response(form_fields)
        
        # Parse the response as JSON
        response_text = response.text
        
        # Check if response text is empty
        if not response_text.strip():
            print("Error: Received empty text from Gemini API")
            return create_fallback_response(form_fields)
            
        # Extract JSON if it's wrapped in markdown code blocks
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
        
        try:
            parsed_response = json.loads(response_text)
            
            # Clean email directly after parsing
            if "Email" in parsed_response:
                email = str(parsed_response["Email"]).strip()
                if "@" in email:
                    parts = email.split("@", 1)
                    username = parts[0]
                    domain = parts[1]
                    # Basic check if username seems duplicated (e.g. nehaneha)
                    if len(username) > 0 and len(username) % 2 == 0 and username[:len(username)//2] == username[len(username)//2:]:
                        username = username[:len(username)//2]
                    parsed_response["Email"] = f"{username}@{domain}"
            
            return parsed_response
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON from Gemini response: {e}")
            print(f"Raw response: {response_text}")
            return create_fallback_response(form_fields)
            
    except Exception as e:
        print(f"Error generating response with Gemini: {e}")
        return create_fallback_response(form_fields)

def create_fallback_response(form_fields):
    """
    Create a fallback response when the Gemini API fails
    
    Args:
        form_fields: List of dictionaries containing field info
        
    Returns:
        Dictionary with field labels as keys and fallback responses as values
    """
    print("Generating fallback response...")
    fallback = {}
    
    for field in form_fields:
        label = field['label']
        
        if field['type'] == 'text':
            if 'Email' in label:
                fallback[label] = f"student{random.randint(1000, 9999)}@medschool.edu"
            elif 'Age' in label:
                fallback[label] = str(random.randint(18, 30))
            elif 'percentage' in label.lower():
                fallback[label] = str(random.randint(40, 95))
            else:
                fallback[label] = "Sample response"
                
        elif field['type'] == 'multiple_choice' and 'options' in field:
            # Choose a random option
            fallback[label] = random.choice(field['options'])
    
    return fallback

# Define your form fields (you'll need to inspect your form and fill this in)
# Example:
form_fields = [
    {
        "label": "Email",
        "type": "text",
        "is_email": True
    },
    {
        "label": "Do you agree to participate in this study?",
        "type": "multiple_choice",
        "options": ["Yes", "No"]
    },
    {
        "label": "Age",
        "type": "text"
    },
    {
        "label": "gender",
        "type": "multiple_choice",
        "options": ["Male", "Female", "Prefer not to say", "Other"]
    },
    {
        "label": "Year of study",
        "type": "multiple_choice",
        "options": ["1st year", "2nd year", "3rd year", "Final year", "Internship"]
    },
    {
        "label": "Your percentage in last prof / class test",
        "type": "text"
    },
    {
        "label": "Have you ever failed a subject in medical school?",
        "type": "multiple_choice",
        "options": ["Yes", "No"]
    },
    {
        "label": "Do you feel satisfied with your academic performance?",
        "type": "multiple_choice",
        "options": ["Yes", "No", "Sometimes"]
    },
    {
        "label": "Do you often feel anxious or overwhelmed?",
        "type": "multiple_choice",
        "options": ["Always", "Never", "Sometimes", "Often", "Rarely"]
    },
    {
        "label": "How often do you consume junk food in a week?",
        "type": "multiple_choice",
        "options": ["Daily", "A few times a week", "Once a week", "Rarely", "Never"]
    },
    {
        "label": "How many days per week do you engage in physical activity (e.g., walking, running, gym, sports)?",
        "type": "multiple_choice",
        "options": ["0 days", "1–2 days", "3–4 days", "5 or more days"]
    },
    {
        "label": "Have you ever been diagnosed or treated for anxiety, depression, or other psychological conditions?",
        "type": "multiple_choice",
        "options": ["Yes", "No", "Sometimes"]
    },
    {
        "label": "How many hours of sleep do you get per night on average?",
        "type": "multiple_choice",
        "options": ["Less than 4 hours", "4-6 hours", "6-8 hours", "More than 8 hours"]
    },
    {
        "label": "How many hours do you study per day on average?",
        "type": "multiple_choice",
        "options": ["Less than 1 hour", "1-2 hours", "3-4 hours", "More than 4 hours"]
    },
    {
        "label": "How would you describe your time management skills?",
        "type": "multiple_choice",
        "options": ["Good", "Excellent", "Poor", "Average"]
    },
    {
        "label": "Do you feel well rested during classes ?",
        "type": "multiple_choice",
        "options": ["Yes", "No", "Sometimes"]
    },
    {
        "label": "Do you use electronic devices (e.g., phone, TV, laptop) before bed?",
        "type": "multiple_choice",
        "options": ["Yes", "No", "Sometimes"]
    },
    {
        "label": "Do you consume caffeine (coffee, tea, energy drinks) after 5pm?",
        "type": "multiple_choice",
        "options": ["Yes", "No", "Sometimes"]
    },
    {
        "label": "Do you eat regular meals?",
        "type": "multiple_choice",
        "options": ["Yes", "No", "Sometimes"]
    },
    {
        "label": "During exam periods, how much time do you spend daily on social media?",
        "type": "multiple_choice",
        "options": ["I avoid social media entirely", "Less than 1 hour", "1–2 hours", "3–4 hours", "More than 4 hours"]
    },
    {
        "label": "Do you take breaks from social media during exams?",
        "type": "multiple_choice",
        "options": ["Yes, always", "Sometimes", "No, but I want to", "No, and I don't plan to"]
    },
    {
        "label": "Do you use social media for academic purposes during exams (e.g., study groups, educational content)?",
        "type": "multiple_choice",
        "options": ["Yes", "No"]
    },
    {
        "label": "Do you practice self medications ?",
        "type": "multiple_choice",
        "options": ["Yes", "No"]
    },
    {
        "label": "What types of medicines do you usually take without a prescription?",
        "type": "multiple_choice",
        "options": ["Pharmacy without prescription", "Leftover from a previous prescription", "Family or friends", "Online stores", "Herbal/traditional shops", "Other"]
    },
    {
        "label": "Have you experienced any negative effects from self-medicating?",
        "type": "multiple_choice",
        "options": ["Yes, serious side effects", "Yes, minor side effects", "No", "Not sure"]
    }
]

def download_chromedriver():
    """
    Download and install ChromeDriver manually
    
    Returns:
        Path to the ChromeDriver executable
    """
    try:
        print("Attempting to download ChromeDriver manually...")
        
        # Create a directory for the driver if it doesn't exist
        driver_dir = os.path.join(os.getcwd(), "chromedriver")
        if not os.path.exists(driver_dir):
            os.makedirs(driver_dir)
        
        # Determine the system architecture and OS
        is_64bits = sys.maxsize > 2**32
        arch = "64" if is_64bits else "32"
        system = platform.system().lower()
        
        # Default to the latest version - in production, you'd want to detect Chrome version
        version = "114.0.5735.90"  # Example version, adjust as needed
        
        # Construct the download URL
        if system == "windows":
            driver_name = "chromedriver_win32.zip"
        elif system == "darwin":  # macOS
            driver_name = "chromedriver_mac64.zip"
        else:  # Linux
            driver_name = f"chromedriver_linux{arch}.zip"
        
        download_url = f"https://chromedriver.storage.googleapis.com/{version}/{driver_name}"
        
        # Download the zip file
        driver_zip = os.path.join(driver_dir, driver_name)
        print(f"Downloading ChromeDriver from {download_url}...")
        
        response = requests.get(download_url)
        with open(driver_zip, "wb") as f:
            f.write(response.content)
        
        # Extract the zip file
        with zipfile.ZipFile(driver_zip, "r") as zip_ref:
            zip_ref.extractall(driver_dir)
        
        # Set the executable permission on Linux/Mac
        driver_executable = os.path.join(driver_dir, "chromedriver.exe" if system == "windows" else "chromedriver")
        if system != "windows":
            os.chmod(driver_executable, 0o755)
        
        print(f"ChromeDriver installed at {driver_executable}")
        return driver_executable
    
    except Exception as e:
        print(f"Error downloading ChromeDriver: {e}")
        return None

def analyze_form_structure(driver):
    """
    Analyze the Google Form structure and print out the CSS classes being used
    This helps with debugging when Google changes their class names
    
    Args:
        driver: Selenium WebDriver instance
    """
    print("\n--- Analyzing Form Structure ---")
    
    # Try to find all form elements
    try:
        # Find the form container
        form = driver.find_element(By.TAG_NAME, "form")
        print(f"Form found: {form.get_attribute('class')}")
        
        # Find all potential question containers
        containers = driver.find_elements(By.CSS_SELECTOR, "div[role='listitem']")
        print(f"Found {len(containers)} potential question containers")
        
        # Analyze the first few containers
        for i, container in enumerate(containers[:3]):  # Just check the first 3
            print(f"\nContainer {i+1} classes: {container.get_attribute('class')}")
            
            # Try to find the question text
            try:
                title_elements = container.find_elements(By.CSS_SELECTOR, "div[role='heading']")
                if title_elements:
                    print(f"Question text: {title_elements[0].text}")
                    print(f"Question element class: {title_elements[0].get_attribute('class')}")
            except:
                print("No question text found")
            
            # Try to find input elements
            try:
                inputs = container.find_elements(By.TAG_NAME, "input")
                print(f"Found {len(inputs)} input elements")
                for j, input_el in enumerate(inputs[:2]):  # Just check the first 2
                    print(f"  Input {j+1} type: {input_el.get_attribute('type')}")
                    print(f"  Input {j+1} class: {input_el.get_attribute('class')}")
            except:
                print("No input elements found")
            
            # Try to find radio/checkbox options
            try:
                options = container.find_elements(By.CSS_SELECTOR, "label")
                print(f"Found {len(options)} label elements (potential options)")
                for j, option in enumerate(options[:2]):  # Just check the first 2
                    print(f"  Option {j+1} text: {option.text}")
                    print(f"  Option {j+1} class: {option.get_attribute('class')}")
            except:
                print("No label elements found")
        
        # Find submit button
        try:
            buttons = driver.find_elements(By.CSS_SELECTOR, "div[role='button']")
            print(f"\nFound {len(buttons)} button elements")
            for i, button in enumerate(buttons):
                print(f"Button {i+1} text: {button.text}")
                print(f"Button {i+1} class: {button.get_attribute('class')}")
        except:
            print("No button elements found")
            
    except Exception as e:
        print(f"Error analyzing form structure: {e}")
    
    print("--- End of Form Structure Analysis ---\n")

def submit_form(responses, max_retries=3):
    """
    Submit the form with the generated responses using Selenium
    
    Args:
        responses: Dictionary with field labels as keys and responses as values
        max_retries: Maximum number of retry attempts
    
    Returns:
        Boolean indicating success or failure
    """
    retries = 0
    
    # Clean up email field if it exists to prevent double entry
    if "Email" in responses:
        email = str(responses["Email"]).strip()
        if "@" in email:
            parts = email.split("@",1)
            username = parts[0]
            domain = parts[1]
            # Basic check if username seems duplicated (e.g. nehaneha)
            if len(username) > 0 and len(username) % 2 == 0 and username[:len(username)//2] == username[len(username)//2:]:
                username = username[:len(username)//2]
            responses["Email"] = f"{username}@{domain}"
    
    # Define Chrome paths to try
    chrome_paths = [
        "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
        "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
        "C:\\ProgramData\\Microsoft\\Windows\\Start Menu\\Programs\\Google Chrome.lnk",
        # Add more potential paths if needed
    ]
    
    # Try to find Chrome executable using 'where' command on Windows
    try:
        chrome_path_from_cmd = subprocess.check_output(["where", "chrome"], text=True).strip().split('\n')[0]
        if chrome_path_from_cmd and os.path.exists(chrome_path_from_cmd):
            chrome_paths.insert(0, chrome_path_from_cmd)
    except:
        pass
    
    while retries < max_retries:
        # Setup Chrome options
        chrome_options = Options()
        chrome_options.add_argument("--headless") # Run in headless mode
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        # Add stealth options to avoid detection
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option("useAutomationExtension", False)
        
        # Try to set binary location if Chrome is not in PATH
        chrome_found = False
        for chrome_path in chrome_paths:
            if os.path.exists(chrome_path):
                print(f"Found Chrome at: {chrome_path}")
                chrome_options.binary_location = chrome_path
                chrome_found = True
                break
        
        if not chrome_found:
            print("Warning: Could not find Chrome executable. Using default location.")
        
        # Initialize the Chrome driver
        driver = None
        
        try:
            # Try different methods to initialize Chrome
            try:
                # Method 1: Use ChromeDriverManager
                print("Trying to initialize Chrome with ChromeDriverManager...")
                driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
            except Exception as e1:
                print(f"ChromeDriverManager failed: {e1}")
                
                try:
                    # Method 2: Try direct initialization
                    print("Trying direct Chrome initialization...")
                    driver = webdriver.Chrome(options=chrome_options)
                except Exception as e2:
                    print(f"Direct initialization failed: {e2}")
                    
                    # Method 3: Try manual download
                    chromedriver_path = download_chromedriver()
                    if chromedriver_path:
                        print(f"Using manually downloaded ChromeDriver at {chromedriver_path}")
                        driver = webdriver.Chrome(service=Service(chromedriver_path), options=chrome_options)
                    else:
                        raise Exception("All Chrome initialization methods failed")
            
            # Apply stealth settings
            stealth(driver,
                languages=["en-US", "en"],
                vendor="Google Inc.",
                platform="Win32",
                webgl_vendor="Intel Inc.",
                renderer="Intel Iris OpenGL Engine",
                fix_hairline=True,
            )
            
            # Navigate to the form
            print(f"Navigating to form URL: {FORM_URL}")
            driver.get(FORM_URL)
            
            # Wait for the form to load
            print("Waiting for form to load...")
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "form"))
            )
            print("Form loaded successfully")
            
            # Take a screenshot for debugging
            screenshot_dir = "screenshots"
            if not os.path.exists(screenshot_dir):
                os.makedirs(screenshot_dir)
            screenshot_path = os.path.join(screenshot_dir, f"form_load_{int(time.time())}.png")
            driver.save_screenshot(screenshot_path)
            print(f"Screenshot saved to {screenshot_path}")
            
            # Analyze the form structure to help with debugging
            analyze_form_structure(driver)
            
            # Google Forms specific approach
            print("Filling form fields...")
            
            # --- Handle Email Field Specifically ---
            email_field_label = "Email" # Assuming this is the label for your email field
            if email_field_label in responses:
                try:
                    print(f"Attempting to fill specific field: {email_field_label}")
                    email_field_element = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='email']"))
                    )
                    
                    # Force clear using JavaScript
                    driver.execute_script("arguments[0].value = '';", email_field_element)
                    time.sleep(0.3) # Short pause
                    
                    # Set value using JavaScript
                    clean_email = responses[email_field_label]
                    driver.execute_script("arguments[0].value = arguments[1];", email_field_element, clean_email)
                    time.sleep(0.3) # Short pause
                    
                    # Trigger input and change events
                    driver.execute_script("arguments[0].dispatchEvent(new Event('input', { bubbles: true }));", email_field_element)
                    driver.execute_script("arguments[0].dispatchEvent(new Event('change', { bubbles: true }));", email_field_element)
                    time.sleep(0.5) # Pause to let events process

                    # Verify
                    value_after_set = email_field_element.get_attribute('value')
                    if value_after_set == clean_email:
                        print(f"Successfully filled and verified {email_field_label} with: {clean_email}")
                    else:
                        print(f"ERROR: {email_field_label} verification failed. Expected: '{clean_email}', Got: '{value_after_set}'. Retrying with send_keys.")
                        # Fallback: Clear again and try send_keys
                        driver.execute_script("arguments[0].value = '';", email_field_element)
                        time.sleep(0.3)
                        email_field_element.send_keys(clean_email)
                        time.sleep(0.5)
                        value_after_retry = email_field_element.get_attribute('value')
                        if value_after_retry == clean_email:
                             print(f"Successfully filled {email_field_label} with send_keys fallback.")
                        else:
                             print(f"ERROR: {email_field_label} send_keys fallback failed. Expected: '{clean_email}', Got: '{value_after_retry}'.")

                except Exception as e:
                    print(f"Error specifically filling {email_field_label}: {e}")
            else:
                print(f"No response found for {email_field_label}")

            # --- Handle Agreement Question Specifically ---
            agreement_field_label = "Do you agree to participate in this study?" # Exact label
            if agreement_field_label in responses and responses[agreement_field_label] == "Yes":
                try:
                    print(f"Attempting to fill specific field: {agreement_field_label}")
                    # More specific XPath to find the "Yes" option related to the question
                    agreement_xpath = f"//div[contains(., '{agreement_field_label}')]/ancestor::div[@role='listitem']//div[@role='radio' and @data-value='Yes']"
                    
                    # Fallback XPath if data-value is not 'Yes' but text is 'Yes'
                    agreement_option_yes = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, agreement_xpath))
                    )
                    driver.execute_script("arguments[0].click();", agreement_option_yes)
                    print(f"Clicked 'Yes' for '{agreement_field_label}'")
                    time.sleep(0.5)
                except Exception as e:
                    print(f"Error specifically clicking 'Yes' for '{agreement_field_label}': {e}. Trying alternative selectors.")
                    # Alternative: find all radio groups under the question and click the one with "Yes"
                    try:
                        question_container_xpath = f"//div[contains(., '{agreement_field_label}')]/ancestor::div[@role='listitem']"
                        question_container = driver.find_element(By.XPATH, question_container_xpath)
                        radio_options = question_container.find_elements(By.CSS_SELECTOR, "div[role='radio']")
                        for option in radio_options:
                            if option.text.strip().lower() == "yes":
                                driver.execute_script("arguments[0].click();", option)
                                print(f"Clicked 'Yes' for '{agreement_field_label}' (alternative method).")
                                time.sleep(0.5)
                                break
                    except Exception as e2:
                        print(f"Error with alternative method for '{agreement_field_label}': {e2}")
            else:
                print(f"No 'Yes' response for {agreement_field_label}, or label not in responses.")
                
            # --- Process Remaining General Questions ---
            processed_specific_fields = {email_field_label, agreement_field_label}
            
            # Find all question containers - try multiple selectors
            selectors = [
                ".freebirdFormviewerViewItemsItemItem", 
                "div[role='listitem']",
                ".freebirdFormviewerViewItemsItemItemHeader",
                ".freebirdFormviewerComponentsQuestionBaseRoot"
            ]
            
            question_containers = []
            for selector in selectors:
                containers = driver.find_elements(By.CSS_SELECTOR, selector)
                if containers:
                    question_containers = containers
                    print(f"Found {len(containers)} question containers using selector: {selector}")
                    break
            
            if not question_containers:
                print("WARNING: Could not find any question containers!")
                
            # Process each question container
            for container in question_containers:
                try:
                    # Try multiple selectors for question text
                    question_text_selectors = [
                        ".freebirdFormviewerViewItemsItemItemTitle",
                        "div[role='heading']",
                        ".freebirdFormviewerComponentsQuestionBaseHeader"
                    ]
                    
                    question_text = ""
                    for selector in question_text_selectors:
                        try:
                            question_text_element = container.find_element(By.CSS_SELECTOR, selector)
                            question_text = question_text_element.text.strip()
                            if question_text:
                                break
                        except:
                            pass
                    
                    if not question_text:
                        print(f"WARNING: Could not find question text in container: {container.get_attribute('outerHTML')[:100]}...")
                        continue
                    
                    # Remove the asterisk for required questions
                    if question_text.endswith("*"):
                        question_text = question_text[:-1].strip()
                    
                    # Check if this question was handled by specific logic
                    if question_text in processed_specific_fields:
                        print(f"Skipping already processed specific field: {question_text}")
                        continue
                        
                    print(f"Processing general question: {question_text}")
                    
                    # Find matching field in our responses
                    matching_field = None
                    for field_label in responses.keys():
                        if field_label in question_text or question_text in field_label:
                            matching_field = field_label
                            break
                    
                    if not matching_field:
                        print(f"No matching response found for question: {question_text}")
                        continue
                    
                    response_value = responses[matching_field]
                    print(f"Found matching field '{matching_field}' with value: {response_value}")
                    
                    # Check if it's a text/number input - try multiple selectors
                    text_input_selectors = [
                        "input.quantumWizTextinputPaperinputInput",
                        "input[type='text']",
                        "input"
                    ]
                    
                    text_input_found = False
                    for selector in text_input_selectors:
                        try:
                            text_inputs = container.find_elements(By.CSS_SELECTOR, selector)
                            if text_inputs:
                                text_inputs[0].send_keys(str(response_value))
                                print(f"Filled text input for {matching_field} using selector: {selector}")
                                text_input_found = True
                                break
                        except:
                            pass
                    
                    if text_input_found:
                        continue
                    
                    # Check if it's a radio button group - try multiple selectors
                    radio_selectors = [
                        ".docssharedWizToggleLabeledLabelWrapper",
                        "label",
                        "div[role='radio']"
                    ]
                    
                    radio_found = False
                    for selector in radio_selectors:
                        try:
                            radio_options = container.find_elements(By.CSS_SELECTOR, selector)
                            if radio_options:
                                for option in radio_options:
                                    option_text = option.text.strip()
                                    if option_text == response_value or response_value in option_text or option_text in response_value:
                                        option.click()
                                        print(f"Selected radio option '{option_text}' for {matching_field} using selector: {selector}")
                                        radio_found = True
                                        break
                                if radio_found:
                                    break
                        except Exception as e:
                            print(f"Error with radio selector {selector}: {e}")
                    
                    if radio_found:
                        continue
                    
                    print(f"Could not find appropriate input element for {matching_field}")
                    
                except Exception as e:
                    print(f"Error processing question container: {e}")
            
            # Take another screenshot after filling the form
            screenshot_path = os.path.join(screenshot_dir, f"form_filled_{int(time.time())}.png")
            driver.save_screenshot(screenshot_path)
            print(f"Screenshot of filled form saved to {screenshot_path}")
            
            # Submit the form - try multiple selectors
            submit_selectors = [
                ".appsMaterialWizButtonPaperbuttonLabel",
                "div[role='button']",
                "div.freebirdFormviewerViewNavigationButtons"
            ]
            
            try:
                submit_button = None
                for selector in submit_selectors:
                    try:
                        buttons = driver.find_elements(By.CSS_SELECTOR, selector)
                        for button in buttons:
                            if button.text.strip().lower() in ["submit", "next", "continue"]:
                                submit_button = button
                                break
                        if submit_button:
                            break
                    except:
                        pass
                
                if submit_button:
                    submit_button.click()
                    print("Clicked submit button")
                    
                    # Wait for submission confirmation
                    WebDriverWait(driver, 20).until(
                        EC.presence_of_element_located((By.XPATH, "//div[contains(text(), 'Your response has been recorded')]"))
                    )
                    
                    # Take a screenshot of the confirmation page
                    screenshot_path = os.path.join(screenshot_dir, f"form_submitted_{int(time.time())}.png")
                    driver.save_screenshot(screenshot_path)
                    print(f"Screenshot of confirmation page saved to {screenshot_path}")
                    
                    return True
                else:
                    print("Could not find submit button")
            except Exception as e:
                print(f"Error submitting form: {e}")
                retries += 1
                print(f"Retrying ({retries}/{max_retries})...")
                time.sleep(2)  # Wait before retrying
        
        except Exception as e:
            print(f"Error during form submission: {e}")
            retries += 1
            print(f"Retrying ({retries}/{max_retries})...")
            time.sleep(2)  # Wait before retrying
        
        finally:
            # Close the browser
            if driver:
                driver.quit()
    
    print(f"Failed to submit form after {max_retries} attempts")
    return False

def save_to_csv(responses_list):
    """
    Save all generated responses to a CSV file
    
    Args:
        responses_list: List of dictionaries containing form responses
    """
    # Create directory if it doesn't exist
    if not os.path.exists('responses'):
        os.makedirs('responses')
    
    # Create a timestamp for the filename
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    filename = f"responses/form_responses_{timestamp}.csv"
    
    # Get all unique field names across all responses
    fieldnames = set()
    for response in responses_list:
        fieldnames.update(response.keys())
    
    # Convert to sorted list for consistent column order
    fieldnames = sorted(list(fieldnames))
    
    # Write to CSV
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(responses_list)
    
    print(f"Saved {len(responses_list)} responses to {filename}")
    return filename

# Main function to generate and submit multiple form responses
def main():
    successful_submissions = 0
    failed_submissions = 0
    all_responses = []
    
    try:
        total_submissions = 100 # Changed to 100 submissions
        print(f"\nStarting submission of {total_submissions} entries...")
        
        for i in range(total_submissions):
            print(f"\n--- Submission {i+1}/{total_submissions} ({(i+1)/total_submissions*100:.1f}%) ---")
            
            # Generate responses
            try:
                responses = generate_form_response(form_fields)
                if not responses:
                    print("Failed to generate valid responses, skipping this submission")
                    failed_submissions += 1
                    continue
                
                # Save responses for later analysis
                all_responses.append(responses)
                
                # Print the generated responses for debugging
                print("\nGenerated responses:")
                for key, value in responses.items():
                    print(f"{key}: {value}")
                print("\n")
                
                # Submit the form
                if submit_form(responses):
                    successful_submissions += 1
                    print(f"Successfully submitted form {i+1}")
                else:
                    failed_submissions += 1
                    print(f"Failed to submit form {i+1}")
                
                # Add a random delay between submissions to appear more natural
                # if i < total_submissions - 1:  # Don't delay after the last submission
                #     delay = random.uniform(10, 20)  # Increased delay between submissions
                #     print(f"Waiting {delay:.2f} seconds before next submission...")
                #     time.sleep(delay)
                
            except Exception as e:
                print(f"Error during submission {i+1}: {e}")
                failed_submissions += 1
            
            # Save progress periodically (every 10 submissions)
            if (i + 1) % 10 == 0 and all_responses:
                temp_csv_file = save_to_csv(all_responses)
                print(f"\nProgress saved to {temp_csv_file}")
                print(f"Current success rate: {successful_submissions/(i+1)*100:.1f}%")
    
    except KeyboardInterrupt:
        print("\nScript interrupted by user. Saving collected responses...")
    
    finally:
        # Save all responses to CSV if we have any
        if all_responses:
            csv_file = save_to_csv(all_responses)
            print(f"\nAll responses have been saved to {csv_file} for analysis.")
        
        print(f"\nFinal Summary:")
        print(f"- Successful submissions: {successful_submissions}")
        print(f"- Failed submissions: {failed_submissions}")
        print(f"- Total attempted: {successful_submissions + failed_submissions}")
        print(f"- Success rate: {successful_submissions/total_submissions*100:.1f}%")

if __name__ == "__main__":
    main()
