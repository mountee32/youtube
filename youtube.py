import logging
import json
import dateutil.parser
from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi
import os
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables
load_dotenv()

youtube_api_key = os.getenv('YOUTUBE_API_KEY')
channel_id = os.getenv('CHANNEL_ID')

if not youtube_api_key:
    logging.error("YouTube API Key not set.")
    exit()

if not channel_id:
    logging.error("Channel ID not set.")
    exit()
    
youtube = build('youtube', 'v3', developerKey=youtube_api_key)

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
            logging.info(f"File {out_file} already exists. Skipping download.")
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
            
def main():
    get_transcripts(youtube, channel_id)

if __name__ == "__main__":
    main()
