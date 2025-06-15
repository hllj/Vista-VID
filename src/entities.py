from dataclasses import dataclass

@dataclass
class Description:
    """Represents a description at any level"""
    level: int
    timestamp: float
    content: str
    segment_index: int

@dataclass
class VideoSegment:
    """Represents a video segment with time boundaries"""
    start_time: float
    end_time: float
    segment_index: int