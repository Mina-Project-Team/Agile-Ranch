import random
from copy import deepcopy


class FarmerEngine:
    # US-05, US-16, US-19: default herd state, new game setup, and action history.
    DEFAULT_HERD = {
        "królik": 0,
        "owca": 0,
        "świnia": 0,
        "krowa": 0,
        "koń": 0,
        "mały_pies": 0,
        "duży_pies": 0,
    }

    # US-01, US-04: two independent 12-sided dice with different face distributions.
    DICE1 = ["królik"] * 6 + ["owca"] * 3 + ["świnia"] + ["krowa"] + ["lis"]
    DICE2 = ["królik"] * 6 + ["owca"] * 2 + ["świnia"] * 2 + ["koń"] + ["wilk"]

    # US-06, US-07, US-08, US-10: fixed exchange rates in both directions with validation.
    EXCHANGE_TABLE = {
        ("królik", "owca"): (6, 1),
        ("owca", "świnia"): (2, 1),
        ("świnia", "krowa"): (3, 1),
        ("krowa", "koń"): (2, 1),
        ("owca", "królik"): (1, 6),
        ("świnia", "owca"): (1, 2),
        ("krowa", "świnia"): (1, 3),
        ("koń", "krowa"): (1, 2),
        ("owca", "mały_pies"): (1, 1),
        ("krowa", "duży_pies"): (1, 1),
    }

    # US-18: victory condition requires one of each core animal.
    VICTORY_SET = {
        "królik": 1,
        "owca": 1,
        "świnia": 1,
        "krowa": 1,
        "koń": 1,
    }

    def __init__(self, initial_herd=None):
        self.dice1 = list(self.DICE1)
        self.dice2 = list(self.DICE2)
        self.history = []
        self.last_roll = None
        self.last_turn_summary = None
        self.reset_game(initial_herd)

    def reset_game(self, initial_herd=None):
        # US-16: start a new game with an empty or configured herd.
        herd = deepcopy(self.DEFAULT_HERD)
        if initial_herd:
            for animal, count in initial_herd.items():
                if animal in herd:
                    herd[animal] = max(0, int(count))
        self.herd = herd
        self.history = []
        self.last_roll = None
        self.last_turn_summary = None
        self._record_history("game_started", before=None, after=self.get_herd_state())

    def _record_history(self, event_type, **payload):
        entry = {"event": event_type, **payload}
        self.history.append(entry)
        return entry

    def get_herd_state(self):
        return deepcopy(self.herd)

    def get_recent_history(self, limit=10):
        if limit is None or limit >= len(self.history):
            return deepcopy(self.history)
        return deepcopy(self.history[-limit:])

    def _normalize_species(self, species):
        aliases = {
            "rabbit": "królik",
            "rabbits": "królik",
            "sheep": "owca",
            "pig": "świnia",
            "pigs": "świnia",
            "cow": "krowa",
            "cows": "krowa",
            "horse": "koń",
            "horses": "koń",
            "small_dog": "mały_pies",
            "small_dogs": "mały_pies",
            "big_dog": "duży_pies",
            "big_dogs": "duży_pies",
        }
        return aliases.get(species, species)

    def _snapshot(self):
        return deepcopy(self.herd)

    def _change_summary(self, before, after):
        changes = []
        for animal in self.DEFAULT_HERD:
            delta = after.get(animal, 0) - before.get(animal, 0)
            if delta != 0:
                changes.append({"animal": animal, "delta": delta})
        return changes

    def roll_dice(self):
        # US-01: roll two dice and expose the result to the caller.
        roll = (random.choice(self.dice1), random.choice(self.dice2))
        self.last_roll = roll
        self._record_history("dice_roll", roll=roll)
        return roll

    def resolve_predators(self, d1, d2):
        # US-11, US-12, US-13, US-14, US-15: resolve fox/wolf effects and dog defense.
        messages = []

        if d1 == "lis" or d2 == "lis":
            if self.herd["mały_pies"] > 0:
                self.herd["mały_pies"] -= 1
                messages.append("small_dog_used_against_fox")
            else:
                self.herd["królik"] = 0
                messages.append("fox_ate_rabbits")

        if d1 == "wilk" or d2 == "wilk":
            if self.herd["duży_pies"] > 0:
                self.herd["duży_pies"] -= 1
                messages.append("big_dog_used_against_wolf")
            else:
                for animal in ["królik", "owca", "świnia", "krowa"]:
                    self.herd[animal] = 0
                messages.append("wolf_ate_herd_except_horses")

        if messages:
            self._record_history(
                "predator_attack",
                roll=(d1, d2),
                messages=messages,
                herd=self.get_herd_state(),
            )
        return messages

    def apply_breeding(self, d1, d2):
        # US-02, US-03: apply breeding and return a change summary for the turn.
        before = self._snapshot()
        for die_result in {d1, d2}:
            if die_result in ["lis", "wilk"]:
                continue
            rolled = [d1, d2].count(die_result)
            total = before.get(die_result, 0) + rolled
            pairs = total // 2
            self.herd[die_result] = before.get(die_result, 0) + pairs

        changes = self._change_summary(before, self.herd)
        if changes:
            self._record_history(
                "breeding",
                roll=(d1, d2),
                before=before,
                after=self.get_herd_state(),
                changes=changes,
            )
        return changes

    def process_turn(self, d1, d2):
        # US-03, US-17, US-19: resolve a full turn and keep a visible summary.
        before = self._snapshot()
        predator_messages = self.resolve_predators(d1, d2)
        breeding_changes = self.apply_breeding(d1, d2)
        after = self.get_herd_state()
        summary = {
            "roll": (d1, d2),
            "before": before,
            "after": after,
            "changes": self._change_summary(before, after),
            "messages": predator_messages,
            "breeding_changes": breeding_changes,
            "victory": self.check_victory(),
        }
        self.last_roll = (d1, d2)
        self.last_turn_summary = summary
        self._record_history("turn_resolved", **summary)
        return summary

    def resolve_turn(self, d1, d2):
        return self.process_turn(d1, d2)

    def exchange(self, give, take):
        # US-06, US-07, US-08, US-10: execute atomic trades and reject invalid ones.
        give = self._normalize_species(give)
        take = self._normalize_species(take)
        trade = self.EXCHANGE_TABLE.get((give, take))
        if trade is None:
            return False

        cost, gain = trade
        if self.herd.get(give, 0) < cost:
            self._record_history(
                "trade_failed",
                give=give,
                take=take,
                reason="insufficient_resources",
                herd=self.get_herd_state(),
            )
            return False

        before = self._snapshot()
        self.herd[give] -= cost
        self.herd[take] += gain
        self._record_history(
            "trade_completed",
            give=give,
            take=take,
            cost=cost,
            gain=gain,
            before=before,
            after=self.get_herd_state(),
        )
        return True

    def check_victory(self):
        # US-18: report whether the current herd satisfies the win condition.
        for animal, required in self.VICTORY_SET.items():
            if self.herd.get(animal, 0) < required:
                return False
        return True