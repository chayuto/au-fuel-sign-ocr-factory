"""Character vocabulary for CTC-based reader experts.

Index 0 is always the CTC blank token.
"""

from __future__ import annotations

from pathlib import Path

import yaml

_CONFIGS_DIR = Path(__file__).resolve().parents[3] / "configs"


class Vocab:
    """Character vocabulary with CTC blank at index 0."""

    BLANK = "<blank>"

    def __init__(self, charset: str):
        self._charset = charset
        # Index 0 = CTC blank, then each character in order
        self._idx_to_char = [self.BLANK] + list(charset)
        self._char_to_idx = {c: i for i, c in enumerate(self._idx_to_char)}

    @property
    def charset(self) -> str:
        return self._charset

    @property
    def size(self) -> int:
        """Total vocab size including CTC blank."""
        return len(self._idx_to_char)

    @property
    def blank_idx(self) -> int:
        return 0

    def encode(self, text: str) -> list[int]:
        """Encode text to list of character indices (no blank)."""
        return [self._char_to_idx[c] for c in text if c in self._char_to_idx]

    def decode(self, indices: list[int]) -> str:
        """Decode indices to text, skipping blanks."""
        return "".join(
            self._idx_to_char[i] for i in indices if 0 < i < len(self._idx_to_char)
        )

    def ctc_decode(self, indices: list[int]) -> str:
        """Greedy CTC decode: collapse repeats, remove blanks."""
        result = []
        prev = -1
        for idx in indices:
            if idx != prev:
                if idx != self.blank_idx:
                    if 0 < idx < len(self._idx_to_char):
                        result.append(self._idx_to_char[idx])
            prev = idx
        return "".join(result)

    def save(self, path: str | Path) -> None:
        """Save charset to vocab.txt (one char per line)."""
        with open(path, "w") as f:
            for char in self._charset:
                f.write(f"{char}\n")

    @classmethod
    def from_file(cls, path: str | Path) -> Vocab:
        """Load from vocab.txt."""
        with open(path) as f:
            chars = [line.rstrip("\n") for line in f if line.rstrip("\n")]
        return cls("".join(chars))

    @classmethod
    def from_config(cls, expert_name: str) -> Vocab:
        """Load vocab from reader_experts.yaml for a given expert."""
        with open(_CONFIGS_DIR / "reader_experts.yaml") as f:
            config = yaml.safe_load(f)
        charset = config["experts"][expert_name]["charset"]
        return cls(charset)

    def __repr__(self) -> str:
        return f"Vocab(size={self.size}, charset={self._charset!r})"
