#!/usr/bin/env python3
"""
Example usage of the WebFAQMCP tool for medical information retrieval.

This script demonstrates how to use the PubMed search functionality
to get medical information in different formats.
"""

import pubmed
from tools import get_medical_faq
from main import get_medical_faq as api_get_medical_faq


def example_direct_pubmed_search():
    """Example of using the PubMed API directly"""
    print("=" * 60)
    print("Example 1: Direct PubMed Search")
    print("=" * 60)
    
    query = "pregnancy morning sickness treatment"
    print(f"Searching for: '{query}'")
    print()
    
    try:
        results = pubmed.search_and_fetch(query, max_results=2)
        
        if results:
            for i, result in enumerate(results, 1):
                print(f"{i}. {result.question}")
                print(f"   Answer: {result.answer}")
                if result.sources:
                    print(f"   URL: {result.sources[0].url}")
                print()
        else:
            print("No results found.")
            
    except Exception as e:
        print(f"Error: {e}")


def example_direct_results():
    """Example of getting direct PubMed results"""
    print("=" * 60)
    print("Example 2: Direct PubMed Results")
    print("=" * 60)
    
    query = "postpartum depression symptoms"
    print(f"Getting direct results for: '{query}'")
    print()
    
    try:
        results = pubmed.search_and_fetch(query, max_results=2)
        
        if results:
            print(f"Found {len(results)} results:")
            print()
            
            for i, result in enumerate(results, 1):
                print(f"Result {i}:")
                print(f"  Question: {result.question}")
                print(f"  Answer: {result.answer[:100]}...")
                if result.sources:
                    print(f"  URL: {result.sources[0].url}")
                print()
        else:
            print("No results found.")
            
    except Exception as e:
        print(f"Error: {e}")


def example_formatted_faq():
    """Example of getting formatted FAQ response"""
    print("=" * 60)
    print("Example 3: Formatted FAQ Response")
    print("=" * 60)
    
    query = "What are the warning signs of preeclampsia?"
    print(f"Getting FAQ for: '{query}'")
    print()
    
    try:
        response = get_medical_faq(query)
        print(response)
        
    except Exception as e:
        print(f"Error: {e}")


def example_api_function():
    """Example of using the API function directly"""
    print("=" * 60)
    print("Example 4: API Function Usage")
    print("=" * 60)
    
    query = "cardiac rehabilitation exercise guidelines"
    print(f"Using API function for: '{query}'")
    print()
    
    try:
        response = api_get_medical_faq(query)
        print(response)
        
    except Exception as e:
        print(f"Error: {e}")


def interactive_example():
    """Interactive example allowing user input"""
    print("=" * 60)
    print("Interactive Example")
    print("=" * 60)
    print("Enter medical questions (type 'quit' to exit):")
    print()
    
    while True:
        try:
            query = input("Your question: ").strip()
            
            if query.lower() in ['quit', 'exit', 'q']:
                print("Goodbye!")
                break
                
            if not query:
                continue
                
            print("\nSearching PubMed...")
            response = get_medical_faq(query)
            print("\n" + "─" * 50)
            print(response)
            print("─" * 50 + "\n")
            
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")


def main():
    """Run all examples"""
    print("WebFAQMCP - Medical Information Retrieval Examples")
    print("=" * 60)
    print()
    
    # Run all examples
    example_direct_pubmed_search()
    example_direct_results()
    example_formatted_faq()
    example_api_function()
    
    # Ask if user wants interactive mode
    print("\n" + "=" * 60)
    choice = input("Would you like to try the interactive mode? (y/n): ").strip().lower()
    
    if choice in ['y', 'yes']:
        interactive_example()
    else:
        print("Examples completed!")


if __name__ == "__main__":
    main() 