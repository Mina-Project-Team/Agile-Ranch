import pytest
from src.engine import FarmerEngine

def test_us01_roll_dice_records_two_independent_results(monkeypatch):
    engine = FarmerEngine()
    rolls = iter(["królik", "wilk"])
    monkeypatch.setattr("src.engine.random.choice", lambda seq: next(rolls))

    result = engine.roll_dice()

    assert result == ("królik", "wilk")
    assert engine.last_roll == ("królik", "wilk")
    assert engine.get_recent_history(1)[0]["event"] == "dice_roll"

def test_us02_us03_process_turn_returns_summary_and_grows_herd():
    engine = FarmerEngine()
    engine.herd["królik"] = 3

    summary = engine.process_turn("królik", "królik")

    assert summary["before"]["królik"] == 3
    assert summary["after"]["królik"] == 5
    assert summary["changes"] == [{"animal": "królik", "delta": 2}]
    assert summary["messages"] == []
    assert engine.last_turn_summary == summary

def test_us07_and_us08_reverse_trade_and_blocked_trade():
    engine = FarmerEngine()
    engine.herd["owca"] = 1

    assert engine.exchange("owca", "królik") is True
    assert engine.herd["owca"] == 0
    assert engine.herd["królik"] == 6

    before = engine.get_herd_state()
    assert engine.exchange("królik", "owca") is True
    assert engine.herd["królik"] == 0
    assert engine.herd["owca"] == 1

    blocked = engine.exchange("królik", "koń")
    assert blocked is False
    assert engine.get_herd_state()["królik"] == 0
    assert engine.get_herd_state()["owca"] == 1
    assert engine.get_herd_state()["koń"] == before["koń"]

def test_us15_process_turn_handles_multiple_predators_deterministically():
    engine = FarmerEngine()
    engine.herd["królik"] = 5
    engine.herd["owca"] = 4
    engine.herd["świnia"] = 3
    engine.herd["krowa"] = 2
    engine.herd["koń"] = 1

    summary = engine.process_turn("lis", "wilk")

    assert summary["messages"] == ["fox_ate_rabbits", "wolf_ate_herd_except_horses"]
    assert engine.herd["królik"] == 0
    assert engine.herd["owca"] == 0
    assert engine.herd["świnia"] == 0
    assert engine.herd["krowa"] == 0
    assert engine.herd["koń"] == 1

def test_us16_us18_us19_initial_state_victory_and_history():
    engine = FarmerEngine(
        {
            "królik": 1,
            "owca": 1,
            "świnia": 1,
            "krowa": 1,
            "koń": 1,
        }
    )

    assert engine.check_victory() is True
    history = engine.get_recent_history()
    assert history[0]["event"] == "game_started"

    engine.roll_dice()
    engine.exchange("owca", "królik")
    engine.process_turn("królik", "królik")

    recent_events = [entry["event"] for entry in engine.get_recent_history(5)]
    assert "dice_roll" in recent_events
    assert "trade_completed" in recent_events
    assert "turn_resolved" in recent_events

def test_us06_exchange_logic():
    engine = FarmerEngine()
    engine.herd["królik"] = 12
    # Próba pojedynczej wymiany 12 królików na 1 owcę
    assert engine.exchange("królik", "owca") is True
    assert engine.herd["królik"] == 6
    assert engine.herd["owca"] == 1

def test_us11_fox_attack_no_dog():
    engine = FarmerEngine()
    engine.herd["królik"] = 10
    engine.process_turn("lis", "królik")
    assert engine.herd["królik"] == 0 # Lis zjadł króliki przed rozmnażaniem

def test_us11_fox_attack_with_dog():
    engine = FarmerEngine()
    engine.herd["królik"] = 10
    engine.herd["mały_pies"] = 1
    engine.process_turn("lis", "królik")
    assert engine.herd["królik"] > 0 # Króliki przetrwały
    assert engine.herd["mały_pies"] == 0 # Pies zniknął

def test_us14_wolf_attack_horse_survives():
    engine = FarmerEngine()
    engine.herd["owca"] = 5
    engine.herd["koń"] = 1
    engine.process_turn("królik", "wilk")
    assert engine.herd["owca"] == 0 # Owce zjedzone
    assert engine.herd["koń"] == 1 # Koń przeżył!