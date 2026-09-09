class TranscriptionService:
    async def transcribe(self, audio_path: str, language: str) -> list:
        # Returns: [{"start": 0.0, "end": 2.5, "text": "..."}]
        # NOT IMPLEMENTED - requires Whisper
        raise NotImplementedError("Whisper not configured")
