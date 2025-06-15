import os
import dotenv
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import json
from pathlib import Path
import logging

# Load environment variables from .env file
dotenv.load_dotenv()

from google import genai
from google.genai import types

from src.entities import VideoSegment, Description
from src.prompts.factory import PromptFactory

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# VideoSegment and Description classes are now imported from factory.py

class VideoDescriptionPipeline:
    """
    Hierarchical video description pipeline implementing three-level approach using Gemini's native video understanding:
    - Level 1: Every 10 seconds (detailed events)
    - Level 2: Every 30 seconds (plot summary)
    - Level 3: End of video (complete overview)
    """
    
    def __init__(self, 
                 google_api_key: Optional[str] = None,
                 level1_interval: int = 10,
                 level2_interval: int = 30,
                 model_name: str = "models/gemini-2.5-flash-preview-05-20"):
        """
        Initialize the pipeline
        
        Args:
            google_api_key: Google API key for Gemini (if None, uses GOOGLE_API_KEY env var)
            level1_interval: Seconds between level-1 descriptions
            level2_interval: Seconds between level-2 descriptions
            model_name: Gemini model to use (must support video understanding)
        """
        api_key = google_api_key or os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("Google API key must be provided either as parameter or GOOGLE_API_KEY environment variable")
        
        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name
        logger.info(f"Using Gemini model: {self.model_name}")

        # Check model availability in Gemini
        available_models = [model.name for model in self.client.models.list()]
        if self.model_name not in available_models:
            raise ValueError(f"Model {self.model_name} is not available in Gemini. Please check the model name.")
        
        self.level1_interval = level1_interval
        self.level2_interval = level2_interval
        
        # Storage for descriptions
        self.level1_descriptions: List[Description] = []
        self.level2_descriptions: List[Description] = []
        self.level3_description: Optional[Description] = None
        
    def _upload_video(self, video_path: str) -> str:
        """
        Upload video to Gemini and return file URI
        
        Args:
            video_path: Path to the video file
            
        Returns:
            File URI for the uploaded video
        """
        logger.info(f"Uploading video: {video_path}")
        
        # Upload file to Gemini
        uploaded_file = self.client.files.upload(path=video_path)
        logger.info(f"Video uploaded with URI: {uploaded_file.uri}")
        
        return uploaded_file.uri
    
    def _get_video_duration(self, video_uri: str) -> float:
        """
        Get video duration using appropriate library based on video source
        
        Args:
            video_uri: URI of the uploaded video or path to video file
            
        Returns:
            Duration in seconds
        """
        logger.info("Getting video duration...")
        
        try:
            # Handle YouTube URLs
            if "youtube.com" in video_uri or "youtu.be" in video_uri:
                import pytube
                try:
                    # Use pytube to get video length
                    yt = pytube.YouTube(video_uri)
                    duration = yt.length
                    logger.info(f"YouTube video duration: {duration} seconds")
                    return float(duration)
                except Exception as yt_error:
                    logger.error(f"Error with pytube: {yt_error}")
                    # Fallback to yt-dlp if available
                    try:
                        import yt_dlp
                        
                        ydl_opts = {
                            'quiet': True,
                            'no_warnings': True,
                            'skip_download': True,
                            'format': 'best',
                        }
                        
                        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                            info = ydl.extract_info(video_uri, download=False)
                            duration = info.get('duration', 0)
                            logger.info(f"YouTube video duration (via yt-dlp): {duration} seconds")
                            return float(duration)
                    except Exception as ydl_error:
                        logger.error(f"Error with yt-dlp: {ydl_error}")
                        # If both methods fail, use default duration
                        logger.warning("Using default duration for YouTube video")
                        return 300.0
            # Handle Gemini file URIs
            elif video_uri.startswith(('gs://', 'file-')):
                # For Gemini URIs, we can't directly get the duration
                # Use a reasonable default duration
                logger.warning("Cannot determine duration for Gemini file URI, using default duration")
                return 300.0
            # Handle local files or other direct video URLs
            else:
                from moviepy.editor import VideoFileClip
                
                # For local files, use the path directly
                video_path = video_uri
                if video_uri.startswith(('http://', 'https://')):
                    # For HTTP URLs, download temporarily or stream
                    import tempfile
                    import requests
                    
                    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
                    with requests.get(video_uri, stream=True) as r:
                        r.raise_for_status()
                        for chunk in r.iter_content(chunk_size=8192):
                            temp_file.write(chunk)
                    temp_file.close()
                    video_path = temp_file.name
                
                # Get duration using moviepy
                clip = VideoFileClip(video_path)
                duration = clip.duration
                clip.close()
                
                # Clean up temp file if created
                if video_uri.startswith(('http://', 'https://')) and 'temp_file' in locals():
                    import os
                    os.unlink(temp_file.name)
                    
                logger.info(f"Video duration: {duration} seconds")
                return duration
        except Exception as e:
            logger.error(f"Error getting video duration: {e}")
            logger.warning("Using default duration estimation of 300 seconds")
            return 300.0  # Default 5 minutes
    
    def _create_video_segments(self, duration: float) -> List[VideoSegment]:
        """
        Create video segments based on level-1 interval
        
        Args:
            duration: Total video duration in seconds
            
        Returns:
            List of VideoSegment objects
        """
        segments = []
        current_time = 0
        segment_index = 0
        
        while current_time < duration:
            end_time = min(current_time + self.level1_interval, duration)
            segment = VideoSegment(
                start_time=current_time,
                end_time=end_time,
                segment_index=segment_index
            )
            segments.append(segment)
            current_time = end_time
            segment_index += 1
        
        logger.info(f"Created {len(segments)} video segments")
        return segments
    
    def generate_level1_description(self, video_uri: str, segment: VideoSegment) -> Description:
        """
        Generate Level-1 description for a video segment
        
        Args:
            video_uri: URI of the uploaded video
            segment: VideoSegment to analyze
            
        Returns:
            Description object with level-1 content
        """
        logger.info(f"Generating Level-1 description for segment {segment.segment_index} ({segment.start_time}s-{segment.end_time}s)")
        
        # Prepare context
        context = self._build_level1_context(segment.segment_index)
        
        # Create prompt
        prompt = self._create_level1_prompt(segment, context)
        
        # Create content with video segment
        content_parts = [
            types.Part(
                file_data=types.FileData(file_uri=video_uri),
                video_metadata=types.VideoMetadata(
                    start_offset=f'{int(segment.start_time)}s',
                    end_offset=f'{int(segment.end_time)}s'
                )
            ),
            types.Part(text=prompt)
        ]
        
        # Call Gemini
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=types.Content(parts=content_parts),
            config=types.GenerateContentConfig(
                max_output_tokens=1024,
                temperature=0.1
            )
        )
        
        description = Description(
            level=1,
            timestamp=segment.start_time,
            content=response.text.strip(),
            segment_index=segment.segment_index
        )
        
        self.level1_descriptions.append(description)
        return description
    
    def generate_level2_description(self, video_uri: str, current_time: float) -> Description:
        """
        Generate Level-2 description (plot summary)
        
        Args:
            video_uri: URI of the uploaded video
            current_time: Current timestamp in the video
            
        Returns:
            Description object with level-2 content
        """
        logger.info(f"Generating Level-2 description at {current_time}s")
        
        # Get the last 3 level-1 descriptions
        recent_level1 = self._get_recent_level1_descriptions(3)
        
        # Get the latest level-2 description
        latest_level2 = self.level2_descriptions[-1] if self.level2_descriptions else None
        
        # Create prompt
        prompt = self._create_level2_prompt(recent_level1, latest_level2, current_time)
        
        content_parts = [
            types.Part(
                file_data=types.FileData(file_uri=video_uri),
                video_metadata=types.VideoMetadata(
                    start_offset=f'{int(current_time - self.level2_interval)}s',
                    end_offset=f'{int(current_time)}s'
                )
            ),
            types.Part(text=prompt)
        ]
        
        # For level-2, we can either use the recent segment or provide context without video
        # Using text-only generation with context from level-1 descriptions
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=types.Content(parts=content_parts),
            config=types.GenerateContentConfig(
                max_output_tokens=2048,
                temperature=0.1
            )
        )
        
        segment_index = len(self.level2_descriptions)
        description = Description(
            level=2,
            timestamp=current_time,
            content=response.text.strip(),
            segment_index=segment_index
        )
        
        self.level2_descriptions.append(description)
        return description
    
    def generate_level3_description(self, video_uri: str, total_duration: float) -> Description:
        """
        Generate Level-3 description (complete video overview)
        
        Args:
            video_uri: URI of the uploaded video
            total_duration: Total duration of the video
            
        Returns:
            Description object with level-3 content
        """
        logger.info("Generating Level-3 description (complete overview)")
        
        # Get recent unsummarized level-1 descriptions
        last_level2_time = self.level2_descriptions[-1].timestamp if self.level2_descriptions else 0
        unsummarized_level1 = [desc for desc in self.level1_descriptions 
                              if desc.timestamp > last_level2_time]
        
        # Get the latest level-2 description
        latest_level2 = self.level2_descriptions[-1] if self.level2_descriptions else None
        
        # Create prompt
        prompt = self._create_level3_prompt(unsummarized_level1, latest_level2, total_duration)
        
        # For level-3, we can analyze the entire video for a comprehensive overview
        content_parts = [
            types.Part(file_data=types.FileData(file_uri=video_uri)),
            types.Part(text=prompt)
        ]
        
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=types.Content(parts=content_parts),
            config=types.GenerateContentConfig(
                max_output_tokens=2048,
                temperature=0.1
            )
        )
        
        self.level3_description = Description(
            level=3,
            timestamp=total_duration,
            content=response.text.strip(),
            segment_index=0
        )
        
        return self.level3_description
    
    def _build_level1_context(self, segment_index: int) -> Dict:
        """Build context for level-1 description generation"""
        context = {
            "previous_level1": None,
            "latest_level2": None
        }
        
        # Get previous level-1 description
        if segment_index > 0 and self.level1_descriptions:
            context["previous_level1"] = self.level1_descriptions[-1].content
        
        # Get latest level-2 description if applicable
        if self.level2_descriptions:
            context["latest_level2"] = self.level2_descriptions[-1].content
        
        return context
    
    def _get_recent_level1_descriptions(self, count: int) -> List[Description]:
        """Get the most recent level-1 descriptions"""
        return self.level1_descriptions[-count:] if len(self.level1_descriptions) >= count else self.level1_descriptions
    
    def _create_level1_prompt(self, segment: VideoSegment, context: Dict) -> str:
        """Create prompt for level-1 description"""
        return PromptFactory.create_level1_prompt(segment, context)
    
    def _create_level2_prompt(self, recent_level1: List[Description], 
                            latest_level2: Optional[Description], 
                            current_time: float) -> str:
        """Create prompt for level-2 description"""
        return PromptFactory.create_level2_prompt(recent_level1, latest_level2, current_time)
    
    def _create_level3_prompt(self, unsummarized_level1: List[Description], 
                            latest_level2: Optional[Description], 
                            total_duration: float) -> str:
        """Create prompt for level-3 description"""
        return PromptFactory.create_level3_prompt(unsummarized_level1, latest_level2, total_duration)
    
    def process_video(self, video_path: str) -> Dict[str, any]:
        """
        Process a complete video through the hierarchical description pipeline
        
        Args:
            video_path: Path to the video file or URL
            
        Returns:
            Dictionary containing all generated descriptions
        """
        logger.info(f"Starting video processing: {video_path}")
        
        # Reset state
        self.level1_descriptions = []
        self.level2_descriptions = []
        self.level3_description = None
        
        # Handle different input types (file path or URL)
        if video_path.startswith(('http://', 'https://', 'gs://')):
            video_uri = video_path
            logger.info(f"Using direct video URI: {video_uri}")
        else:
            # Upload local video file
            video_uri = self._upload_video(video_path)
        
        # Get video duration
        duration = self._get_video_duration(video_uri)
        
        # Create segments
        segments = self._create_video_segments(duration)
        
        # Process each segment for Level-1 descriptions
        for segment in segments:
            self.generate_level1_description(video_uri, segment)
            
            # Generate Level-2 description every 30 seconds
            current_time = segment.end_time
            if (segment.segment_index + 1) * self.level1_interval % self.level2_interval == 0 or current_time >= duration - 1:
                self.generate_level2_description(video_uri, current_time)
        
        # Generate Level-3 description
        self.generate_level3_description(video_uri, duration)
        
        # Compile results
        results = {
            "video_path": video_path,
            "video_uri": video_uri,
            "duration": duration,
            "processing_timestamp": datetime.now().isoformat(),
            "level1_descriptions": [
                {
                    "timestamp": desc.timestamp,
                    "content": desc.content,
                    "segment_index": desc.segment_index
                }
                for desc in self.level1_descriptions
            ],
            "level2_descriptions": [
                {
                    "timestamp": desc.timestamp,
                    "content": desc.content,
                    "segment_index": desc.segment_index
                }
                for desc in self.level2_descriptions
            ],
            "level3_description": {
                "timestamp": self.level3_description.timestamp,
                "content": self.level3_description.content
            } if self.level3_description else None
        }
        
        logger.info("Video processing completed successfully")
        return results
    
    def save_results(self, results: Dict, output_path: str):
        """Save results to JSON file"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        logger.info(f"Results saved to {output_path}")