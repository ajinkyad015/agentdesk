from __future__ import annotations

from typing import Any
import httpx

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"


async def get_weather(
    location: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
) -> dict[str, Any]:
    """
    Fetch current weather using Open-Meteo API.
    """
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            if location and (latitude is None or longitude is None):
                # Geocode location string
                geo_resp = await client.get(GEOCODING_URL, params={"name": location, "count": 1})
                geo_data = geo_resp.json()
                if not geo_data.get("results"):
                    return {"error": f"Location '{location}' not found"}
                loc_info = geo_data["results"][0]
                latitude = loc_info["latitude"]
                longitude = loc_info["longitude"]
                location_name = loc_info.get("name", location)
            else:
                location_name = f"{latitude}, {longitude}"

            if latitude is None or longitude is None:
                return {"error": "Latitude and longitude or location name required"}

            params = {
                "latitude": latitude,
                "longitude": longitude,
                "current": "temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code",
            }
            resp = await client.get(OPEN_METEO_URL, params=params)
            resp.raise_for_status()
            data = resp.json()

            current = data.get("current", {})
            return {
                "location": location_name,
                "latitude": latitude,
                "longitude": longitude,
                "temperature_c": current.get("temperature_2m"),
                "humidity_percent": current.get("relative_humidity_2m"),
                "wind_speed_kmh": current.get("wind_speed_10m"),
                "weather_code": current.get("weather_code"),
            }
        except httpx.HTTPError as e:
            return {"error": f"Weather API error: {str(e)}"}
        except Exception as e:
            return {"error": f"Failed to fetch weather: {str(e)}"}
