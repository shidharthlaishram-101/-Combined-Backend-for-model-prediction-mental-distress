import serial
import time
import os
from dotenv import load_dotenv

load_dotenv()

PORT = os.getenv('SERIAL_PORT', 'COM9')

# IMPORTANT:
# Must match ESP32 Serial.begin(...)
BAUD_RATE = int(os.getenv('BAUD_RATE', 115200))

DURATION = 600  # 10 minutes

# Raw chunk size
CHUNK_SIZE = 4096


from firebase_upload import fetch_user_id, fetch_user_details

# ---------------- USER INFO ----------------
def get_user_info():

    print("\n--- Subject Information ---")
    
    user_id = fetch_user_id()
    user_details = None
    if user_id:
        print(f"Fetched User ID from Firebase: {user_id}")
        user_details = fetch_user_details(user_id)
    else:
        print("No User ID found in Firebase.")

    if user_details:
        print("Fetched user details from Firebase:")
        print(f"  First Name: {user_details.get('firstname')}")
        print(f"  Age: {user_details.get('age')}")
        print(f"  Gender: {user_details.get('gender')}")

    first_name = user_details.get('firstname') if user_details and user_details.get('firstname') else input("Enter First Name: ")
    age = user_details.get('age') if user_details and user_details.get('age') else input("Enter Age: ")
    gender = user_details.get('gender') if user_details and user_details.get('gender') else input("Enter Gender: ")

    print("---------------------------\n")

    os.makedirs('data', exist_ok=True)

    user_info_path = 'data/user_info.txt'

    with open(user_info_path, 'w', encoding='utf-8') as f:

        f.write(f"First Name: {first_name}\n")
        f.write(f"Age: {age}\n")
        f.write(f"Gender: {gender}\n")

    print(f"User information saved to {user_info_path}!")


# ---------------- MAIN ----------------
def main():

    # Create data folder
    os.makedirs('data', exist_ok=True)

    # Ask subject info
    get_user_info()

    # Output file
    output_filename = 'data/raw_serial_data.txt'

    try:

        ser = serial.Serial(
            PORT,
            BAUD_RATE,
            timeout=0.01
        )

        print(f"\nConnected to {PORT} at {BAUD_RATE} baud.")

    except Exception as e:

        print(f"Error connecting to serial port: {e}")
        return

    # Wait for ESP32 auto-reset
    time.sleep(2)

    # Clear startup buffer
    ser.reset_input_buffer()

    start = time.time()

    total_bytes = 0

    print(
        f"\nCollecting RAW serial data for "
        f"{DURATION} seconds..."
    )

    print(f"Saving to: {output_filename}\n")

    # Open in binary mode
    with open(output_filename, 'wb',
              buffering=1024 * 1024) as f:

        while time.time() - start < DURATION:

            try:

                waiting = ser.in_waiting

                if waiting:

                    # Read raw bytes directly
                    data = ser.read(
                        min(waiting, CHUNK_SIZE)
                    )

                    # Save EXACT raw data
                    f.write(data)

                    total_bytes += len(data)

                else:
                    time.sleep(0.001)

            except Exception as e:

                print("Read Error:", e)

    ser.close()

    print("\n===== COLLECTION FINISHED =====")

    print(f"Total bytes saved : {total_bytes}")

    print(f"Saved file        : {output_filename}")


# ---------------- RUN ----------------
if __name__ == "__main__":
    main()