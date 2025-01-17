import os
import shutil
from functions import generate_pages_recursive


def copy_static():
    """
    Recursively copy static directory to public directory.
    First cleans the public directory if it exists.
    """
    src = "static"
    dst = "public"

    # Clean public directory if it exists
    if os.path.exists(dst):
        print(f"Cleaning directory: {dst}")
        shutil.rmtree(dst)

    def copy_recursive(src_path, dst_path):
        """
        Recursively copy contents from src_path to dst_path.
        Creates directories as needed and copies all files.
        """
        # Create destination directory if it doesn't exist
        if not os.path.exists(dst_path):
            print(f"Creating directory: {dst_path}")
            os.mkdir(dst_path)

        # Iterate through all items in source directory
        for item in os.listdir(src_path):
            src_item = os.path.join(src_path, item)
            dst_item = os.path.join(dst_path, item)

            if os.path.isfile(src_item):
                # Copy file
                print(f"Copying file: {src_item} -> {dst_item}")
                shutil.copy(src_item, dst_item)
            else:
                # Recursively copy directory
                copy_recursive(src_item, dst_item)

    # Start the recursive copy
    if os.path.exists(src):
        copy_recursive(src, dst)
        print("Static directory copy complete!")
    else:
        print("No static directory found, skipping copy.")


def main():
    # First, clean and recreate public directory
    public_dir = "public"
    if os.path.exists(public_dir):
        print(f"Cleaning directory: {public_dir}")
        shutil.rmtree(public_dir)
    os.makedirs(public_dir)

    # Copy static files to public directory
    copy_static()

    # Generate pages recursively from content directory
    generate_pages_recursive(
        "content",
        "template.html",
        "public"
    )


if __name__ == "__main__":
    main()