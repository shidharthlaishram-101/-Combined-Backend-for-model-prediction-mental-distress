import importlib.util
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
ANXIETY_DIR = BASE_DIR / 'anxiety'
STRESS_DIR = BASE_DIR / 'stress'


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, str(path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def find_input_file(raw_data_dir):
    if not raw_data_dir.exists():
        return None
    txt_files = [f for f in raw_data_dir.iterdir() if f.suffix == '.txt']
    return txt_files[0] if txt_files else None


def ensure_dirs():
    paths = [
        BASE_DIR / 'data',
        BASE_DIR / 'data' / 'processed',
        BASE_DIR / 'data' / 'predictions',
        BASE_DIR / 'raw_data',
    ]
    for path in paths:
        path.mkdir(parents=True, exist_ok=True)


if __name__ == '__main__':
    ensure_dirs()

    anxiety_converter = load_module('anxiety_txt_to_csv', ANXIETY_DIR / 'txt_to_csv_converter.py')
    anxiety_preprocess = load_module('anxiety_preprocess', ANXIETY_DIR / 'preprocessing.py')
    anxiety_extract = load_module('anxiety_extract', ANXIETY_DIR / 'feature_extraction.py')
    anxiety_predict = load_module('anxiety_predict', ANXIETY_DIR / 'prediction.py')
    anxiety_firebase = load_module('anxiety_firebase', ANXIETY_DIR / 'firebase_upload.py')
    anxiety_logger = load_module('anxiety_logger', ANXIETY_DIR / 'data_logger.py')

    stress_converter = load_module('stress_txt_to_csv', STRESS_DIR / 'txt_to_csv_converter.py')
    stress_preprocess = load_module('stress_preprocess', STRESS_DIR / 'preprocessing.py')
    stress_extract = load_module('stress_extract', STRESS_DIR / 'feature_extraction.py')
    stress_predict = load_module('stress_predict', STRESS_DIR / 'prediction.py')
    stress_firebase = load_module('stress_firebase', STRESS_DIR / 'firebase_upload.py')

    print('STEP 1 - Subject Information')
    anxiety_logger.get_user_info()

    raw_data_dir = BASE_DIR / 'raw_data'
    input_file = find_input_file(raw_data_dir)
    if input_file is None:
        print(f"Error: No .txt files found in '{raw_data_dir}'.")
        print('Please place your raw text file there and run again.')
        raise SystemExit(1)

    if input_file.stat().st_size == 0:
        print(f"Error: The file '{input_file}' is empty. Please provide a file with data.")
        raise SystemExit(1)

    print(f"\nUsing input file: {input_file}")
    cleaned_csv = BASE_DIR / 'data' / 'cleaned_output.csv'

    print('\nSTEP 2 - Convert TXT to CSV')
    anxiety_converter.convert_and_clean_txt(str(input_file), str(cleaned_csv))

    print('\nSTEP 3 - Preprocess for anxiety')
    anxiety_processed = anxiety_preprocess.preprocess_data(
        str(cleaned_csv),
        str(BASE_DIR / 'data' / 'processed' / 'anxiety_processed.csv')
    )

    print('\nSTEP 3 - Preprocess for stress')
    stress_processed = stress_preprocess.preprocess_data(
        str(cleaned_csv),
        str(BASE_DIR / 'data' / 'processed' / 'stress_processed.csv')
    )

    if anxiety_processed.empty and stress_processed.empty:
        print('Both preprocessing flows failed.')
        raise SystemExit(1)

    anxiety_feature_df = None
    stress_feature_df = None

    if not anxiety_processed.empty:
        print('\nSTEP 4 - Feature Extraction for anxiety')
        anxiety_feature_df = anxiety_extract.extract_features(
            anxiety_processed,
            str(BASE_DIR / 'data' / 'processed' / 'anxiety_features.csv')
        )

    if not stress_processed.empty:
        print('\nSTEP 4 - Feature Extraction for stress')
        stress_feature_df = stress_extract.extract_features(
            stress_processed,
            str(BASE_DIR / 'data' / 'processed' / 'stress_features.csv')
        )

    anxiety_result = None
    stress_result = None

    if anxiety_feature_df is not None and not anxiety_feature_df.empty:
        print('\nSTEP 5 - Anxiety Prediction')
        anxiety_result = anxiety_predict.predict_anxiety(
            anxiety_feature_df,
            str(BASE_DIR / 'data' / 'predictions' / 'anxiety_final_predictions.csv')
        )

    if stress_feature_df is not None and not stress_feature_df.empty:
        print('\nSTEP 5 - Stress Prediction')
        stress_result = stress_predict.predict_stress(
            stress_feature_df,
            str(BASE_DIR / 'data' / 'predictions' / 'stress_final_predictions.csv')
        )

    uid = anxiety_firebase.fetch_user_id()
    if uid:
        print(f"\nActive session found with UID: {uid}")
        if anxiety_result is not None and not anxiety_result.empty:
            anxiety_firebase.upload_result(anxiety_result, uid=uid)
        else:
            print('Anxiety result is empty; skipping anxiety upload.')

        if stress_result is not None and not stress_result.empty:
            stress_firebase.upload_result(stress_result, uid=uid)
        else:
            print('Stress result is empty; skipping stress upload.')
    else:
        print('No active session found. Skipping Firebase upload for both results.')

    print('\nFULL COMBINED PIPELINE COMPLETED')
