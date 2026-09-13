# core/detectors/ner_detector.py
from natasha import Segmenter, NewsEmbedding, NewsNERTagger, Doc
from typing import List, Dict


class NERDetector:
    def __init__(self):
        self.segmenter = Segmenter()
        self.emb = NewsEmbedding()
        self.ner_tagger = NewsNERTagger(self.emb)

    def find_entities(self, text: str) -> List[Dict]:
        if not text or not text.strip():
            return []

        doc = Doc(text)
        doc.segment(self.segmenter)
        doc.tag_ner(self.ner_tagger)

        results = []
        for span in doc.spans:
            if span.type in {"PER", "ORG"}:
                category = "PERSON" if span.type == "PER" else "ORG"
                results.append({
                    'start': span.start,
                    'end': span.stop,
                    'value': text[span.start:span.stop],
                    'category': category
                })
        return results

    def find_persons(self, text: str) -> List[Dict]:
        return [item for item in self.find_entities(text) if item['category'] == 'PERSON']

    def find_organizations(self, text: str) -> List[Dict]:
        return [item for item in self.find_entities(text) if item['category'] == 'ORG']