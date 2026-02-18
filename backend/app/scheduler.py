"""Recurring task scheduler — DEPRECATED.

Recurring task generation is now event-driven via Dapr pub/sub.
When a task is completed, the /events/task handler in events/handlers.py
checks for recurrence_pattern and creates the next occurrence automatically.

This module is retained as an empty stub for backward compatibility.
The background loop in main.py has been removed.
"""
