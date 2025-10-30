import os
import time
import pandas as pd
import polars as pl
import yfinance as yf
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Optional, List

# ========== SETTINGS ==========
SYMBOLS_FILE = "EQUITY_L.csv"
DAYS = 365
MAX_WORKERS = 10
RETRY_COUNT = 3
RETRY_BACKOFF = 1.5
MIN_ROWS = 10

# ========== DOWNLOAD LOGIC ==========
def fetch_symbol(symbol: str, start: datetime, end: datetime) -> Optional[pd.DataFrame]:
    """Download data for a single symbol with retry logic"""
    yf_symbol = f"{symbol}.NS" if not symbol.upper().endswith(".NS") else symbol
    
    for attempt in range(1, RETRY_COUNT + 1):
        try:
            # Primary download method
            df = yf.download(
                tickers=yf_symbol,
                start=start.strftime("%Y-%m-%d"),
                end=end.strftime("%Y-%m-%d"),
                interval="1d",
                auto_adjust=False,
                progress=False,
                threads=False,
            )
            
            # Fallback to Ticker.history if needed
            if df.empty or isinstance(df.columns, pd.MultiIndex):
                ticker = yf.Ticker(yf_symbol)
                df = ticker.history(
                    start=start.strftime("%Y-%m-%d"),
                    end=end.strftime("%Y-%m-%d"),
                    interval="1d"
                )
            
            if df.empty:
                raise ValueError("No data returned")
            
            # Clean and format data
            df = df.reset_index()
            
            # Standardize date column
            if "Date" in df.columns:
                df["Date"] = pd.to_datetime(df["Date"]).dt.strftime("%Y-%m-%d")
            elif "Datetime" in df.columns:
                df["Date"] = pd.to_datetime(df["Datetime"]).dt.strftime("%Y-%m-%d")
                df = df.drop(columns=["Datetime"])
            
            # Add symbol column
            df["Symbol"] = symbol
            
            # Validate
            if len(df) < MIN_ROWS:
                raise ValueError(f"Only {len(df)} rows (minimum {MIN_ROWS} required)")
            
            print(f"✅ {symbol}: Downloaded {len(df)} rows")
            return df
            
        except Exception as e:
            if attempt == RETRY_COUNT:
                print(f"❌ {symbol}: All {RETRY_COUNT} attempts failed - {str(e)[:100]}")
            else:
                time.sleep(RETRY_BACKOFF * attempt)
    
    return None

def download_all_symbols(symbols: List[str], start: datetime, end: datetime) -> List[pd.DataFrame]:
    """Download all symbols concurrently"""
    print(f"\n📥 Downloading data for {len(symbols)} symbols...")
    
    dataframes = []
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(fetch_symbol, sym, start, end): sym for sym in symbols}
        
        completed = 0
        for future in as_completed(futures):
            result = future.result()
            completed += 1
            
            print(f"Progress: {completed}/{len(symbols)} symbols processed")
            
            if result is not None:
                dataframes.append(result)
    
    return dataframes

def export_parquet(dataframes: List[pd.DataFrame]) -> Optional[str]:
    """Merge and export to Parquet"""
    if not dataframes:
        print("🚫 No data to export")
        return None
    
    print(f"\n📊 Merging {len(dataframes)} datasets...")
    
    # Concatenate all dataframes
    merged_df = pd.concat(dataframes, ignore_index=True)
    
    # Convert to Polars for efficient Parquet export
    df_pl = pl.from_pandas(merged_df)
    
    # Parse date column properly
    if "Date" in df_pl.columns:
        df_pl = df_pl.with_columns(
            pl.col("Date").str.strptime(pl.Date, "%Y-%m-%d", strict=False)
        )
    
    # Sort by Symbol and Date
    df_pl = df_pl.sort(["Symbol", "Date"])
    
    # Generate filename with date
    parquet_path = f"nse_data_{datetime.now().strftime('%Y%m%d')}.parquet"
    
    # Save Parquet
    df_pl.write_parquet(parquet_path, compression="zstd")
    
    print(f"✅ Parquet saved: {parquet_path}")
    print(f"📊 Total rows: {len(merged_df)}, Unique symbols: {merged_df['Symbol'].nunique()}")
    
    # File size
    size_mb = Path(parquet_path).stat().st_size / (1024 * 1024)
    print(f"💾 File size: {size_mb:.2f} MB")
    
    return parquet_path

# ========== MAIN WORKFLOW ==========
def main():
    print("=" * 60)
    print("🚀 NSE Data Downloader - GitHub Action")
    print("=" * 60)
    
    # Load symbols
    try:
        if not Path(SYMBOLS_FILE).exists():
            print(f"❌ {SYMBOLS_FILE} not found!")
            return
        
        symbols_df = pd.read_csv(SYMBOLS_FILE)
        symbol_col = next((c for c in symbols_df.columns if c.strip().lower() == "symbol"), None)
        
        if not symbol_col:
            print("❌ EQUITY_L.csv must have a 'Symbol' column")
            return
        
        symbols = symbols_df[symbol_col].dropna().astype(str).str.strip().unique().tolist()
        
        if not symbols:
            print("❌ No symbols found in file")
            return
        
        print(f"📋 Found {len(symbols)} unique symbols")
        
    except Exception as e:
        print(f"❌ Error reading symbols file: {e}")
        return
    
    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=DAYS)
    
    print(f"📅 Date range: {start_date.date()} to {end_date.date()}")
    
    # Download all symbols
    dataframes = download_all_symbols(symbols, start_date, end_date)
    
    print(f"\n✅ Successfully downloaded: {len(dataframes)}/{len(symbols)} symbols")
    
    if not dataframes:
        print("❌ No data downloaded. Exiting.")
        return
    
    # Export to Parquet
    parquet_path = export_parquet(dataframes)
    
    if parquet_path:
        print(f"\n🎉 Success! Data saved to {parquet_path}")
        
        # Delete old parquet files (keep only latest)
        for old_file in Path(".").glob("nse_data_*.parquet"):
            if old_file.name != parquet_path:
                old_file.unlink()
                print(f"🗑️  Deleted old file: {old_file.name}")
    
    print("=" * 60)
    print("✨ Process completed!")
    print("=" * 60)

if __name__ == "__main__":
    main()
