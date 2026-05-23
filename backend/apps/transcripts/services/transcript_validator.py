"""Data validation and cleaning pipeline for lecture transcripts."""

from dataclasses import dataclass
from typing import Optional
import re


@dataclass
class TranscriptValidationResult:
    """Result of transcript validation."""
    is_valid: bool
    cleaned_text: Optional[str]
    issues: list[str]
    quality_score: float  # 0-1, higher is better
    estimated_duration_seconds: int


class TranscriptValidator:
    """Validates and cleans raw lecture transcripts before LLM processing."""
    
    MIN_LENGTH = 100  # Minimum characters
    MAX_LENGTH = 1_000_000  # Maximum characters
    QUALITY_THRESHOLD = 0.5  # Minimum quality to accept
    
    # Filler patterns to remove
    FILLER_WORDS = {
        r'\b(um|uh|ah|eh|erm|like|you know|sort of|kind of)\b': '',
        r'\[.*?\]': '',  # Remove bracketed notes
        r'\(.*?\)': ' ',  # Remove parentheses notes (keep spacing)
        r'\s+': ' ',  # Normalize whitespace
    }
    
    # Sentence segmentation pattern
    SENTENCE_PATTERN = r'(?<=[.!?])\s+'
    
    def validate(self, transcript: str) -> TranscriptValidationResult:
        """
        Validate and clean transcript.
        
        Returns:
            TranscriptValidationResult with cleaned text and quality metrics
        """
        issues = []
        
        # Length checks
        if not transcript or len(transcript.strip()) < self.MIN_LENGTH:
            issues.append(f"Transcript too short (min {self.MIN_LENGTH} chars)")
            return TranscriptValidationResult(
                is_valid=False,
                cleaned_text=None,
                issues=issues,
                quality_score=0.0,
                estimated_duration_seconds=0,
            )
        
        if len(transcript) > self.MAX_LENGTH:
            issues.append(f"Transcript too long (max {self.MAX_LENGTH} chars)")
            return TranscriptValidationResult(
                is_valid=False,
                cleaned_text=None,
                issues=issues,
                quality_score=0.0,
                estimated_duration_seconds=0,
            )
        
        # Clean transcript
        cleaned = self._clean_text(transcript)
        
        # Quality checks
        quality_score = self._compute_quality_score(transcript, cleaned)
        
        if quality_score < self.QUALITY_THRESHOLD:
            issues.append(f"Quality score too low ({quality_score:.2f} < {self.QUALITY_THRESHOLD})")
        
        # Language check (basic)
        if not self._is_valid_language(cleaned):
            issues.append("Invalid or unsuitable language detected")
        
        is_valid = len(issues) == 0 and quality_score >= self.QUALITY_THRESHOLD
        
        # Estimate duration (assume ~130 words per minute)
        word_count = len(cleaned.split())
        estimated_duration = int((word_count / 130) * 60)
        
        return TranscriptValidationResult(
            is_valid=is_valid,
            cleaned_text=cleaned if is_valid else None,
            issues=issues,
            quality_score=quality_score,
            estimated_duration_seconds=estimated_duration,
        )
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize transcript text."""
        # Remove filler patterns
        for pattern, replacement in self.FILLER_WORDS.items():
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def _compute_quality_score(self, original: str, cleaned: str) -> float:
        """
        Compute quality score based on various metrics.
        
        Score = (has_content * avg_word_length * sentence_diversity * readability) / 4
        """
        scores = []
        
        # Content presence
        has_content = 1.0 if len(cleaned.split()) > 50 else 0.5
        scores.append(has_content)
        
        # Average word length (optimal: 4-7 chars)
        words = cleaned.split()
        avg_word_length = sum(len(w) for w in words) / len(words) if words else 0
        word_length_score = min(1.0, avg_word_length / 6.0)
        scores.append(word_length_score)
        
        # Sentence diversity (number of unique sentences)
        sentences = re.split(self.SENTENCE_PATTERN, cleaned)
        unique_sentences = len(set(sentences)) / max(len(sentences), 1)
        scores.append(unique_sentences)
        
        # Readability (ratio of filler removal)
        removed_ratio = 1.0 - (len(cleaned) / max(len(original), 1))
        readability = min(1.0, removed_ratio)  # More removal = better cleaning
        scores.append(readability)
        
        return sum(scores) / len(scores) if scores else 0.0
    
    def _is_valid_language(self, text: str) -> bool:
        """Check if text is valid English."""
        # Basic checks: has alphabetic characters, reasonable ratio
        alpha_count = sum(1 for c in text if c.isalpha())
        if alpha_count < len(text) * 0.5:  # At least 50% alphabetic
            return False
        
        # No excessive special characters
        special_count = sum(1 for c in text if not c.isalnum() and c not in ' \n\t.,!?-')
        if special_count > len(text) * 0.1:  # Max 10% special chars
            return False
        
        return True
    
    def chunk_transcript(self, transcript: str, chunk_size: int = 2000, overlap: int = 200) -> list[str]:
        """
        Split transcript into overlapping chunks for processing.
        
        Args:
            transcript: Clean transcript text
            chunk_size: Target characters per chunk
            overlap: Number of overlapping characters between chunks
        
        Returns:
            List of transcript chunks
        """
        chunks = []
        start = 0
        
        while start < len(transcript):
            end = min(start + chunk_size, len(transcript))
            chunk = transcript[start:end]
            chunks.append(chunk)
            start = end - overlap
        
        return chunks
