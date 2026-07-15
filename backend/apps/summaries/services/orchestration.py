"""
Orchestration service that coordinates preprocessing, LLM ensemble, and response aggregation.
This is the main entry point for lecture processing workflow.
"""
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

from common.utils.preprocessing import (
    TranscriptPreprocessor,
    DataValidator,
    CleaningLevel,
    PreprocessingResult,
)
from apps.integrations.llm.ensemble import (
    LLMEnsemble,
    EnsembleConfig,
    EnsembleResult,
    MergeStrategy,
)
from apps.integrations.matlab import is_matlab_enabled, get_matlab_service


logger = logging.getLogger(__name__)


class ProcessingStage(Enum):
    """Stages of lecture processing."""
    AUDIO_PROCESSING = "audio_processing"
    PREPROCESSING = "preprocessing"
    SUMMARIZATION = "summarization"
    QUESTION_GENERATION = "question_generation"
    EVALUATION = "evaluation"
    COMPLETE = "complete"


@dataclass
class ProcessingStageResult:
    """Result from a single processing stage."""
    stage: ProcessingStage
    success: bool
    output: Any
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LectureProcessingResult:
    """Complete lecture processing result."""
    session_id: str
    transcript_original: str
    transcript_cleaned: Optional[str]
    summary: Optional[str]
    questions: Optional[List[Dict[str, str]]]
    processing_stages: List[ProcessingStageResult] = field(default_factory=list)
    overall_success: bool = False
    total_processing_time_ms: float = 0.0
    errors: List[str] = field(default_factory=list)
    audio_enhanced: bool = False


class LectureProcessingOrchestrator:
    """
    Orchestrates the complete lecture processing pipeline.
    Coordinates preprocessing, ensemble inference, and result aggregation.
    """

    def __init__(
        self,
        ensemble: LLMEnsemble,
        preprocessing_level: CleaningLevel = CleaningLevel.STANDARD,
        matlab_service=None,
    ):
        """
        Initialize orchestrator.

        Args:
            ensemble: LLMEnsemble instance for inference
            preprocessing_level: Text cleaning aggressiveness
            matlab_service: Optional MatlabAudioService used for advanced audio
                preprocessing. When None, the singleton from
                ``apps.integrations.matlab`` is consulted at call time, which
                returns None unless ENABLE_MATLAB is True. Passing the service in
                explicitly allows tests/DI to control behavior.
        """
        self.ensemble = ensemble
        self.preprocessor = TranscriptPreprocessor(cleaning_level=preprocessing_level)
        self.validator = DataValidator()
        self.matlab_service = matlab_service
        self.logger = logging.getLogger(__name__)

    def _get_matlab_service(self):
        """Resolve the MATLAB audio service, honoring ENABLE_MATLAB."""
        if self.matlab_service is not None:
            return self.matlab_service
        if is_matlab_enabled():
            return get_matlab_service()
        return None

    async def process_lecture(
        self,
        session_id: str,
        raw_transcript: str,
        target_question_count: int = 5,
        audio: list = None,
        sample_rate: int = 16000,
    ) -> LectureProcessingResult:
        """
        Process complete lecture from raw transcript to final summary + questions.

        Args:
            session_id: Unique session identifier
            raw_transcript: Raw transcript from STT service
            target_question_count: Number of questions to generate
            audio: Optional raw audio samples (list of floats). When provided
                AND MATLAB is enabled, the audio is enhanced via MATLAB before
                transcription. If MATLAB is unavailable, the audio is ignored
                and the existing Python pipeline is used unchanged.
            sample_rate: Sample rate of ``audio`` in Hz.

        Returns:
            LectureProcessingResult with all processing outputs
        """
        import time

        start_time = time.time()
        result = LectureProcessingResult(session_id=session_id, transcript_original=raw_transcript)

        try:
            # OPTIONAL STAGE 0: MATLAB audio preprocessing (advanced, opt-in).
            # Never blocks the existing flow: any failure falls back to Python.
            processed_audio = await self._stage_audio_processing(audio, sample_rate)
            if processed_audio is not None:
                result.processing_stages.append(processed_audio)
                # If MATLAB produced enhanced audio, it can be re-transcribed
                # upstream; here we simply record that enhancement occurred so the
                # downstream STT/transcript stages benefit from cleaner signal.
                result.audio_enhanced = True

            # STAGE 1: Preprocessing
            preprocessing_stage = await self._stage_preprocessing(raw_transcript)
            result.processing_stages.append(preprocessing_stage)

            if not preprocessing_stage.success:
                result.errors.extend(preprocessing_stage.errors)
                result.overall_success = False
                return result

            cleaned_transcript = preprocessing_stage.output.cleaned_text
            result.transcript_cleaned = cleaned_transcript

            # STAGE 2: Summarization
            summarization_stage = await self._stage_summarization(cleaned_transcript)
            result.processing_stages.append(summarization_stage)

            if summarization_stage.success:
                result.summary = summarization_stage.output
            else:
                result.errors.extend(summarization_stage.errors)

            # STAGE 3: Question Generation
            if result.summary:
                question_stage = await self._stage_generate_questions(
                    result.summary, target_question_count
                )
                result.processing_stages.append(question_stage)

                if question_stage.success:
                    result.questions = question_stage.output
                else:
                    result.errors.extend(question_stage.errors)

            # Mark overall success (audio stage failure must NOT block pipeline)
            result.overall_success = (
                preprocessing_stage.success
                and summarization_stage.success
                and (not result.questions or question_stage.success)
            )

        except Exception as e:
            self.logger.exception(f"Lecture processing failed for session {session_id}")
            result.errors.append(f"Unexpected error: {str(e)}")
            result.overall_success = False

        finally:
            result.total_processing_time_ms = (time.time() - start_time) * 1000

        return result

    async def _stage_audio_processing(
        self, audio: list, sample_rate: int
    ) -> Optional[ProcessingStageResult]:
        """Optional Stage 0: enhanced audio via MATLAB.

        Runs only when ``audio`` is supplied and MATLAB is enabled. Any failure
        (MATLAB missing, timeout, error) is logged and the stage is skipped so
        the existing Python-only pipeline continues unchanged.
        """
        if not audio:
            return None

        service = self._get_matlab_service()
        if service is None:
            self.logger.info(
                "MATLAB audio stage skipped (disabled or unavailable); "
                "using existing Python pipeline."
            )
            return None

        try:
            processed = service.process_audio(audio, sample_rate)
            self.logger.info(
                "MATLAB audio processing applied stages: %s",
                processed.metadata.get("stages"),
            )
            return ProcessingStageResult(
                stage=ProcessingStage.AUDIO_PROCESSING,
                success=True,
                output=processed,
                metadata={
                    "engine": "matlab",
                    "sample_rate": sample_rate,
                    "stages": processed.metadata.get("stages", []),
                },
            )
        except Exception as exc:
            self.logger.warning(
                "MATLAB audio processing failed; falling back to Python pipeline: %s",
                exc,
            )
            return ProcessingStageResult(
                stage=ProcessingStage.AUDIO_PROCESSING,
                success=False,
                output=None,
                errors=[f"MATLAB audio processing unavailable: {exc}"],
            )

    async def _stage_preprocessing(self, raw_transcript: str) -> ProcessingStageResult:
        """Stage 1: Preprocess and validate transcript."""
        try:
            # Preprocess transcript
            preprocessing_result = self.preprocessor.preprocess(raw_transcript)

            # Validate cleaned transcript
            is_valid, validation_issues = self.validator.validate_transcript(
                preprocessing_result.cleaned_text
            )

            if not is_valid:
                return ProcessingStageResult(
                    stage=ProcessingStage.PREPROCESSING,
                    success=False,
                    output=None,
                    errors=validation_issues,
                )

            # Validate preprocessing quality
            is_quality_valid, quality_issues = (
                self.validator.validate_preprocessing_result(preprocessing_result)
            )

            warnings = []
            if not is_quality_valid:
                warnings.extend(quality_issues)

            return ProcessingStageResult(
                stage=ProcessingStage.PREPROCESSING,
                success=True,
                output=preprocessing_result,
                warnings=warnings,
                metadata={
                    "original_length": len(raw_transcript),
                    "cleaned_length": len(preprocessing_result.cleaned_text),
                    "confidence_score": preprocessing_result.confidence_score,
                    "removed_items": len(
                        preprocessing_result.removed_items.get("filler_words", [])
                    ),
                },
            )

        except Exception as e:
            self.logger.exception("Preprocessing failed")
            return ProcessingStageResult(
                stage=ProcessingStage.PREPROCESSING,
                success=False,
                output=None,
                errors=[f"Preprocessing error: {str(e)}"],
            )

    async def _stage_summarization(self, cleaned_transcript: str) -> ProcessingStageResult:
        """Stage 2: Generate lecture summary using LLM ensemble."""
        try:
            ensemble_result = await self.ensemble.process_lecture_summary(
                cleaned_transcript=cleaned_transcript
            )

            # Validate ensemble result
            if not ensemble_result.merged_response:
                return ProcessingStageResult(
                    stage=ProcessingStage.SUMMARIZATION,
                    success=False,
                    output=None,
                    errors=["Ensemble produced empty response"],
                )

            return ProcessingStageResult(
                stage=ProcessingStage.SUMMARIZATION,
                success=True,
                output=ensemble_result.merged_response,
                metadata={
                    "agreement_score": ensemble_result.agreement_score,
                    "confidence_score": ensemble_result.confidence_score,
                    "models_used": len(ensemble_result.model_inferences),
                    "processing_time_ms": ensemble_result.processing_time_ms,
                },
            )

        except Exception as e:
            self.logger.exception("Summarization failed")
            return ProcessingStageResult(
                stage=ProcessingStage.SUMMARIZATION,
                success=False,
                output=None,
                errors=[f"Summarization error: {str(e)}"],
            )

    async def _stage_generate_questions(
        self,
        lecture_summary: str,
        target_count: int,
    ) -> ProcessingStageResult:
        """Stage 3: Generate assessment questions using LLM ensemble."""
        try:
            ensemble_result = await self.ensemble.generate_assessment_questions(
                lecture_summary=lecture_summary,
                num_questions=target_count,
            )

            # Parse question response (should be JSON)
            import json

            try:
                questions = json.loads(ensemble_result.merged_response)
                if not isinstance(questions, list):
                    questions = [questions]
            except json.JSONDecodeError:
                # If not valid JSON, wrap response
                questions = [{"question": ensemble_result.merged_response, "model_answer": ""}]

            return ProcessingStageResult(
                stage=ProcessingStage.QUESTION_GENERATION,
                success=True,
                output=questions,
                metadata={
                    "question_count": len(questions),
                    "target_count": target_count,
                    "agreement_score": ensemble_result.agreement_score,
                    "confidence_score": ensemble_result.confidence_score,
                    "processing_time_ms": ensemble_result.processing_time_ms,
                },
            )

        except Exception as e:
            self.logger.exception("Question generation failed")
            return ProcessingStageResult(
                stage=ProcessingStage.QUESTION_GENERATION,
                success=False,
                output=None,
                errors=[f"Question generation error: {str(e)}"],
            )

    async def evaluate_student_responses(
        self,
        questions_with_student_answers: List[Dict[str, str]],
    ) -> ProcessingStageResult:
        """
        Evaluate student responses using LLM ensemble.
        
        Args:
            questions_with_student_answers: List of dicts with:
                - question: The question text
                - model_answer: Expected answer
                - student_answer: Student's verbal response
        """
        try:
            evaluations = []

            for item in questions_with_student_answers:
                ensemble_result = await self.ensemble.evaluate_student_response(
                    question=item["question"],
                    student_answer=item["student_answer"],
                    model_answer=item["model_answer"],
                )

                # Parse evaluation JSON
                import json

                try:
                    evaluation = json.loads(ensemble_result.merged_response)
                except json.JSONDecodeError:
                    evaluation = {"score": 0, "feedback": ensemble_result.merged_response}

                evaluations.append(evaluation)

            return ProcessingStageResult(
                stage=ProcessingStage.EVALUATION,
                success=True,
                output=evaluations,
                metadata={
                    "evaluations_count": len(evaluations),
                    "average_ensemble_confidence": sum(
                        e.get("confidence", 0.5) for e in evaluations
                    )
                    / len(evaluations),
                },
            )

        except Exception as e:
            self.logger.exception("Student evaluation failed")
            return ProcessingStageResult(
                stage=ProcessingStage.EVALUATION,
                success=False,
                output=None,
                errors=[f"Evaluation error: {str(e)}"],
            )


class ResponseAggregator:
    """
    Aggregates multiple LLM responses into final output.
    Handles different response types (summaries, questions, evaluations).
    """

    @staticmethod
    def aggregate_summaries(
        ensemble_results: List[EnsembleResult],
    ) -> Dict[str, Any]:
        """
        Aggregate multiple summary ensemble runs into consolidated summary.
        
        Args:
            ensemble_results: List of EnsembleResult from multiple runs
            
        Returns:
            Aggregated summary dict
        """
        if not ensemble_results:
            return {}

        # Use highest-confidence result as primary
        best_result = max(
            ensemble_results,
            key=lambda x: x.confidence_score,
        )

        # Compute aggregate metrics
        avg_agreement = sum(r.agreement_score for r in ensemble_results) / len(
            ensemble_results
        )
        avg_confidence = sum(r.confidence_score for r in ensemble_results) / len(
            ensemble_results
        )

        return {
            "primary_summary": best_result.merged_response,
            "agreement_score": avg_agreement,
            "confidence_score": avg_confidence,
            "processing_ensembles": len(ensemble_results),
        }

    @staticmethod
    def aggregate_questions(
        questions_list: List[List[Dict[str, str]]],
    ) -> List[Dict[str, Any]]:
        """
        Aggregate question sets from multiple runs.
        Deduplicates and ranks by agreement.
        
        Args:
            questions_list: Multiple lists of question dicts
            
        Returns:
            Aggregated, ranked questions
        """
        if not questions_list:
            return []

        # Flatten and deduplicate by question text similarity
        aggregated = []
        seen_questions = set()

        for question_set in questions_list:
            for q in question_set:
                q_text = q.get("question", "")
                if q_text not in seen_questions:
                    seen_questions.add(q_text)
                    aggregated.append(q)

        return aggregated[:10]  # Limit to 10 questions

    @staticmethod
    def aggregate_evaluations(
        evaluations_list: List[List[Dict[str, Any]]],
    ) -> List[Dict[str, Any]]:
        """
        Aggregate student response evaluations from multiple runs.
        
        Args:
            evaluations_list: Multiple lists of evaluation dicts
            
        Returns:
            Aggregated evaluations with consensus scores
        """
        if not evaluations_list:
            return []

        # Average scores across runs
        aggregated = []
        num_runs = len(evaluations_list)

        for run_idx, evaluation_set in enumerate(evaluations_list):
            for q_idx, evaluation in enumerate(evaluation_set):
                if q_idx >= len(aggregated):
                    aggregated.append([])

                aggregated[q_idx].append(evaluation)

        # Compute consensus for each question
        consensus_evaluations = []
        for evaluations in aggregated:
            if evaluations:
                avg_score = sum(e.get("score", 0) for e in evaluations) / len(evaluations)
                consensus_evaluations.append(
                    {
                        "consensus_score": avg_score,
                        "evaluation_runs": len(evaluations),
                        "feedback": evaluations[0].get("feedback", ""),
                    }
                )

        return consensus_evaluations
