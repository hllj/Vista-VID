import os
from dotenv import load_dotenv
# Load environment variables from .env file
load_dotenv()

from datetime import datetime
from src.generate import VideoDescriptionPipeline
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    pipeline = VideoDescriptionPipeline(
        level1_interval=10,
        level2_interval=30,
        model_name=os.environ["MODEL_NAME"],
        google_api_key=os.environ["GOOGLE_API_KEY"],
    )
    
    # Process YouTube video directly
    youtube_url = "https://www.youtube.com/watch?v=M8VqHdq37HY"
    
    try:
        results = pipeline.process_video(youtube_url)
        
        # Print results
        print(f"Processed YouTube video: {youtube_url}")
        print(f"Duration: {results['duration']:.2f} seconds")
        print(f"Generated {len(results['level1_descriptions'])} detailed descriptions")
        print(f"Generated {len(results['level2_descriptions'])} plot summaries")
        
        if results['level3_description']:
            print(f"\nFinal Overview:")
            print(results['level3_description']['content'])
        
        # Save results to JSON
        results['timestamp'] = datetime.now().isoformat()
        with open('youtube_video_analysis.json', 'w') as f:
            import json
            json.dump(results, f, indent=4)
        logger.info("YouTube video processed successfully.")
            
    except Exception as e:
        logger.error(f"Error processing YouTube video: {str(e)}")
        raise

if __name__ == "__main__":
    main()