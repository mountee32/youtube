import logging
from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize logging
logging.basicConfig(level=logging.INFO)  # Set the logging level to INFO
logger = logging.getLogger(__name__)

# Get YouTube API key from environment variables
youtube_api_key = os.getenv('YOUTUBE_API_KEY')
channel_id = os.getenv('CHANNEL_ID')

if not youtube_api_key:
    logger.error("YouTube API key not found. Make sure to set the YOUTUBE_API_KEY environment variable.")
    exit(1)

if not channel_id:
    logger.error("YouTube Channel ID not found. Make sure to set the CHANNEL_ID environment variable.")
    exit(1)

# Initialize YouTube API with the API key
youtube = build('youtube', 'v3', developerKey=youtube_api_key)

# Get the latest 10 videos from the channel
try:
    results = youtube.search().list(part='id', channelId=channel_id, order='date', maxResults=10).execute()
except Exception as e:
    logger.error(f"Failed to fetch videos for channel ID: {channel_id}. Error: {e}")
    exit(1)

# Loop through the results and get transcripts
for item in results['items']:
    video_id = item['id']['videoId']
    logger.info(f"Processing video ID: {video_id}")
    
    # Attempt to fetch the transcript for the video
    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        for transcript in transcript_list:
            # Fetch the actual transcript data
            transcript_data = transcript.fetch()

            # Construct the filename
            filename = f"{video_id}-full.txt"
            
            # Write the transcript data to a file
            with open(filename, 'w', encoding='utf-8') as file:
                for item in transcript_data:
                    file.write(f"{item['text']}\n")
            
            logger.info(f"Transcript written to {filename}")
    except Exception as e:
        logger.error(f"Could not fetch transcript for video ID: {video_id}. Error: {e}")
