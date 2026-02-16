"""
Phrase-to-Sentiment Mapping Dictionaries
========================================

Comprehensive dictionaries mapping phrases to sentiment scores for
enhanced sentiment analysis. Supports both Arabic and English phrases.

Sentiment scores:
- Positive: 1.0 to 0.6
- Neutral: 0.5 to -0.5
- Negative: -0.6 to -1.0
"""

from typing import Dict, Set, Tuple

# English Positive Phrases
ENGLISH_POSITIVE_PHRASES = {
    # Strong positive
    "thank you": 1.0,
    "thanks a lot": 1.0,
    "thank you so much": 1.0,
    "excellent service": 1.0,
    "amazing work": 1.0,
    "outstanding quality": 1.0,
    "perfect solution": 1.0,
    "brilliant idea": 1.0,
    "fantastic job": 1.0,
    "love it": 1.0,
    "absolutely love": 1.0,
    "highly recommend": 1.0,
    "very satisfied": 1.0,
    "completely satisfied": 1.0,
    "extremely happy": 1.0,
    "great experience": 1.0,
    "wonderful experience": 1.0,
    "amazing experience": 1.0,
    "best ever": 1.0,
    "top quality": 1.0,
    "premium quality": 1.0,
    "exceeded expectations": 1.0,
    "beyond expectations": 1.0,
    "could not be better": 1.0,
    "perfect match": 1.0,
    "exactly what i needed": 1.0,
    # Moderate positive
    "very good": 0.8,
    "really good": 0.8,
    "quite good": 0.8,
    "good quality": 0.8,
    "nice work": 0.8,
    "well done": 0.8,
    "happy with": 0.8,
    "pleased with": 0.8,
    "satisfied with": 0.8,
    "recommend this": 0.8,
    "would recommend": 0.8,
    "definitely recommend": 0.8,
    "worth it": 0.8,
    "worth the money": 0.8,
    "good value": 0.8,
    "fast delivery": 0.8,
    "quick response": 0.8,
    "prompt service": 0.8,
    "helpful staff": 0.8,
    "friendly service": 0.8,
    "professional service": 0.8,
    "easy to use": 0.8,
    "user friendly": 0.8,
    "simple to use": 0.8,
    "works well": 0.8,
    "works perfectly": 0.8,
    "works great": 0.8,
    # Mild positive
    "not bad": 0.6,
    "pretty good": 0.6,
    "decent quality": 0.6,
    "acceptable": 0.6,
    "reasonable price": 0.6,
    "fair price": 0.6,
    "okay": 0.6,
    "alright": 0.6,
    "fine": 0.6,
    "meets expectations": 0.6,
    "as expected": 0.6,
    "standard quality": 0.6,
}

# English Negative Phrases
ENGLISH_NEGATIVE_PHRASES = {
    # Strong negative
    "terrible service": -1.0,
    "awful experience": -1.0,
    "worst ever": -1.0,
    "completely disappointed": -1.0,
    "extremely disappointed": -1.0,
    "hate it": -1.0,
    "absolutely hate": -1.0,
    "totally useless": -1.0,
    "waste of money": -1.0,
    "complete waste": -1.0,
    "money down the drain": -1.0,
    "never again": -1.0,
    "will never use": -1.0,
    "avoid at all costs": -1.0,
    "scam": -1.0,
    "fraud": -1.0,
    "rip off": -1.0,
    "unacceptable": -1.0,
    "intolerable": -1.0,
    "unbearable": -1.0,
    "completely broken": -1.0,
    "does not work": -1.0,
    "not working": -1.0,
    "poor quality": -1.0,
    "cheap quality": -1.0,
    "low quality": -1.0,
    "terrible quality": -1.0,
    "awful quality": -1.0,
    "horrible quality": -1.0,
    # Moderate negative
    "not good": -0.8,
    "not great": -0.8,
    "not satisfied": -0.8,
    "disappointed": -0.8,
    "unhappy": -0.8,
    "frustrated": -0.8,
    "slow service": -0.8,
    "late delivery": -0.8,
    "delayed response": -0.8,
    "rude staff": -0.8,
    "unhelpful": -0.8,
    "poor customer service": -0.8,
    "difficult to use": -0.8,
    "confusing": -0.8,
    "complicated": -0.8,
    "overpriced": -0.8,
    "too expensive": -0.8,
    "not worth it": -0.8,
    "below expectations": -0.8,
    "disappointing": -0.8,
    "unsatisfactory": -0.8,
    "has issues": -0.8,
    "has problems": -0.8,
    "not reliable": -0.8,
    # Mild negative
    "could be better": -0.6,
    "room for improvement": -0.6,
    "needs improvement": -0.6,
    "average": -0.6,
    "mediocre": -0.6,
    "ordinary": -0.6,
    "not impressed": -0.6,
    "nothing special": -0.6,
    "run of the mill": -0.6,
    "so so": -0.6,
    "meh": -0.6,
    "whatever": -0.6,
}

# Arabic Positive Phrases
ARABIC_POSITIVE_PHRASES = {
    # Strong positive
    "شكرا لك": 1.0,
    "شكرا جزيلا": 1.0,
    "شكرا كثيرا": 1.0,
    "خدمة ممتازة": 1.0,
    "عمل رائع": 1.0,
    "جودة عالية": 1.0,
    "حل مثالي": 1.0,
    "فكرة رائعة": 1.0,
    "عمل ممتاز": 1.0,
    "أحبها": 1.0,
    "أحبها جدا": 1.0,
    "أنصح بها": 1.0,
    "راض جدا": 1.0,
    "راض تماما": 1.0,
    "سعيد جدا": 1.0,
    "تجربة رائعة": 1.0,
    "تجربة ممتازة": 1.0,
    "تجربة مذهلة": 1.0,
    "الأفضل على الإطلاق": 1.0,
    "جودة عالية": 1.0,
    "جودة ممتازة": 1.0,
    "تجاوز التوقعات": 1.0,
    "أفضل من المتوقع": 1.0,
    "لا يمكن أن يكون أفضل": 1.0,
    "مطابق تماما": 1.0,
    "بالضبط ما أحتاجه": 1.0,
    # Moderate positive
    "جيد جدا": 0.8,
    "جيد حقا": 0.8,
    "جيد إلى حد ما": 0.8,
    "جودة جيدة": 0.8,
    "عمل لطيف": 0.8,
    "عمل جيد": 0.8,
    "راض عن": 0.8,
    "سعيد بـ": 0.8,
    "مقتنع بـ": 0.8,
    "أنصح بهذا": 0.8,
    "سأنصح به": 0.8,
    "أنصح به بالتأكيد": 0.8,
    "يستحق": 0.8,
    "يستحق المال": 0.8,
    "قيمة جيدة": 0.8,
    "توصيل سريع": 0.8,
    "استجابة سريعة": 0.8,
    "خدمة سريعة": 0.8,
    "موظفين مفيدين": 0.8,
    "خدمة ودودة": 0.8,
    "خدمة مهنية": 0.8,
    "سهل الاستخدام": 0.8,
    "ودود للمستخدم": 0.8,
    "بسيط الاستخدام": 0.8,
    "يعمل بشكل جيد": 0.8,
    "يعمل بشكل مثالي": 0.8,
    "يعمل بشكل رائع": 0.8,
    # Mild positive
    "ليس سيئا": 0.6,
    "جيد نوعا ما": 0.6,
    "جودة مقبولة": 0.6,
    "مقبول": 0.6,
    "سعر معقول": 0.6,
    "سعر عادل": 0.6,
    "حسنا": 0.6,
    "لا بأس": 0.6,
    "جيد": 0.6,
    "يلبي التوقعات": 0.6,
    "كما هو متوقع": 0.6,
    "جودة عادية": 0.6,
}

# Arabic Negative Phrases
ARABIC_NEGATIVE_PHRASES = {
    # Strong negative
    "خدمة رهيبة": -1.0,
    "تجربة مروعة": -1.0,
    "الأسوأ على الإطلاق": -1.0,
    "خيبة أمل كاملة": -1.0,
    "خيبة أمل شديدة": -1.0,
    "أكرهها": -1.0,
    "أكرهها تماما": -1.0,
    "عديمة الفائدة تماما": -1.0,
    "إهدار للمال": -1.0,
    "إهدار كامل": -1.0,
    "المال في البالوعة": -1.0,
    "لن أستخدمها مرة أخرى": -1.0,
    "لن أستخدمها أبدا": -1.0,
    "تجنبها بأي ثمن": -1.0,
    "احتيال": -1.0,
    "نصب": -1.0,
    "سرقة": -1.0,
    "غير مقبول": -1.0,
    "لا يطاق": -1.0,
    "لا يحتمل": -1.0,
    "معطل تماما": -1.0,
    "لا يعمل": -1.0,
    "لا يعمل بشكل صحيح": -1.0,
    "جودة رديئة": -1.0,
    "جودة رخيصة": -1.0,
    "جودة منخفضة": -1.0,
    "جودة مروعة": -1.0,
    "جودة رهيبة": -1.0,
    "جودة فظيعة": -1.0,
    # Moderate negative
    "ليس جيدا": -0.8,
    "ليس رائعا": -0.8,
    "غير راض": -0.8,
    "خيبة أمل": -0.8,
    "غير سعيد": -0.8,
    "محبط": -0.8,
    "خدمة بطيئة": -0.8,
    "توصيل متأخر": -0.8,
    "استجابة متأخرة": -0.8,
    "موظفين وقحين": -0.8,
    "غير مفيد": -0.8,
    "خدمة عملاء رديئة": -0.8,
    "صعب الاستخدام": -0.8,
    "مربك": -0.8,
    "معقد": -0.8,
    "مكلف جدا": -0.8,
    "غالي جدا": -0.8,
    "لا يستحق": -0.8,
    "أقل من التوقعات": -0.8,
    "مخيب للآمال": -0.8,
    "غير مرض": -0.8,
    "له مشاكل": -0.8,
    "له عيوب": -0.8,
    "غير موثوق": -0.8,
    # Mild negative
    "يمكن أن يكون أفضل": -0.6,
    "مجال للتحسين": -0.6,
    "يحتاج تحسين": -0.6,
    "عادي": -0.6,
    "متوسط": -0.6,
    "عادي": -0.6,
    "لست منبهرا": -0.6,
    "لا شيء مميز": -0.6,
    "عادي جدا": -0.6,
    "لا بأس": -0.6,
    "مهما": -0.6,
    "أيا كان": -0.6,
}

# Sentiment Modifiers (intensifiers and negators)
SENTIMENT_MODIFIERS = {
    # Intensifiers (make sentiment stronger)
    "very": 1.5,
    "really": 1.5,
    "extremely": 1.8,
    "absolutely": 1.8,
    "totally": 1.8,
    "completely": 1.8,
    "perfectly": 1.8,
    "entirely": 1.8,
    "quite": 1.3,
    "pretty": 1.2,
    "rather": 1.2,
    "fairly": 1.1,
    "جدا": 1.5,
    "حقا": 1.5,
    "تماما": 1.8,
    "مطلقا": 1.8,
    "كليا": 1.8,
    "بالكامل": 1.8,
    "تماما": 1.8,
    "كامل": 1.8,
    "نوعا ما": 1.3,
    "إلى حد ما": 1.2,
    "قليلا": 1.1,
    # Negators (reverse sentiment)
    "not": -1.0,
    "no": -1.0,
    "never": -1.0,
    "nothing": -1.0,
    "nobody": -1.0,
    "nowhere": -1.0,
    "none": -1.0,
    "neither": -1.0,
    "لا": -1.0,
    "لم": -1.0,
    "لن": -1.0,
    "ليس": -1.0,
    "لست": -1.0,
    "لن": -1.0,
    "لا شيء": -1.0,
    "لا أحد": -1.0,
    # Diminishers (make sentiment weaker)
    "slightly": 0.7,
    "somewhat": 0.8,
    "a bit": 0.8,
    "a little": 0.8,
    "kind of": 0.8,
    "sort of": 0.8,
    "more or less": 0.9,
    "قليلا": 0.7,
    "إلى حد ما": 0.8,
    "نوعا ما": 0.8,
    "قليلا": 0.8,
    "نوعا ما": 0.8,
    "إلى حد ما": 0.8,
    "أكثر أو أقل": 0.9,
}

# Context-dependent phrases (phrases that change sentiment based on context)
CONTEXT_PHRASES = {
    "not bad": 0.6,  # Usually positive despite "not"
    "could be worse": 0.4,  # Mildly positive
    "better than nothing": 0.3,  # Slightly positive
    "at least": 0.2,  # Context-dependent
    "ليس سيئا": 0.6,  # Arabic equivalent
    "يمكن أن يكون أسوأ": 0.4,  # Arabic equivalent
    "أفضل من لا شيء": 0.3,  # Arabic equivalent
    "على الأقل": 0.2,  # Arabic equivalent
}


def get_phrase_sentiment_score(phrase: str, language: str = "auto") -> float:
    """
    Get sentiment score for a phrase.

    Args:
        phrase: The phrase to analyze
        language: Language code ('en', 'ar', 'auto')

    Returns:
        Sentiment score between -1.0 (negative) and 1.0 (positive)
    """
    phrase_lower = phrase.lower().strip()

    # Check context-dependent phrases first
    if phrase_lower in CONTEXT_PHRASES:
        return CONTEXT_PHRASES[phrase_lower]

    # Check English phrases
    if language in ["en", "auto"]:
        if phrase_lower in ENGLISH_POSITIVE_PHRASES:
            return ENGLISH_POSITIVE_PHRASES[phrase_lower]
        if phrase_lower in ENGLISH_NEGATIVE_PHRASES:
            return ENGLISH_NEGATIVE_PHRASES[phrase_lower]

    # Check Arabic phrases
    if language in ["ar", "auto"]:
        if phrase_lower in ARABIC_POSITIVE_PHRASES:
            return ARABIC_POSITIVE_PHRASES[phrase_lower]
        if phrase_lower in ARABIC_NEGATIVE_PHRASES:
            return ARABIC_NEGATIVE_PHRASES[phrase_lower]

    return 0.0  # Neutral if not found


def get_all_phrases() -> Dict[str, float]:
    """Get all phrases with their sentiment scores."""
    all_phrases = {}
    all_phrases.update(ENGLISH_POSITIVE_PHRASES)
    all_phrases.update(ENGLISH_NEGATIVE_PHRASES)
    all_phrases.update(ARABIC_POSITIVE_PHRASES)
    all_phrases.update(ARABIC_NEGATIVE_PHRASES)
    all_phrases.update(CONTEXT_PHRASES)
    return all_phrases


def get_positive_phrases() -> Dict[str, float]:
    """Get only positive phrases."""
    positive_phrases = {}
    positive_phrases.update(ENGLISH_POSITIVE_PHRASES)
    positive_phrases.update(ARABIC_POSITIVE_PHRASES)
    # Add context phrases that are positive
    for phrase, score in CONTEXT_PHRASES.items():
        if score > 0:
            positive_phrases[phrase] = score
    return positive_phrases


def get_negative_phrases() -> Dict[str, float]:
    """Get only negative phrases."""
    negative_phrases = {}
    negative_phrases.update(ENGLISH_NEGATIVE_PHRASES)
    negative_phrases.update(ARABIC_NEGATIVE_PHRASES)
    # Add context phrases that are negative
    for phrase, score in CONTEXT_PHRASES.items():
        if score < 0:
            negative_phrases[phrase] = score
    return negative_phrases


def get_sentiment_modifiers() -> Dict[str, float]:
    """Get sentiment modifiers (intensifiers, negators, diminishers)."""
    return SENTIMENT_MODIFIERS.copy()


def is_positive_phrase(phrase: str, language: str = "auto") -> bool:
    """Check if a phrase is positive."""
    score = get_phrase_sentiment_score(phrase, language)
    return score > 0.5


def is_negative_phrase(phrase: str, language: str = "auto") -> bool:
    """Check if a phrase is negative."""
    score = get_phrase_sentiment_score(phrase, language)
    return score < -0.5


def is_neutral_phrase(phrase: str, language: str = "auto") -> bool:
    """Check if a phrase is neutral."""
    score = get_phrase_sentiment_score(phrase, language)
    return -0.5 <= score <= 0.5


def get_phrase_sentiment_label(phrase: str, language: str = "auto") -> str:
    """
    Get sentiment label for a phrase.

    Returns:
        'positive', 'negative', or 'neutral'
    """
    score = get_phrase_sentiment_score(phrase, language)

    if score > 0.5:
        return "positive"
    elif score < -0.5:
        return "negative"
    else:
        return "neutral"
