import json
import os
import requests


METABASE_URL = os.getenv("METABASE_URL", "http://localhost:3001")
METABASE_USER = os.getenv("METABASE_USER", "admin")
METABASE_PASSWORD = os.getenv("METABASE_PASSWORD", "admin")
DASHBOARD_FILE = os.getenv("METABASE_DASHBOARD", "docs/data/metabase_dashboard.json")
METABASE_DB = os.getenv("METABASE_DB", "warehouse")


def get_session_token():
    resp = requests.post(
        f"{METABASE_URL}/api/session",
        json={"username": METABASE_USER, "password": METABASE_PASSWORD},
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()["id"]


def get_database_id(token: str):
    resp = requests.get(
        f"{METABASE_URL}/api/database",
        headers={"X-Metabase-Session": token},
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()
    for db in data.get("data", []):
        if db.get("name") == METABASE_DB:
            return db.get("id")
    if data.get("data"):
        return data["data"][0].get("id")
    raise RuntimeError("Nenhum database encontrado no Metabase.")


def create_card(token: str, db_id: int, title: str, query: str):
    resp = requests.post(
        f"{METABASE_URL}/api/card",
        headers={"X-Metabase-Session": token},
        json={
            "name": title,
            "dataset_query": {
                "type": "native",
                "native": {"query": query},
                "database": db_id,
            },
            "display": "table",
        },
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()["id"]


def import_dashboard(token: str, db_id: int):
    with open(DASHBOARD_FILE, "r", encoding="utf-8") as f:
        dashboard = json.load(f)

    resp = requests.post(
        f"{METABASE_URL}/api/dashboard",
        headers={"X-Metabase-Session": token},
        json={
            "name": dashboard.get("name", "LuisBank Dashboard"),
            "description": dashboard.get("description", ""),
        },
        timeout=10,
    )
    resp.raise_for_status()
    dashboard_id = resp.json()["id"]

    cards = []
    for page in dashboard.get("pages", []):
        for card in page.get("cards", []):
            card_id = create_card(token, db_id, card.get("title", "Card"), card.get("query", "select 1"))
            cards.append({
                "cardId": card_id,
                "sizeX": 8,
                "sizeY": 6,
                "row": 0,
                "col": 0,
            })

    if cards:
        requests.put(
            f"{METABASE_URL}/api/dashboard/{dashboard_id}/cards",
            headers={"X-Metabase-Session": token},
            json={"cards": cards},
            timeout=10,
        ).raise_for_status()

    return dashboard_id


if __name__ == "__main__":
    token = get_session_token()
    db_id = get_database_id(token)
    dashboard_id = import_dashboard(token, db_id)
    print("Dashboard criado:", dashboard_id)
