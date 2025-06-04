import os
import shutil
from datetime import datetime
import tempfile
from pathlib import Path
import logging
from docxtpl import DocxTemplate  # For template validation

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FileManager:
    def __init__(self, base_dir=None):
        """Initialize FileManager with a base directory for operations"""
        if base_dir is None:
            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        self.base_dir = base_dir
        self.temp_dir = os.path.join(base_dir, '.tmp')
        self.outputs_dir = os.path.join(base_dir, 'outputs')
        self.template_dir = os.path.join(base_dir, 'template')
        self._ensure_directories()
        self._ensure_default_template()

    def _ensure_directories(self):
        """Ensure required directories exist"""
        for directory in [self.temp_dir, self.outputs_dir, self.template_dir]:
            if not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)

    def get_temp_filename(self, prefix='', suffix=''):
        """Generate a temporary filename in the temp directory"""
        return os.path.join(self.temp_dir, f"{prefix}{datetime.now().strftime('%Y%m%d_%H%M%S')}{suffix}")

    def save_uploaded_file(self, uploaded_file, directory='temp', prefix=''):
        """Save an uploaded file and return its path"""
        if directory == 'temp':
            target_dir = self.temp_dir
        elif directory == 'outputs':
            target_dir = self.outputs_dir
        elif directory == 'templates':
            target_dir = self.template_dir
        else:
            raise ValueError(f"Invalid directory: {directory}")

        filename = os.path.join(target_dir, f"{prefix}{uploaded_file.name}")
        
        try:
            with open(filename, 'wb') as f:
                f.write(uploaded_file.getbuffer())
            return filename
        except Exception as e:
            logger.error(f"Error saving uploaded file: {e}")
            raise

    def cleanup_temp_files(self, max_age_hours=24):
        """Clean up temporary files older than max_age_hours"""
        try:
            now = datetime.now()
            cleaned = 0
            
            for item in os.listdir(self.temp_dir):
                item_path = os.path.join(self.temp_dir, item)
                if not os.path.isfile(item_path):
                    continue
                    
                file_time = datetime.fromtimestamp(os.path.getctime(item_path))
                age_hours = (now - file_time).total_seconds() / 3600
                
                if age_hours > max_age_hours:
                    try:
                        os.remove(item_path)
                        cleaned += 1
                    except Exception as e:
                        logger.error(f"Error deleting temp file {item}: {e}")
                        
            logger.info(f"Cleaned up {cleaned} temporary files")
            return cleaned
        except Exception as e:
            logger.error(f"Error during temp file cleanup: {e}")
            return 0

    def save_output_file(self, content, filename, overwrite=False):
        """Save content to an output file"""
        filepath = os.path.join(self.outputs_dir, filename)
        
        if os.path.exists(filepath) and not overwrite:
            base, ext = os.path.splitext(filename)
            counter = 1
            while os.path.exists(filepath):
                new_filename = f"{base}_{counter}{ext}"
                filepath = os.path.join(self.outputs_dir, new_filename)
                counter += 1
                
        try:
            with open(filepath, 'wb' if isinstance(content, bytes) else 'w') as f:
                f.write(content)
            return filepath
        except Exception as e:
            logger.error(f"Error saving output file: {e}")
            raise

    def _ensure_default_template(self):
        """Ensure default template exists"""
        default_template = os.path.join(self.template_dir, 'cv_template.docx')
        if not os.path.exists(default_template):
            logger.warning("Default template not found at: %s", default_template)
            return None
        return default_template

    def get_default_template(self):
        """Get the path to the default template"""
        return os.path.join(self.template_dir, 'cv_template.docx')

    def validate_template(self, template_path):
        """Validate that a template file has the correct structure"""
        try:
            doc = DocxTemplate(template_path)
            content = doc.get_docx().element.body.xml
            required_vars = ['summary', 'experience', 'education', 'skills']
            found_vars = []
            for var in required_vars:
                if f'{{{{ {var} }}}}' in content:
                    found_vars.append(var)
            
            if not found_vars:
                raise ValueError("Template must contain at least one CV section variable")
                
            missing = set(required_vars) - set(found_vars)
            if missing:
                logger.warning(f"Template missing recommended variables: {', '.join(missing)}")
            
            return True
        except Exception as e:
            logger.error(f"Template validation failed: {e}")
            return False

    def save_template(self, uploaded_file):
        """Save an uploaded template file after validation"""
        try:
            temp_path = self.save_uploaded_file(uploaded_file, 'temp', prefix='template_')
            if not self.validate_template(temp_path):
                os.remove(temp_path)
                raise ValueError("Invalid template structure")
                
            template_path = os.path.join(self.template_dir, uploaded_file.name)
            shutil.move(temp_path, template_path)
            logger.info(f"Template saved successfully: {template_path}")
            return template_path
        except Exception as e:
            logger.error(f"Error saving template: {e}")
            raise

    def list_templates(self):
        """List all available templates"""
        try:
            templates = []
            for file in os.listdir(self.template_dir):
                if file.endswith('.docx'):
                    templates.append(file)
            return sorted(templates)
        except Exception as e:
            logger.error(f"Error listing templates: {e}")
            return []