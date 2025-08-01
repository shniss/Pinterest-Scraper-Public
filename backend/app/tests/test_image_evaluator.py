#!/usr/bin/env python3
"""
Test script for image_evaluator.py
Run with: python test_image_evaluator.py
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.automation.image_evaluator import (
    split_prompt_by_nouns_and_adjectives,
    create_image_evaluation_prompt,
    score_image_against_prompt,
)


def test_prompt_splitting():
    """Test the prompt splitting function"""
    print("=== Testing Prompt Splitting ===")

    test_prompts = [
        "boho minimalist bedroom",
        "modern scandinavian kitchen",
        "industrial vintage living room",
        "cozy cottage garden",
        "luxury minimalist bathroom",
    ]

    for prompt in test_prompts:
        style, obj = split_prompt_by_nouns_and_adjectives(prompt)
        print(f"Prompt: '{prompt}'")
        print(f"  Style: '{style}'")
        print(f"  Object: '{obj}'")
        print()


def test_prompt_creation():
    """Test the prompt creation function"""
    print("=== Testing Prompt Creation ===")

    prompt = "boho minimalist bedroom"
    image_url = (
        "https://i.pinimg.com/1200x/b4/c0/20/b4c020bd95d85cd2ea5e4a0932bc8013.jpg"
    )
    style, obj = split_prompt_by_nouns_and_adjectives(prompt)

    evaluation_prompt = create_image_evaluation_prompt(prompt, image_url, style, obj)

    print(f"Original prompt: {prompt}")
    print(f"Image URL: {image_url}")
    print(f"Style phrase: {style}")
    print(f"Object phrase: {obj}")
    print(f"Evaluation prompt created: {len(evaluation_prompt)} keys")
    print(f"Model: {evaluation_prompt['model']}")
    print(f"Temperature: {evaluation_prompt['temperature']}")
    print()


def test_image_scoring():
    """Test the image scoring function"""
    print("=== Testing Image Scoring ===")

    prompt = "boho minimalist bedroom"
    test_images = [
        "https://i.pinimg.com/736x/4c/5f/a8/4c5fa81ed9899a9e3acea93a56816c9e.jpg",
        "https://i.pinimg.com/736x/42/24/9a/42249a353f1b866408c141138561242d.jpg",
        "https://i.pinimg.com/1200x/ae/48/67/ae486742c4b06e4d3975160d419282df.jpg",
    ]

    for i, image_url in enumerate(test_images, 1):
        print(f"Testing image {i}: {image_url}")
        try:
            score, details = score_image_against_prompt(image_url, prompt)
            print(f"  Final Score: {score:.2f}")
            print(f"  Object Score: {details['object_score']:.2f}")
            print(f"  Style Score: {details['style_score']:.2f}")
            print(f"  Explanation: {details['explanation']}")
        except Exception as e:
            print(f"  Error: {e}")
        print()


def main():
    """Run all tests"""
    print("Image Evaluator Test Suite")
    print("=" * 50)

    # Test 1: Prompt splitting
    test_prompt_splitting()

    # Test 2: Prompt creation
    test_prompt_creation()

    # Test 3: Image scoring (requires OpenAI API key)
    print("Note: Image scoring test requires OpenAI API key to be set")
    response = input("Do you want to test image scoring? (y/n): ").lower().strip()

    if response == "y":
        test_image_scoring()
    else:
        print("Skipping image scoring test")

    print("Test suite completed!")


if __name__ == "__main__":
    main()
