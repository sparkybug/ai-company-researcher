from __future__ import annotations

import time
from apify import Actor
from crewai import Agent, Crew, Task

from src.tools import (
    WebsiteScraperTool,
    CrunchbaseScraperTool,
    LinkedInScraperTool
)
from src.utils.report_generator import generate_pdf_report
from src.utils.visuals import plot_funding_timeline

def handle_rate_limit():
    """Handle rate limit error by pausing execution."""
    Actor.log.info("Rate limit exceeded, retrying in 60 seconds...")
    time.sleep(60)  # Sleep for a minute before retrying
    return True  # Indicate retry attempt

async def main() -> None:
    """Main function executed by Apify Actor."""
    async with Actor:
        # Charge for Actor start event
        await Actor.charge('actor-start')

        # Handle and validate input
        actor_input = await Actor.get_input()
        company_name = actor_input.get('company_name')
        model_name = actor_input.get('modelName', 'gpt-4o-mini')
        report_depth = actor_input.get('report_depth', 'summary')  # Added depth for user customization

        if not company_name:
            raise ValueError('Missing "company_name" attribute in input!')

        # Initialize tools for data retrieval and processing
        tools = [
            WebsiteScraperTool(),
            CrunchbaseScraperTool(),
            LinkedInScraperTool()
        ]

        # Define the AI Agent
        agent = Agent(
            role='Business Intelligence Researcher',
            goal='Collect and analyze detailed company data for actionable insights.',
            backstory=(
                'I specialize in business intelligence, researching companies to reveal insights about their focus areas, '
                'products, funding history, executives, competitors, and online presence for strategic decision-making.'
            ),
            tools=tools,
            verbose=True,
            llm=model_name,
        )

        # Define the task for the agent
        task = Task(
            description=f'Gather comprehensive data about the company "{company_name}" including focus areas, products, funding, key personnel, competitors, and social media presence.',
            expected_output='A detailed, structured report with insights about the company.',
            agent=agent,
        )

        # Assemble and execute the AI Crew
        crew = Crew(agents=[agent], tasks=[task])
        
        try:
            crew_output = crew.kickoff()  # Try to execute the task
        except Exception as e:
            if "RateLimitError" in str(e):  # Check if it's a rate limit error
                if handle_rate_limit():  # Call the rate limit handler
                    crew_output = crew.kickoff()  # Retry the task
            else:
                raise e  # Raise other exceptions normally

        raw_response = crew_output.raw

        # Log token usage
        Actor.log.info(f'Total tokens used: {crew_output.token_usage.total_tokens}')

        # Charge for task completion event
        await Actor.charge('task-completed')

        # Generate the report and visualizations
        if report_depth == 'detailed':
            generate_pdf_report(raw_response, output_path=f"{company_name}_report.pdf")
            plot_funding_timeline(raw_response.get('funding_timeline', []), company_name)

        # Push results to the dataset
        await Actor.push_data({
            'company_name': company_name,
            'response': raw_response,
        })
        Actor.log.info('Company research data pushed to the dataset successfully!')