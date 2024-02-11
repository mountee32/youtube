import requests
import json

# Correctly set the full API key
OPENROUTER_API_KEY = "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"

# Making the POST request
url = "https://openrouter.ai/api/v1/chat/completions"
headers = {
    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
    "HTTP-Referer": "YOUR_SITE_URL",  # Optional, replace with your actual site URL
    "X-Title": "YOUR_APP_NAME",  # Optional, replace with your actual app name
}
data = json.dumps({
  "model": "gryphe/mythomist-7b:free", # Optional
    "messages": [
        {"role": "user", "content": "What is the meaning of life?"}
    ]
})

# Debugging: Print the headers and data being sent
print("Sending request with headers:", headers)
print("And data:", data)

response = requests.post(url=url, headers=headers, data=data)

# Debugging: Print the status code and response text
print("Received response status code:", response.status_code)
print("And response text:", response.text)

if response.status_code == 200:
    # Parse the JSON response
    data = response.json()
    # Display the results
    for message in data.get('messages', []):
        print(f"Role: {message['role']}, Content: {message['content']}")
else:
    print("Failed to fetch data. Please check the debug information above for details.")
