from google.adk.plugins.save_files_as_artifacts_plugin import SaveFilesAsArtifactsPlugin
from google.adk.runners import InMemoryRunner
from google.genai import types as genai_types
from PlotMyData.agent import root_agent
from datetime import datetime
from pathlib import Path
import asyncio
import json
import csv
import sys
import os


async def run_eval(
    runner,
    eval_number: int,
    prompt: str,
    session_dir: str,
    generated_dir: str,
    csv_file: str,
):
    """
    Run an ADK eval with the given prompt and save results.

    Args:
        eval_number: The eval number
        prompt: The prompt to send to the agent
        session_dir: Directory to save session data
        generated_dir: Directory to save generated artifacts
        csv_file: Path to the CSV file to update
    """

    # Format eval number with leading zeros
    eval_str = f"{eval_number:03d}"
    session_file = os.path.join(session_dir, f"{eval_str}.json")
    artifact_file = os.path.join(generated_dir, f"{eval_str}.png")

    # Prepare the user's message in ADK format
    content = genai_types.Content(role="user", parts=[genai_types.Part(text=prompt)])

    # Set up the session service
    user_id = "eval_user"
    session = await runner.session_service.create_session(
        app_name=runner.app_name, user_id=user_id
    )

    print(f"Running eval {eval_number}: {prompt[:100]}...")

    event_history = []
    tool_calls = []
    gen_code = []

    try:

        # Send the prompt and get response
        print("Sending prompt to agent...")

        # run_async executes the agent logic and yields events
        async for event in runner.run_async(
            user_id=session.user_id, session_id=session.id, new_message=content
        ):
            # Append events to event history
            event_history.append(
                f"[Event] Author: {event.author}, Type: {type(event).__name__}, Final: {event.is_final_response()}, Content: {event.content}"
            )

            # Parse event content to extract tool calls
            if hasattr(event, "content") and event.content:
                for part in event.content.parts:
                    if hasattr(part, "function_call") and part.function_call:
                        fc = part.function_call
                        tool_name = fc.name

                        # Skip transfer_to_agent
                        if tool_name == "transfer_to_agent":
                            continue

                        # Record tool name
                        tool_calls.append(tool_name)

                        # Extract code based on tool type
                        if tool_name in [
                            "run_hidden",
                            "run_visible",
                            "make_plot",
                            "make_ggplot",
                        ]:
                            # Extract code from 'code' argument
                            if hasattr(fc, "args") and "code" in fc.args:
                                gen_code.append(f"# {tool_name}\n{fc.args['code']}")
                            else:
                                gen_code.append(f"# {tool_name}\n")
                        else:
                            # For other tools (help_package, help_topic, etc), put all args as comments
                            if hasattr(fc, "args") and fc.args:
                                # Format args nicely - use repr to get proper string representation
                                args_items = []
                                for key, value in fc.args.items():
                                    args_items.append(f"'{key}': {repr(value)}")
                                args_str = "\n".join(f"# {item}" for item in args_items)
                                gen_code.append(f"# {tool_name}\n{args_str}")
                            else:
                                gen_code.append(f"# {tool_name}")

            # Notify if final response was received
            if event.is_final_response():
                print("Final response received")

        # Get the artifact keys
        artifact_keys = await runner.artifact_service.list_artifact_keys(
            app_name=runner.app_name, user_id=session.user_id, session_id=session.id
        )
        print(f"artifact keys: {artifact_keys}")

        # Save the last PNG artifact (if any)
        artifact_filename = f"{eval_str}.png"
        artifact_path = os.path.join(generated_dir, artifact_filename)
        if artifact_keys:
            artifact = await runner.artifact_service.load_artifact(
                app_name=runner.app_name,
                user_id=session.user_id,
                session_id=session.id,
                filename=artifact_keys[-1],
            )
            if artifact.inline_data.mime_type.startswith("image/"):
                # Write the file
                try:
                    byte_data = artifact.inline_data.data
                    with open(artifact_path, "wb") as f:
                        f.write(byte_data)
                    print(f"Artifact saved to {artifact_path}")
                except Exception as e:
                    print(f"Warning: Could not save artifact: {e}")
        else:
            # If no artifact was generated, then delete an existing PNG file
            if os.path.exists(artifact_path):
                os.remove(artifact_path)
                print(f"No artifact generated; {artifact_path} has been deleted")

        # Use this to avoid error with MCP stdio tools:
        # RuntimeError: Attempted to exit cancel scope in a different task than it was entered in
        # https://github.com/google/adk-python/issues/929
        await runner.close()

        # Save session data
        session_data = {
            "eval_number": eval_number,
            "prompt": prompt,
            "events": event_history,
            "artifacts": artifact_keys,
        }

        with open(session_file, "w", encoding="utf-8") as f:
            json.dump(session_data, f, indent=2, ensure_ascii=False)

        print(f"Session saved to {session_file}")

        # Update CSV with results
        update_csv_results(csv_file, eval_number, tool_calls, gen_code)

    except Exception as e:
        print(f"Error running eval: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        # Save error to session file anyway
        session_data = {
            "eval_number": eval_number,
            "prompt": prompt,
            "error": str(e),
        }
        with open(session_file, "w", encoding="utf-8") as f:
            json.dump(session_data, f, indent=2, ensure_ascii=False)
        return 1

    return 0


def get_prompt_from_csv(eval_number: int, csv_file: str) -> str:
    """Read the Prompt column from evals.csv for the given eval number."""
    with open(csv_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                if int(row["Number"]) == eval_number:
                    return row["Prompt"]
            except (ValueError, KeyError):
                continue
    raise ValueError(f"Eval number {eval_number} not found in {csv_file}")


def update_csv_results(
    csv_file: str, eval_number: int, tool_calls: list, gen_code: list
):
    """Update the CSV file with eval results."""
    try:
        # Read all rows
        rows = []
        with open(csv_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames
            for row in reader:
                rows.append(row)

        # Update the row for this eval number
        for row in rows:
            try:
                if int(row["Number"]) == eval_number:
                    # Update Date column
                    row["Date"] = datetime.now().strftime("%Y-%m-%d")

                    # Update Gen_Tool column
                    tool_calls_str = ", ".join(tool_calls)
                    row["Gen_Tool"] = tool_calls_str

                    # Update Gen_Code column
                    gen_code_str = "\n\n".join(gen_code)
                    row["Gen_Code"] = gen_code_str
                    break
            except (ValueError, KeyError):
                continue

        # Write updated rows back to file
        with open(csv_file, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

        print(f"CSV updated with results for eval {eval_number}")
    except Exception as e:
        print(f"Error updating CSV: {e}", file=sys.stderr)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <eval_number>", file=sys.stderr)
        sys.exit(1)

    try:
        eval_number = int(sys.argv[1])
    except ValueError:
        print(f"Error: Invalid eval number: {sys.argv[1]}", file=sys.stderr)
        sys.exit(1)

    # Get paths
    csv_file = os.path.join("evals", "evals.csv")
    session_dir = os.path.join("evals", "sessions")
    generated_dir = os.path.join("evals", "generated")

    # Ensure directories exist
    Path(session_dir).mkdir(parents=True, exist_ok=True)
    Path(generated_dir).mkdir(parents=True, exist_ok=True)

    # Read prompt from CSV
    try:
        prompt = get_prompt_from_csv(eval_number, csv_file)
        if not prompt or not prompt.strip():
            print(
                f"Error: Prompt is empty for eval number {eval_number}", file=sys.stderr
            )
            sys.exit(1)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Create a runner instance
    runner = InMemoryRunner(agent=root_agent, plugins=[SaveFilesAsArtifactsPlugin()])
    # Start the asynchronous event loop and run the eval
    exit_code = asyncio.run(
        run_eval(runner, eval_number, prompt, session_dir, generated_dir, csv_file)
    )

    sys.exit(exit_code)
