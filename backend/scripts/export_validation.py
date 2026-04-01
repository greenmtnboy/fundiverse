import time
from typing import Optional

import httpx

# Configuration
BASE_URL = "http://localhost:3042"
AUTH_TOKEN = "your-auth-token-here"  # Set this to your FUNDIVERSE_API_SECRET_KEY

# Headers with authentication
headers = {
    "Authorization": f"Bearer {AUTH_TOKEN}",
    "Content-Type": "application/json"
}


def export_portfolio(
    portfolio_name: str,
    providers: list[str],
    timeout: int = 300
) -> dict:
    """
    Export portfolio data to a DuckDB database.
    
    Args:
        portfolio_name: Name for the portfolio database
        providers: List of provider types (e.g., ["ALPACA", "ROBINHOOD"])
        timeout: Timeout in seconds for the request
    
    Returns:
        Export response with database path and statistics
    """
    payload = {
        "portfolio_name": portfolio_name,
        "providers": providers
    }

    print(f"Exporting portfolio '{portfolio_name}'...")

    with httpx.Client(timeout=timeout) as client:
        response = client.post(
            f"{BASE_URL}/export_portfolio_database",
            json=payload,
            headers=headers
        )
        print(response.text)
        response.raise_for_status()
        return response.json()


def export_portfolio_async(
    portfolio_name: str,
    providers: list[str]
) -> str:
    """
    Export portfolio asynchronously and return task GUID.
    
    Args:
        portfolio_name: Name for the portfolio database
        providers: List of provider types
    
    Returns:
        GUID of the background task
    """
    payload = {
        "portfolioName": portfolio_name,
        "providers": providers
    }
    
    print(f"Starting async export for portfolio '{portfolio_name}'...")
    
    with httpx.Client() as client:
        response = client.post(
            f"{BASE_URL}/async_export_portfolio_database",
            json=payload,
            headers=headers
        )
        print(response.text)
        response.raise_for_status()
        return response.json()["guid"]


def check_background_task(guid: str, max_attempts: int = 60) -> dict:
    """
    Poll a background task until completion.
    
    Args:
        guid: Task GUID to check
        max_attempts: Maximum number of polling attempts
    
    Returns:
        Task result when complete
    """
    print(f"Polling task {guid}...")
    
    with httpx.Client() as client:
        for attempt in range(max_attempts):
            try:
                response = client.get(
                    f"{BASE_URL}/background_tasks/{guid}",
                    headers=headers
                )
                
                if response.status_code == 202:
                    print(f"  Attempt {attempt + 1}: Task still running...")
                    time.sleep(2)
                    continue
                
                response.raise_for_status()
                print("Task completed!")
                return response.json()
                
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 202:
                    continue
                raise
    
    raise TimeoutError(f"Task {guid} did not complete within {max_attempts * 2} seconds")


def get_database_info(portfolio_name: str) -> dict:
    """
    Get information about an existing portfolio database.
    
    Args:
        portfolio_name: Name of the portfolio
    
    Returns:
        Database information including path, stats, and providers
    """
    print(f"\nFetching database info for '{portfolio_name}'...")
    
    with httpx.Client() as client:
        response = client.get(
            f"{BASE_URL}/database_info/{portfolio_name}",
            headers=headers
        )
        print(response.text)
        response.raise_for_status()
        return response.json()


def download_database(portfolio_name: str, output_path: Optional[str] = None) -> str:
    """
    Download the portfolio database file.
    
    Args:
        portfolio_name: Name of the portfolio
        output_path: Optional custom output path (defaults to {portfolio_name}.db)
    
    Returns:
        Path where the database was saved
    """
    if output_path is None:
        output_path = f"{portfolio_name}.db"
    
    print(f"\nDownloading database to '{output_path}'...")
    
    with httpx.Client() as client:
        response = client.get(
            f"{BASE_URL}/database/download/{portfolio_name}",
            headers=headers
        )
        response.raise_for_status()
        
        with open(output_path, "wb") as f:
            f.write(response.content)
    
    print("Database downloaded successfully!")
    return output_path


def delete_database(portfolio_name: str) -> dict:
    """
    Delete a portfolio database.
    
    Args:
        portfolio_name: Name of the portfolio to delete
    
    Returns:
        Deletion confirmation
    """
    print(f"\nDeleting database '{portfolio_name}'...")
    
    with httpx.Client() as client:
        response = client.delete(
            f"{BASE_URL}/database/{portfolio_name}",
            headers=headers
        )
        response.raise_for_status()
        return response.json()


def main(portfolio: str):
    """Example usage of the portfolio export client."""
    
    # Example portfolio configuration
    portfolio_name = portfolio
    #providers = ["alpaca", "robinhood", "moomoo", "webull", "schwab"]  # Adjust based on your logged-in providers

    # Method 1: Synchronous export (blocks until complete)
    print("=" * 60)
    print("METHOD 1: Synchronous Export")
    print("=" * 60)
    
    # export_result = export_portfolio(portfolio_name, providers)
    # print(f"\nExport completed!")
    # print(f"  Database path: {export_result['database_path']}")
    # print(export_result)
    # print(f"  Holdings exported: {export_result['total_holdings']}")
    # print(f"  Dividends exported: {export_result['total_dividends']}")
    
    # Get database information
    db_info = get_database_info(portfolio_name)
    print("\nDatabase Information:")
    print(f"  Total holdings: {db_info['total_holdings']}")
    print(f"  Total dividends: {db_info['total_dividends']}")
    print(f"  Providers: {', '.join(db_info['providers'])}")
    print(f"  File size: {db_info['file_size_mb']:.2f} MB")
    
    # Optional: Download the database
    # download_database(portfolio_name, "./my_portfolio_backup.db")
    
    # Optional: Delete the database
    # delete_result = delete_database(portfolio_name)
    # print(f"\nDeleted: {delete_result['deleted']}")

if __name__ == "__main__":
    main('Core Portfolio')