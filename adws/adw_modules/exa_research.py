"""
Exa AI Research module for ML/AI model and technique research.

This module provides helper functions for conducting ML/AI research
using the Exa API during the scoping phase.
"""

import os
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv
from exa_py import Exa

# Load environment variables
load_dotenv()


class ExaResearcher:
    """Helper class for conducting AI/ML research using Exa API."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Exa researcher.

        Args:
            api_key: Exa API key. If None, reads from EXA_API_KEY env var.
        """
        self.api_key = api_key or os.getenv("EXA_API_KEY")
        if not self.api_key:
            raise ValueError("EXA_API_KEY not found. Set it in .env file or pass as argument.")

        self.client = Exa(api_key=self.api_key)

    def research_ml_models(
        self,
        use_case: str,
        problem_type: str = "classification",
        domain: str = "general",
        model: str = "exa-research-fast"
    ) -> str:
        """
        Research ML models for a specific use case.

        Args:
            use_case: Description of the ML use case
            problem_type: Type of ML problem (classification, regression, etc.)
            domain: Domain area (computer vision, NLP, time-series, etc.)
            model: Exa model to use (exa-research-fast or exa-research-deep)

        Returns:
            Research findings as a string
        """
        instructions = f"""
        Research state-of-the-art machine learning models for the following use case:

        **Use Case:** {use_case}
        **Problem Type:** {problem_type}
        **Domain:** {domain}

        For the top 3-5 recommended models, provide:
        1. Model name and architecture
        2. Performance benchmarks (accuracy, speed, resource requirements)
        3. Pre-trained models available (HuggingFace, AWS Marketplace, etc.)
        4. Links to papers and implementations
        5. Suitable AWS services (SageMaker, Bedrock, etc.)

        Focus on production-ready models suitable for deployment in 2025.
        """

        return self._execute_research(instructions, model)

    def research_data_techniques(
        self,
        data_type: str,
        challenge: str,
        model: str = "exa-research-fast"
    ) -> str:
        """
        Research data science techniques for specific data challenges.

        Args:
            data_type: Type of data (images, text, time-series, tabular, etc.)
            challenge: Specific challenge (small dataset, imbalanced, noisy, etc.)
            model: Exa model to use

        Returns:
            Research findings as a string
        """
        instructions = f"""
        Research data science techniques for handling:

        **Data Type:** {data_type}
        **Challenge:** {challenge}

        Provide:
        1. Data preprocessing best practices
        2. Data augmentation techniques
        3. Feature engineering approaches
        4. Handling imbalanced/noisy data
        5. Practical Python implementations
        6. Recent research papers (2023-2025)

        Include code examples and benchmarks where available.
        """

        return self._execute_research(instructions, model)

    def research_mlops_practices(
        self,
        deployment_target: str = "AWS SageMaker",
        model: str = "exa-research-fast"
    ) -> str:
        """
        Research MLOps best practices for model deployment and monitoring.

        Args:
            deployment_target: Target deployment platform
            model: Exa model to use

        Returns:
            Research findings as a string
        """
        instructions = f"""
        Research MLOps best practices for deploying ML models on {deployment_target}.

        Cover:
        1. Model deployment strategies (real-time, batch, serverless)
        2. Model monitoring and drift detection
        3. A/B testing and experimentation
        4. CI/CD pipelines for ML
        5. Cost optimization techniques
        6. Model versioning and registry
        7. Retraining pipelines

        Focus on production-ready, scalable architectures with cost estimates.
        """

        return self._execute_research(instructions, model)

    def research_aws_services(
        self,
        use_case: str,
        services_of_interest: Optional[List[str]] = None,
        model: str = "exa-research-fast"
    ) -> str:
        """
        Research AWS services and architectures for specific use case.

        Args:
            use_case: Description of the use case
            services_of_interest: List of AWS services to research
            model: Exa model to use

        Returns:
            Research findings as a string
        """
        services_str = ", ".join(services_of_interest) if services_of_interest else "any relevant AWS services"

        instructions = f"""
        Research AWS architecture and services for:

        **Use Case:** {use_case}
        **Services of Interest:** {services_str}

        Provide:
        1. Recommended AWS services and why
        2. Architecture patterns and best practices
        3. Cost estimates (monthly for typical workloads)
        4. Performance characteristics
        5. Example implementations or case studies
        6. CDK construct libraries available

        Focus on AWS Well-Architected Framework principles.
        """

        return self._execute_research(instructions, model)

    def research_custom(
        self,
        instructions: str,
        model: str = "exa-research-fast",
        stream: bool = True
    ) -> str:
        """
        Execute custom research with user-provided instructions.

        Args:
            instructions: Research instructions
            model: Exa model to use (exa-research-fast or exa-research-deep)
            stream: If True, stream results; else return complete result

        Returns:
            Research findings as a string
        """
        return self._execute_research(instructions, model, stream)

    def _execute_research(
        self,
        instructions: str,
        model: str = "exa-research-fast",
        stream: bool = True
    ) -> str:
        """
        Internal method to execute research and return results.

        Args:
            instructions: Research instructions
            model: Exa model to use
            stream: If True, stream results

        Returns:
            Research findings as a string
        """
        # Create research task
        research = self.client.research.create(
            instructions=instructions,
            model=model,
        )

        # Get results
        full_result = ""
        if stream:
            for event in self.client.research.get(research.research_id, stream=True):
                full_result += str(event)
        else:
            result = self.client.research.get(research.research_id, stream=False)
            full_result = str(result)

        return full_result


# Convenience functions for quick access
def research_ml_models(use_case: str, problem_type: str = "classification", domain: str = "general") -> str:
    """Quick function to research ML models."""
    researcher = ExaResearcher()
    return researcher.research_ml_models(use_case, problem_type, domain)


def research_data_techniques(data_type: str, challenge: str) -> str:
    """Quick function to research data techniques."""
    researcher = ExaResearcher()
    return researcher.research_data_techniques(data_type, challenge)


def research_mlops_practices(deployment_target: str = "AWS SageMaker") -> str:
    """Quick function to research MLOps practices."""
    researcher = ExaResearcher()
    return researcher.research_mlops_practices(deployment_target)


def research_aws_services(use_case: str, services_of_interest: Optional[List[str]] = None) -> str:
    """Quick function to research AWS services."""
    researcher = ExaResearcher()
    return researcher.research_aws_services(use_case, services_of_interest)


# Example usage
if __name__ == "__main__":
    # Test the researcher
    researcher = ExaResearcher()

    print("Testing Exa Researcher...\n")

    # Test ML model research
    result = researcher.research_ml_models(
        use_case="Real-time fraud detection in financial transactions",
        problem_type="classification",
        domain="anomaly detection"
    )

    print("Research Result:")
    print(result)
