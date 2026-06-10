from rapidfuzz import process, fuzz
from .models import DatabaseSchema, MatchResult
from typing import List, Optional, Dict
import re

class SemanticMatcher:
    def __init__(self, schema: DatabaseSchema, threshold: float = 75.0, data_profile: Dict = None):
        self.schema = schema
        self.threshold = threshold
        self.data_profile = data_profile or {}
        self.elements = self._build_element_list()

    def _build_element_list(self):
        elements = []
        for table in self.schema.tables:
            # Add table name and its aliases
            for alias in [table.name] + table.aliases:
                elements.append({"name": alias.lower(), "type": "table", "table": table.name, "column": None, "exact_match": table.name.lower() == alias.lower()})
            for col in table.columns:
                # Add column name and its aliases
                for alias in [col.name] + col.aliases:
                    elements.append({"name": alias.lower(), "type": "column", "table": table.name, "column": col.name, "exact_match": col.name.lower() == alias.lower()})
                
                # Add sampled data values as synonyms for the column
                if table.name in self.data_profile and col.name in self.data_profile[table.name]:
                    for val in self.data_profile[table.name][col.name]:
                        elements.append({"name": val.lower(), "type": "value", "table": table.name, "column": col.name, "exact_match": False, "value": val})
        return elements

    def _get_ngrams(self, tokens: List[str], n: int) -> List[str]:
        return [" ".join(tokens[i:i+n]) for i in range(len(tokens)-n+1)]

    def match(self, question: str) -> List[MatchResult]:
        tokens = re.findall(r'\b\w+\b', question.lower())
        results = []
        
        element_names = [e['name'] for e in self.elements]
        
        # Unigrams, Bigrams, Trigrams
        phrases = []
        for n in range(1, 4):
            phrases.extend(self._get_ngrams(tokens, n))
            
        for phrase in phrases:
            if len(phrase) < 3 and phrase.lower() not in ["id", "no", "ok"]: continue 
            
            matches = process.extract(phrase, element_names, scorer=fuzz.WRatio, limit=5)
            for match_name, score, idx in matches:
                if score >= self.threshold:
                    el = self.elements[idx]
                    
                    # Boost score based on ngram length and exactness
                    phrase_words = len(phrase.split())
                    if phrase == match_name:
                        score += 10 + (phrase_words * 2)
                    
                    if el.get('exact_match'):
                        score += 5
                        
                    if el['type'] == 'table':
                        score += 2 # Slight priority for tables over columns
                        
                    results.append(MatchResult(
                        token=phrase,
                        table=el['table'],
                        column=el['column'],
                        score=score,
                        type=el['type'] if el['type'] != 'value' else 'column' # map value back to column
                    ))

        # Sort and deduplicate
        results.sort(key=lambda x: x.score, reverse=True)
        unique_results = {}
        for r in results:
            key = (r.table, r.column)
            if key not in unique_results or r.score > unique_results[key].score:
                unique_results[key] = r
                
        return list(unique_results.values())
