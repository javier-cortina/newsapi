"""
Pytest configuration and fixtures for testing the news pipeline.

This module provides reusable fixtures for loading test data and mocking Dagster components.
"""

import json
import pytest
import pandas as pd
from pathlib import Path
from unittest.mock import Mock
from dagster import OpExecutionContext, build_op_context


@pytest.fixture
def sample_news_data():
    """
    Load sample news data from the fixtures JSON file.
    
    Returns:
        list: List of dictionaries containing sample news articles
    """
    fixtures_path = Path(__file__).parent / "fixtures" / "sample_news.json"
    with open(fixtures_path, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def sample_news_df(sample_news_data):
    """
    Convert sample news data to a pandas DataFrame.
    
    Returns:
        pd.DataFrame: DataFrame with sample news articles
    """
    return pd.DataFrame(sample_news_data)


@pytest.fixture
def valid_articles_df(sample_news_data):
    """
    Create a DataFrame with only valid articles (first 3 articles).
    
    Returns:
        pd.DataFrame: DataFrame with valid news articles only
    """
    valid_articles = sample_news_data[:3]
    return pd.DataFrame(valid_articles)


@pytest.fixture
def invalid_articles_df(sample_news_data):
    """
    Create a DataFrame with invalid articles (articles 4-6).
    
    Returns:
        pd.DataFrame: DataFrame with invalid articles (no title, no body, [Removed])
    """
    invalid_articles = sample_news_data[3:6]
    return pd.DataFrame(invalid_articles)


@pytest.fixture
def duplicate_articles_df(sample_news_data):
    """
    Create a DataFrame with duplicate URLs (articles 7-8).
    
    Returns:
        pd.DataFrame: DataFrame with duplicate articles
    """
    duplicate_articles = sample_news_data[6:8]
    return pd.DataFrame(duplicate_articles)


@pytest.fixture
def mock_dagster_context():
    """
    Create a mock Dagster OpExecutionContext for testing.
    
    Returns:
        OpExecutionContext: Mocked Dagster context with logging capabilities
    """
    context = build_op_context(
        resources={
            "io_manager": Mock(),
            "duckdb": Mock(),
        }
    )
    return context


@pytest.fixture
def empty_dataframe():
    """
    Create an empty DataFrame with the expected news schema.
    
    Returns:
        pd.DataFrame: Empty DataFrame with correct column structure
    """
    return pd.DataFrame(columns=["title", "url", "body", "dateTime", "source"])


@pytest.fixture
def mock_eventregistry_response():
    """
    Create a mock response from EventRegistry API.
    
    Returns:
        dict: Mocked API response structure
    """
    return {
        "articles": {
            "results": [
                {
                    "uri": "article-1",
                    "title": "Test Article 1",
                    "body": "Test content 1",
                    "url": "https://example.com/article-1",
                    "dateTime": "2024-12-15T10:00:00Z",
                    "source": {
                        "uri": "example.com",
                        "title": "Example News"
                    }
                }
            ]
        }
    }
