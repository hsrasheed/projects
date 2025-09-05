from __future__ import annotations

import asyncio
from dataclasses import dataclass
from pydantic import BaseModel, Field
from agents import Agent, ItemHelpers, Runner, TResponseInputItem, trace

"""
This example shows the LLM as a judge pattern. The first agent generates an outline for a story.
The second agent judges the outline and provides feedback. We loop until the judge is satisfied
with the outline.
"""

story_outline_generator = Agent(
    name="story_outline_generator",
    instructions=(
        "You generate a very short story outline based on the user's input."
        "If there is any feedback provided, use it to improve the outline."
    ),
    model="gpt-4o-mini",
)


class EvaluationFeedback(BaseModel):
    """The feedback from the evaluator on the story outline."""
    feedback: str
    # score: Literal["pass", "needs_improvement", "fail"]
    score: int = Field(
        description="Score for the outline, 0-10. 0 means fail, ge 7 means pass.",
        ge=0,
        le=10,
    )

evaluator = Agent[None](
    name="evaluator",
    instructions=(
        "You evaluate a story outline and decide if it's good enough."
        "If it's not good enough, you provide feedback on what needs to be improved."
        "Never give it a pass on the first try."
    ),
    output_type=EvaluationFeedback,
    model="gpt-4o-mini",
)


async def main() -> None:
    msg = input("What kind of story would you like to hear? ")
    input_items: list[TResponseInputItem] = [{"content": msg, "role": "user"}]

    latest_outline: str | None = None
    num_iterations: int = 0

    # We'll run the entire workflow in a single trace
    with trace("LLM as a judge"):
        while True and num_iterations < 5:
            num_iterations += 1
            print(f"Iteration {num_iterations}")
            story_outline_result = await Runner.run(
                story_outline_generator,
                input_items,
            )

            input_items = story_outline_result.to_input_list()
            latest_outline = ItemHelpers.text_message_outputs(story_outline_result.new_items)
            print("Story outline generated")

            evaluator_result = await Runner.run(evaluator, input_items)
            result: EvaluationFeedback = evaluator_result.final_output

            print(f"Evaluator score: {result.score}")

            if result.score >= 7:
                print("Story outline is good enough, exiting.")
                break

            print("Re-running with feedback")

            input_items.append({"content": f"Feedback: {result.feedback}", "role": "user"})

    print(f"Final story outline: {latest_outline}")


if __name__ == "__main__":
    asyncio.run(main())
