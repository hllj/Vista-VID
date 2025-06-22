from typing import Dict, List, Optional
from src.entities import VideoSegment, Description

class PromptFactory:
    """
    Factory class for generating prompts for different levels of video description.
    - Level 1: Detailed events for specific segments
    - Level 2: Plot summaries at regular intervals
    - Level 3: Complete overview of the entire video
    """
    
    @staticmethod
    def create_level1_prompt(segment: VideoSegment, context: Dict) -> str:
        """
        Create prompt for level-1 description (detailed events)
        
        Args:
            segment: VideoSegment to analyze
            context: Dictionary containing previous descriptions context
            
        Returns:
            Formatted prompt string
        """
        prompt = f"""Analyze the video segment from {segment.start_time:.1f}s to {segment.end_time:.1f}s and provide a comprehensive description covering:
Primary Elements:

Actions: Describe all human/object movements, gestures, and interactions
Scene composition: Spatial relationships, camera angles, and framing changes
Temporal progression: Sequence of events and their causal relationships

Secondary Elements:

Visual details: Colors, lighting, textures, and environmental context
Audio-visual sync: Dialogue, sound effects, music, and their relation to visuals
Narrative significance: Plot advancement, character development, or thematic elements

Output Format:
Structure your response as a flowing narrative that captures both the literal events and their contextual meaning within the broader video content. Prioritize clarity and specificity over brevity.

"""
        
        if context.get("previous_level1"):
            prompt += f"Previous segment description: {context['previous_level1']}\n\n"
        
        if context.get("latest_level2"):
            prompt += f"Overall plot summary so far: {context['latest_level2']}\n\n"
        
        prompt += "Describe what happens in the current segment in 3-5 sentences:"
        
        return prompt
    
    @staticmethod
    def create_level2_prompt(recent_level1: List[Description], 
                           latest_level2: Optional[Description], 
                           current_time: float) -> str:
        """
        Create prompt for level-2 description (plot summary)
        
        Args:
            recent_level1: Recent level-1 descriptions
            latest_level2: Latest level-2 description if available
            current_time: Current timestamp in the video
            
        Returns:
            Formatted prompt string
        """
        prompt = f"You are creating a plot summary for a video up to {current_time:.1f} seconds.\n\n"
        
        if latest_level2:
            prompt += f"Previous plot summary: {latest_level2.content}\n\n"
        
        prompt += "Recent events:\n"
        for desc in recent_level1:
            prompt += f"- At {desc.timestamp:.1f}s: {desc.content}\n"
        
        prompt += "\nProvide an updated plot summary that incorporates these recent events. Keep it concise but comprehensive (5-7 sentences):"
        
        return prompt
    
    @staticmethod
    def create_level3_prompt(unsummarized_level1: List[Description], 
                           latest_level2: Optional[Description], 
                           total_duration: float) -> str:
        """
        Create prompt for level-3 description (complete overview)
        
        Args:
            unsummarized_level1: Level-1 descriptions not yet summarized
            latest_level2: Latest level-2 description if available
            total_duration: Total duration of the video
            
        Returns:
            Formatted prompt string
        """
        prompt = f"""You are creating a complete overview of this {total_duration:.1f}-second video.

Please analyze the entire video and provide a comprehensive description that captures:
- The complete narrative arc
- Key themes and messages
- Main characters and their roles
- Important visual or audio elements
- Overall tone and style

"""
        
        if latest_level2:
            prompt += f"Main plot summary from earlier analysis: {latest_level2.content}\n\n"
        
        if unsummarized_level1:
            prompt += "Final events not yet summarized:\n"
            for desc in unsummarized_level1:
                prompt += f"- At {desc.timestamp:.1f}s: {desc.content}\n"
            prompt += "\n"
        
        prompt += "\nProvide a comprehensive description of the entire video that would serve as a standalone summary (7-10 sentences):"
        
        return prompt
