import textstat as ts

class ERTD:
    def __init__(self):
        pass

    # Clamp helper function to ensure a value is within 0 to 100 only
    def clamp(self, value, min_value=0, max_value=100):
        return max(min_value, min(max_value, value))
    
    # Calculates the English Readability Transfer Difference 
    # by subtracting the Flesch Reading Ease score of the two texts.
    def calculate_ertd(self, text1, text2):
        
        # Textstat library takes care of the Flesch Reading Ease calculation
        # 206.835 - (1.015 * ASL) - (84.6 * ASW)
        # ASL = average sentence length in the text (number of words / number of sentences)
        # ASW = average syllables per word in the text (number of syllables / number of words)

        # Clamp score to value of 0 to 100 in case of edge cases where Flesch Reading Ease score is out of expected bounds
        readability1 = self.clamp(ts.flesch_reading_ease(text1))
        readability2 = self.clamp(ts.flesch_reading_ease(text2))

        print(f"Dialogue Readability: {readability1:.2f}")
        print(f"Roleplay Readability: {readability2:.2f}")
        
        ertd_score = (100-(abs(readability1 - readability2))) # The lower the difference, the higher the score

        return ertd_score
    
