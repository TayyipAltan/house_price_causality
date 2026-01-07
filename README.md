# house_price_causality

## KNMI API Access

This project includes tools to access earthquake catalog data from the KNMI Open Data API.

### Quick Start

1. **Get API Key:** Register at [KNMI Developer Portal](https://developer.dataplatform.knmi.nl/apis/)
2. **Configure API Key (choose one method):**
   
   **Option A: Using keys.py (Recommended for local development)**
   ```bash
   cp keys.py.example keys.py
   # Then edit keys.py and add your API key
   ```
   
   **Option B: Environment Variable**
   ```powershell
   # PowerShell
   $env:KNMI_API_KEY="your-api-key-here"
   ```
   ```bash
   # Linux/Mac
   export KNMI_API_KEY="your-api-key-here"
   ```
3. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
4. **Run Example:**
   ```bash
   python knmi_api_access.py
   ```

**Note:** `keys.py` is git-ignored to prevent accidentally committing your API key.

See `example_usage.md` for detailed documentation.