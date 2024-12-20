
class UWU:
    def __init__(self):
        pass

    def calculate_uwu_score(self, nvcs, ertd, jera, almp):

        # Convert JERA metric to a 0-40 scale
        # Convert other metrics to a 0-20 scale
        # Totals to 100
        nvcs_score = nvcs * 20  # Highest NVCS score is 1.0, so 1.0 * 20 = 20
        ertd_score = ertd / 5   # Highest ERTD score is 100, so 100 / 5 = 20
        jera_score = jera / 7.5 # Highest JERA score is 300, so 300 / 7.5 = 40 
        almp_score = almp * 20  # Highest ALMP score is 1.0, so 1.0 * 20 = 20
        
        # Calculate the total benchmark score
        benchmark_score = nvcs_score +  ertd_score + jera_score + almp_score 

        print(f"Normalized NVCS = {nvcs_score:.2f}/20")
        print(f"Normalized ERTD = {ertd_score:.2f}/20")
        print(f"Normalized JERA = {jera_score:.2f}/40")
        print(f"Normalized ALMP = {almp_score:.2f}/20")

        # Ensure the score is within the 0–100 range (in case of rounding errors)
        return max(0, min(100, benchmark_score))