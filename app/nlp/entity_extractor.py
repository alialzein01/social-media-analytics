"""
Entity Extraction Module using GLiNER
=====================================

This module provides Named Entity Recognition (NER) capabilities using GLiNER,
which supports multilingual entity extraction including Arabic.

Features:
- Extract entities: people, organizations, locations, dates, etc.
- Multilingual support (Arabic, English)
- Custom entity types
- Entity frequency analysis
- Entity context extraction
"""

import functools
from typing import List, Dict, Tuple, Optional, Set
from collections import Counter

try:
    from gliner import GLiNER
    GLINER_AVAILABLE = True
except ImportError:
    GLINER_AVAILABLE = False


class EntityExtractor:
    """
    Named Entity Recognition using GLiNER.
    
    GLiNER is a generalist model for NER that works well with multiple languages
    including Arabic, without requiring language-specific training.
    """
    
    def __init__(self, model_name: str = "urchade/gliner_multi"):
        """
        Initialize entity extractor.
        
        Args:
            model_name: GLiNER model to use
                - "urchade/gliner_multi" - Multilingual (recommended for Arabic)
                - "urchade/gliner_large-v2.1" - Large English model
                - "urchade/gliner_small-v2.1" - Small English model
        """
        if not GLINER_AVAILABLE:
            raise ImportError("GLiNER is not installed. Install with: pip install gliner")
        
        self.model_name = model_name
        self._model = None
        self._cache = {}
    
    @property
    def model(self):
        """Lazy load the model."""
        if self._model is None:
            self._model = GLiNER.from_pretrained(self.model_name)
        return self._model
    
    def extract_entities(
        self,
        text: str,
        labels: Optional[List[str]] = None,
        threshold: float = 0.5
    ) -> List[Dict]:
        """
        Extract entities from text.
        
        Args:
            text: Text to extract entities from
            labels: List of entity types to extract. If None, uses default types.
            threshold: Confidence threshold (0-1)
            
        Returns:
            List of entity dictionaries with keys:
                - text: Entity text
                - label: Entity type
                - score: Confidence score
                - start: Start position in text
                - end: End position in text
        """
        if not text or not text.strip():
            return []
        
        # Default entity types (work well for both Arabic and English)
        if labels is None:
            labels = [
                "person",           # أشخاص / People
                "organization",     # منظمات / Organizations  
                "location",         # أماكن / Locations
                "date",            # تواريخ / Dates
                "time",            # أوقات / Times
                "money",           # مبالغ مالية / Money amounts
                "product",         # منتجات / Products
                "event",           # أحداث / Events
                "language",        # لغات / Languages
                "nationality"      # جنسيات / Nationalities
            ]
        
        # Extract entities using GLiNER
        entities = self.model.predict_entities(text, labels, threshold=threshold)
        
        # Convert to standard format
        result = []
        for entity in entities:
            result.append({
                'text': entity['text'],
                'label': entity['label'],
                'score': entity['score'],
                'start': entity['start'],
                'end': entity['end']
            })
        
        return result
    
    def extract_entities_from_corpus(
        self,
        texts: List[str],
        labels: Optional[List[str]] = None,
        threshold: float = 0.5
    ) -> Dict[str, List[Dict]]:
        """
        Extract entities from multiple texts.
        
        Args:
            texts: List of texts to process
            labels: Entity types to extract
            threshold: Confidence threshold
            
        Returns:
            Dictionary mapping text to list of entities
        """
        results = {}
        for i, text in enumerate(texts):
            if text and text.strip():
                entities = self.extract_entities(text, labels, threshold)
                results[f"text_{i}"] = entities
        
        return results
    
    def get_entity_frequencies(
        self,
        texts: List[str],
        labels: Optional[List[str]] = None,
        threshold: float = 0.5,
        top_n: int = 20
    ) -> Dict[str, Dict[str, int]]:
        """
        Get frequency counts of entities by type.
        
        Args:
            texts: List of texts to analyze
            labels: Entity types to extract
            threshold: Confidence threshold
            top_n: Number of top entities per type to return
            
        Returns:
            Dictionary mapping entity type to entity frequencies:
            {
                'person': {'John Smith': 5, 'Jane Doe': 3, ...},
                'location': {'New York': 8, 'London': 4, ...},
                ...
            }
        """
        # Count entities by type
        entity_counts = {}
        
        for text in texts:
            if not text or not text.strip():
                continue
                
            entities = self.extract_entities(text, labels, threshold)
            
            for entity in entities:
                label = entity['label']
                text = entity['text']
                
                if label not in entity_counts:
                    entity_counts[label] = Counter()
                
                entity_counts[label][text] += 1
        
        # Get top N for each type
        result = {}
        for label, counter in entity_counts.items():
            result[label] = dict(counter.most_common(top_n))
        
        return result
    
    def extract_entity_contexts(
        self,
        texts: List[str],
        entity_text: str,
        context_window: int = 50
    ) -> List[str]:
        """
        Extract context around specific entity mentions.
        
        Args:
            texts: List of texts to search
            entity_text: Entity to find context for
            context_window: Number of characters before/after entity
            
        Returns:
            List of context strings
        """
        contexts = []
        entity_lower = entity_text.lower()
        
        for text in texts:
            if not text:
                continue
                
            text_lower = text.lower()
            start_pos = 0
            
            while True:
                pos = text_lower.find(entity_lower, start_pos)
                if pos == -1:
                    break
                
                # Extract context
                context_start = max(0, pos - context_window)
                context_end = min(len(text), pos + len(entity_text) + context_window)
                
                context = text[context_start:context_end]
                contexts.append(context)
                
                start_pos = pos + len(entity_text)
        
        return contexts[:10]  # Limit to 10 contexts
    
    def summarize_entities(
        self,
        texts: List[str],
        labels: Optional[List[str]] = None,
        threshold: float = 0.5
    ) -> Dict:
        """
        Get comprehensive entity summary.
        
        Returns:
            Dictionary with entity statistics and frequencies
        """
        # Extract all entities
        all_entities = []
        for text in texts:
            if text and text.strip():
                entities = self.extract_entities(text, labels, threshold)
                all_entities.extend(entities)
        
        # Calculate statistics
        total_entities = len(all_entities)
        
        # Count by type
        entity_types = Counter(e['label'] for e in all_entities)
        
        # Get unique entities per type
        unique_by_type = {}
        for entity in all_entities:
            label = entity['label']
            if label not in unique_by_type:
                unique_by_type[label] = set()
            unique_by_type[label].add(entity['text'])
        
        unique_counts = {label: len(entities) for label, entities in unique_by_type.items()}
        
        # Get top entities per type
        frequencies = self.get_entity_frequencies(texts, labels, threshold, top_n=10)
        
        return {
            'total_entities': total_entities,
            'entity_types': dict(entity_types),
            'unique_entities_by_type': unique_counts,
            'top_entities': frequencies
        }


# Convenience functions for easy integration
@functools.lru_cache(maxsize=1)
def get_entity_extractor(model_name: str = "urchade/gliner_multi") -> EntityExtractor:
    """Get cached entity extractor instance."""
    return EntityExtractor(model_name)


def extract_entities_simple(
    texts: List[str],
    entity_types: Optional[List[str]] = None,
    threshold: float = 0.5,
    top_n: int = 20
) -> Dict[str, Dict[str, int]]:
    """
    Simple function to extract entity frequencies from texts.
    
    Args:
        texts: List of texts to analyze
        entity_types: Types of entities to extract (None = use defaults)
        threshold: Confidence threshold
        top_n: Number of top entities per type
        
    Returns:
        Dictionary mapping entity type to frequencies
    """
    if not GLINER_AVAILABLE:
        return {}
    
    try:
        extractor = get_entity_extractor()
        return extractor.get_entity_frequencies(texts, entity_types, threshold, top_n)
    except Exception:
        return {}


def extract_entities_summary(
    texts: List[str],
    entity_types: Optional[List[str]] = None,
    threshold: float = 0.5
) -> Dict:
    """
    Get entity summary statistics.
    
    Args:
        texts: List of texts to analyze
        entity_types: Types of entities to extract
        threshold: Confidence threshold
        
    Returns:
        Dictionary with entity statistics
    """
    if not GLINER_AVAILABLE:
        return {
            'total_entities': 0,
            'entity_types': {},
            'unique_entities_by_type': {},
            'top_entities': {}
        }
    
    try:
        extractor = get_entity_extractor()
        return extractor.summarize_entities(texts, entity_types, threshold)
    except Exception:
        return {
            'total_entities': 0,
            'entity_types': {},
            'unique_entities_by_type': {},
            'top_entities': {}
        }
