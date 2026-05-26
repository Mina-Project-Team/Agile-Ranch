import random

class FarmerEngine:
    def __init__(self):
        # US-05: Stan stada (początkowy)
        self.herd = {
            "królik": 0, "owca": 0, "świnia": 0, 
            "krowa": 0, "koń": 0, "mały_pies": 0, "duży_pies": 0
        }
        
        # US-04: Rozkład zwierząt na kostkach
        self.dice1 = ["królik"] * 6 + ["owca"] * 3 + ["świnia"] + ["krowa"] + ["lis"]
        self.dice2 = ["królik"] * 6 + ["owca"] * 2 + ["świnia"] * 2 + ["koń"] + ["wilk"]

    def roll_dice(self):
        # US-01: Rzut dwiema kostkami
        return random.choice(self.dice1), random.choice(self.dice2)

    def process_turn(self, d1, d2):
        # Kolejność: 1. Drapieżniki, 2. Rozmnażanie
        
        # US-11: Atak lisa
        if d1 == "lis" or d2 == "lis":
            if self.herd["mały_pies"] > 0:
                self.herd["mały_pies"] -= 1
            else:
                self.herd["królik"] = 0

        # US-14: Atak wilka
        if d1 == "wilk" or d2 == "wilk":
            if self.herd["duży_pies"] > 0:
                self.herd["duży_pies"] -= 1
            else:
                # Wilk zjada wszystko oprócz konia
                for animal in ["królik", "owca", "świnia", "krowa"]:
                    self.herd[animal] = 0

        # US-02: Rozmnażanie (tylko jeśli kostka nie wyrzuciła drapieżnika)
        herd_before_reproduction = self.herd.copy()
        for die_result in set([d1, d2]):
            if die_result not in ["lis", "wilk"]:
                pairs = (herd_before_reproduction[die_result] + [d1, d2].count(die_result)) // 2
                self.herd[die_result] += pairs

    def exchange(self, give, take):
        # US-06: Cennik wymiany
        rates = {
            ("królik", "owca"): 6,
            ("owca", "świnia"): 2,
            ("świnia", "krowa"): 3,
            ("krowa", "koń"): 2,
            ("owca", "mały_pies"): 1,
            ("krowa", "duży_pies"): 1
        }
        
        cost = rates.get((give, take))
        if cost and self.herd[give] >= cost:
            self.herd[give] -= cost
            self.herd[take] += 1
            return True
        return False