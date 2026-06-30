"""
Voice Interface for J.A.R.V.I.S.

Main interactive loop that combines Speech-to-Text and Text-to-Speech
with the core orchestrator. Provides graceful fallback to text-only mode
when voice dependencies are not available.

Features:
    - STT via faster-whisper (optional)
    - TTS via edge-tts (optional)
    - Wake word detection ('jarvis')
    - Enter-key activation or continuous listening mode
    - Text-only fallback when voice deps unavailable
    - Terminal transcript display
"""

import logging
import os
import sys

from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

logger = logging.getLogger(__name__)
console = Console()


class VoiceInterface:
    """J.A.R.V.I.S Voice Interface.

    Provides a voice-controlled interface to the orchestrator with
    graceful degradation when voice dependencies are unavailable.
    """

    def __init__(self) -> None:
        """Initialize the Voice Interface with STT, TTS, and Orchestrator."""
        from interfaces.voice.speech_to_text import SpeechToText
        from interfaces.voice.text_to_speech import TextToSpeech

        self.stt = SpeechToText()
        self.tts = TextToSpeech()
        self.orchestrator = None
        self.wake_word = "jarvis"
        self.continuous_mode = False
        self.recording_duration = 5.0

        # Determine available modes
        self.stt_available = self.stt.is_available()
        self.tts_available = self.tts.is_available()

        # Initialize orchestrator
        try:
            from core.orchestrator import Orchestrator
            self.orchestrator = Orchestrator()
        except Exception as e:
            logger.error("Failed to initialize Orchestrator: %s", str(e))
            console.print(
                "[bold red]Error:[/bold red] Failed to initialize Orchestrator: "
                f"{str(e)}"
            )

    def _print_banner(self) -> None:
        """Display the voice interface welcome banner."""
        stt_status = (
            "[green]Active[/green]" if self.stt_available
            else "[yellow]Disabled[/yellow] (text input)"
        )
        tts_status = (
            "[green]Active[/green]" if self.tts_available
            else "[yellow]Disabled[/yellow] (text output)"
        )

        banner_text = (
            "[bold cyan]J.A.R.V.I.S[/bold cyan] Voice Interface\n"
            "[dim]Just A Rather Very Intelligent System[/dim]\n\n"
            f"STT (Speech-to-Text): {stt_status}\n"
            f"TTS (Text-to-Speech): {tts_status}\n\n"
            "[dim]Commands: [bold]exit[/bold] to quit, "
            "[bold]mode[/bold] to toggle continuous, "
            "[bold]wake[/bold] to toggle wake word[/dim]"
        )

        console.print(Panel(
            banner_text,
            title="[bold white]Voice Mode[/bold white]",
            border_style="cyan",
            padding=(1, 2),
        ))

        if not self.stt_available:
            console.print(
                "[yellow]Note:[/yellow] Voice input unavailable. "
                "Using text input mode.\n"
                "[dim]Install faster-whisper and sounddevice for voice: "
                "pip install faster-whisper sounddevice numpy[/dim]\n"
            )

        if not self.tts_available:
            console.print(
                "[yellow]Note:[/yellow] Voice output unavailable. "
                "Using text display mode.\n"
                "[dim]Install edge-tts for speech: "
                "pip install edge-tts[/dim]\n"
            )

    def _get_voice_input(self) -> str:
        """Get input from voice (STT) or text fallback.

        Returns:
            User input text.
        """
        if self.stt_available and not self.continuous_mode:
            # Enter-key activation mode
            console.print(
                "[dim]Press [bold]Enter[/bold] to start recording "
                f"({self.recording_duration}s), or type your message:[/dim]"
            )
            user_input = console.input("[bold cyan]You>[/bold cyan] ")

            if user_input.strip() == "":
                # Empty input = record voice
                console.print("[cyan]Listening...[/cyan]")
                text = self.stt.listen(duration=self.recording_duration)
                if text:
                    console.print(f"[green]Heard:[/green] {text}")
                    return text
                else:
                    console.print("[yellow]No speech detected. Try again.[/yellow]")
                    return ""
            else:
                return user_input.strip()

        elif self.stt_available and self.continuous_mode:
            # Continuous listening mode
            console.print("[cyan]Listening (continuous)...[/cyan]")
            text = self.stt.listen(duration=self.recording_duration)
            if text:
                console.print(f"[green]Heard:[/green] {text}")
                return text
            return ""

        else:
            # Text-only fallback
            return console.input("[bold cyan]You>[/bold cyan] ").strip()

    def _check_wake_word(self, text: str) -> bool:
        """Check if the wake word is present in the input.

        Args:
            text: Input text to check.

        Returns:
            True if wake word is found or wake word checking is disabled.
        """
        if not self.continuous_mode:
            # Wake word only matters in continuous mode
            return True

        return self.wake_word.lower() in text.lower()

    def _process_input(self, user_input: str) -> None:
        """Process user input through the orchestrator and output response.

        Args:
            user_input: The text to process.
        """
        if self.orchestrator is None:
            console.print(
                "[bold red]Error:[/bold red] Orchestrator not available."
            )
            return

        # Show processing indicator
        with console.status("[cyan]Processing...[/cyan]", spinner="dots"):
            result = self.orchestrator.process(user_input)

        # Display metadata
        meta_text = "[dim][{provider}] {model} | {task_type} ({difficulty})[/dim]".format(
            provider=result["provider"],
            model=result["model"],
            task_type=result["task_type"],
            difficulty=result["difficulty"],
        )
        console.print(meta_text)

        # Display response
        response_text = result["response"]
        if response_text:
            try:
                md = Markdown(response_text)
                console.print(Panel(md, border_style="green", padding=(0, 1)))
            except Exception:
                console.print(Panel(response_text, border_style="green", padding=(0, 1)))

            # Speak the response if TTS available
            if self.tts_available:
                # Strip markdown for cleaner speech
                clean_text = self._strip_markdown(response_text)
                self.tts.speak(clean_text)
        else:
            console.print(
                "[yellow]No response received. "
                "Check provider status.[/yellow]"
            )

    def _strip_markdown(self, text: str) -> str:
        """Strip basic markdown formatting for cleaner TTS output.

        Args:
            text: Markdown-formatted text.

        Returns:
            Plain text suitable for speech.
        """
        import re

        # Remove code blocks
        text = re.sub(r"```[\s\S]*?```", "", text)
        # Remove inline code
        text = re.sub(r"`[^`]+`", "", text)
        # Remove headers
        text = re.sub(r"#{1,6}\s*", "", text)
        # Remove bold/italic markers
        text = re.sub(r"\*{1,3}([^*]+)\*{1,3}", r"\1", text)
        # Remove links, keep text
        text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
        # Remove bullet points
        text = re.sub(r"^\s*[-*+]\s+", "", text, flags=re.MULTILINE)
        # Collapse whitespace
        text = re.sub(r"\n{2,}", ". ", text)
        text = re.sub(r"\s+", " ", text)

        return text.strip()

    def _handle_command(self, command: str) -> bool:
        """Handle special commands.

        Args:
            command: The command string (lowercase).

        Returns:
            True if a command was handled, False otherwise.
        """
        if command in ("exit", "quit", "q"):
            console.print("\n[cyan]J.A.R.V.I.S Voice Interface signing off.[/cyan]\n")
            return True

        if command == "mode":
            self.continuous_mode = not self.continuous_mode
            mode_str = "continuous" if self.continuous_mode else "push-to-talk"
            console.print(f"[green]Switched to {mode_str} mode.[/green]")
            return True

        if command == "wake":
            if self.continuous_mode:
                console.print(
                    f"[green]Wake word is: '{self.wake_word}'. "
                    "Say it to activate in continuous mode.[/green]"
                )
            else:
                console.print(
                    "[yellow]Wake word only applies in continuous mode. "
                    "Type 'mode' to switch.[/yellow]"
                )
            return True

        if command == "status":
            stt_str = "Available" if self.stt_available else "Unavailable"
            tts_str = "Available" if self.tts_available else "Unavailable"
            mode_str = "Continuous" if self.continuous_mode else "Push-to-talk"
            console.print(
                f"[bold]Status:[/bold]\n"
                f"  STT: {stt_str}\n"
                f"  TTS: {tts_str}\n"
                f"  Mode: {mode_str}\n"
                f"  Wake word: {self.wake_word}"
            )
            return True

        if command == "help":
            console.print(
                "[bold]Commands:[/bold]\n"
                "  exit/quit/q - Exit voice interface\n"
                "  mode        - Toggle continuous/push-to-talk\n"
                "  wake        - Show wake word info\n"
                "  status      - Show interface status\n"
                "  help        - Show this message\n\n"
                "[dim]In push-to-talk mode: press Enter to record, "
                "or type your message directly.[/dim]"
            )
            return True

        return False

    def run(self) -> None:
        """Run the voice interface main loop."""
        self._print_banner()

        if self.orchestrator is None:
            console.print(
                "[bold red]Cannot start: Orchestrator initialization failed.[/bold red]"
            )
            return

        while True:
            try:
                console.print()  # Blank line for readability

                # Get input (voice or text)
                user_input = self._get_voice_input()

                if not user_input:
                    continue

                # Check for commands
                command = user_input.lower().strip()
                if self._handle_command(command):
                    if command in ("exit", "quit", "q"):
                        break
                    continue

                # Check wake word in continuous mode
                if self.continuous_mode and not self._check_wake_word(user_input):
                    logger.debug("Wake word not detected, skipping.")
                    continue

                # Remove wake word from input if present
                if self.wake_word.lower() in user_input.lower():
                    import re
                    user_input = re.sub(
                        r"\b" + re.escape(self.wake_word) + r"\b",
                        "",
                        user_input,
                        flags=re.IGNORECASE,
                    ).strip()
                    if not user_input:
                        console.print(
                            "[dim]Wake word detected. What can I help you with?[/dim]"
                        )
                        continue

                # Process through orchestrator
                self._process_input(user_input)

            except KeyboardInterrupt:
                console.print(
                    "\n\n[cyan]Interrupted. J.A.R.V.I.S signing off.[/cyan]\n"
                )
                break

            except EOFError:
                console.print(
                    "\n[cyan]End of input. J.A.R.V.I.S signing off.[/cyan]\n"
                )
                break

            except Exception as e:
                logger.error("Error in voice loop: %s", str(e))
                console.print(f"[bold red]Error:[/bold red] {str(e)}")
                console.print("[dim]Type 'help' for commands.[/dim]")
