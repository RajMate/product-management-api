import os
import sys
import subprocess
from pybuilder.core import use_plugin, init, Author, task

# Core plugins
use_plugin("python.core")
use_plugin("python.unittest")
use_plugin("python.install_dependencies")
use_plugin("python.coverage")
use_plugin("python.distutils")

# Project information
name = "product_management"
version = "1.0.0"
summary = "FastAPI Product Management API"
description = "A RESTful API for managing products using FastAPI and SQLAlchemy"
authors = [Author("Project Team", "")]
license = "MIT"
url = "https://gitlab.com/your-group/product-management"
default_task = "custom_test"

@init
def set_properties(project):
    # Source directories
    project.set_property("dir_source_main_python", "src/main/python")
    project.set_property("dir_source_unittest_python", "src/unittest/python")
    
    # Dependencies
    project.depends_on("fastapi")
    project.depends_on("sqlalchemy")
    project.depends_on("python-dotenv")
    project.depends_on("pydantic")
    project.depends_on("uvicorn")
    project.build_depends_on("httpx")
    
    # Test settings
    project.set_property("dir_source_unittest_python", "src/unittest/python")
    project.set_property("unittest_module_glob", "test_*")
    project.set_property("unittest_test_method_prefix", "test")
    # Remove deprecated unittest_file_suffix
    project.set_property("unittest_test_file_glob", "test_*.py")
    # Skip test discovery and use explicit modules
    project.set_property("unittest_test_method_prefix", "test")
    
    # Coverage settings
    project.set_property("coverage_break_build", False)
    project.set_property("coverage_threshold_warn", 90)
    project.set_property("coverage_branch", True)
    project.set_property("coverage_html", True)
    project.set_property("coverage_xml", True)
    
    # Distribution settings
    project.set_property("distutils_console_scripts", ["product-api = app:run_app"])
    
    # Package structure settings - ensure src directory is included
    project.set_property("distutils_packages", ["src", "src.main", "src.main.python"])
    project.set_property("distutils_readme_description", True)
    project.set_property("distutils_description_overwrite", True)
    project.set_property("distutils_commands", ["sdist", "bdist_wheel"])
    
    # Build settings
    project.set_property("dir_dist", "target/dist")
    project.set_property("dir_reports", "target/reports")
    
    # Debug settings
    project.set_property("verbose", True)
    project.set_property("unittest_always_verbose", True)
    project.set_property("unittest_output_on_failure", True)

@task
def custom_test(project, logger):
    """Run unit tests with explicit output"""
    logger.info("Running tests with explicit output...")
    
    # Set up environment for better output
    os.environ["PYTHONUNBUFFERED"] = "1"
    os.environ["PYBUILDER_DEBUG"] = "1"
    
    # Run unittest directly with subprocess
    test_dir = os.path.join(os.getcwd(), "src", "unittest", "python")
    cmd = [sys.executable, "-m", "unittest", "discover", "-v", test_dir]
    
    logger.info(f"Running command: {' '.join(cmd)}")
    
    try:
        # Run the tests and capture output
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        
        # Print the output
        print("\n===== TEST OUTPUT =====\n")
        print(result.stdout)
        
        if result.stderr:
            print("\n===== TEST ERRORS =====\n")
            print(result.stderr)
        
        # Run coverage
        logger.info("Running coverage...")
        coverage_cmd = [sys.executable, "-m", "coverage", "run", "-m", "unittest", "discover", test_dir]
        subprocess.run(coverage_cmd, check=True)
        
        # Generate coverage reports
        subprocess.run([sys.executable, "-m", "coverage", "report", "-m"], check=True)
        subprocess.run([sys.executable, "-m", "coverage", "html"], check=True)
        subprocess.run([sys.executable, "-m", "coverage", "xml"], check=True)
        
        logger.info("Tests completed successfully")
        logger.info("Coverage reports available in htmlcov/index.html and coverage.xml")
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Tests failed with exit code {e.returncode}")
        print("\n===== TEST OUTPUT =====\n")
        print(e.stdout)
        print("\n===== TEST ERRORS =====\n")
        print(e.stderr)
        raise Exception("Tests failed") from e
    
    # Test settings
    project.set_property('unittest_module_glob', 'test_*.py')
    project.set_property('unittest_test_method_prefix', 'test')
    project.set_property('unittest_file_suffix', '.py')
    project.set_property('unittest_test_file_glob', 'test_*.py')
    
    # Coverage settings
    project.set_property('coverage_threshold_warn', 90)
    project.set_property('coverage_break_build', False)
    project.set_property('coverage_reset_modules', True)
    project.set_property('coverage_exceptions', ['__init__'])
    project.set_property('coverage_html', True)
    project.set_property('coverage_xml', True)
    
    # Distribution settings
    project.set_property('distutils_readme_description', True)
    project.set_property('distutils_description_overwrite', True)
    project.set_property('distutils_upload_skip_existing', True)
    project.set_property('distutils_console_scripts', ['product-api = app:run_app'])
    
    # Package structure settings - ensure src directory is included
    project.set_property('distutils_packages', ['src', 'src.main', 'src.main.python'])
    
    # Build settings
    project.set_property('dir_dist', 'dist')
    project.set_property('dir_reports', 'reports')
    project.set_property('unittest_test_method_prefix', 'test')
    project.set_property('unittest_parallel', True)  # Run tests in parallel
    
    # Distutils Settings
    project.set_property('distutils_commands', ['bdist_wheel'])
    project.set_property('distutils_classifiers', [
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Framework :: FastAPI',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Topic :: Internet :: WWW/HTTP :: HTTP Servers',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ])
    
    # Skip certain files from coverage
    project.set_property("coverage_exceptions", [
        "__init__",
    ])