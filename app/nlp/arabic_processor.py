"""
Arabic Text Processing Module
============================

Specialized Arabic text processing for phrase extraction and sentiment analysis.
Handles Arabic-specific challenges like morphology, diacritics, and text direction.

Features:
- Arabic text normalization
- Diacritic removal and handling
- Arabic phrase boundary detection
- Morphological analysis support
- Text direction handling
"""

import re
from typing import List, Dict, Set, Tuple, Optional
from collections import Counter

# Arabic Unicode ranges
ARABIC_LETTERS = r"\u0621-\u064A\u0660-\u0669"
ARABIC_DIACRITICS = re.compile("""
        ّ    | # Tashdid
        َ    | # Fatha
        ً    | # Tanwin Fath
        ُ    | # Damma
        ٌ    | # Tanwin Damm
        ِ    | # Kasra
        ٍ    | # Tanwin Kasr
        ْ    | # Sukun
        ـ     # Tatwil/Kashida
    """, re.VERBOSE)

# Arabic punctuation and symbols
ARABIC_PUNCTUATION = re.compile(r'[،؛؟]')
ARABIC_NUMBERS = re.compile(r'[٠-٩]')

# Extended Arabic stopwords
ARABIC_STOPWORDS = {
    # Articles and prepositions
    'ال', 'في', 'من', 'إلى', 'على', 'عن', 'مع', 'بعد', 'قبل', 'عند', 'كل', 'بين', 'حتى', 'لكن', 'ثم',
    
    # Pronouns
    'هذا', 'هذه', 'ذلك', 'تلك', 'التي', 'الذي', 'اللذان', 'اللتان', 'اللذين', 'اللتين',
    'أنا', 'أنت', 'أنتِ', 'هو', 'هي', 'نحن', 'أنتم', 'أنتن', 'هم', 'هن',
    
    # Verbs (common forms)
    'كان', 'يكون', 'كانت', 'تكون', 'كانوا', 'يكونوا', 'كنت', 'كنتِ', 'كنا', 'كنتم', 'كنتن',
    'قال', 'يقول', 'قالت', 'تقول', 'قالوا', 'يقولون', 'قلت', 'قلتِ', 'قلنا', 'قلتم', 'قلتن',
    'ذهب', 'يذهب', 'ذهبت', 'تذهب', 'ذهبوا', 'يذهبون', 'ذهبت', 'ذهبتِ', 'ذهبنا', 'ذهبتم', 'ذهبتن',
    
    # Conjunctions and particles
    'و', 'أو', 'لكن', 'إلا', 'إن', 'أن', 'لأن', 'حيث', 'إذا', 'لما', 'حين', 'بينما',
    'قد', 'لقد', 'سوف', 'س', 'لم', 'لن', 'ما', 'لا', 'نعم', 'هل', 'أم',
    
    # Common adjectives (that don't carry much sentiment)
    'كبير', 'صغير', 'طويل', 'قصير', 'عريض', 'ضيق', 'جديد', 'قديم', 'حار', 'بارد',
    
    # Common nouns (generic)
    'شيء', 'أمر', 'حال', 'وقت', 'مكان', 'شخص', 'ناس', 'أشخاص', 'أمور', 'أشياء',
    
    # Numbers
    'واحد', 'اثنان', 'ثلاثة', 'أربعة', 'خمسة', 'ستة', 'سبعة', 'ثمانية', 'تسعة', 'عشرة',
    'أول', 'ثاني', 'ثالث', 'رابع', 'خامس', 'سادس', 'سابع', 'ثامن', 'تاسع', 'عاشر',
}

# Arabic sentiment words (for fallback analysis)
ARABIC_POSITIVE_WORDS = {
    'جيد', 'ممتاز', 'رائع', 'حلو', 'جميل', 'عظيم', 'مذهل', 'رائع', 'مفيد', 'مفيد',
    'ممتاز', 'مثالي', 'مذهل', 'رائع', 'جميل', 'حلو', 'لطيف', 'رائع', 'مفيد', 'مفيد',
    'سعيد', 'فرح', 'مبتهج', 'مسرور', 'راض', 'مقتنع', 'مبسوط', 'فرحان', 'مسرور', 'راضي',
    'حب', 'أحب', 'أعجب', 'أعجبت', 'أحببت', 'أحب', 'أعجب', 'أعجبت', 'أحببت', 'أحب',
    'شكر', 'شكرا', 'شكرا لك', 'شكرا جزيلا', 'شكرا كثيرا', 'شكرا', 'شكرا لك', 'شكرا جزيلا',
    'أنصح', 'أنصح به', 'أنصح بها', 'أنصح بهذا', 'أنصح بهذه', 'أنصح به', 'أنصح بها',
    'يستحق', 'يستحق المال', 'يستحق الثمن', 'يستحق', 'يستحق المال', 'يستحق الثمن',
}

ARABIC_NEGATIVE_WORDS = {
    'سيء', 'سئ', 'رديء', 'مروع', 'فظيع', 'رهيب', 'مخيب', 'محبط', 'مؤلم', 'مؤلم',
    'مخيب للآمال', 'مخيب', 'محبط', 'مؤلم', 'مؤلم', 'مخيب للآمال', 'مخيب', 'محبط',
    'حزين', 'محبط', 'مكتئب', 'مهموم', 'قلق', 'متوتر', 'مضطرب', 'مضطرب', 'مضطرب',
    'أكره', 'أكرهه', 'أكرهها', 'أكره هذا', 'أكره هذه', 'أكرهه', 'أكرهها', 'أكره هذا',
    'لا يعجبني', 'لا يعجبني', 'لا يعجبني', 'لا يعجبني', 'لا يعجبني', 'لا يعجبني',
    'لا أنصح', 'لا أنصح به', 'لا أنصح بها', 'لا أنصح بهذا', 'لا أنصح بهذه', 'لا أنصح به',
    'لا يستحق', 'لا يستحق المال', 'لا يستحق الثمن', 'لا يستحق', 'لا يستحق المال',
}

class ArabicTextProcessor:
    """
    Specialized Arabic text processor for phrase extraction and sentiment analysis.
    """
    
    def __init__(self, remove_diacritics: bool = True, normalize_numbers: bool = True):
        """
        Initialize Arabic text processor.
        
        Args:
            remove_diacritics: Whether to remove Arabic diacritics
            normalize_numbers: Whether to normalize Arabic numbers to English
        """
        self.remove_diacritics = remove_diacritics
        self.normalize_numbers = normalize_numbers
    
    def clean_arabic_text(self, text: str) -> str:
        """
        Clean Arabic text by removing diacritics, normalizing, and handling special characters.
        
        Args:
            text: Input Arabic text
            
        Returns:
            Cleaned Arabic text
        """
        if not text:
            return ""
        
        # Remove diacritics if requested
        if self.remove_diacritics:
            text = ARABIC_DIACRITICS.sub('', text)
        
        # Normalize Arabic numbers to English if requested
        if self.normalize_numbers:
            text = self._normalize_arabic_numbers(text)
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        # Remove excessive punctuation
        text = re.sub(r'[،]{2,}', '،', text)
        text = re.sub(r'[؛]{2,}', '؛', text)
        text = re.sub(r'[؟]{2,}', '؟', text)
        
        return text.strip()
    
    def _normalize_arabic_numbers(self, text: str) -> str:
        """Convert Arabic numbers to English numbers."""
        arabic_to_english = {
            '٠': '0', '١': '1', '٢': '2', '٣': '3', '٤': '4',
            '٥': '5', '٦': '6', '٧': '7', '٨': '8', '٩': '9'
        }
        
        for arabic, english in arabic_to_english.items():
            text = text.replace(arabic, english)
        
        return text
    
    def tokenize_arabic_text(self, text: str) -> List[str]:
        """
        Tokenize Arabic text into words, handling Arabic-specific patterns.
        
        Args:
            text: Input Arabic text
            
        Returns:
            List of tokens
        """
        text = self.clean_arabic_text(text)
        
        # Use Arabic-aware tokenization
        # This regex matches Arabic letters, numbers, and common punctuation
        arabic_token_pattern = re.compile(fr'[{ARABIC_LETTERS}]+|[A-Za-z0-9]+|[،؛؟]')
        tokens = arabic_token_pattern.findall(text)
        
        # Filter out stopwords and short tokens
        filtered_tokens = []
        for token in tokens:
            token = token.strip()
            if (len(token) > 2 and 
                token not in ARABIC_STOPWORDS and 
                not token.isdigit() and
                not re.match(r'^[،؛؟]+$', token)):
                filtered_tokens.append(token)
        
        return filtered_tokens
    
    def extract_arabic_phrases(self, text: str, max_phrase_length: int = 3) -> List[str]:
        """
        Extract meaningful Arabic phrases from text.
        
        Args:
            text: Input Arabic text
            max_phrase_length: Maximum phrase length in words
            
        Returns:
            List of extracted phrases
        """
        tokens = self.tokenize_arabic_text(text)
        if len(tokens) < 2:
            return []
        
        phrases = []
        
        # Extract n-grams of different lengths
        for n in range(2, min(max_phrase_length + 1, len(tokens) + 1)):
            for i in range(len(tokens) - n + 1):
                phrase_tokens = tokens[i:i+n]
                phrase = ' '.join(phrase_tokens)
                
                # Check if phrase is meaningful
                if self._is_meaningful_arabic_phrase(phrase_tokens):
                    phrases.append(phrase)
        
        return phrases
    
    def _is_meaningful_arabic_phrase(self, phrase_tokens: List[str]) -> bool:
        """
        Check if an Arabic phrase is meaningful.
        
        Args:
            phrase_tokens: List of tokens in the phrase
            
        Returns:
            True if phrase is meaningful, False otherwise
        """
        phrase_text = ' '.join(phrase_tokens)
        
        # Check for repeated words
        if len(set(phrase_tokens)) < len(phrase_tokens):
            return False
        
        # Check for very short words (likely noise)
        if any(len(token) < 2 for token in phrase_tokens):
            return False
        
        # Check for meaningless combinations
        meaningless_combinations = {
            'في في', 'من من', 'على على', 'هذا هذا', 'هذه هذه',
            'كان كان', 'يكون يكون', 'قال قال', 'يقول يقول'
        }
        
        if phrase_text in meaningless_combinations:
            return False
        
        # Check if all words are stopwords
        if all(token in ARABIC_STOPWORDS for token in phrase_tokens):
            return False
        
        return True
    
    def analyze_arabic_sentiment_words(self, text: str) -> Dict[str, int]:
        """
        Analyze sentiment using Arabic word-level analysis.
        
        Args:
            text: Input Arabic text
            
        Returns:
            Dictionary with sentiment word counts
        """
        text_lower = text.lower()
        
        positive_count = sum(1 for word in ARABIC_POSITIVE_WORDS if word in text_lower)
        negative_count = sum(1 for word in ARABIC_NEGATIVE_WORDS if word in text_lower)
        
        return {
            'positive': positive_count,
            'negative': negative_count,
            'neutral': max(0, len(self.tokenize_arabic_text(text)) - positive_count - negative_count)
        }
    
    def get_arabic_phrase_frequency(self, texts: List[str], top_n: int = 50) -> Dict[str, int]:
        """
        Get frequency of Arabic phrases across multiple texts.
        
        Args:
            texts: List of Arabic texts
            top_n: Number of top phrases to return
            
        Returns:
            Dictionary of phrase frequencies
        """
        all_phrases = []
        
        for text in texts:
            phrases = self.extract_arabic_phrases(text)
            all_phrases.extend(phrases)
        
        phrase_freqs = Counter(all_phrases)
        return dict(phrase_freqs.most_common(top_n))
    
    def detect_arabic_language(self, text: str) -> bool:
        """
        Detect if text contains Arabic characters.
        
        Args:
            text: Input text
            
        Returns:
            True if text contains Arabic characters
        """
        arabic_pattern = re.compile(fr'[{ARABIC_LETTERS}]')
        return bool(arabic_pattern.search(text))
    
    def get_arabic_text_statistics(self, text: str) -> Dict[str, int]:
        """
        Get statistics about Arabic text.
        
        Args:
            text: Input Arabic text
            
        Returns:
            Dictionary with text statistics
        """
        tokens = self.tokenize_arabic_text(text)
        phrases = self.extract_arabic_phrases(text)
        
        return {
            'total_characters': len(text),
            'total_tokens': len(tokens),
            'total_phrases': len(phrases),
            'average_token_length': sum(len(token) for token in tokens) / len(tokens) if tokens else 0,
            'average_phrase_length': sum(len(phrase.split()) for phrase in phrases) / len(phrases) if phrases else 0,
            'has_arabic': self.detect_arabic_language(text)
        }


# Convenience functions
def clean_arabic_text(text: str, remove_diacritics: bool = True) -> str:
    """Clean Arabic text (convenience function)."""
    processor = ArabicTextProcessor(remove_diacritics=remove_diacritics)
    return processor.clean_arabic_text(text)


def tokenize_arabic_text(text: str) -> List[str]:
    """Tokenize Arabic text (convenience function)."""
    processor = ArabicTextProcessor()
    return processor.tokenize_arabic_text(text)


def extract_arabic_phrases(text: str, max_phrase_length: int = 3) -> List[str]:
    """Extract Arabic phrases (convenience function)."""
    processor = ArabicTextProcessor()
    return processor.extract_arabic_phrases(text, max_phrase_length)


def get_arabic_phrase_frequency(texts: List[str], top_n: int = 50) -> Dict[str, int]:
    """Get Arabic phrase frequency (convenience function)."""
    processor = ArabicTextProcessor()
    return processor.get_arabic_phrase_frequency(texts, top_n)
