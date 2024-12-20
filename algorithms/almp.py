import spacy
from nltk.corpus import wordnet as wn
from openai import OpenAI
from fuzzywuzzy import fuzz
import re
from functools import lru_cache

class ALMP:
    def __init__(self):
        # Load spaCy model
        self.nlp = spacy.load('en_core_web_sm')
        # Initialize caches
        self.synonym_cache = {}
        self.fuzzy_match_cache = {}

    def parse_attributes(self, text, key, reference_attributes=None):
        # Tokenize and parse text
        doc = self.nlp(text)
        attributes = set()

        # Step 1: Extract adjectives as attributes
        for token in doc:
            if token.pos_ == "ADJ":
                attributes.add(token.text.lower())

        # Step 2: Use GPT to infer additional attributes and clean the list
        inferred_attributes = self.infer_attributes_with_gpt(text, attributes, key, reference_attributes)
        attributes.update(inferred_attributes)

        return attributes

    def infer_attributes_with_gpt(self, text, attributes, key, reference_attributes=None):
        # Constructs the prompt for GPT to infer new attributes and remove irrelevant ones.
        prompt = (
            "The following text describes a character or situation:\n\n"
            f"{text}\n\n"
            "Based on the description or scene above, infer additional character traits, roles, or preferences. "
            "Include adjectives and relevant short phrases (like 'shy', 'likes mangoes', 'university student', etc.). "
            "Avoid irrelevant or overly verbose attributes. Only include attributes that are directly relevant based on the text context.\n\n"
            "Here is the current list of attributes:\n"
            f"{', '.join(attributes)}.\n"
            "Analyze each attribute and update this list by inferring new relevant attributes and removing irrelevant ones. Ensure each attribute is contextually appropriate and does not refer to generic or unrelated information (e.g., 'black' when referring to 'black shoes' is not relevant as an independent attribute). Return the final list as a simple, comma-separated list without numbering or explanations."
        )

        # Include reference attributes if they exist
        if reference_attributes:
            prompt += (
                "\n\nYou may also use the following reference attributes to help guide your inference: "
                f"{', '.join(reference_attributes)}."
            )

        client = OpenAI(api_key=key)
        try:
            response = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are an AI assistant helping to infer character attributes."},
                    {"role": "user", "content": prompt}
                ],
                model="gpt-4",
            )
            inferred_text = response.choices[0].message.content.strip()
            cleaned_attributes = self.clean_inferred_attributes(inferred_text)
            return cleaned_attributes
        except Exception as e:
            print(f"Error with ChatGPT API: {e}")
            return set()

    def clean_inferred_attributes(self, inferred_text):
        # Cleans up GPT's response to generate a neat set of attributes
        inferred_text = re.sub(r'\d+\.\s*', '', inferred_text)  # Remove numbering
        inferred_text = re.sub(r'\n+', ',', inferred_text)  # Replace newlines with commas
        attributes = set(attr.strip().lower() for attr in inferred_text.split(',') if len(attr.strip().split()) <= 3)
        return attributes

    @lru_cache(maxsize=None)
    def expand_with_synonyms(self, attribute):
        # Expands a given attribute with its direct synonyms and hypernyms.
        expanded_set = set([attribute])

        words = attribute.split()
        if len(words) == 1:
            # Single-word attribute handling (use wordnet)
            for syn in wn.synsets(attribute):
                synonyms = [lemma.name().replace('_', ' ') for lemma in syn.lemmas()]
                expanded_set.update(synonyms)

                for hypernym in syn.hypernyms():
                    expanded_set.add(hypernym.name().split('.')[0].replace('_', ' '))
        else:
            # Multi-word attribute: Try to expand each part of the phrase
            for word in words:
                for syn in wn.synsets(word):
                    synonyms = [lemma.name().replace('_', ' ') for lemma in syn.lemmas()]
                    expanded_set.update(synonyms)

        return expanded_set

    def calculate_almp(self, attribute_text, roleplay_text, config):
        # Extract attributes from both texts
        attribute_set = sorted(self.parse_attributes(attribute_text, config.gpt_key, reference_attributes=None))
        roleplay_set = sorted(self.parse_attributes(roleplay_text, config.gpt_key, reference_attributes=attribute_set))

        print(f"Attributes Observed in Attribute List: {attribute_set}")
        print(f"Attributes Observed in Roleplay Scene: {roleplay_set}")

        # Precompute synonyms for attributes to avoid redundant computations
        attribute_synonyms = {attr: self.expand_with_synonyms(attr) for attr in attribute_set}
        roleplay_synonyms = {attr: self.expand_with_synonyms(attr) for attr in roleplay_set}

        # Match attributes using optimized comparisons
        match_count = 0
        roleplay_set_set = set(roleplay_set)

        for at_attr in attribute_set:
            # 1. Exact match
            if at_attr in roleplay_set_set:
                match_count += 1
                continue

            # 2. Fuzzy match
            fuzzy_matched = False
            for rp_attr in roleplay_set:
                key = (at_attr, rp_attr)
                if key in self.fuzzy_match_cache:
                    ratio = self.fuzzy_match_cache[key]
                else:
                    ratio = fuzz.ratio(at_attr, rp_attr)
                    self.fuzzy_match_cache[key] = ratio
                if ratio > 85:
                    match_count += 1
                    fuzzy_matched = True
                    break
            if fuzzy_matched:
                continue

            # 3. Synonym match
            at_synonyms = attribute_synonyms[at_attr]
            for rp_attr in roleplay_set:
                rp_synonyms = roleplay_synonyms[rp_attr]
                if at_synonyms.intersection(rp_synonyms):
                    match_count += 1
                    break

        # Calculate the percentage score based on the number of matches
        score = (match_count / len(attribute_set)) if attribute_set else 0
        return score
