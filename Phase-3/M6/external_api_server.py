import os
import requests
from dotenv import load_dotenv
from langchain_core.tools import tool
from mcp.server.fastmcp import FastMCP

load_dotenv()

mcp = FastMCP("external-api-server")


@tool
def get_weather(city: str) -> str:
    """Get current weather by city name using OpenWeatherMap API."""
    api_key = os.getenv("OPENWEATHER_API_KEY")

    if not api_key or api_key == "your_openweather_api_key_here":
        return "Error: OPENWEATHER_API_KEY is not configured in .env."

    url = (
        f"https://api.openweathermap.org/data/2.5/weather"
        f"?q={city}&appid={api_key}&units=metric"
    )

    try:
        response = requests.get(url, timeout=10)

        if response.status_code == 200:
            data = response.json()
            temp = data["main"]["temp"]
            desc = data["weather"][0]["description"]

            return f"Weather in {city}: {temp}°C, {desc}"

        elif response.status_code == 404:
            return f"Error: City '{city}' not found."

        elif response.status_code == 401:
            return "Error: Invalid or activating OPENWEATHER_API_KEY."

        else:
            return (
                f"Error: OpenWeatherMap request failed "
                f"(Status Code: {response.status_code})"
            )

    except Exception as e:
        return f"Error fetching weather for '{city}': {str(e)}"


@tool
def get_crypto_price(coin: str) -> str:
    """Get current cryptocurrency price in USD using CoinGecko public API."""

    url = (
        f"https://api.coingecko.com/api/v3/simple/price"
        f"?ids={coin.lower().strip()}&vs_currencies=usd"
    )

    try:
        headers = {"User-Agent": "MCP-Student-Agent/1.0"}
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 200:
            data = response.json()
            coin_key = coin.lower().strip()

            if coin_key in data:
                price = data[coin_key]["usd"]
                return f"Current price of {coin.capitalize()} is ${price:,} USD"

            return f"Error: Cryptocurrency '{coin}' not found on CoinGecko."

        return (
            f"Error: CoinGecko API request failed "
            f"(Status Code: {response.status_code})"
        )

    except Exception as e:
        return f"Error fetching crypto price for '{coin}': {str(e)}"


@tool
def get_covid_stats() -> str:
    """Get latest global COVID-19 pandemic statistics."""

    url = "https://disease.sh/v3/covid-19/all"

    try:
        response = requests.get(url, timeout=10)

        if response.status_code == 200:
            data = response.json()

            cases = data.get("cases", 0)
            deaths = data.get("deaths", 0)
            recovered = data.get("recovered", 0)

            return (
                f"Global COVID-19 Stats:\n"
                f"- Total Cases: {cases:,}\n"
                f"- Total Deaths: {deaths:,}\n"
                f"- Total Recovered: {recovered:,}"
            )

        return (
            f"Error: Unable to fetch COVID stats "
            f"(Status Code: {response.status_code})"
        )

    except Exception as e:
        return f"Error fetching COVID stats: {str(e)}"


@tool
def get_country_info(country: str) -> str:
    """Get basic information about a country using REST Countries API."""

    url = f"https://restcountries.com/v3.1/name/{country}"

    try:
        response = requests.get(url, timeout=10)

        if response.status_code == 200:
            data = response.json()
            country_data = data[0] if isinstance(data, list) else data

            name = country_data.get("name", {}).get("common", country)
            capital = ", ".join(country_data.get("capital", ["N/A"]))
            population = country_data.get("population", 0)
            region = country_data.get("region", "N/A")

            return (
                f"Country: {name}\n"
                f"- Capital: {capital}\n"
                f"- Population: {population:,}\n"
                f"- Region: {region}"
            )

        return f"Error: Country '{country}' not found."

    except Exception as e:
        return f"Error fetching country info for '{country}': {str(e)}"


@mcp.resource("api://metadata/weather")
def weather_metadata() -> str:
    """Read-only metadata resource for OpenWeatherMap API."""

    return (
        "API Name: OpenWeatherMap API\n"
        "Purpose: Retrieve current weather and temperature by city name.\n"
        "Endpoint: https://api.openweathermap.org/data/2.5/weather\n"
        "Required Input: city (string, e.g., 'Nablus')\n"
        "Returned Information: Temperature in °C and weather description\n"
        "Authentication Requirement: Requires OPENWEATHER_API_KEY in .env\n"
        "Example Query: query_api('weather', 'Nablus')"
    )


@mcp.resource("api://metadata/crypto")
def crypto_metadata() -> str:
    """Read-only metadata resource for CoinGecko API."""

    return (
        "API Name: CoinGecko Public API\n"
        "Purpose: Retrieve current cryptocurrency price in USD.\n"
        "Endpoint: https://api.coingecko.com/api/v3/simple/price\n"
        "Required Input: coin (string, e.g., 'bitcoin')\n"
        "Returned Information: Price in USD\n"
        "Authentication Requirement: None (Public API)\n"
        "Example Query: query_api('crypto', 'bitcoin')"
    )


@mcp.resource("api://metadata/covid")
def covid_metadata() -> str:
    """Read-only metadata resource for COVID-19 Stats API."""

    return (
        "API Name: Disease.sh COVID-19 API\n"
        "Purpose: Retrieve global COVID-19 pandemic statistics.\n"
        "Endpoint: https://disease.sh/v3/covid-19/all\n"
        "Required Input: None (Global Overview)\n"
        "Returned Information: Total cases, total deaths, and total recovered\n"
        "Authentication Requirement: None (Public API)\n"
        "Example Query: query_api('covid', '')"
    )


@mcp.resource("api://metadata/country")
def country_metadata() -> str:
    """Read-only metadata resource for REST Countries API."""

    return (
        "API Name: REST Countries API\n"
        "Purpose: Retrieve basic geographic and demographic info about a country.\n"
        "Endpoint: https://restcountries.com/v3.1/name/{country}\n"
        "Required Input: country (string, e.g., 'Palestine')\n"
        "Returned Information: Capital, population, and region\n"
        "Authentication Requirement: None (Public API)\n"
        "Example Query: query_api('country', 'Palestine')"
    )


@mcp.tool()
def query_api(api: str, value: str = "") -> str:
    """MCP Tool to dynamically query external APIs by dispatching to LangChain Tools."""

    api_clean = api.lower().strip()

    if api_clean == "weather":
        if not value:
            return "Error: City name is required for weather query."

        return get_weather.invoke({"city": value})

    elif api_clean == "crypto":
        if not value:
            return "Error: Cryptocurrency ID is required for crypto query."

        return get_crypto_price.invoke({"coin": value})

    elif api_clean == "covid":
        return get_covid_stats.invoke({})

    elif api_clean == "country":
        if not value:
            return "Error: Country name is required for country query."

        return get_country_info.invoke({"country": value})

    else:
        return (
            f"Error: Unknown API '{api}'. "
            f"Supported APIs: weather, crypto, covid, country."
        )


if __name__ == "__main__":
    mcp.run(transport="stdio")
