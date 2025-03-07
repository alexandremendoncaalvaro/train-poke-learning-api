from fastapi.testclient import TestClient
from main import app  # Certifique-se de importar corretamente sua aplicação
import base64

client = TestClient(app)

def test_valid_training():
    response = client.post(
        "/train/",
        json={
            "pokemon": "charmander",
            "epochs": 5,
            "batch_size": 3,
            "learning_rate": 0.5,
            "optimizer": "ofensivo",
            "early_stopping": False
        }
    )
    data = response.json()
    assert response.status_code == 200
    assert "pokemon" in data
    assert "final_pokemon" in data
    assert "total_xp" in data
    assert "battles" in data
    assert "optimizer" in data
    assert "learning_rate" in data

def test_pokemon_not_found():
    response = client.post(
        "/train/",
        json={
            "pokemon": "missingno",
            "epochs": 5,
            "batch_size": 3,
            "learning_rate": 0.5,
            "optimizer": "ofensivo",
            "early_stopping": False
        }
    )
    data = response.json()
    assert response.status_code == 200
    assert "error" in data
    assert data["error"] == "Pokémon não encontrado."

def test_evolution_occurs():
    response = client.post(
        "/train/",
        json={
            "pokemon": "bulbasaur",
            "epochs": 20,
            "batch_size": 5,
            "learning_rate": 1.0,
            "optimizer": "equilibrado",
            "early_stopping": False
        }
    )
    data = response.json()
    assert response.status_code == 200
    assert data["final_pokemon"] != "bulbasaur"  # Deve ter evoluído

def test_no_evolution():
    response = client.post(
        "/train/",
        json={
            "pokemon": "bulbasaur",
            "epochs": 2,
            "batch_size": 2,
            "learning_rate": 0.2,
            "optimizer": "defensivo",
            "early_stopping": False
        }
    )
    data = response.json()
    assert response.status_code == 200
    assert data["final_pokemon"] == "bulbasaur"  # Não evolui com poucas batalhas

def test_early_stopping():
    response = client.post(
        "/train/",
        json={
            "pokemon": "pikachu",
            "epochs": 50,
            "batch_size": 10,
            "learning_rate": 0.9,
            "optimizer": "ofensivo",
            "early_stopping": True
        }
    )
    data = response.json()
    assert response.status_code == 200
    assert "final_pokemon" in data
    assert data["total_xp"] >= 500  # Early stopping deve ocorrer ao atingir o limite

def test_invalid_parameters():
    response = client.post(
        "/train/",
        json={
            "pokemon": "charmander",
            "epochs": 51,
            "batch_size": 11,
            "learning_rate": 0.009,
            "optimizer": "aleatorio",
            "early_stopping": False
        }
    )
    assert response.status_code == 422  # Deve falhar pois ultrapassa limites

def test_pokemon_without_evolution():
    response = client.post(
        "/train/",
        json={
            "pokemon": "ditto",
            "epochs": 10,
            "batch_size": 5,
            "learning_rate": 0.7,
            "optimizer": "equilibrado",
            "early_stopping": False
        }
    )
    data = response.json()
    assert response.status_code == 200
    assert data["final_pokemon"] == "ditto"  # Ditto não evolui

def test_pokemon_image():
    response = client.get("/pokemon/pikachu/image")
    data = response.json()
    assert response.status_code == 200
    assert "pokemon" in data
    assert "image_base64" in data
    assert isinstance(data["image_base64"], str)
    
    # Testa se a string base64 é válida
    try:
        base64.b64decode(data["image_base64"], validate=True)
    except Exception:
        assert False, "Invalid base64 encoding"

def test_pokemon_list_pagination():
    response = client.get("/pokemon?limit=5&offset=10")
    data = response.json()
    assert response.status_code == 200
    assert "pokemons" in data
    assert len(data["pokemons"]) == 5

def test_high_load_training():
    response = client.post(
        "/train/",
        json={
            "pokemon": "charizard",
            "epochs": 50,
            "batch_size": 10,
            "learning_rate": 1.0,
            "optimizer": "ofensivo",
            "early_stopping": False
        }
    )
    data = response.json()
    assert response.status_code == 200
    assert data["total_xp"] > 0  # Garante que a API aguenta alta carga

def test_health_check():
    response = client.get("/health")
    data = response.json()
    assert response.status_code == 200
    assert "status" in data
