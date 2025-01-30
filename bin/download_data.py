import os
import requests

def download_csv(url, save_path):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Check if the request was successful
    except requests.exceptions.RequestException as e:
        print(f"Error downloading the file: {e}")
        return False

    try:
        with open(save_path, 'wb') as file:
            file.write(response.content)
        print(f"File saved successfully at {save_path}")
        return True
    except IOError as e:
        print(f"Error saving the file: {e}")
        return False

def main():
    url = "https://www.socialscienceregistry.org/site/csv"
    save_dir = "_data"
    save_path = os.path.join(save_dir, "trials.csv")

    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    if download_csv(url, save_path):
        print("Download and save completed successfully.")
    else:
        print("Download or save failed.")

if __name__ == "__main__":
    main()
