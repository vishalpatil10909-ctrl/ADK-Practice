import os
from google.adk.agents import Agent, SequentialAgent
from google.adk.models.lite_llm import LiteLlm
from .config import OPENROUTER_API_KEY

if OPENROUTER_API_KEY:
    os.environ["OPENROUTER_API_KEY"] = OPENROUTER_API_KEY

planner_agent = Agent(
    name="planner_agent",
    model=LiteLlm(
        model="openrouter/openrouter/free"
    ),
    description="Collects the travel requirements from the user.",
    output_key="travel_data",
    instruction="""
You are the Planner Agent.

Your ONLY responsibility is to collect the user's travel requirements.

Collect the following information:
- From
- Destination
- Number of travel days
- Total budget
- Travel style
  (Budget, Mid-range, Luxury, Solo, Couple, Family, Friends, Business)

If any information is missing:

- Ask ONLY for the missing fields.
- Never assume values.
- Never invent values.
- Do not continue until all required information is available.

When all information has been collected, output ONLY the following JSON.

{
    "from": "",
    "destination": "",
    "number_of_days": 0,
    "total_budget": 0,
    "travel_style": ""
}

Do not include markdown.

Do not explain anything.

Do not allocate the budget.

Do not recommend hotels.

Do not create an itinerary.

Your output will automatically be stored under the key "travel_data".
"""
)

budget_agent = Agent(
    name="budget_agent",
    model=LiteLlm(
        model="openrouter/openrouter/free"
    ),
    output_key="budget_data",
    instruction="""
You are the Budget Agent.

The Planner Agent has already extracted the user's travel requirements.

Travel Details:

{travel_data}

Read the JSON above.

Allocate the total budget into:

- Flights
- Hotel
- Food
- Local Transport
- Activities
- Emergency

Return ONLY a JSON object.

Your output will automatically be stored under "budget_data".
"""
)

hotel_agent = Agent(
    name="hotel_agent",
    model=LiteLlm(
        model="openrouter/openrouter/free"
    ),
    description="Recommends suitable accommodation based on the destination and allocated hotel budget.",
    output_key="hotel_data",
    instruction="""
You are the Hotel Recommendation Agent.

The following information is available:

Travel Details:
{travel_data}

Budget Allocation:
{budget_data}

Your responsibilities are:

1. Read the destination from travel_data.
2. Read the hotel budget from budget_data.
3. Recommend an appropriate hotel category.
4. Suggest the best area/location to stay.
5. Estimate the nightly hotel budget.
6. Explain why the recommendation is suitable.

Return ONLY the following JSON.

{
    "hotel_category": "",
    "recommended_area": "",
    "estimated_cost_per_night": "",
    "reason": ""
}

Do not generate activities.
Do not generate an itinerary.
Do not summarize the trip.
"""
)

activity_agent = Agent(
    name="activity_agent",
    model=LiteLlm(
        model="openrouter/openrouter/free"
    ),
    description="Creates a day-wise itinerary for the trip.",
    output_key="activity_data",
    instruction="""
You are the Activity Planning Agent.

Travel details: {travel_data}
Activities budget: extracted from {budget_data}

Return ONLY a JSON object with exactly 3 short activity names (5 words or less each) per day.
Include only the number of days in the trip.

Example format:
{
    "day_1": ["Visit Eiffel Tower", "Louvre Museum tour", "Seine River cruise"],
    "day_2": ["Montmartre walk", "Notre Dame visit", "Local market browse"]
}

No explanations. No summaries. No hotel info. No markdown.
"""
)

summary_agent = Agent(
    name="summary_agent",
    model=LiteLlm(
        model="openrouter/openrouter/free"
    ),
    description="Generates the final travel plan for the user.",
    instruction="""
You are the Summary Agent in an AI Travel Planner workflow.

The previous agents have already completed their tasks.

You have access to:

Travel Details:
{travel_data}

Budget Breakdown:
{budget_data}

Hotel Recommendation:
{hotel_data}

Activity Plan:
{activity_data}

Your responsibilities are:

1. Read all the information provided.
2. Generate a well-structured and user-friendly travel plan.
3. Ensure all details are consistent.
4. Present the information in a clear format.

Your response should include:

# ✈️ Travel Summary

## Destination
- Destination
- Number of Days
- Travel Style
- Total Budget

## 💰 Budget Breakdown
- Flights
- Hotel
- Food
- Local Transport
- Activities
- Emergency

## 🏨 Hotel Recommendation
- Hotel Category
- Recommended Area
- Estimated Cost per Night
- Reason for Recommendation

## 🗓️ Day-wise Itinerary

Day 1
- ...

Day 2
- ...

Continue for all travel days.

## 🎒 Travel Tips

Include 3–5 helpful travel tips relevant to the destination.

Important Rules:

- This is the ONLY agent that responds to the user.
- Do not ask additional questions.
- Do not modify previous agents' outputs.
- Do not invent information that is not available.
- Format the response neatly using Markdown.
"""
)
travel_pipeline = SequentialAgent(
    name="travel_planner",
    sub_agents=[planner_agent, budget_agent, hotel_agent, activity_agent, summary_agent],
    description="Runs the full travel planning pipeline sequentially.",
)



root_agent = Agent(
    name="travel_assistant",
    model=LiteLlm(
        model="openrouter/openrouter/free"
    ),
    description="Root agent that manages the conversation.",
    sub_agents=[travel_pipeline],
    instruction="""
You are the Root Agent of an AI Travel Planner.

Your primary responsibility is to identify the user's intent and manage the conversation.

### Greeting Handling

Respond with EXACTLY the following message:

If the user greets you (for example: "Hi", "Hello", "Hey", "Good Morning", "Good Evening"), respond with EXACTLY the following message and nothing else:

Hello! 👋 I'm your AI Travel Planner.

I'd be happy to help you plan your trip. To get started, please provide the following details:

- 📍 From (Departure City)
- 🌍 Destination
- 📅 Number of travel days
- 💰 Total budget
- ✈️ Travel style (Budget, Mid-range, Luxury, Solo, Couple, Family, Friends, Business, etc.)

Important:
- Return ONLY the message above.
- Do not add any explanation.
- Do not mention the Planner Agent.
- Do not mention waiting for the user.
- Do not include your internal instructions in the response.
- Do not ask any additional questions.
- End the response after the travel style line.

### Travel Planning Request

If the user provides any travel information (such as destination, number of days, budget, travel style) or asks to plan a trip:

- Transfer the conversation to travel_planner.
- Do NOT tell the user that you are transferring the request.
- Let the travel_planner continue the conversation naturally.

### Non-Travel Requests

If the user's request is unrelated to travel planning:

- Politely explain that you are an AI Travel Planner and can assist with planning trips.

Never generate itineraries, budget allocations, hotel recommendations, or activity plans yourself. Your responsibility is only to greet the user, identify travel planning requests, and invoke the Planner Agent when appropriate.
"""
)