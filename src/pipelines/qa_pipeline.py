import os
import json
import logging
import re  # Add regex module for JSON string sanitization
from pathlib import Path
from typing import Dict, List, Optional, Union

from google import genai
from google.genai import types

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class QAPipeline:
    """
    Pipeline for generating question-answer pairs from video descriptions
    based on predefined task dimensions.
    """
    
    def __init__(
        self,
        model_name: str = "models/gemini-2.5-flash-preview-05-20",
        google_api_key: Optional[str] = None,
        task_definition_path: Optional[str] = None,
        temperature: float = 0.5,  # Lower default temperature for more reliable JSON formatting
    ):
        """
        Initialize the QA pipeline.
        
        Args:
            model_name: Name of the model to use (default: "models/gemini-2.5-flash-preview-05-20")
            google_api_key: Google API key for Google models
            task_definition_path: Path to task definitions markdown file
            temperature: Temperature for model generation (default: 0.1)
        """
        api_key = google_api_key or os.environ.get("GOOGLE_API_KEY")
        logger.debug(f"API key provided for Google models: {api_key is not None}")
        if not api_key:
            raise ValueError("Google API key must be provided either as parameter or GOOGLE_API_KEY environment variable")
        
        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name
        self.temperature = temperature
        logger.info(f"Using Gemini model: {self.model_name} with temperature: {self.temperature}")

        # # Check model availability in Gemini
        # available_models = [model.name for model in self.client.models.list()]
        # if self.model_name not in available_models:
        #     raise ValueError(f"Model {self.model_name} is not available in Gemini. Available models: {available_models}")
            
        # Load task definitions
        if task_definition_path:
            self.task_definitions = self._load_task_definitions(task_definition_path)
        else:
            # Use the default path
            base_dir = Path(__file__).parents[2]  # Go up to Vista-VID directory
            default_path = base_dir / "src" / "prompts" / "tasks.md"
            self.task_definitions = self._load_task_definitions(default_path)
            
        # Prepare system message template
        self.system_message_template = self._create_system_message()
        self.user_message_template = """
        Please generate question-answer pairs for the following video description:

        Description: {caption}

        IMPORTANT: Your response MUST be a valid JSON array containing ONLY the question-answer pairs.
        No explanations, no code blocks, no additional text - just the JSON array.
        """
    
    def _load_task_definitions(self, file_path: Union[str, Path]) -> str:
        """Load task definitions from a markdown file."""
        try:
            with open(file_path, 'r') as f:
                return f.read()
        except FileNotFoundError:
            logger.error(f"Task definitions file not found at {file_path}")
            raise
            
    def _create_system_message(self) -> str:
        """Create the system message with task definitions."""
        return """
        ### Task:
        Given a detailed description that summarizes the content of a video, generate question-answer pairs
        based on the description to help humans better understand the video. The question-answer pairs
        should be faithful to the content of the video description and developed from different dimensions to
        promote comprehensive understanding of the video.

        Here are some question dimensions and their explanations and example question-answer pairs for
        reference:
        {task_definitions}

        #### Guidelines For Question-Answer Pairs Generation:
        - Read the video description provided carefully, paying attention to the content, such as the scene
          where the video takes place, the main characters and their behaviors, and the development of the
          events.
        - Generate appropriate question-answer pairs based on the description. The question-answer pairs
          should cover as many question dimensions as possible and not deviate from the content of the video description.
        - Generate 1 question-answer pair for each dimension.
        - Choose appropriate dimensions from the list provided above based on the video content.
        - Try to create diversity, complex question pairs.

        ### Output Format Requirements:
        1. IMPORTANT: Your output MUST be ONLY a valid JSON array with no additional text.
        2. Do not include any explanation, preamble, or conclusions.
        3. Do not wrap the JSON in code blocks or markdown.
        4. Each object in the array must have exactly these three keys: "Dimension", "Question", "Answer".
        5. All JSON syntax must be strictly valid with proper quotes, commas, and brackets.
        6. Ensure all strings are properly escaped, especially quotes inside the text.
        7. Do not use line breaks within the string values, replace them with spaces.
        
        Expected JSON structure:
        [
          {{"Dimension": "<dimension-1>", "Question": "<question-1>", "Answer": "<answer-1>"}},
          {{"Dimension": "<dimension-2>", "Question": "<question-2>", "Answer": "<answer-2>"}},
          ...
        ]
        """
    
    def generate_qa_pairs(self, caption: str, max_retries: int = 3) -> List[Dict[str, str]]:
        """
        Generate question-answer pairs for a given video description.
        
        Args:
            caption: The video description
            max_retries: Maximum number of retries on failure
            
        Returns:
            List of dictionaries containing dimension, question, and answer
        """
        logger.debug(f"system message_template: {self.system_message_template}")
        system_message = self.system_message_template.format(task_definitions=self.task_definitions)
        user_message = self.user_message_template.format(caption=caption)
        
        # Try to generate QA pairs with retries
        qa_pairs = []
        attempts = 0
        success = False
        
        while attempts < max_retries and not success:
            attempts += 1
            try:
                logger.info(f"Attempt {attempts}/{max_retries} to generate QA pairs")
                
                # Send the request to the model
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=user_message,
                    config=types.GenerateContentConfig(
                        system_instruction=system_message,
                        temperature=self.temperature,
                        max_output_tokens=8192
                    )
                )
                
                if response.text is None:
                    raise ValueError("Received empty response from model")
                    
                raw_text = response.text
                
                logger.debug(f"Raw response text: {raw_text}")
                
                # Try to parse the JSON response
                qa_pairs = self._parse_json_response(raw_text)
                
                # If we get here without an exception, we have valid JSON
                success = True
                logger.info(f"Successfully generated {len(qa_pairs)} QA pairs")
                
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse JSON response: {e}")
                
                if attempts == max_retries:
                    logger.error(f"Failed to generate valid JSON after {max_retries} attempts")
                    return []
                    
                # Wait a moment before retrying
                import time
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Unexpected error generating QA pairs: {e}")
                if attempts == max_retries:
                    logger.error(f"Failed after {max_retries} attempts")
                    return []
        
        return qa_pairs
        
    def _parse_json_response(self, text: str) -> List[Dict[str, str]]:
        """
        Parse the JSON response from the model.
        
        Args:
            text: Raw text response from the model
            
        Returns:
            List of dictionaries containing dimension, question, and answer
            
        Raises:
            json.JSONDecodeError: If the response cannot be parsed as JSON
        """
        # Clean the text to ensure it's valid JSON
        # Remove any non-JSON content before and after the array
        text = text.strip()
        
        # Find the first '[' and last ']' to extract just the JSON array
        start_idx = text.find('[')
        end_idx = text.rfind(']')
        
        if start_idx == -1 or end_idx == -1 or start_idx > end_idx:
            logger.error("Response does not contain a valid JSON array structure")
            raise json.JSONDecodeError("No valid JSON array found", text, 0)
            
        json_text = text[start_idx:end_idx+1]
        
        # Parse the JSON
        qa_pairs = json.loads(json_text)
        
        # Validate the structure
        if not isinstance(qa_pairs, list):
            raise json.JSONDecodeError("Response is not a list", json_text, 0)
            
        return qa_pairs
    
    def _verify_qa_pairs_format(self, qa_pairs: List[Dict[str, str]]) -> bool:
        """
        Verify that QA pairs have the correct format.
        
        Args:
            qa_pairs: List of dictionaries to verify
            
        Returns:
            True if the format is correct, False otherwise
        """
        if not isinstance(qa_pairs, list):
            logger.error("QA pairs is not a list")
            return False
            
        for i, pair in enumerate(qa_pairs):
            if not isinstance(pair, dict):
                logger.error(f"QA pair {i} is not a dictionary")
                return False
                
            # Check required keys
            required_keys = ["Dimension", "Question", "Answer"]
            for key in required_keys:
                if key not in pair:
                    logger.error(f"QA pair {i} is missing required key: {key}")
                    return False
                if not isinstance(pair[key], str):
                    logger.error(f"QA pair {i}: {key} is not a string")
                    return False
                    
        return True
    
    def process_video_descriptions(self, descriptions: List[str], output_path: Optional[str] = None) -> List[Dict]:
        """
        Process multiple video descriptions and generate QA pairs for each.
        
        Args:
            descriptions: List of video descriptions
            output_path: Optional path to save results
            
        Returns:
            List of results, each containing the description and generated QA pairs
        """
        results = []
        
        for i, description in enumerate(descriptions):
            logger.info(f"Processing description {i+1}/{len(descriptions)}")
            qa_pairs = self.generate_qa_pairs(description)
            
            # Verify QA pairs format
            if not self._verify_qa_pairs_format(qa_pairs):
                logger.warning(f"QA pairs for description {i+1} failed verification, using empty list")
                qa_pairs = []
            
            result = {
                "description": description,
                "qa_pairs": qa_pairs
            }
            results.append(result)
        
        # Save results if output path is provided
        if output_path:
            with open(output_path, 'w') as f:
                json.dump(results, f, indent=2)
            logger.info(f"Saved QA pairs to {output_path}")
        
        return results
    
    def process_single_description(self, description: str) -> List[Dict[str, str]]:
        """
        Process a single video description and generate QA pairs.
        
        Args:
            description: The video description
            
        Returns:
            List of dictionaries containing dimension, question, and answer
        """
        qa_pairs = self.generate_qa_pairs(description)
        
        # Verify QA pairs format
        if not self._verify_qa_pairs_format(qa_pairs):
            logger.warning("QA pairs failed verification, using empty list")
            return []
            
        return qa_pairs
    
    def process_video_analysis(self, level: int, video_analysis: Dict) -> List[Dict[str, str]]:
        """
        Process a video description at a specific level and generate QA pairs.
        
        Args:
            level: The level of the description (1, 2, or 3)
            description: The video description
            
        Returns:
            List of dictionaries containing dimension, question, and answer
        """
        if level in [1, 2]:
            descriptions: Optional[Union[List, Dict]] = video_analysis.get(f"level{level}_descriptions", None)
            level_interval = video_analysis.get(f"level{level}_interval", 10)
            logger.info(f"Processing level {level} descriptions with interval {level_interval}s")
        elif level == 3:
            descriptions = video_analysis.get(f"level{level}_description", None)
            level_interval = None
        
        if not descriptions:
            logger.warning(f"No descriptions found for level {level}")
            return []

        if isinstance(descriptions, list):
            all_description = ""
            for i, desc in enumerate(descriptions):
                content = desc["content"]
                if level_interval:
                    start = i * level_interval
                    end = min(start + level_interval, video_analysis["duration"])
                    description = f"From {start:.1f}s to {end:.1f}s): {content}"
                else:
                    description = content
                all_description += f"\n{description}"
        else:
            all_description = descriptions["content"]
            
        logger.debug(f"Processing description: {all_description}")
        qa_pairs = self.process_single_description(all_description)
        return qa_pairs
        
        
if __name__ == "__main__":
    # Load environment variables (assuming they are set)
    pipeline = QAPipeline()
    
    # Load the YouTube video analysis JSON file
    json_path = Path(__file__).parents[2] / "youtube_video_analysis.json"
    with open(json_path, 'r') as f:
        video_analysis = json.load(f)
    
    results = []
    for level in [1, 2, 3]:
        qa_pairs = pipeline.process_video_analysis(level, video_analysis)
        results.append({
            "level": level,
            "qa_pairs": qa_pairs
        })
    
    # Optionally, save all results to a file
    output_path = Path(__file__).parents[2] / "qa_results.json"
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nResults saved to {output_path}")