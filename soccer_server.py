from fastmcp import FastMCP
from dotenv import load_dotenv
load_dotenv()
import requests
import os

mcp = FastMCP("SoccerStats")

API_KEY = os.getenv("RAPID_API_KEY")
HOST = "free-api-live-football-data.p.rapidapi.com"
BASE_URL = f"https://{HOST}"

HEADERS = {
    "x-rapidapi-key": API_KEY,
    "x-rapidapi-host": HOST
}


def _error(status_code: int) -> str:
    messages = {
        401: "Error 401: Unauthorized — check your RAPID_API_KEY",
        403: "Error 403: Forbidden — your plan may not include this endpoint",
        404: "Error 404: Endpoint not found",
        429: "Error 429: Rate limit exceeded",
    }
    return messages.get(status_code, f"Error {status_code}: Unexpected response")


def _get(endpoint: str, params: dict) -> dict | str:
    try:
        response = requests.get(f"{BASE_URL}/{endpoint}", headers=HEADERS, params=params, timeout=10)
        if response.status_code == 200:
            return response.json()
        return _error(response.status_code)
    except requests.exceptions.Timeout:
        return "Error: Request timed out"
    except requests.exceptions.ConnectionError:
        return "Error: Could not connect to API"



@mcp.tool()
def get_standings(league_id: str = "47") -> str:
    """
    Fetches the current league standings/table.
    Default league_id is 47 (Premier League).
    """
    data = _get("football-get-standing-all", {"leagueid": league_id})
    if isinstance(data, str):
        return data

    standings = data.get("response", {}).get("standing", [])
    if not standings:
        return "No standings data found."

    lines = []
    for entry in standings:
        rank = entry.get("idx", "?")
        name = entry.get("name", "?")
        pts = entry.get("pts", "?")
        played = entry.get("played", "?")
        wins = entry.get("wins", "?")
        draws = entry.get("draws", "?")
        losses = entry.get("losses", "?")
        gd = entry.get("goalConDiff", "?")
        scores = entry.get("scoresStr", "?")
        lines.append(f"{rank}. {name} — {pts} pts | {played} played ({wins}W {draws}D {losses}L) | {scores} GD:{gd}")

    return "\n".join(lines) if lines else "Could not parse standings."



@mcp.tool()
def get_live_scores() -> str:
    """Returns all football matches currently being played live."""
    # Ensure this matches your confirmed endpoint from RapidAPI
    data = _get("football-current-live", {}) 
    
    # 1. Handle string errors from _get helper
    if isinstance(data, str):
        return data

    matches = data.get("response", {}).get("live", [])
    
    if not matches:
        return "No live matches right now."

    lines = []
    for m in matches:
        # Accessing data based on the EXACT keys you pasted
        home = m.get("home", {})
        away = m.get("away", {})
        status = m.get("status", {})
        
        # Pulling the '14'' style time
        live_time_obj = status.get("liveTime", {})
        minute = live_time_obj.get("short", "?")
        
        # Pulling the "0 - 0" score string
        score_str = status.get("scoreStr", "vs")
        
        home_name = home.get("name", "Unknown")
        away_name = away.get("name", "Unknown")
        
        lines.append(f"⚽ {home_name} {score_str} {away_name} ({minute})")

    return "\n".join(lines)


if __name__ == "__main__":
    mcp.run()

