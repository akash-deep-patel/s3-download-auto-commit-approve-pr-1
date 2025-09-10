import os
import time
import zipfile
import logging
from pathlib import Path
from typing import List, Tuple

logger = logging.getLogger(__name__)

class ZipService:
    """Service for handling ZIP file operations"""
    
    @staticmethod
    def is_zip_file(file_path: str) -> bool:
        """Check if a file is a ZIP file"""
        try:
            return zipfile.is_zipfile(file_path)
        except Exception:
            return False
    
    @staticmethod
    def extract_zip_file(zip_path: str, extract_to: str) -> Tuple[bool, List[str]]:
        """
        Extract a ZIP file to the specified directory with smart flattening
        
        Args:
            zip_path: Path to the ZIP file
            extract_to: Directory to extract to
            
        Returns:
            Tuple of (success: bool, extracted_files: List[str])
        """
        try:
            extracted_files = []
            
            # Ensure extraction directory exists
            os.makedirs(extract_to, exist_ok=True)
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # Get list of files in the ZIP
                file_list = zip_ref.namelist()
                logger.info(f"Extracting {len(file_list)} files from {zip_path}")
                
                # Check if all files are under a single root directory
                should_flatten = ZipService._should_flatten_zip(file_list)
                root_dir = None
                
                if should_flatten:
                    # Find the common root directory
                    root_dir = ZipService._get_zip_root_directory(file_list)
                    logger.info(f"Detected single root directory '{root_dir}' - will flatten structure")
                
                # Extract all files first
                zip_ref.extractall(extract_to)
                
                if should_flatten and root_dir:
                    # Move files from root directory to extract_to directory
                    ZipService._flatten_extracted_directory(extract_to, root_dir)
                
                # Build list of final extracted file paths
                for root, dirs, files in os.walk(extract_to):
                    for file in files:
                        file_path = os.path.join(root, file)
                        extracted_files.append(file_path)
                
                logger.info(f"Successfully extracted {len(extracted_files)} files to {extract_to}")
                return True, extracted_files
                
        except zipfile.BadZipFile:
            logger.error(f"Bad ZIP file: {zip_path}")
            return False, []
        except Exception as e:
            logger.error(f"Error extracting ZIP file {zip_path}: {e}")
            return False, []
    
    @staticmethod
    def extract_all_zips_in_directory(directory: str) -> Tuple[bool, List[str]]:
        """
        Find and extract all ZIP files in a directory
        
        Args:
            directory: Directory to scan for ZIP files
            
        Returns:
            Tuple of (all_success: bool, all_extracted_files: List[str])
        """
        all_extracted_files = []
        all_success = True
        
        if not os.path.exists(directory):
            logger.error(f"Directory does not exist: {directory}")
            return False, []
        
        # Find all ZIP files in the directory
        zip_files = []
        time.sleep(5)  # Add a small delay to avoid overwhelming the system
        for root, dirs, files in os.walk(directory):

            for file in files:
                file_path = os.path.join(root, file)
                file_path = os.path.join(root, file).replace("\\", "/")
                if file.lower().endswith('.zip'):
                    zip_files.append(file_path)
        
        logger.info(f"Found {len(zip_files)} ZIP files in {directory}")
        
        for zip_path in zip_files:
            logger.info(f"Extracting ZIP file: {zip_path}")
            if not os.path.exists(zip_path):
                logger.warning(f"ZIP file does not exist (skipping): {zip_path}")
                continue
            # Create extraction directory next to ZIP file
            
            zip_name = Path(zip_path).stem
            extract_dir = os.path.join(os.path.dirname(zip_path), f"{zip_name}_extracted")
            
            success, extracted_files = ZipService.extract_zip_file(zip_path, extract_dir)
            
            if success:
                all_extracted_files.extend(extracted_files)
                logger.info(f"Successfully extracted {len(extracted_files)} files from {zip_path}")
                
                # Optionally remove the ZIP file after successful extraction
                try:
                    os.remove(zip_path)
                    logger.info(f"Removed original ZIP file: {zip_path}")
                except Exception as e:
                    logger.warning(f"Could not remove ZIP file {zip_path}: {e}")
            else:
                all_success = False
                logger.error(f"Failed to extract ZIP file: {zip_path}")
        
        return all_success, all_extracted_files
    
    @staticmethod
    def get_all_files_after_extraction(directory: str) -> List[str]:
        """
        Get all files in directory after ZIP extraction
        
        Args:
            directory: Directory to scan
            
        Returns:
            List of all file paths (excluding ZIP files)
        """
        all_files = []
        
        if not os.path.exists(directory):
            return all_files
        
        for root, dirs, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file)
                # Skip ZIP files since they should have been extracted and removed
                if not file.lower().endswith('.zip'):
                    all_files.append(file_path)
        
        return all_files
    
    @staticmethod
    def _should_flatten_zip(file_list: List[str]) -> bool:
        """
        Determine if a ZIP file should be flattened (all files under single root directory)
        
        Args:
            file_list: List of file paths in the ZIP
            
        Returns:
            bool: True if should flatten, False otherwise
        """
        if not file_list:
            return False
        
        # Get all top-level entries (no slashes except at the end for directories)
        top_level_entries = set()
        for file_path in file_list:
            # Get the first path component
            parts = file_path.split('/')
            if parts:
                top_level_entries.add(parts[0])
        
        # If there's only one top-level entry and it's a directory, we should flatten
        if len(top_level_entries) == 1:
            root_entry = list(top_level_entries)[0]
            # Check if this root entry is a directory (appears as folder/ in the zip)
            has_root_as_dir = any(f.startswith(root_entry + '/') for f in file_list)
            return has_root_as_dir
        
        return False
    
    @staticmethod
    def _get_zip_root_directory(file_list: List[str]) -> str:
        """
        Get the root directory name from ZIP file list
        
        Args:
            file_list: List of file paths in the ZIP
            
        Returns:
            str: Root directory name
        """
        if not file_list:
            return ""
        
        # Get the first path component from the first file
        first_file = file_list[0]
        parts = first_file.split('/')
        return parts[0] if parts else ""
    
    @staticmethod
    def _flatten_extracted_directory(extract_to: str, root_dir: str):
        """
        Move all files from root_dir to extract_to directory and remove root_dir
        
        Args:
            extract_to: Base extraction directory
            root_dir: Root directory name to flatten
        """
        import shutil
        
        root_path = os.path.join(extract_to, root_dir)
        
        if not os.path.exists(root_path):
            logger.warning(f"Root directory {root_path} does not exist - skipping flattening")
            return
        
        logger.info(f"Flattening directory structure: moving contents from {root_path} to {extract_to}")
        
        # Move all files and subdirectories from root_path to extract_to
        for item in os.listdir(root_path):
            src = os.path.join(root_path, item)
            dst = os.path.join(extract_to, item)
            
            # Handle potential conflicts by adding suffix if destination exists
            if os.path.exists(dst):
                counter = 1
                base_name = item
                while os.path.exists(dst):
                    name, ext = os.path.splitext(base_name)
                    dst = os.path.join(extract_to, f"{name}_{counter}{ext}")
                    counter += 1
                logger.info(f"Destination exists, renaming to: {os.path.basename(dst)}")
            
            # Move the item
            shutil.move(src, dst)
            logger.debug(f"Moved {src} to {dst}")
        
        # Remove the now-empty root directory
        try:
            os.rmdir(root_path)
            logger.info(f"Removed empty root directory: {root_path}")
        except Exception as e:
            logger.warning(f"Could not remove root directory {root_path}: {e}")
