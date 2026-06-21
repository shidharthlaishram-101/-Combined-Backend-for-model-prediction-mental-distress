import pandas as pd
import numpy as np
from scipy.signal import find_peaks
from scipy.stats import linregress
import os

# WESAD dataset sampling rate is 700. 
# Update this if your Arduino sampling rate is different!
FS = 32 
WINDOW_SEC = 60
STEP_SEC = 30

def extract_eda_features(segment):
    if len(segment) == 0:
        return [0.0]*6
    mean  = np.mean(segment)
    std   = np.std(segment)
    mn    = np.min(segment)
    mx    = np.max(segment)
    slope, *_ = linregress(np.arange(len(segment)), segment)
    peaks, _  = find_peaks(segment, distance=max(1, FS // 2))
    return [mean, std, mn, mx, slope, len(peaks)]

def extract_ecg_features(segment):
    if len(segment) == 0:
        return [0.0]*7
    mean = np.mean(segment)
    std  = np.std(segment)
    mn   = np.min(segment)
    mx   = np.max(segment)
    rms  = np.sqrt(np.mean(segment ** 2))
    peaks, _ = find_peaks(segment, distance=max(1, int(FS * 0.4)), height=np.mean(segment))
    if len(peaks) > 1:
        rr       = np.diff(peaks) / FS * 1000
        hrv_std  = np.std(rr)
        hrv_mean = np.mean(rr)
    else:
        hrv_std, hrv_mean = 0.0, 0.0
    return [mean, std, mn, mx, rms, hrv_std, hrv_mean]

def extract_features(df, output_path='data/processed/features.csv'):
    if df.empty:
        return pd.DataFrame()
        
    ecg_signal = df['ecg'].values
    eda_signal = df['eda'].values
    
    WINDOW_SIZE = FS * WINDOW_SEC
    STEP_SIZE = FS * STEP_SEC

    print(f"Total samples: {min(len(ecg_signal), len(eda_signal))}")
    print(f"Window size needed: {WINDOW_SIZE}")
    print(f"Windows extracted: will count after loop...")
    
    rows = []
    n = min(len(ecg_signal), len(eda_signal))
    
    # Process overlapping windows
    for start in range(0, n - WINDOW_SIZE + 1, STEP_SIZE):
        end = start + WINDOW_SIZE
        ecg_win = ecg_signal[start:end]
        eda_win = eda_signal[start:end]
        
        ecg_feats = extract_ecg_features(ecg_win)
        eda_feats = extract_eda_features(eda_win)
        
        row_dict = {
            "Time": (start + end) / 2 / FS,
            "ecg_mean": ecg_feats[0],
            "ecg_std": ecg_feats[1],
            "ecg_min": ecg_feats[2],
            "ecg_max": ecg_feats[3],
            "ecg_rms": ecg_feats[4],
            "ecg_hrv_std": ecg_feats[5],
            "ecg_hrv_mean": ecg_feats[6],
            "eda_mean": eda_feats[0],
            "eda_std": eda_feats[1],
            "eda_min": eda_feats[2],
            "eda_max": eda_feats[3],
            "eda_slope": eda_feats[4],
            "eda_npeaks": eda_feats[5]
        }
        rows.append(row_dict)
        
    print(f"Windows extracted: {len(rows)}")

    features_df = pd.DataFrame(rows)
    
    if features_df.empty:
        print("Feature extraction failed: Insufficient data to form windows.")
        return pd.DataFrame()
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    features_df.to_csv(output_path, index=False)
    
    return features_df
