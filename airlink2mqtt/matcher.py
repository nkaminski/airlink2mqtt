import logging
import re
from dataclasses import dataclass
from typing import Optional, List

from aioairlinksms.udp import AirlinkSMSMessage

logger = logging.getLogger(__name__)

class MatchCondition:
    name: str
    regex: re.Pattern

    def __init__(self, name: str, regex: str):
        self.name = name
        self.regex = re.compile(regex)

@dataclass
class MatchResult:
    condition: MatchCondition
    named_groups: dict[str, str]

    def serialize(self) -> dict:
        """Return the name, named groups"""
        return {
            "name": self.condition.name,
            "named_groups": self.named_groups,
            }


class Matcher:
    def __init__(self, conditions: List[MatchCondition]) -> None:
        """
        Initialize the matcher with a dictionary of one or more MatchConditions
        """
        self.conditions = conditions

    def match(self, message: AirlinkSMSMessage) -> Optional[MatchResult]:
        """
        Check if the message matches any of the defined conditions.

        Returns a MatchResult for the first matching condition, or None if no match is found.
        """
        if not message.message:
            # Empty message
            logger.debug("Empty message - no matching keywords")
            return None

        for condition in self.conditions:
            match_obj = condition.regex.search(message.message)
            if match_obj:
                return MatchResult(
                    condition=condition,
                    named_groups=match_obj.groupdict(),
                )

        return None
