import logging
import json
import os
from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi
import dateutil.parser
from dotenv import load_dotenv
import requests
import openai   

# Setup Consts, logging and Keys
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
load_dotenv()
qty_videos = 5
youtube_api_key = os.getenv('YOUTUBE_API_KEY')
channel_id = os.getenv('CHANNEL_ID')
llm_api_key = os.getenv('LLM_API_KEY')
llm_model = os.getenv('LLM_MODEL')
llm_api_url = os.getenv('LLM_API_URL')
youtube = build('youtube', 'v3', developerKey=youtube_api_key)
transcription_dir = './transcription'
summary_dir = './summary'
os.makedirs(transcription_dir, exist_ok=True)
os.makedirs(summary_dir, exist_ok=True)
# Check required environment variables
if not youtube_api_key or not channel_id or not llm_api_key or not llm_model or not llm_api_key:
    logging.error("One or more required environment variables are not set.")
    exit()


def get_transcripts(youtube, channel_id):
    try:
        logging.info("Starting to fetch videos from YouTube API.")
        results = youtube.search().list(part='id', channelId=channel_id, order='date', maxResults=qty_videos).execute()
        logging.info(f"Successfully fetched videos for channel ID: {channel_id}")
    except Exception as e:
        logging.error(f"Failed to fetch videos for channel ID: {channel_id}. Error: {e}")
        return

    for item in results['items']:
        video_id = item['id']['videoId']
        out_file = os.path.join(transcription_dir, f"{video_id}.json") 
        if os.path.exists(out_file):
            logging.info(f"File {out_file} already exists. Skipping.")
            continue

        try:
            logging.info(f"Fetching video details for video ID: {video_id}")
            video_details = youtube.videos().list(part='snippet', id=video_id).execute()

            logging.info(f"Attempting to fetch transcript for video ID: {video_id}")
            transcript_data = YouTubeTranscriptApi.get_transcript(video_id)

            logging.info(f"Transcript fetched successfully for video ID: {video_id}")

            output = {
                "name": video_details['items'][0]['snippet']['title'],
                "date": dateutil.parser.parse(video_details['items'][0]['snippet']['publishedAt']).strftime("%Y-%m-%d"),
                "transcript": [item['text'] for item in transcript_data]
            }

            with open(out_file, 'w') as f:
                json.dump(output, f)
            logging.info(f"Successfully wrote transcript to {out_file}")

        except Exception as e:
            logging.error(f"Could not fetch transcript for video ID: {video_id}. Error: {e}")



def summarize_text_with_requests(text):
    # Replace this with your openrouter.ai API key


    if not llm_api_key:
        logging.error("OpenRouter API key is not set.")
        return None

    logging.info("Starting to summarize text with OpenRouter API.")

    url = llm_api_url
    headers = {
        "Authorization": f"Bearer {llm_api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "YOUR_SITE_URL",  # Optional, replace with your actual site URL
        "X-Title": "YOUR_APP_NAME",  # Optional, replace with your actual app name
    }
    data = json.dumps({
        "model": "gryphe/mythomist-7b:free",  # Optional, ensure this model is available in openrouter.ai
        "messages": [
            {"role": "user", "content": f"Summarize the following text into a concise summary:\n\n{text}"}
        ]
    })

    # Debugging: Print the headers and data being sent
    print("-------- Request Sent -----------")
    print(f"Sending request to {url} with headers: {headers} and data: {data}")


    response = requests.post(url=url, headers=headers, data=data)
    print("-------- Request Received -----------")
    # Debugging: Print the status code and response text
    print("Received response status code:", response.status_code)
    print("And response text:", response.text)

    if response.status_code == 200:
        summary = response.json()['choices'][0]['message']['content'].strip()
        logging.info("Text summarized successfully with OpenRouter API.")
        return summary
    else:
        logging.error(f"Failed to generate summary. Status code: {response.status_code}, Response: {response.text}")
        return None

def summarize_transcripts():
    for filename in os.listdir(transcription_dir):
        if filename.endswith('.json') and not filename.endswith('_summary.json'):
            base_name = filename.rsplit('.', 1)[0]
            summary_file = os.path.join(summary_dir, f"{base_name}_summary.json")

            if os.path.exists(summary_file):
                logging.info(f"Summary file {summary_file} already exists. Skipping.")
                continue

            try:
                with open(os.path.join(transcription_dir, filename), 'r') as f:
                    data = json.load(f)

                transcript = " ".join(data['transcript'])
                logging.info(f"Starting to summarize transcript for file {filename}")
                summary = summarize_text_with_requests(transcript)

                if summary:
                    summary_data = {
                        "title": data['name'],
                        "date": data['date'],
                        "summary": summary
                    }

                    with open(summary_file, 'w') as f:
                        json.dump(summary_data, f)
                    logging.info(f"Successfully wrote summary to {summary_file}")
            except Exception as e:
                logging.error(f"Error processing file {filename}. Error: {e}")

def main():
  logging.info(f"--- Started ---")
  get_transcripts(youtube, channel_id)
  summarize_transcripts()
  logging.info(f"--- Ended ---")
if __name__ == "__main__":
    main()
