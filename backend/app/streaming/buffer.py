"""SentenceBuffer — accumulates streaming tokens and splits on sentence boundaries."""

from __future__ import annotations

import re


# Split on sentence-ending punctuation followed by whitespace/newline, or bare newlines.
# Avoid splitting on abbreviations like "Dr." or single-letter abbrevs ("U.S.").
# Consumes the punctuation + trailing whitespace so the sentence includes them.
_SENTENCE_END = re.compile(
    r"(?<![A-Z])\.\s+"    # period (not after single uppercase) + whitespace
    r"|[!?]\s+"           # exclamation/question + whitespace
    r"|\n"                # bare newline
)


class SentenceBuffer:
    """Accumulates tokens and emits complete sentences."""

    def __init__(self) -> None:
        self._buffer: str = ""
        self._full: str = ""

    def add_token(self, token: str) -> list[str]:
        """Add a token, return list of complete sentences (may be empty)."""
        self._full += token
        self._buffer += token

        sentences: list[str] = []
        while True:
            match = _SENTENCE_END.search(self._buffer)
            if not match:
                break
            # Include the delimiter in the sentence
            end = match.end()
            sentences.append(self._buffer[:end])
            self._buffer = self._buffer[end:]

        return sentences

    def flush(self) -> str | None:
        """Return remaining buffer content at stream end."""
        if self._buffer:
            remaining = self._buffer
            self._buffer = ""
            return remaining
        return None

    @property
    def full_response(self) -> str:
        """Complete accumulated response (unredacted, for DB storage)."""
        return self._full
