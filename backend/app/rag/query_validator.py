"""
Query Quality Validator
Detects gibberish, meaningless, or low-quality queries
"""
from typing import Dict, Any
import re
from loguru import logger


class QueryValidator:
    """Validates query quality to detect gibberish and meaningless input"""

    def __init__(self):
        # Common words that indicate a real query (can be expanded)
        self.common_words = {
            'what', 'when', 'where', 'who', 'why', 'how', 'is', 'are', 'was', 'were',
            'do', 'does', 'did', 'can', 'could', 'would', 'should', 'will', 'shall',
            'the', 'a', 'an', 'in', 'on', 'at', 'for', 'to', 'of', 'with', 'by',
            'from', 'about', 'tell', 'me', 'explain', 'describe', 'define', 'show',
            'find', 'search', 'list', 'give', 'provide', 'help', 'please', 'thanks',
            'hello', 'hi', 'hey', 'good', 'morning', 'evening', 'afternoon'
        }

    def validate_query(self, query: str) -> Dict[str, Any]:
        """
        Validate query quality and detect gibberish

        Args:
            query: User query to validate

        Returns:
            Dictionary with validation results:
            - is_valid: Whether the query appears to be meaningful
            - quality_score: Quality score from 0.0 (gibberish) to 1.0 (high quality)
            - issues: List of detected issues
            - confidence_penalty: Penalty to apply to confidence score (0.0-1.0)
        """
        if not query or not query.strip():
            return {
                'is_valid': False,
                'quality_score': 0.0,
                'issues': ['Empty query'],
                'confidence_penalty': 1.0  # Maximum penalty
            }

        query = query.strip()
        issues = []
        penalties = []

        # Check 1: Length - too short or suspiciously long repetitive text
        if len(query) < 3:
            issues.append('Query too short')
            penalties.append(0.8)
        elif len(query) > 500:
            issues.append('Query unusually long')
            penalties.append(0.2)

        # Check 2: Character repetition patterns (e.g., "asdasdasdasd")
        repetition_score = self._check_character_repetition(query)
        if repetition_score > 0.5:  # More than 50% repetitive
            issues.append(f'High character repetition ({repetition_score:.1%})')
            penalties.append(0.9)
        elif repetition_score > 0.3:  # 30-50% repetitive
            issues.append(f'Moderate character repetition ({repetition_score:.1%})')
            penalties.append(0.5)

        # Check 3: Consonant-to-vowel ratio (gibberish often has unusual ratios)
        consonant_vowel_ratio = self._check_consonant_vowel_ratio(query)
        if consonant_vowel_ratio > 5.0 or consonant_vowel_ratio < 0.3:
            issues.append(f'Unusual consonant-vowel ratio ({consonant_vowel_ratio:.2f})')
            penalties.append(0.6)

        # Check 4: Presence of spaces/word boundaries
        words = query.split()
        if len(words) == 1 and len(query) > 20:
            issues.append('No word boundaries in long text')
            penalties.append(0.7)

        # Check 5: Recognizable words vs random characters
        recognizable_word_ratio = self._check_recognizable_words(query)
        if recognizable_word_ratio < 0.1:  # Less than 10% recognizable words
            issues.append(f'Very few recognizable words ({recognizable_word_ratio:.1%})')
            penalties.append(0.9)
        elif recognizable_word_ratio < 0.3:  # Less than 30% recognizable
            issues.append(f'Low recognizable word ratio ({recognizable_word_ratio:.1%})')
            penalties.append(0.6)

        # Check 6: Digit-only or special character heavy
        alpha_ratio = sum(c.isalpha() for c in query) / len(query)
        if alpha_ratio < 0.3:  # Less than 30% alphabetic characters
            issues.append(f'Low alphabetic character ratio ({alpha_ratio:.1%})')
            penalties.append(0.5)

        # Check 7: Keyboard mashing patterns (qwerty adjacency)
        keyboard_mash_score = self._check_keyboard_mashing(query)
        if keyboard_mash_score > 0.5:
            issues.append(f'Keyboard mashing detected ({keyboard_mash_score:.1%})')
            penalties.append(0.9)

        # Calculate overall quality score
        if penalties:
            # Use maximum penalty (most severe issue)
            max_penalty = max(penalties)
            quality_score = 1.0 - max_penalty
        else:
            quality_score = 1.0

        # Determine if valid (quality above threshold)
        is_valid = quality_score >= 0.3  # Require at least 30% quality

        # Calculate confidence penalty to apply
        # Gibberish queries should result in very low confidence
        if quality_score < 0.2:
            confidence_penalty = 0.9  # Reduce confidence by 90%
        elif quality_score < 0.4:
            confidence_penalty = 0.7  # Reduce confidence by 70%
        elif quality_score < 0.6:
            confidence_penalty = 0.4  # Reduce confidence by 40%
        else:
            confidence_penalty = 0.0  # No penalty

        result = {
            'is_valid': is_valid,
            'quality_score': quality_score,
            'issues': issues,
            'confidence_penalty': confidence_penalty
        }

        if issues:
            logger.warning(f"Query quality issues detected: {', '.join(issues)} (score: {quality_score:.2f})")

        return result

    def _check_character_repetition(self, text: str) -> float:
        """
        Check for repetitive character patterns (e.g., "asdasdasd")
        Returns ratio of repetitive characters to total length
        """
        if len(text) < 6:
            return 0.0

        # Look for repeated 2-4 character patterns
        max_repetition = 0
        for pattern_len in range(2, 5):
            for i in range(len(text) - pattern_len):
                pattern = text[i:i+pattern_len]
                # Count how many times this pattern repeats consecutively
                consecutive_count = 1
                pos = i + pattern_len
                while pos + pattern_len <= len(text) and text[pos:pos+pattern_len] == pattern:
                    consecutive_count += 1
                    pos += pattern_len

                if consecutive_count > 1:
                    repetition_length = consecutive_count * pattern_len
                    max_repetition = max(max_repetition, repetition_length)

        return max_repetition / len(text)

    def _check_consonant_vowel_ratio(self, text: str) -> float:
        """
        Calculate consonant-to-vowel ratio
        Normal English text typically has ratio between 1.0 and 3.0
        """
        text_lower = text.lower()
        vowels = sum(1 for c in text_lower if c in 'aeiou')
        consonants = sum(1 for c in text_lower if c.isalpha() and c not in 'aeiou')

        if vowels == 0:
            return 10.0 if consonants > 0 else 0.0

        return consonants / vowels

    def _check_recognizable_words(self, text: str) -> float:
        """
        Check ratio of recognizable words to total words
        Uses common words and basic word patterns
        """
        words = text.lower().split()
        if not words:
            return 0.0

        recognizable = 0
        for word in words:
            # Remove punctuation
            clean_word = re.sub(r'[^\w]', '', word)
            if not clean_word:
                continue

            # Check if it's a common word
            if clean_word in self.common_words:
                recognizable += 1
            # Check if it looks like a real word (has vowels, reasonable length, etc.)
            elif self._looks_like_word(clean_word):
                recognizable += 1

        return recognizable / len(words)

    def _looks_like_word(self, word: str) -> bool:
        """
        Check if a string looks like a plausible English word
        """
        if len(word) < 2:
            return False

        # Must have at least one vowel (unless very short)
        if len(word) > 3 and not any(c in 'aeiou' for c in word.lower()):
            return False

        # Check for reasonable consonant clusters
        # No more than 3 consecutive consonants typically
        consonant_cluster = 0
        for c in word.lower():
            if c.isalpha() and c not in 'aeiou':
                consonant_cluster += 1
                if consonant_cluster > 4:
                    return False
            else:
                consonant_cluster = 0

        return True

    def _check_keyboard_mashing(self, text: str) -> float:
        """
        Detect keyboard mashing by checking for QWERTY keyboard adjacency
        """
        # QWERTY keyboard layout rows
        keyboard_rows = [
            'qwertyuiop',
            'asdfghjkl',
            'zxcvbnm'
        ]

        text_lower = text.lower()
        adjacent_count = 0
        total_pairs = 0

        for i in range(len(text_lower) - 1):
            if not text_lower[i].isalpha() or not text_lower[i+1].isalpha():
                continue

            total_pairs += 1

            # Check if consecutive characters are adjacent on keyboard
            for row in keyboard_rows:
                if text_lower[i] in row and text_lower[i+1] in row:
                    pos1 = row.index(text_lower[i])
                    pos2 = row.index(text_lower[i+1])
                    if abs(pos1 - pos2) == 1:
                        adjacent_count += 1
                        break

        if total_pairs == 0:
            return 0.0

        return adjacent_count / total_pairs


# Global instance
query_validator = QueryValidator()
