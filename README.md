# MindCare: Automated IoT Stress & Anxiety Detection Pipelines

An automated machine learning backend pipeline in Python that captures physiological sensor data (such as EDA, HR, etc.) from an ESP32 (or a raw text file), processes it, predicts stress and anxiety levels via pre-trained machine learning models, and uploads the results to a Firebase Realtime Database.

The project is divided into two separate pipelines:
- **Anxiety Pipeline (`anxiety/`)**: Uses `scipy`-based feature extraction.
- **Stress Pipeline (`stress/`)**: Uses advanced `neurokit2`-based feature extraction.

## Features

- **Data Logging:** Collects raw sensor data from an ESP32 over a serial connection.
- **Data Cleaning:** Converts raw text data into structured CSV format.
- **Preprocessing:** Handles missing values and filters physiological signals.
- **Feature Extraction:** Utilizes `scipy` (Anxiety) and `neurokit2` (Stress) to extract meaningful features from raw signals.
- **Predictions:** Uses pre-trained models to predict user stress and anxiety levels.
- **Firebase Integration:** Automatically uploads prediction summaries alongside user metadata to a Firebase Realtime Database.

## Prerequisites

- **Python 3.8+**
- ESP32 hardware properly configured and connected (if using the serial data logger).
- Firebase Realtime Database and service account key.

## Installation

1. **Clone the repository:**
   ```bash
   git clone <your-repo-url>
   cd Backend
   ```

2. **Create a virtual environment (optional but recommended):**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows use: .venv\Scripts\activate
   ```

3. **Install the dependencies:**
   Navigate into either the `anxiety` or `stress` folders and install requirements:
   ```bash
   cd anxiety
   pip install -r requirements.txt
   ```
   *(Repeat or apply accordingly for `stress/`)*

## Configuration

This project uses `python-dotenv` for managing sensitive credentials and hardware configurations inside the respective pipeline folders (`anxiety/` or `stress/`).

1. Navigate to the pipeline you want to run (e.g., `cd anxiety`).
2. Create a `.env` file (you can copy from `.env.example`):
   ```bash
   cp .env.example .env
   ```
3. Update the `.env` file with your specific configurations:
   ```ini
   FIREBASE_KEY_PATH=firebase/firebase_key.json
   FIREBASE_DATABASE_URL=https://your-firebase-database-url.firebasedatabase.app/
   SERIAL_PORT=COM9
   BAUD_RATE=115200
   ```
4. **Firebase Credentials:** Ensure you place your downloaded Firebase Admin SDK private key at `firebase/firebase_key.json` within the respective pipeline folder.

## Usage

1. **Provide Data:** 
   Upload your raw data `.txt` file into the `raw_data` folder located at the root of this repository.
   
2. **Run the Pipeline:**
   Navigate to the desired pipeline and execute the main script:
   ```bash
   cd anxiety  # or cd stress
   python main.py
   ```

3. **Provide Subject Information:** 
   The prompt will ask for your `Name`, `Age`, and `Gender`. This information will be saved to `data/user_info.txt` and attached to the final Firebase upload.

## Combined Pipeline (Anxiety + Stress)

A convenience runner is provided at the repository root to execute both pipelines sequentially and handle shared files and uploads:

- **Script:** `run_both_stress_anxiety.py`
- **Behavior:**
   - Looks for a raw `.txt` file in the repository `raw_data/` folder.
   - Converts and cleans the data to `data/cleaned_output.csv`.
   - Runs preprocessing, feature extraction, and prediction for both `anxiety` and `stress` pipelines.
   - Writes processed artifacts to `data/processed/` and final predictions to `data/predictions/`.
   - Attempts to fetch an active Firebase UID and upload non-empty results for each pipeline.

To run the combined pipeline from the repo root:

```bash
python run_both_stress_anxiety.py
```

Notes:
- Ensure you have placed your raw `.txt` file in `raw_data/` before running.
- If no active Firebase session (UID not found), uploads are skipped but CSV outputs are still generated.

### Running the automated Serial Logger (Optional)

If you want the Python script to directly listen to the ESP32 rather than manually dropping in the `.txt` file:

```bash
python data_logger.py
```

This will automatically connect to your configured `SERIAL_PORT` and listen for 10 minutes. Afterwards, you can run `python main.py` to process the newly generated data.

## File Structure

```text
Backend/
├── raw_data/
│   ├── (Upload raw .txt data files here)
├── anxiety/
│   ├── main.py: Entry point for anxiety pipeline.
│   ├── data_logger.py: Connects to ESP32 over serial.
│   ├── txt_to_csv_converter.py
│   ├── preprocessing.py
│   ├── feature_extraction.py
│   ├── prediction.py
│   ├── firebase_upload.py
│   ├── .env
│   ├── models/ (Pre-trained models)
│   └── data/ (Auto-generated folder)
└── stress/
   └── run_both_stress_anxiety.py: Combined runner to execute both pipelines from repository root.
    ├── main.py: Entry point for stress pipeline.
    ├── data_logger.py: Connects to ESP32 over serial.
    ├── txt_to_csv_converter.py
    ├── preprocessing.py
    ├── feature_extraction.py
    ├── prediction.py
    ├── firebase_upload.py
    ├── .env
    ├── models/ (Pre-trained models)
    └── data/ (Auto-generated folder)
```
