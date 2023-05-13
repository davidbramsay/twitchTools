import os
import datetime

def get_files_sorted_by_created_date(folder_path):
    files = []
    for root, _, filenames in os.walk(folder_path):
        for filename in filenames:
            if '.DS_Store' not in filename:
                file_path = os.path.join(root, filename)
                created_date = datetime.datetime.fromtimestamp(os.path.getmtime(file_path))
                files.append((file_path, created_date))

    sorted_files = sorted(files, key=lambda f: f[1])
    return sorted_files

# Example usage
folder_path = '~/Library/Messages/Attachments'
expanded_folder_path = os.path.expanduser(folder_path)
sorted_files = get_files_sorted_by_created_date(expanded_folder_path)

for file_path, created_date in sorted_files:
    print(f'{file_path} - Modified Date: {created_date}')
