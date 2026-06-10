import datetime
from typing import Optional, Tuple
import re

class DateResolver:
    @staticmethod
    def resolve(question: str) -> Optional[Tuple[str, str, str]]:
        """
        Extracts date references and returns (start_date, end_date, original_phrase).
        Dates are returned as 'YYYY-MM-DD' strings.
        """
        today = datetime.date.today()
        q = question.lower()
        
        # Exact date match: YYYY-MM-DD
        match = re.search(r'(\d{4}-\d{2}-\d{2})', q)
        if match:
            return match.group(1), match.group(1), match.group(1)

        ranges = {
            "today": (today, today),
            "yesterday": (today - datetime.timedelta(days=1), today - datetime.timedelta(days=1)),
            "this week": (today - datetime.timedelta(days=today.weekday()), today + datetime.timedelta(days=6-today.weekday())),
            "last week": (today - datetime.timedelta(days=today.weekday()+7), today - datetime.timedelta(days=today.weekday()+1)),
            "this month": (today.replace(day=1), (today.replace(day=28) + datetime.timedelta(days=4)).replace(day=1) - datetime.timedelta(days=1)),
            "last month": ((today.replace(day=1) - datetime.timedelta(days=1)).replace(day=1), today.replace(day=1) - datetime.timedelta(days=1)),
            "this year": (today.replace(month=1, day=1), today.replace(month=12, day=31)),
            "last year": (today.replace(year=today.year-1, month=1, day=1), today.replace(year=today.year-1, month=12, day=31))
        }

        for phrase, (start, end) in ranges.items():
            if phrase in q:
                return start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d"), phrase

        return None
