# 🚀 NSE Data Downloader GitHub Action

![GitHub stars](https://img.shields.io/github/stars/your-username/your-repo?style=social)
![GitHub forks](https://img.shields.io/github/forks/your-username/your-repo?style=social)
![GitHub issues](https://img.shields.io/github/issues/your-username/your-repo)
![GitHub license](https://img.shields.io/github/license/your-username/your-repo)

A robust and efficient GitHub Action to download historical stock data from the National Stock Exchange (NSE) of India. 📈

## ✨ Features

- **Automated Workflows**: Fetches data automatically on a schedule.
- **Concurrent Downloads**: Utilizes multithreading to download data for multiple symbols simultaneously.
- **Data Storage**: Saves the data in Parquet format for efficient storage and analysis.
- **Error Handling**: Implements retry logic to handle network issues.
- **Customizable**: Easily configure the symbols and the number of days of data to download.

## 📚 Getting Started

To get started, simply fork this repository and set up the GitHub Action in your own repository. The workflow is defined in `.github/workflows/main.yml`.

### Prerequisites

- A GitHub account.
- Basic knowledge of Git and GitHub Actions.

## 🔧 Usage

1.  **Fork the repository**: Click the "Fork" button at the top right of this page.
2.  **Add your symbols**: Modify the `EQUITY_L.csv` file to include the symbols you want to track. The file must contain a "Symbol" column.
3.  **Configure the workflow**: The GitHub Action is configured to run on a schedule. You can customize the schedule in `.github/workflows/main.yml`.
4.  **Run the workflow**: The workflow will run automatically based on the schedule or you can trigger it manually from the "Actions" tab in your repository.
5.  **Access the data**: The downloaded data will be saved as a Parquet file in the root of the repository.

## ⚙️ Configuration

The following settings can be configured in the `nse_downloader_action.py` file:

- `SYMBOLS_FILE`: The name of the CSV file containing the list of symbols.
- `DAYS`: The number of days of historical data to download.
- `MAX_WORKERS`: The number of concurrent threads for downloading data.
- `RETRY_COUNT`: The number of retries for failed downloads.
- `RETRY_BACKOFF`: The backoff factor for retries.
- `MIN_ROWS`: The minimum number of rows a symbol must have to be considered valid.

## CONTRIBUTING 🤝

Contributions are welcome! Please feel free to submit a pull request or open an issue if you have any suggestions or find any bugs.

## LICENSE 📄

This project is licensed under the MIT License - see the LICENSE file for details.

## DISCLAIMER ⚠️

This project is for educational purposes only. The data is provided by Yahoo Finance and may not be accurate. Please do your own research before making any investment decisions.
