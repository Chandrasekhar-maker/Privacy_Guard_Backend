import hashlib
import random
from typing import Optional


class JumbleEngine:
    """
    Reversible character-preserving jumble engine.
    SHA-256 seeded Fisher-Yates permutation.
    - Zero characters added or removed
    - Works on any Unicode (English, Hindi, Emojis, Arabic, etc.)
    - Deterministic: same text + same PIN → same output always
    """

    SALT = "PrivacyGuard_v1_Salt_2024"

    @classmethod
    def _derive_seed(cls, password: str) -> int:
        combined = f"{password}:{cls.SALT}".encode("utf-8")
        digest = hashlib.sha256(combined).hexdigest()
        return int(digest[:16], 16)

    @classmethod
    def _generate_permutation(cls, length: int, seed: int) -> list[int]:
        rng = random.Random(seed)
        indices = list(range(length))
        for i in range(length - 1, 0, -1):
            j = rng.randint(0, i)
            indices[i], indices[j] = indices[j], indices[i]
        return indices

    @classmethod
    def jumble(cls, text: str, password: str) -> str:
        if not text:
            return text
        chars = list(text)  # Unicode-aware character list
        n = len(chars)
        seed = cls._derive_seed(password)
        perm = cls._generate_permutation(n, seed)
        scrambled = [chars[perm[i]] for i in range(n)]
        return "".join(scrambled)

    @classmethod
    def unjumble(cls, scrambled: str, password: str) -> str:
        if not scrambled:
            return scrambled
        chars = list(scrambled)
        n = len(chars)
        seed = cls._derive_seed(password)
        perm = cls._generate_permutation(n, seed)
        restored = [""] * n
        for i in range(n):
            restored[perm[i]] = chars[i]
        return "".join(restored)

    @classmethod
    def verify(cls, text: str, password: str) -> bool:
        """Self-test: jumble then unjumble, confirm match."""
        jumbled = cls.jumble(text, password)
        restored = cls.unjumble(jumbled, password)
        return restored == text and len(jumbled) == len(text)
