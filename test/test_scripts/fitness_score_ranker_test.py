import pytest
import os
import sys
sys.path.insert(0, os.getcwd())
import json
from shutil import rmtree
from scripts.fitness_score_ranker import load_fitness_function, test_images


def mock_fitness_function(image):
    """Mock fitness function that returns 0.5 for all images."""
    return 0.5

def test_test_images():
    # Define mock arguments
    fitness_function_path = 'path/to/your/mock_fitness_function.py'  # Replace with actual path
    zip_path = 'path/to/sample.zip'  # Replace with actual sample ZIP file path
    output_path = 'test_output'
    
    # Call the function under test
    fitness_function, fitness_function_name = load_fitness_function(fitness_function_path)
    test_images(fitness_function, zip_path, output_path)
    
    # Verify that the output directories are created
    assert os.path.exists(output_path)
    for score in range(11):
        assert os.path.exists(os.path.join(output_path, f"{score / 10:.1f}"))
    
    # Verify that the JSON file is created and has content
    json_path = os.path.join(output_path, 'fitness_scores.json')
    assert os.path.exists(json_path)
    
    with open(json_path, 'r') as f:
        json_data = json.load(f)
    assert "fitness_function_name" in json_data
    assert "images" in json_data
    
    # Clean up
    rmtree(output_path)

