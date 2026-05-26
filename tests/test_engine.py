import pytest
from src.engine import FarmerEngine

def test_us06_exchange_logic():
    engine = FarmerEngine()
    engine.herd["królik"] = 12
    # Próba wymiany 12 królików na 2 owce (krok po kroku)
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