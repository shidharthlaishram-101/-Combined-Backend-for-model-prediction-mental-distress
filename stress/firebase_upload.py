import firebase_admin
from firebase_admin import credentials, db
import os
from dotenv import load_dotenv

load_dotenv()

FIREBASE_KEY_PATH = os.getenv('FIREBASE_KEY_PATH', 'firebase/firebase_key.json')
DATABASE_URL = os.getenv('FIREBASE_DATABASE_URL', '')

if not firebase_admin._apps:
    try:
        cred = credentials.Certificate(FIREBASE_KEY_PATH)
        firebase_admin.initialize_app(cred, {
            'databaseURL': DATABASE_URL
        })
    except Exception as e:
        print(f"Warning: Firebase initialization failed. Please ensure '{FIREBASE_KEY_PATH}' exists.\nError: {e}")

def fetch_user_id():
    try:
        ref = db.reference('active_session')
        sessions = ref.get()
        if sessions:
            pending_sessions = {k: v for k, v in sessions.items() if v.get('status') == 'pending'}
            if pending_sessions:
                sorted_sessions = sorted(pending_sessions.items(), key=lambda x: x[1].get('timestamp', ''))
                return sorted_sessions[0][0]
        return None
    except Exception as e:
        print(f"Failed to fetch user ID: {e}")
        return None


def fetch_user_details(uid):
    try:
        if not uid:
            return None
        ref = db.reference(f'active_session/{uid}')
        details = ref.get()
        if not details:
            return None
        return {
            'firstname': details.get('firstname'),
            'age': details.get('age'),
            'gender': details.get('gender')
        }
    except Exception as e:
        print(f"Failed to fetch user details for {uid}: {e}")
        return None


def upload_result(result_df, uid=None):
    if result_df.empty:
        print("No predictions to upload.")
        return
        
    if not uid:
        print("No active session found. Skipping Firebase upload.")
        return
    
    try:
        # Extract the most recent prediction window
        latest_data = result_df.iloc[-1].to_dict()
        
        # Map Predicted_Label to stress_detected (0 = no stress, 1 = stress detected)
        stress_detected = latest_data.get('Predicted_Label')
        
        # Upload to active_session/{uid}
        ref = db.reference(f'active_session/{uid}')
        ref.update({
            'stress_detected': stress_detected,
            'status': 'done'
        })
        
        stress_label = 'Stress detected' if stress_detected == 1 else 'No stress detected'
        print(f'Successfully uploaded {stress_label} to active_session/{uid}!')
    except Exception as e:
        print(f"Failed to upload to Firebase: {e}")
