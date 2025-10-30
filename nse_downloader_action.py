name: NSE Data Downloader

on:
  schedule:
    # Every Friday at 9:00 PM IST (3:30 PM UTC)
    - cron: '30 15 * * 5'
  workflow_dispatch: # Manual trigger

permissions:
  contents: write

jobs:
  download-and-save:
    runs-on: ubuntu-latest
    
    steps:
      - name: 🧾 Checkout repository
        uses: actions/checkout@v4
      
      - name: ⚙️ Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'
      
      - name: 📦 Install dependencies
        run: |
          pip install -r requirements.txt
      
      - name: 🚀 Run NSE Downloader (with retry)
        uses: nick-fields/retry@v3
        with:
          timeout_minutes: 10
          max_attempts: 3
          retry_wait_seconds: 30
          command: python nse_downloader_action.py
      
      - name: 🔍 Check for parquet files
        id: check_files
        run: |
          PARQUET_FILE=$(find . -maxdepth 1 -name "nse_data_*.parquet" -type f | head -1)
          
          if [ -z "$PARQUET_FILE" ]; then
            echo "❌ No parquet file found"
            echo "file_found=false" >> $GITHUB_OUTPUT
            exit 1
          fi
          
          echo "✅ Found: $PARQUET_FILE"
          FILE_SIZE=$(du -h "$PARQUET_FILE" | cut -f1)
          echo "📊 File size: $FILE_SIZE"
          echo "file_found=true" >> $GITHUB_OUTPUT
          echo "parquet_file=$PARQUET_FILE" >> $GITHUB_OUTPUT
          echo "file_size=$FILE_SIZE" >> $GITHUB_OUTPUT
      
      - name: ✅ Validate parquet file
        if: steps.check_files.outputs.file_found == 'true'
        run: |
          python -c "
          import pandas as pd
          import sys
          try:
              df = pd.read_parquet('${{ steps.check_files.outputs.parquet_file }}')
              rows = len(df)
              cols = len(df.columns)
              print(f'✅ Validation passed: {rows} rows, {cols} columns')
              print(f'📋 Columns: {list(df.columns)}')
              if rows == 0:
                  print('❌ Warning: Parquet file is empty!')
                  sys.exit(1)
          except Exception as e:
              print(f'❌ Validation failed: {e}')
              sys.exit(1)
          "
      
      - name: 🔐 Configure Git credentials
        if: steps.check_files.outputs.file_found == 'true'
        env:
          NIFTY_TOKEN: ${{ secrets.NIFTY_TOKEN }}
        run: |
          git config --global user.email "github-actions[bot]@users.noreply.github.com"
          git config --global user.name "github-actions[bot]"
          git config --global credential.helper store
          echo "https://x-access-token:${NIFTY_TOKEN}@github.com" > ~/.git-credentials
      
      - name: 📥 Clone NIFTY repository
        if: steps.check_files.outputs.file_found == 'true'
        run: |
          echo "🔄 Cloning NIFTY repository..."
          git clone https://github.com/navikaran2/NIFTY.git
          cd NIFTY
          echo "📂 Current directory contents:"
          ls -lh
      
      - name: 🗑️ Delete old parquet files from NIFTY repo
        if: steps.check_files.outputs.file_found == 'true'
        id: delete_old
        run: |
          cd NIFTY
          
          echo "🔍 Checking for old parquet files..."
          OLD_FILES=$(find . -maxdepth 1 -name "nse_data_*.parquet" -type f)
          
          if [ -n "$OLD_FILES" ]; then
            echo "🗑️ Found old files to delete:"
            echo "$OLD_FILES"
            rm -f nse_data_*.parquet
            
            git add -A
            
            DATE_IST=$(TZ='Asia/Kolkata' date +"%Y-%m-%d %I:%M:%S %p IST")
            git commit -m "🗑️ Removed old NSE data on ${DATE_IST}" -m "🤖 Automated cleanup via GitHub Actions"
            
            echo "deleted=true" >> $GITHUB_OUTPUT
            echo "✅ Old files deleted and committed"
          else
            echo "✅ No old parquet files found to delete"
            echo "deleted=false" >> $GITHUB_OUTPUT
          fi
      
      - name: 📦 Copy and commit new parquet file
        if: steps.check_files.outputs.file_found == 'true'
        id: add_new
        run: |
          echo "📦 Copying new parquet file(s) to NIFTY repo..."
          cp nse_data_*.parquet NIFTY/
          
          cd NIFTY
          echo "✅ Files after copy:"
          ls -lh nse_data_*.parquet
          
          git add nse_data_*.parquet
          
          DATE_IST=$(TZ='Asia/Kolkata' date +"%Y-%m-%d %I:%M:%S %p IST")
          FILE_SIZE="${{ steps.check_files.outputs.file_size }}"
          
          git commit -m "✅ NSE data updated on ${DATE_IST}" -m "📊 File size: ${FILE_SIZE}" -m "🤖 Automated update via GitHub Actions"
          
          echo "added=true" >> $GITHUB_OUTPUT
          echo "✅ New file committed successfully"
      
      - name: 🚀 Push all changes to NIFTY repo
        if: steps.check_files.outputs.file_found == 'true'
        run: |
          cd NIFTY
          
          echo "🚀 Pushing all commits to remote..."
          git push origin main
          
          echo "✨ All changes successfully pushed to NIFTY repo!"
      
      - name: 📊 Generate summary
        if: always()
        run: |
          echo "## 📈 NSE Data Downloader Summary" >> $GITHUB_STEP_SUMMARY
          echo "" >> $GITHUB_STEP_SUMMARY
          
          if [ "${{ steps.check_files.outputs.file_found }}" == "true" ]; then
            echo "✅ **Status**: Success" >> $GITHUB_STEP_SUMMARY
            echo "📁 **File**: \`${{ steps.check_files.outputs.parquet_file }}\`" >> $GITHUB_STEP_SUMMARY
            echo "📊 **Size**: ${{ steps.check_files.outputs.file_size }}" >> $GITHUB_STEP_SUMMARY
            echo "" >> $GITHUB_STEP_SUMMARY
            
            if [ "${{ steps.delete_old.outputs.deleted }}" == "true" ]; then
              echo "🗑️ **Old files**: Deleted" >> $GITHUB_STEP_SUMMARY
            else
              echo "🗑️ **Old files**: None found" >> $GITHUB_STEP_SUMMARY
            fi
            
            if [ "${{ steps.add_new.outputs.added }}" == "true" ]; then
              echo "✅ **New file**: Added and pushed" >> $GITHUB_STEP_SUMMARY
            else
              echo "⚠️ **New file**: Status unknown" >> $GITHUB_STEP_SUMMARY
            fi
          else
            echo "❌ **Status**: Failed - No parquet file generated" >> $GITHUB_STEP_SUMMARY
          fi
          
          echo "" >> $GITHUB_STEP_SUMMARY
          DATE_IST=$(TZ='Asia/Kolkata' date +"%Y-%m-%d %I:%M:%S %p IST")
          echo "🕒 **Completed**: ${DATE_IST}" >> $GITHUB_STEP_SUMMARY
      
      - name: 🧹 Cleanup credentials
        if: always()
        run: |
          rm -f ~/.git-credentials
          echo "✅ Credentials cleaned up"
      
      - name: 📧 Notify on failure
        if: failure()
        run: |
          echo "::error::❌ NSE data download/upload workflow failed!"
          echo "::error::Please check the logs for details"
          exit 1
