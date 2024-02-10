import logging
import json
import os
import openai
from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi
import dateutil.parser
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables
load_dotenv()

youtube_api_key = os.getenv('YOUTUBE_API_KEY')
channel_id = os.getenv('CHANNEL_ID')
openai_api_key = os.getenv('OPENAI_API_KEY')

if not youtube_api_key or not channel_id or not openai_api_key:
    logging.error("One or more required environment variables (YOUTUBE_API_KEY, CHANNEL_ID, OPENAI_API_KEY) are not set.")
    exit()

youtube = build('youtube', 'v3', developerKey=youtube_api_key)
openai.api_key = openai_api_key

def get_transcripts(youtube, channel_id):
    try:
        results = youtube.search().list(part='id', channelId=channel_id, order='date', maxResults=10).execute()
        logging.info(f"Fetching videos for channel ID: {channel_id}")
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
            # Get video details
            video_details = youtube.videos().list(part='snippet', id=video_id).execute()
            logging.info(f"Fetching transcript for video ID: {video_id}")

            # Fetch transcript
            transcript_data = YouTubeTranscriptApi.get_transcript(video_id)

            # Construct JSON output
            output = {
                "name": video_details['items'][0]['snippet']['title'],
                "date": dateutil.parser.parse(video_details['items'][0]['snippet']['publishedAt']).strftime("%Y-%m-%d"),
                "transcript": [item['text'] for item in transcript_data]
            }
            
            # Write json file
            with open(out_file, 'w') as f:
                json.dump(output, f)
            logging.info(f"Successfully wrote transcript to {out_file}")

        except Exception as e:
            logging.error(f"Could not fetch transcript for video ID: {video_id}. Error: {e}")

def summarize_text(text):
    try:
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=f"Summarize the following text into a concise summary:\n\n{text}",
            max_tokens=1500,  # Adjust based on your needs
            temperature=0.5
        )
        summary = response.choices[0].text.strip()
        return summary
    except Exception as e:
        logging.error(f"Failed to generate summary. Error: {e}")
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
                summary = summarize_text(transcript)
                
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
