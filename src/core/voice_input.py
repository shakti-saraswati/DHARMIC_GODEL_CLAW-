"""
Dharmic Agent Voice Input

Optional voice-to-text interface using OpenAI Whisper API.

Features:
- Record audio from microphone
- Convert voice memos to text
- Process through Dharmic Agent
- Save transcripts

Setup:
    export OPENAI_API_KEY=your-openai-key
    pip install openai pyaudio

Usage:
    python3 voice_input.py --record
    python3 voice_input.py --file audio.mp3
"""

import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv

# Load .env
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)

# Try to import Whisper client
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("Warning: openai not installed")
    print("Install with: pip install openai")

# Try to import audio recording
try:
    import pyaudio
    import wave
    PYAUDIO_AVAILABLE = True
except ImportError:
    PYAUDIO_AVAILABLE = False
    print("Warning: pyaudio not installed (needed for recording)")
    print("Install with: pip install pyaudio")

# Import Dharmic Agent
sys.path.insert(0, str(Path(__file__).parent))
from dharmic_agent import DharmicAgent


class VoiceInputConfig:
    """Voice input configuration."""

    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY")

        if not self.openai_api_key:
            raise ValueError(
                "OPENAI_API_KEY must be set.\n"
                "Get your key from: https://platform.openai.com/api-keys\n"
                "Then: export OPENAI_API_KEY=your-key"
            )

        self.client = OpenAI(api_key=self.openai_api_key) if OPENAI_AVAILABLE else None

    def __repr__(self):
        return "VoiceInputConfig(api_key=*****)"


class AudioRecorder:
    """Simple audio recorder using PyAudio."""

    def __init__(self, sample_rate=16000, channels=1, chunk=1024):
        if not PYAUDIO_AVAILABLE:
            raise RuntimeError("pyaudio not installed - cannot record")

        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk = chunk
        self.format = pyaudio.paInt16

        self.audio = pyaudio.PyAudio()

    def record(self, duration_seconds: int, output_file: str):
        """
        Record audio for specified duration.

        Args:
            duration_seconds: How long to record
            output_file: Where to save the recording
        """
        print(f"Recording for {duration_seconds} seconds...")
        print("Speak now!")

        stream = self.audio.open(
            format=self.format,
            channels=self.channels,
            rate=self.sample_rate,
            input=True,
            frames_per_buffer=self.chunk
        )

        frames = []
        for i in range(0, int(self.sample_rate / self.chunk * duration_seconds)):
            data = stream.read(self.chunk)
            frames.append(data)

        print("Recording complete!")

        stream.stop_stream()
        stream.close()

        # Save to file
        with wave.open(output_file, 'wb') as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(self.audio.get_sample_size(self.format))
            wf.setframerate(self.sample_rate)
            wf.writeframes(b''.join(frames))

        print(f"Saved to: {output_file}")

    def __del__(self):
        if hasattr(self, 'audio'):
            self.audio.terminate()


class VoiceInput:
    """
    Voice input interface for Dharmic Agent.

    Uses OpenAI Whisper API for transcription.
    """

    def __init__(
        self,
        agent: DharmicAgent,
        config: VoiceInputConfig = None,
        log_dir: str = None,
    ):
        if not OPENAI_AVAILABLE:
            raise RuntimeError("openai not installed")

        self.agent = agent
        self.config = config or VoiceInputConfig()

        # Log directory
        if log_dir is None:
            log_dir = Path(__file__).parent.parent.parent / "logs" / "voice"
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Transcript directory
        self.transcript_dir = self.log_dir / "transcripts"
        self.transcript_dir.mkdir(exist_ok=True)

    def _log(self, message: str):
        """Log with timestamp."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_line = f"[{timestamp}] {message}"
        print(log_line)

        log_file = self.log_dir / f"voice_{datetime.now().strftime('%Y%m%d')}.log"
        with open(log_file, 'a') as f:
            f.write(log_line + '\n')

    def transcribe(self, audio_file: str, language: str = None) -> Optional[str]:
        """
        Transcribe audio file using Whisper.

        Args:
            audio_file: Path to audio file (mp3, mp4, wav, etc.)
            language: Optional language code (e.g., 'en', 'ja')

        Returns:
            Transcribed text or None on error
        """
        if not self.config.client:
            raise RuntimeError("OpenAI client not initialized")

        audio_path = Path(audio_file)
        if not audio_path.exists():
            self._log(f"Audio file not found: {audio_file}")
            return None

        self._log(f"Transcribing: {audio_file}")

        try:
            with open(audio_file, 'rb') as f:
                transcript = self.config.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=f,
                    language=language,
                    response_format="text"
                )

            text = transcript.strip() if isinstance(transcript, str) else transcript.text.strip()
            self._log(f"Transcription complete: {len(text)} characters")

            # Save transcript
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            transcript_file = self.transcript_dir / f"transcript_{timestamp}.txt"
            with open(transcript_file, 'w') as f:
                f.write(f"Audio: {audio_path.name}\n")
                f.write(f"Timestamp: {datetime.now().isoformat()}\n")
                f.write(f"Language: {language or 'auto'}\n\n")
                f.write(text)

            self._log(f"Transcript saved: {transcript_file}")

            return text

        except Exception as e:
            self._log(f"Transcription error: {e}")
            import traceback
            traceback.print_exc()
            return None

    def process_voice_message(self, audio_file: str, session_id: str = "voice", language: str = None) -> Optional[str]:
        """
        Transcribe audio and process through agent.

        Args:
            audio_file: Path to audio file
            session_id: Session identifier
            language: Optional language code

        Returns:
            Agent's response or None on error
        """
        # Transcribe
        text = self.transcribe(audio_file, language=language)

        if not text:
            return None

        self._log(f"Processing voice message: {text[:100]}...")

        # Process through agent
        try:
            response = self.agent.run(text, session_id=session_id)

            # Record in memory
            self.agent.strange_memory.record_observation(
                content=f"Voice message: {text[:200]}",
                context={"type": "voice", "audio_file": str(audio_file)}
            )

            self._log(f"Response generated: {len(response)} characters")

            return response

        except Exception as e:
            self._log(f"Error processing message: {e}")
            import traceback
            traceback.print_exc()
            return None

    def record_and_process(self, duration_seconds: int = 30, session_id: str = "voice", language: str = None) -> Optional[str]:
        """
        Record audio, transcribe, and process through agent.

        Args:
            duration_seconds: How long to record
            session_id: Session identifier
            language: Optional language code

        Returns:
            Agent's response or None on error
        """
        if not PYAUDIO_AVAILABLE:
            self._log("PyAudio not installed - cannot record")
            return None

        # Record
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        audio_file = self.log_dir / f"recording_{timestamp}.wav"

        recorder = AudioRecorder()
        recorder.record(duration_seconds, str(audio_file))

        # Process
        return self.process_voice_message(str(audio_file), session_id=session_id, language=language)


def main():
    """CLI for voice input."""
    import argparse

    parser = argparse.ArgumentParser(description="Dharmic Agent Voice Input")
    parser.add_argument("--record", action="store_true", help="Record from microphone")
    parser.add_argument("--duration", type=int, default=30, help="Recording duration in seconds (default: 30)")
    parser.add_argument("--file", type=str, help="Transcribe existing audio file")
    parser.add_argument("--language", type=str, help="Language code (e.g., 'en', 'ja')")
    parser.add_argument("--session", type=str, default="voice", help="Session ID")
    parser.add_argument("--transcribe-only", action="store_true", help="Only transcribe, don't process through agent")

    args = parser.parse_args()

    print("=" * 60)
    print("DHARMIC AGENT - Voice Input")
    print("=" * 60)

    # Initialize agent (unless transcribe-only)
    agent = None
    if not args.transcribe_only:
        agent = DharmicAgent()
        print(f"Agent: {agent.name}")
        print(f"Telos: {agent.telos.telos['ultimate']['aim']}")

    # Initialize voice input
    try:
        config = VoiceInputConfig()
        voice = VoiceInput(agent=agent, config=config) if agent else None

    except ValueError as e:
        print(f"\nConfiguration error:\n{e}")
        return
    except RuntimeError as e:
        print(f"\nRuntime error:\n{e}")
        return

    print("=" * 60)

    if args.record:
        # Record and process
        if not PYAUDIO_AVAILABLE:
            print("\nError: PyAudio not installed. Cannot record.")
            print("Install with: pip install pyaudio")
            return

        print(f"\nRecording for {args.duration} seconds...")
        print("Get ready to speak!\n")

        response = voice.record_and_process(
            duration_seconds=args.duration,
            session_id=args.session,
            language=args.language
        )

        if response:
            print("\n--- Agent Response ---")
            print(response)
        else:
            print("\nFailed to process recording")

    elif args.file:
        # Transcribe file
        audio_file = Path(args.file)
        if not audio_file.exists():
            print(f"\nError: File not found: {args.file}")
            return

        if args.transcribe_only:
            # Just transcribe
            from openai import OpenAI
            client = OpenAI(api_key=config.openai_api_key)

            print(f"\nTranscribing: {args.file}")

            with open(args.file, 'rb') as f:
                transcript = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=f,
                    language=args.language,
                    response_format="text"
                )

            text = transcript.strip() if isinstance(transcript, str) else transcript.text.strip()

            print("\n--- Transcript ---")
            print(text)

        else:
            # Transcribe and process
            print(f"\nProcessing: {args.file}")

            response = voice.process_voice_message(
                audio_file=str(args.file),
                session_id=args.session,
                language=args.language
            )

            if response:
                print("\n--- Agent Response ---")
                print(response)
            else:
                print("\nFailed to process audio file")

    else:
        print("\nUsage:")
        print("  --record                Record from microphone and process")
        print("  --duration 60           Recording duration (default: 30s)")
        print("  --file audio.mp3        Process existing audio file")
        print("  --language en           Specify language code")
        print("  --transcribe-only       Only transcribe, don't process")
        print("\nExamples:")
        print("  python3 voice_input.py --record --duration 60")
        print("  python3 voice_input.py --file memo.mp3")
        print("  python3 voice_input.py --file memo.mp3 --transcribe-only")


if __name__ == "__main__":
    main()
