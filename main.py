import logging
import json
import os
from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi
import dateutil.parser
from dotenv import load_dotenv
import requests
import openai


# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables
load_dotenv()

# API Keys and Channel ID
youtube_api_key = os.getenv('YOUTUBE_API_KEY')
channel_id = os.getenv('CHANNEL_ID')
openai_api_key = os.getenv('OPENAI_API_KEY')

# LLM Model and API URL
llm_model = os.getenv('LLM_MODEL')
openai_api_url = os.getenv('OPENAI_API_URL')

if not youtube_api_key or not channel_id or not openai_api_key or not llm_model or not openai_api_url:
    logging.error("One or more required environment variables are not set.")
    exit()

# Initialize YouTube API client
youtube = build('youtube', 'v3', developerKey=youtube_api_key)
openai.api_key = openai_api_key

def get_transcripts(youtube, channel_id):
    try:
        logging.info("Starting to fetch videos from YouTube API.")
        results = youtube.search().list(part='id', channelId=channel_id, order='date', maxResults=10).execute()
        logging.info(f"Successfully fetched videos for channel ID: {channel_id}")
    except Exception as e:
        logging.error(f"Failed to fetch videos for channel ID: {channel_id}. Error: {e}")
        return

    for item in results['items']:
        video_id = item['id']['videoId']

        # File path 
        out_file = f"{video_id}.json"

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
    if not openai_api_key:
        logging.error("OpenAI API key is not set.")
        return None

    logging.info("Starting to summarize text with OpenAI API.")

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {openai_api_key}'
    }
    data = {
        "model": llm_model,
        "messages": [{"role": "user", "content": f"Summarize the following text into a concise summary:\n\n{text}"}],
    }

    response = requests.post(openai_api_url, headers=headers, json=data)

    if response.status_code == 200:
        summary = response.json()['choices'][0]['message']['content'].strip()
        logging.info("Text summarized successfully with OpenAI API.")
        return summary
    else:
        logging.error(f"Failed to generate summary. Status code: {response.status_code}, Response: {response.text}")
        return None

def summarize_transcripts():
  for filename in os.listdir('.'):
      if filename.endswith('.json') and not filename.endswith('_summary.json'):
          base_name = filename.rsplit('.', 1)[0]
          summary_file = f"{base_name}_summary.json"

          if os.path.exists(summary_file):
              logging.info(f"Summary file {summary_file} already exists. Skipping.")
              continue

          try:
              with open(filename, 'r') as f:
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
    get_transcripts(youtube, channel_id)
    summarize_transcripts()

if __name__ == "__main__":
    main()
