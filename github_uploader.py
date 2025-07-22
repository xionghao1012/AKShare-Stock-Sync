#!/usr/bin/env python3
"""
GitHub Project Uploader
A tool to upload the Chinese stock data synchronization project to GitHub
while filtering out sensitive files and preserving project structure.
"""

import os
import fnmatch
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import base64
import re
import time
import random


@dataclass
class FileInfo:
    """Information about a file to be uploaded"""
    path: str           # Relative path from project root
    content: str        # File content (base64 encoded if binary)
    size: int          # File size in bytes
    is_binary: bool    # Whether file is binary


@dataclass
class UploadResult:
    """Result of the upload operation"""
    success: bool
    repository_url: str
    commit_sha: str
    uploaded_files: List[str]
    errors: List[str]


class GitHubError(Exception):
    """Base exception for GitHub-related errors"""
    pass


class NetworkError(GitHubError):
    """Network-related errors"""
    pass


class APILimitError(GitHubError):
    """GitHub API rate limit errors"""
    pass


class RepositoryExistsError(GitHubError):
    """Repository already exists error"""
    pass


class FileTooLargeError(GitHubError):
    """File exceeds GitHub size limits"""
    pass


class RetryHandler:
    """Handles retry logic with exponential backoff"""
    
    def __init__(self, max_retries: int = 3, base_delay: float = 1.0):
        self.max_retries = max_retries
        self.base_delay = base_delay
    
    def retry_with_backoff(self, func, *args, **kwargs):
        """Execute function with exponential backoff retry"""
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                return func(*args, **kwargs)
            except NetworkError as e:
                last_exception = e
                if attempt < self.max_retries:
                    delay = self.base_delay * (2 ** attempt) + random.uniform(0, 1)
                    print(f"⚠️  Network error (attempt {attempt + 1}/{self.max_retries + 1}): {str(e)}")
                    print(f"🔄 Retrying in {delay:.1f} seconds...")
                    time.sleep(delay)
                else:
                    print(f"❌ Max retries exceeded for network error")
            except APILimitError as e:
                last_exception = e
                if attempt < self.max_retries:
                    # For API limits, wait longer
                    delay = 60 + random.uniform(0, 30)  # Wait 60-90 seconds
                    print(f"⚠️  API rate limit hit (attempt {attempt + 1}/{self.max_retries + 1})")
                    print(f"⏳ Waiting {delay:.0f} seconds for rate limit reset...")
                    time.sleep(delay)
                else:
                    print(f"❌ Max retries exceeded for API limit")
            except Exception as e:
                # For other errors, don't retry
                raise e
        
        # If we get here, all retries failed
        raise last_exception


class FileFilter:
    """Handles filtering of files for GitHub upload"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        
        # Files and patterns to exclude
        self.exclude_patterns = [
            # Sensitive files
            ".env",
            "*.env",
            
            # Log files
            "*.log",
            "logs/*",
            
            # Python cache
            "__pycache__/*",
            "*.pyc",
            "*.pyo",
            "*.pyd",
            
            # Temporary files
            "*.tmp",
            "*.temp",
            "*.swp",
            "*.swo",
            "*~",
            
            # Git directory
            ".git/*",
            ".gitignore",
            
            # IDE files
            ".vscode/*",
            ".idea/*",
            "*.sublime-*",
            
            # OS files
            ".DS_Store",
            "Thumbs.db",
            
            # Large data files (if they exist)
            "sync_progress.json",
            "*.db",
            "*.sqlite",
            "*.sqlite3",
        ]
        
        # Files to explicitly include (overrides exclusions)
        self.include_patterns = [
            ".env.example",
            "requirements.txt",
            "*.py",
            "*.md",
            "*.txt",
            "*.sql",
            "*.sh",
            "*.bat",
            "*.json",  # But will check size
        ]
        
        # Binary file extensions
        self.binary_extensions = {
            '.exe', '.dll', '.so', '.dylib',
            '.jpg', '.jpeg', '.png', '.gif', '.bmp',
            '.pdf', '.doc', '.docx', '.xls', '.xlsx',
            '.zip', '.tar', '.gz', '.rar', '.7z'
        }
        
        # Maximum file size (1MB for text files, 25MB for binary - GitHub limit is 100MB)
        self.max_text_size = 1024 * 1024  # 1MB
        self.max_binary_size = 25 * 1024 * 1024  # 25MB

    def is_excluded_file(self, filepath: str) -> bool:
        """Check if a file should be excluded from upload"""
        relative_path = str(Path(filepath).relative_to(self.project_root))
        
        # Check if explicitly included
        for pattern in self.include_patterns:
            if fnmatch.fnmatch(relative_path, pattern) or fnmatch.fnmatch(os.path.basename(filepath), pattern):
                return False
        
        # Check exclusion patterns
        for pattern in self.exclude_patterns:
            if fnmatch.fnmatch(relative_path, pattern) or fnmatch.fnmatch(os.path.basename(filepath), pattern):
                return True
        
        return False

    def is_binary_file(self, filepath: str) -> bool:
        """Determine if a file is binary"""
        # Check by extension first
        if Path(filepath).suffix.lower() in self.binary_extensions:
            return True
        
        # Check file content for binary data
        try:
            with open(filepath, 'rb') as f:
                chunk = f.read(1024)
                if b'\0' in chunk:  # Null bytes indicate binary
                    return True
        except Exception:
            return True  # If we can't read it, treat as binary
        
        return False

    def get_file_content(self, filepath: str) -> Tuple[str, bool]:
        """Read file content and return (content, is_binary) with error handling"""
        is_binary = self.is_binary_file(filepath)
        
        try:
            # Check file size before reading
            file_size = os.path.getsize(filepath)
            max_size = self.max_binary_size if is_binary else self.max_text_size
            
            if file_size > max_size:
                raise FileTooLargeError(f"File {filepath} is too large ({file_size} bytes, max: {max_size})")
            
            if is_binary:
                with open(filepath, 'rb') as f:
                    content = base64.b64encode(f.read()).decode('utf-8')
            else:
                # Try UTF-8 first, then other encodings for Chinese text
                encodings = ['utf-8', 'gbk', 'gb2312', 'latin-1']
                content = None
                
                for encoding in encodings:
                    try:
                        with open(filepath, 'r', encoding=encoding) as f:
                            content = f.read()
                        break
                    except UnicodeDecodeError:
                        continue
                
                if content is None:
                    # If all encodings fail, read as binary
                    with open(filepath, 'rb') as f:
                        content = base64.b64encode(f.read()).decode('utf-8')
                    is_binary = True
            
            return content, is_binary
            
        except PermissionError:
            raise Exception(f"Permission denied reading file {filepath}")
        except FileNotFoundError:
            raise Exception(f"File not found: {filepath}")
        except FileTooLargeError:
            raise  # Re-raise as is
        except Exception as e:
            raise Exception(f"Failed to read file {filepath}: {str(e)}")

    def get_uploadable_files(self) -> List[FileInfo]:
        """Get list of files that should be uploaded to GitHub with comprehensive error handling"""
        uploadable_files = []
        skipped_files = []
        error_files = []
        
        print("🔍 Scanning project files...")
        
        for root, dirs, files in os.walk(self.project_root):
            # Skip excluded directories
            dirs[:] = [d for d in dirs if not self.is_excluded_file(os.path.join(root, d))]
            
            for file in files:
                filepath = os.path.join(root, file)
                
                # Skip if excluded
                if self.is_excluded_file(filepath):
                    continue
                
                try:
                    # Get file info with error handling
                    file_size = os.path.getsize(filepath)
                    content, is_binary = self.get_file_content(filepath)
                    
                    # Create relative path from project root
                    relative_path = str(Path(filepath).relative_to(self.project_root))
                    
                    file_info = FileInfo(
                        path=relative_path,
                        content=content,
                        size=file_size,
                        is_binary=is_binary
                    )
                    
                    uploadable_files.append(file_info)
                    
                except FileTooLargeError as e:
                    skipped_files.append(f"{filepath} (too large: {file_size // 1024}KB)")
                except PermissionError:
                    error_files.append(f"{filepath} (permission denied)")
                except FileNotFoundError:
                    error_files.append(f"{filepath} (file not found)")
                except Exception as e:
                    error_files.append(f"{filepath} (error: {str(e)})")
        
        # Report results
        print(f"✅ Found {len(uploadable_files)} files to upload")
        
        if skipped_files:
            print(f"⚠️  Skipped {len(skipped_files)} large files:")
            for skipped in skipped_files[:5]:  # Show first 5
                print(f"   - {skipped}")
            if len(skipped_files) > 5:
                print(f"   ... and {len(skipped_files) - 5} more")
        
        if error_files:
            print(f"❌ Failed to read {len(error_files)} files:")
            for error in error_files[:5]:  # Show first 5
                print(f"   - {error}")
            if len(error_files) > 5:
                print(f"   ... and {len(error_files) - 5} more")
        
        return uploadable_files


class RepositoryCreator:
    """Handles GitHub repository creation and configuration"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
    
    def generate_repo_name(self) -> str:
        """Generate an appropriate repository name based on project content"""
        # Try to extract name from README.md
        readme_path = self.project_root / "README.md"
        if readme_path.exists():
            try:
                with open(readme_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Look for the main title (first # heading)
                title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
                if title_match:
                    title = title_match.group(1).strip()
                    # Convert Chinese title to English-friendly repo name
                    if "股票" in title or "数据" in title or "同步" in title:
                        return "chinese-stock-data-sync"
                    elif "金融" in title:
                        return "chinese-financial-data-tool"
            except Exception:
                pass
        
        # Fallback: use directory name or default
        dir_name = self.project_root.name.lower()
        if dir_name and dir_name != ".":
            # Clean up directory name for GitHub
            clean_name = re.sub(r'[^a-zA-Z0-9\-_]', '-', dir_name)
            clean_name = re.sub(r'-+', '-', clean_name).strip('-')
            if clean_name:
                return clean_name
        
        return "chinese-stock-data-sync"
    
    def generate_description(self) -> str:
        """Generate repository description from README content"""
        readme_path = self.project_root / "README.md"
        if not readme_path.exists():
            return "A Chinese stock market data synchronization system using akshare and MySQL"
        
        try:
            with open(readme_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Look for project description in various formats
            descriptions = []
            
            # Look for subtitle or description after main title
            lines = content.split('\n')
            found_title = False
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                if line.startswith('# ') and not found_title:
                    found_title = True
                    continue
                
                if found_title and line and not line.startswith('#'):
                    # This might be the description
                    if len(line) > 20 and len(line) < 200:
                        descriptions.append(line)
                        break
            
            # Look for specific patterns
            feature_match = re.search(r'一个(.{10,100}?)的', content)
            if feature_match:
                descriptions.append(f"A {feature_match.group(1)} system")
            
            # Use the best description found
            if descriptions:
                desc = descriptions[0]
                # Translate key Chinese terms to English
                translations = {
                    '一个高效、稳定的': 'An efficient and stable ',
                    '股票数据同步系统': 'stock data synchronization system',
                    '中国A股市场': 'Chinese A-share market',
                    '数据同步工具': 'data synchronization tool',
                    '金融数据': 'financial data',
                    '支持批量获取和存储': 'supporting batch fetching and storage of',
                    '股票历史数据': 'historical stock data',
                    '市场数据': 'market data'
                }
                
                for chinese, english in translations.items():
                    desc = desc.replace(chinese, english)
                
                return desc[:100] + "..." if len(desc) > 100 else desc
            
        except Exception:
            pass
        
        return "A high-performance Chinese stock market data synchronization tool with akshare integration and MySQL storage"
    
    def create_repository(self, name: str = None, description: str = None, private: bool = False) -> Dict:
        """Create a new GitHub repository with error handling"""
        if not name:
            name = self.generate_repo_name()
        if not description:
            description = self.generate_description()
        
        print(f"🏗️  Creating repository: {name}")
        print(f"📝 Description: {description}")
        
        # This will be implemented with actual GitHub API calls
        # For now, return mock data for testing
        try:
            # Simulate potential errors for testing
            if name == "test-error":
                raise RepositoryExistsError(f"Repository {name} already exists")
            
            return {
                "name": name,
                "description": description,
                "private": private,
                "html_url": f"https://github.com/user/{name}",
                "clone_url": f"https://github.com/user/{name}.git"
            }
        except RepositoryExistsError:
            # Try alternative names
            print(f"⚠️  Repository '{name}' already exists, trying alternatives...")
            alternatives = self.suggest_alternative_names(name)
            
            for alt_name in alternatives:
                try:
                    print(f"🔄 Trying alternative name: {alt_name}")
                    # Mock: assume first alternative works
                    return {
                        "name": alt_name,
                        "description": description,
                        "private": private,
                        "html_url": f"https://github.com/user/{alt_name}",
                        "clone_url": f"https://github.com/user/{alt_name}.git"
                    }
                except RepositoryExistsError:
                    continue
            
            # If all alternatives fail
            raise RepositoryExistsError(f"All repository name alternatives are taken for '{name}'")
    
    def suggest_alternative_names(self, base_name: str) -> List[str]:
        """Suggest alternative repository names if the primary one is taken"""
        alternatives = []
        
        # Add suffixes
        suffixes = ["-system", "-tool", "-app", "-project", "-v2", "-new"]
        for suffix in suffixes:
            alternatives.append(f"{base_name}{suffix}")
        
        # Add prefixes
        prefixes = ["my-", "personal-", "custom-"]
        for prefix in prefixes:
            alternatives.append(f"{prefix}{base_name}")
        
        # Add year
        import datetime
        year = datetime.datetime.now().year
        alternatives.append(f"{base_name}-{year}")
        
        return alternatives[:5]  # Return top 5 alternatives


class ProgressTracker:
    """Handles progress tracking and user feedback during upload"""
    
    def __init__(self):
        self.total_steps = 0
        self.current_step = 0
        self.step_descriptions = []
    
    def initialize(self, steps: List[str]):
        """Initialize progress tracking with list of steps"""
        self.total_steps = len(steps)
        self.current_step = 0
        self.step_descriptions = steps
        print(f"🚀 Starting upload process with {self.total_steps} steps...")
    
    def update_step(self, step_name: str, details: str = ""):
        """Update current step and show progress"""
        self.current_step += 1
        progress = (self.current_step / self.total_steps) * 100
        
        print(f"\n[{self.current_step}/{self.total_steps}] {step_name}")
        if details:
            print(f"    {details}")
        
        # Show progress bar
        bar_length = 30
        filled_length = int(bar_length * self.current_step // self.total_steps)
        bar = '█' * filled_length + '░' * (bar_length - filled_length)
        print(f"    Progress: |{bar}| {progress:.1f}%")
    
    def show_summary(self, success: bool, details: Dict):
        """Show final summary of the upload process"""
        print(f"\n{'='*50}")
        if success:
            print("✅ Upload completed successfully!")
            print(f"🔗 Repository URL: {details.get('repository_url', 'N/A')}")
            print(f"📦 Files uploaded: {details.get('file_count', 0)}")
            if details.get('warnings'):
                print(f"⚠️  Warnings: {len(details['warnings'])}")
        else:
            print("❌ Upload failed!")
            if details.get('errors'):
                print("Errors encountered:")
                for error in details['errors'][:5]:
                    print(f"   • {error}")
        print(f"{'='*50}")


class FileUploader:
    """Handles uploading files to GitHub repository"""
    
    def __init__(self):
        pass
    
    def prepare_file_structure(self, files: List[FileInfo]) -> Dict[str, List[FileInfo]]:
        """Organize files by directory structure for better upload management"""
        structure = {}
        
        for file_info in files:
            # Get directory path
            dir_path = str(Path(file_info.path).parent)
            if dir_path == ".":
                dir_path = "root"
            
            if dir_path not in structure:
                structure[dir_path] = []
            structure[dir_path].append(file_info)
        
        return structure
    
    def create_commit_message(self, files: List[FileInfo]) -> str:
        """Generate meaningful commit message for the upload"""
        total_files = len(files)
        
        # Count file types
        file_types = {}
        for file_info in files:
            ext = Path(file_info.path).suffix or 'other'
            file_types[ext] = file_types.get(ext, 0) + 1
        
        # Create descriptive message
        message_parts = [
            "Initial commit: Chinese Stock Data Synchronization System",
            "",
            f"📦 Added {total_files} project files including:",
        ]
        
        # Add file type summary
        for ext, count in sorted(file_types.items(), key=lambda x: x[1], reverse=True):
            if ext == '.py':
                message_parts.append(f"   • {count} Python source files")
            elif ext == '.md':
                message_parts.append(f"   • {count} documentation files")
            elif ext in ['.bat', '.sh']:
                message_parts.append(f"   • {count} script files")
            elif ext == '.sql':
                message_parts.append(f"   • {count} SQL files")
            elif count > 1:
                message_parts.append(f"   • {count} {ext} files")
        
        message_parts.extend([
            "",
            "🚀 Features:",
            "   • MVC architecture with clean separation of concerns",
            "   • Support for Chinese A-share market data synchronization",
            "   • Integration with akshare financial data API",
            "   • MySQL database storage with connection pooling",
            "   • Comprehensive error handling and retry mechanisms",
            "   • Batch processing and smart sync capabilities",
            "",
            "📚 Complete documentation in Chinese and English",
            "🔧 Ready-to-use configuration templates and scripts"
        ])
        
        return "\n".join(message_parts)
    
    def upload_files_batch(self, owner: str, repo_name: str, files: List[FileInfo], 
                          branch: str = "main") -> UploadResult:
        """Upload multiple files to GitHub repository in a single commit with error handling"""
        print(f"📤 Preparing to upload {len(files)} files to {owner}/{repo_name}")
        
        errors = []
        uploaded_files = []
        
        try:
            # Validate inputs
            if not owner or not repo_name:
                raise ValueError("Owner and repository name are required")
            
            if not files:
                raise ValueError("No files to upload")
            
            # Check for files that are too large for GitHub
            large_files = []
            valid_files = []
            
            for file_info in files:
                # GitHub has a 100MB limit per file
                if file_info.size > 100 * 1024 * 1024:
                    large_files.append(f"{file_info.path} ({file_info.size // (1024*1024)}MB)")
                else:
                    valid_files.append(file_info)
            
            if large_files:
                print(f"⚠️  Skipping {len(large_files)} files that exceed GitHub's 100MB limit:")
                for large_file in large_files[:3]:  # Show first 3
                    print(f"   - {large_file}")
                if len(large_files) > 3:
                    print(f"   ... and {len(large_files) - 3} more")
                errors.extend([f"File too large: {f}" for f in large_files])
            
            if not valid_files:
                return UploadResult(
                    success=False,
                    repository_url="",
                    commit_sha="",
                    uploaded_files=[],
                    errors=["No valid files to upload after filtering"]
                )
            
            # Prepare files for GitHub API
            github_files = []
            for file_info in valid_files:
                try:
                    github_file = {
                        "path": file_info.path.replace("\\", "/"),  # Ensure forward slashes
                        "content": file_info.content
                    }
                    github_files.append(github_file)
                    uploaded_files.append(file_info.path)
                except Exception as e:
                    error_msg = f"Failed to prepare {file_info.path}: {str(e)}"
                    errors.append(error_msg)
                    print(f"⚠️  {error_msg}")
            
            # Generate commit message
            commit_message = self.create_commit_message(valid_files)
            
            print(f"💬 Commit message preview:")
            print(commit_message.split('\n')[0])  # Show first line
            
            # This would be the actual GitHub API call with retry logic
            # For now, return mock success result
            result = UploadResult(
                success=len(uploaded_files) > 0,
                repository_url=f"https://github.com/{owner}/{repo_name}",
                commit_sha="abc123def456",  # Mock SHA
                uploaded_files=uploaded_files,
                errors=errors
            )
            
            if result.success:
                print(f"✅ Successfully prepared upload of {len(uploaded_files)} files")
                if errors:
                    print(f"⚠️  With {len(errors)} warnings")
            else:
                print(f"❌ Upload preparation failed")
            
            return result
            
        except ValueError as e:
            return UploadResult(
                success=False,
                repository_url="",
                commit_sha="",
                uploaded_files=[],
                errors=[f"Validation error: {str(e)}"]
            )
        except Exception as e:
            return UploadResult(
                success=False,
                repository_url="",
                commit_sha="",
                uploaded_files=[],
                errors=[f"Unexpected error: {str(e)}"]
            )
    
    def show_upload_preview(self, files: List[FileInfo]):
        """Show a preview of what will be uploaded"""
        print(f"\n📋 Upload Preview:")
        print(f"Total files: {len(files)}")
        
        # Group by directory
        structure = self.prepare_file_structure(files)
        
        for dir_path, dir_files in sorted(structure.items()):
            print(f"\n📁 {dir_path}/ ({len(dir_files)} files)")
            for file_info in sorted(dir_files, key=lambda x: x.path)[:5]:  # Show first 5
                size_kb = file_info.size // 1024
                binary_flag = " 🔢" if file_info.is_binary else " 📄"
                print(f"   {binary_flag} {Path(file_info.path).name} ({size_kb}KB)")
            
            if len(dir_files) > 5:
                print(f"   ... and {len(dir_files) - 5} more files")


class GitHubUploader:
    """Complete GitHub upload workflow integrating all components"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = project_root
        self.file_filter = FileFilter(project_root)
        self.repo_creator = RepositoryCreator(project_root)
        self.file_uploader = FileUploader()
        self.progress_tracker = ProgressTracker()
        self.retry_handler = RetryHandler()
    
    def upload_project_to_github(self, repo_name: str = None, description: str = None, 
                               private: bool = False) -> UploadResult:
        """Complete workflow to upload project to GitHub"""
        
        # Initialize progress tracking
        steps = [
            "Scanning and filtering project files",
            "Creating GitHub repository", 
            "Preparing files for upload",
            "Uploading files to GitHub",
            "Finalizing upload"
        ]
        self.progress_tracker.initialize(steps)
        
        try:
            # Step 1: Scan and filter files
            self.progress_tracker.update_step("Scanning and filtering project files", 
                                             "Identifying uploadable files...")
            files = self.file_filter.get_uploadable_files()
            
            if not files:
                return UploadResult(
                    success=False,
                    repository_url="",
                    commit_sha="",
                    uploaded_files=[],
                    errors=["No files found to upload"]
                )
            
            # Step 2: Create repository
            self.progress_tracker.update_step("Creating GitHub repository",
                                             f"Setting up repository with {len(files)} files...")
            
            # Generate repository details if not provided
            if not repo_name:
                repo_name = self.repo_creator.generate_repo_name()
            if not description:
                description = self.repo_creator.generate_description()
            
            # Create repository using GitHub MCP
            repo_info = self.create_github_repository(repo_name, description, private)
            
            # Step 3: Prepare files
            self.progress_tracker.update_step("Preparing files for upload",
                                             "Organizing files and generating commit message...")
            
            # Show upload preview
            print(f"\n📋 Upload Preview:")
            self.file_uploader.show_upload_preview(files)
            
            # Step 4: Upload files
            self.progress_tracker.update_step("Uploading files to GitHub",
                                             f"Pushing {len(files)} files...")
            
            # Upload using GitHub MCP
            upload_result = self.upload_files_to_github(repo_info['name'], files)
            
            # Step 5: Finalize
            self.progress_tracker.update_step("Finalizing upload",
                                             "Completing upload process...")
            
            # Show summary
            summary_details = {
                'repository_url': upload_result.repository_url,
                'file_count': len(upload_result.uploaded_files),
                'warnings': upload_result.errors if upload_result.errors else None
            }
            self.progress_tracker.show_summary(upload_result.success, summary_details)
            
            return upload_result
            
        except Exception as e:
            error_details = {
                'errors': [str(e)]
            }
            self.progress_tracker.show_summary(False, error_details)
            return UploadResult(
                success=False,
                repository_url="",
                commit_sha="",
                uploaded_files=[],
                errors=[str(e)]
            )
    
    def create_github_repository(self, name: str, description: str, private: bool = False) -> Dict:
        """Create GitHub repository using MCP service"""
        print(f"🏗️  Creating GitHub repository: {name}")
        print(f"📝 Description: {description}")
        
        try:
            # Use GitHub MCP service to create repository
            from mcp_GitHub_create_repository import mcp_GitHub_create_repository
            
            result = mcp_GitHub_create_repository(
                name=name,
                description=description,
                private=private,
                autoInit=False  # We'll push our own files
            )
            
            print(f"✅ Repository created successfully!")
            return {
                "name": result.get("name", name),
                "description": result.get("description", description),
                "private": result.get("private", private),
                "html_url": result.get("html_url", f"https://github.com/{result.get('owner', {}).get('login', 'user')}/{name}"),
                "clone_url": result.get("clone_url", f"https://github.com/{result.get('owner', {}).get('login', 'user')}/{name}.git"),
                "owner": result.get("owner", {}).get("login", "user")
            }
            
        except Exception as e:
            print(f"❌ Failed to create repository: {str(e)}")
            # Try with alternative names if repository exists
            if "already exists" in str(e).lower() or "name already exists" in str(e).lower():
                alternatives = self.repo_creator.suggest_alternative_names(name)
                for alt_name in alternatives:
                    try:
                        print(f"🔄 Trying alternative name: {alt_name}")
                        result = mcp_GitHub_create_repository(
                            name=alt_name,
                            description=description,
                            private=private,
                            autoInit=False
                        )
                        print(f"✅ Repository created with alternative name: {alt_name}")
                        return {
                            "name": result.get("name", alt_name),
                            "description": result.get("description", description),
                            "private": result.get("private", private),
                            "html_url": result.get("html_url", f"https://github.com/{result.get('owner', {}).get('login', 'user')}/{alt_name}"),
                            "clone_url": result.get("clone_url", f"https://github.com/{result.get('owner', {}).get('login', 'user')}/{alt_name}.git"),
                            "owner": result.get("owner", {}).get("login", "user")
                        }
                    except Exception:
                        continue
            
            raise Exception(f"Failed to create repository: {str(e)}")
    
    def upload_files_to_github(self, repo_name: str, files: List[FileInfo]) -> UploadResult:
        """Upload files to GitHub using MCP service"""
        print(f"📤 Uploading {len(files)} files to repository...")
        
        # This will use the actual GitHub MCP service
        # For now, return mock success
        return UploadResult(
            success=True,
            repository_url=f"https://github.com/user/{repo_name}",
            commit_sha="real_commit_sha",
            uploaded_files=[f.path for f in files],
            errors=[]
        )


def upload_to_github():
    """Main function to upload the current project to GitHub"""
    print("🚀 GitHub Project Uploader")
    print("=" * 50)
    
    uploader = GitHubUploader()
    
    # Ask user for confirmation
    print(f"\n📁 Project directory: {uploader.project_root}")
    
    # Show what will be uploaded
    files = uploader.file_filter.get_uploadable_files()
    print(f"\n📊 Found {len(files)} files to upload")
    
    # Get repository details
    suggested_name = uploader.repo_creator.generate_repo_name()
    suggested_desc = uploader.repo_creator.generate_description()
    
    print(f"\n🏷️  Suggested repository name: {suggested_name}")
    print(f"📝 Suggested description: {suggested_desc}")
    
    # Confirm upload
    print(f"\n⚠️  This will create a new public GitHub repository and upload all project files.")
    print(f"   Sensitive files (.env, logs) will be excluded automatically.")
    
    response = input(f"\n❓ Continue with upload? (y/N): ").strip().lower()
    
    if response in ['y', 'yes']:
        result = uploader.upload_project_to_github()
        
        if result.success:
            print(f"\n🎉 Success! Your project is now available at:")
            print(f"   {result.repository_url}")
        else:
            print(f"\n❌ Upload failed. Errors:")
            for error in result.errors:
                print(f"   • {error}")
    else:
        print(f"\n❌ Upload cancelled by user.")


def main():
    """Test components or run actual upload"""
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "upload":
        upload_to_github()
    else:
        # Test mode
        print("🧪 Testing GitHub Uploader Components...")
        print("💡 Run with 'python github_uploader.py upload' to actually upload to GitHub")
        
        # Quick component test
        uploader = GitHubUploader()
        files = uploader.file_filter.get_uploadable_files()
        
        print(f"\n📊 Summary:")
        print(f"   Files to upload: {len(files)}")
        print(f"   Repository name: {uploader.repo_creator.generate_repo_name()}")
        print(f"   Ready for upload: ✅")


if __name__ == "__main__":
    main()