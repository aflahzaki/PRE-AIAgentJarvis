"""
Cognition Module - Chain-of-Thought, Multi-Step Planning, Self-Reflection, Error Learning.

Provides cognitive enhancement capabilities for J.A.R.V.I.S agents:
- Chain-of-thought prompting based on task difficulty
- Multi-step planning for complex tasks
- Self-reflection prompts for quality improvement
- Error learning from past mistakes

Usage:
    from core.cognition import ThinkingEngine

    thinking = ThinkingEngine()
    enhanced_prompt = thinking.enhance_system_prompt(
        base_prompt, task="write a function", difficulty="hard", task_type="code"
    )
"""

from core.cognition.thinking import ThinkingEngine

__all__ = ["ThinkingEngine"]
