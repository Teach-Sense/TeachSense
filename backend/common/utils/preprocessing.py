"""
Pre-processing engine for lecture transcript data.
Handles validation, cleaning, and normalization before LLM ensemble inference.
"""
import re
from typing import Dict, List, Tuple
from dataclasses import dataclass
from enum import Enum


class CleaningLevel(Enum):
    """Levels of text cleaning aggressiveness."""
    MINIMAL = "minimal"  # Only remove null bytes
    STANDARD = "standard"  # Fix punctuation, normalize whitespace
    AGGRESSIVE = "aggressive"  # Remove filler words, normalize speech patterns


@dataclass
class PreprocessingResult:
    """Result of preprocessing operation."""
    original_text: str
    cleaned_text: str
    removed_items: Dict[str, List[str]]
    confidence_score: float
    issues: List[str]
    stats: Dict[str, int]


class TranscriptPreprocessor:
    """
    Preprocesses lecture transcripts for accurate LLM ensemble inference.
    Removes noise, normalizes speech patterns, validates structure.
    """

    # Filler words common in speech transcription
    FILLER_WORDS = {
        r"\b(um|uh|ah|er|erm|hmm|yeah|yep|nope|gonna|wanna|kinda|sorta)\b": "",
        r"\b(like|you know|I mean|basically|literally)\s+": " ",
        r"\s+\(inaudible\)": "",
        r"\s+\[crosstalk\]": "",
    }

    # Common speech-to-text errors
    COMMON_STT_ERRORS = {
        r"(?i)\brecieve\b": "receive",
        r"(?i)\bteh\b": "the",
        r"(?i)\boccured\b": "occurred",
        r"(?i)\bneccessary\b": "necessary",
    }

    # Punctuation normalization
    PUNCTUATION_PATTERNS = {
        r"([.!?])\s+([.!?])": r"\1",  # Remove duplicate sentence ends
        r"\s+([.,:;!?])": r"\1",  # Remove space before punctuation
        r"([.!?])\s{2,}": r"\1 ",  # Normalize spacing after sentence end
    }

    def __init__(self, cleaning_level: CleaningLevel = CleaningLevel.STANDARD):
        """Initialize preprocessor with cleaning level."""
        self.cleaning_level = cleaning_level
        self.removed_items: Dict[str, List[str]] = {
            "filler_words": [],
            "speech_markers": [],
            "corrections": [],
        }

    def preprocess(self, text: str) -> PreprocessingResult:
        """
        Main preprocessing pipeline.
        
        Args:
            text: Raw transcript text from STT service
            
        Returns:
            PreprocessingResult with cleaned text and metadata
        """
        if not text or not isinstance(text, str):
            return PreprocessingResult(
                original_text=text or "",
                cleaned_text="",
                removed_items={},
                confidence_score=0.0,
                issues=["Invalid or empty input text"],
                stats={"original_length": 0, "final_length": 0},
            )

        original_text = text
        cleaned_text = text
        issues = []

        # Step 1: Basic validation and sanitization
        cleaned_text, validation_issues = self._validate_and_sanitize(cleaned_text)
        issues.extend(validation_issues)

        # Step 2: Remove/normalize based on cleaning level
        if self.cleaning_level in (CleaningLevel.STANDARD, CleaningLevel.AGGRESSIVE):
            cleaned_text, removed = self._remove_filler_words(cleaned_text)
            self.removed_items["filler_words"] = removed

        if self.cleaning_level == CleaningLevel.AGGRESSIVE:
            cleaned_text, removed = self._remove_speech_markers(cleaned_text)
            self.removed_items["speech_markers"] = removed

        # Step 3: Fix common STT errors
        cleaned_text, corrections = self._fix_stt_errors(cleaned_text)
        self.removed_items["corrections"] = corrections

        # Step 4: Normalize punctuation
        cleaned_text = self._normalize_punctuation(cleaned_text)

        # Step 5: Normalize whitespace
        cleaned_text = self._normalize_whitespace(cleaned_text)

        # Calculate quality metrics
        stats = {
            "original_length": len(original_text),
            "final_length": len(cleaned_text),
            "sentences_detected": len(re.split(r'[.!?]+', cleaned_text)),
            "words": len(cleaned_text.split()),
        }

        confidence_score = self._calculate_confidence(original_text, cleaned_text, issues)

        return PreprocessingResult(
            original_text=original_text,
            cleaned_text=cleaned_text,
            removed_items=self.removed_items,
            confidence_score=confidence_score,
            issues=issues,
            stats=stats,
        )

    def _validate_and_sanitize(self, text: str) -> Tuple[str, List[str]]:
        """Remove null bytes, invalid chars; validate encoding."""
        issues = []
        
        # Remove null bytes
        text = text.replace('\x00', '')
        
        # Remove control characters except common whitespace
        text = re.sub(r'[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F-\x9F]', '', text)
        
        if not text.strip():
            issues.append("Text is empty after sanitization")
        
        return text, issues

    def _remove_filler_words(self, text: str) -> Tuple[str, List[str]]:
        """Remove filler words like 'um', 'uh', 'like', etc."""
        removed = []
        for pattern, replacement in self.FILLER_WORDS.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                removed.extend(matches)
                text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        return text, list(set(removed))

    def _remove_speech_markers(self, text: str) -> Tuple[str, List[str]]:
        """Remove [crosstalk], (inaudible), etc."""
        removed = []
        markers = [
            r"\[crosstalk\]",
            r"\(inaudible\)",
            r"\[pause\]",
            r"\[silence\]",
            r"\[cough\]",
            r"\[laughter\]",
        ]
        for marker in markers:
            if re.search(marker, text, re.IGNORECASE):
                removed.append(marker)
                text = re.sub(marker, "", text, flags=re.IGNORECASE)
        return text, removed

    def _fix_stt_errors(self, text: str) -> Tuple[str, List[str]]:
        """Fix common speech-to-text mistakes."""
        corrections = []
        for error_pattern, correction in self.COMMON_STT_ERRORS.items():
            matches = re.findall(error_pattern, text)
            if matches:
                corrections.append(f"{error_pattern} -> {correction}")
                text = re.sub(error_pattern, correction, text)
        return text, corrections

    def _normalize_punctuation(self, text: str) -> str:
        """Standardize punctuation patterns."""
        for pattern, replacement in self.PUNCTUATION_PATTERNS.items():
            text = re.sub(pattern, replacement, text)
        return text

    def _normalize_whitespace(self, text: str) -> str:
        """Normalize all whitespace."""
        # Remove leading/trailing whitespace from entire text
        text = text.strip()
        # Normalize internal whitespace
        text = re.sub(r'\s+', ' ', text)
        # Ensure space after sentence-ending punctuation
        text = re.sub(r'([.!?])([A-Z])', r'\1 \2', text)
        return text

    def _calculate_confidence(self, original: str, cleaned: str, issues: List[str]) -> float:
        """
        Estimate confidence in preprocessing quality.
        Higher score = better preprocessing outcome.
        """
        score = 100.0
        
        # Penalty for issues detected
        score -= len(issues) * 5
        
        # Penalty if too much text was removed (possible data loss)
        removal_ratio = 1 - (len(cleaned) / max(len(original), 1))
        if removal_ratio > 0.3:  # More than 30% removed
            score -= (removal_ratio - 0.3) * 20
        
        # Penalty if too little text remains
        if len(cleaned.split()) < 10:
            score -= 20
        
        return max(0.0, min(100.0, score))


class DataValidator:
    """Validates preprocessed data structure before LLM ensemble inference."""

    MIN_TRANSCRIPT_LENGTH = 50  # Minimum words
    MAX_TRANSCRIPT_LENGTH = 50000  # Maximum words
    MIN_CONFIDENCE_SCORE = 0.5  # Minimum confidence threshold

    @staticmethod
    def validate_transcript(transcript_text: str) -> Tuple[bool, List[str]]:
        """
        Validate transcript meets minimum quality requirements.
        
        Returns:
            (is_valid, issues_list)
        """
        issues = []

        if not transcript_text or not isinstance(transcript_text, str):
            issues.append("Transcript must be non-empty string")
            return False, issues

        word_count = len(transcript_text.split())

        if word_count < DataValidator.MIN_TRANSCRIPT_LENGTH:
            issues.append(
                f"Transcript too short: {word_count} words "
                f"(minimum: {DataValidator.MIN_TRANSCRIPT_LENGTH})"
            )

        if word_count > DataValidator.MAX_TRANSCRIPT_LENGTH:
            issues.append(
                f"Transcript too long: {word_count} words "
                f"(maximum: {DataValidator.MAX_TRANSCRIPT_LENGTH})"
            )

        # Check for reasonable sentence structure
        sentences = len(re.split(r'[.!?]+', transcript_text.strip()))
        if sentences < 2:
            issues.append("Transcript appears to lack sentence structure")

        is_valid = len(issues) == 0
        return is_valid, issues

    @staticmethod
    def validate_preprocessing_result(result: PreprocessingResult) -> Tuple[bool, List[str]]:
        """Validate preprocessing result quality."""
        issues = []

        if result.confidence_score < DataValidator.MIN_CONFIDENCE_SCORE * 100:
            issues.append(
                f"Preprocessing confidence too low: {result.confidence_score:.1f}% "
                f"(minimum: {DataValidator.MIN_CONFIDENCE_SCORE * 100}%)"
            )

        if result.stats["words"] < DataValidator.MIN_TRANSCRIPT_LENGTH:
            issues.append("Post-preprocessing text too short for LLM inference")

        if len(result.issues) > 5:
            issues.append(f"Too many preprocessing issues detected: {len(result.issues)}")

        return len(issues) == 0, issues
