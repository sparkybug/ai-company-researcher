import matplotlib.pyplot as plt
from datetime import datetime

def plot_funding_timeline(funding_data: list, company_name: str):
    dates = [datetime.strptime(f["date"], "%Y-%m-%d") for f in funding_data]
    amounts = [f["amount_usd"] for f in funding_data]

    plt.figure(figsize=(10, 5))
    plt.plot(dates, amounts, marker='o')
    plt.title(f"{company_name} Funding Timeline")
    plt.xlabel("Date")
    plt.ylabel("Funding (USD)")
    plt.grid(True)
    plt.savefig(f"{company_name}_funding_timeline.png")
    plt.close()