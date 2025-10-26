import streamlit as st
import pandas as pd
import os
from datetime import datetime
import io
from streamlit_shortcuts import add_shortcuts

# Set page config
st.set_page_config(page_title="Edit Evals CSV", layout="wide")

# File path
CSV_FILE = "evals.csv"


def shortcut_form_submit_button(
    label: str, shortcut: str | list[str], hint: bool = True, **kwargs
) -> bool:  # noqa: FBT002 (boolean positional arg)
    """
    This is streamlit_shortcuts.shortcut_button modified to use
    st.form_submit_button instead of st.button  20251025 jmd

    Streamlit button with a keyboard shortcut.

    Args:
        label: Button text (can be empty string)
        shortcut: Single shortcut or list of shortcuts like 'ctrl+s', ['arrowleft', 'a'], etc.
        hint: Show shortcut hint in button label (default: True)
        **kwargs: All other st.button args (key, type, disabled, use_container_width, etc.)

    Returns:
        bool: True if button was clicked (same as st.button)
    """
    assert label is not None, "Button label cannot be None"
    assert shortcut, "Shortcut parameter is required"

    # Generate key if not provided
    shortcut_str = shortcut if isinstance(shortcut, str) else str(shortcut)
    if "key" not in kwargs:
        kwargs["key"] = f"btn_{hash(label + shortcut_str) % 10000000}"

    # Add hint to label if requested
    if hint and label:
        if isinstance(shortcut, str):
            button_label = f"{label} `{shortcut}`"
        else:
            # For multiple shortcuts, show them separated by " or "
            button_label = f"{label} `{' or '.join(shortcut)}`"
    else:
        button_label = label

    # Create button WITHOUT hint parameter
    clicked = st.form_submit_button(button_label, **kwargs)

    # Add the shortcut
    add_shortcuts(**{kwargs["key"]: shortcut})

    return clicked


def load_csv():
    """Load the CSV file and return as DataFrame"""
    try:
        df = pd.read_csv(CSV_FILE)
        return df
    except FileNotFoundError:
        st.error(f"File {CSV_FILE} not found!")
        return None
    except Exception as e:
        st.error(f"Error loading CSV: {e}")
        return None


def find_last_nonblank_row(df):
    """Find the last row where both Date and Prompt are non-empty.

    Returns the index of the last completed row. If all rows are blank,
    returns 0 to start at the first row.
    """
    for idx in range(len(df) - 1, -1, -1):
        row = df.iloc[idx]
        date_filled = pd.notna(row.get("Date")) and str(row.get("Date")).strip() != ""
        prompt_filled = (
            pd.notna(row.get("Prompt")) and str(row.get("Prompt")).strip() != ""
        )
        if date_filled and prompt_filled:
            return idx
    return 0


def validate_date(date_str):
    """Validate date format YYYY-MM-DD"""
    if not date_str:
        return True, ""
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True, ""
    except ValueError:
        return False, "Date must be in YYYY-MM-DD format"


def validate_boolean(bool_str):
    """Validate boolean format TRUE/FALSE"""
    if not bool_str:
        return True, ""
    if bool_str.upper() in ["TRUE", "FALSE"]:
        return True, ""
    return False, "Must be TRUE or FALSE"


# Handle form submission
def save_form(form_data, current_row):
    # Load CSV
    df = load_csv()

    # Update the DataFrame with form data
    if current_row < len(df):
        for col, value in form_data.items():
            df.loc[current_row, col] = value
    else:
        # Add a new row
        df = pd.concat([df, pd.DataFrame([form_data])], ignore_index=True)

    # Save to CSV
    try:
        df.to_csv(CSV_FILE, index=False)
        st.success("Changes saved successfully!")
        return True
    except Exception as e:
        st.error(f"Error saving CSV: {e}")
        st.error("Failed to save changes!")
        return False


def main():
    # Load CSV
    df = load_csv()
    if df is None:
        return

    # Initialize session state
    if "current_row" not in st.session_state:
        st.session_state.current_row = find_last_nonblank_row(df)

    # Row selector (outside form)
    selected_row = st.selectbox(
        "Select Row:",
        range(len(df)),
        index=st.session_state.current_row,
        format_func=lambda x: f"{x + 1}: {str(df.iloc[x]['Prompt'])[:50]}{'...' if len(str(df.iloc[x]['Prompt'])) > 50 else ''}",
    )

    # Change in row selector updates page without saving current row
    if selected_row != st.session_state.current_row:
        # Update current row
        st.session_state.current_row = selected_row
        # Force a rerun to update the page
        st.rerun()

    # Load current row data
    current_data = df.iloc[st.session_state.current_row].to_dict()

    # Form for editing row data
    with st.form("edit_row_form", enter_to_submit=False, border=False):

        # Create three columns for better layout
        col1, col2, col3 = st.columns(3)

        with col1:
            # Date field
            date_value = current_data["Date"] if pd.notna(current_data["Date"]) else ""
            date_str = st.text_input(
                "Date (YYYY-MM-DD)",
                value=str(date_value) if date_value else "",
                help="Enter date in YYYY-MM-DD format",
            )

            # Source field
            source = st.text_input(
                "Source",
                value=(
                    str(current_data["Source"])
                    if pd.notna(current_data["Source"])
                    else ""
                ),
            )

            # Prompt field
            prompt = st.text_area(
                "Prompt",
                value=(
                    str(current_data["Prompt"])
                    if pd.notna(current_data["Prompt"])
                    else ""
                ),
                height=100,
            )

            # Gen_Tool field
            gen_tool = st.text_input(
                "Gen_Tool",
                value=(
                    str(current_data["Gen_Tool"])
                    if pd.notna(current_data["Gen_Tool"])
                    else ""
                ),
            )

            # Correct field
            correct_value = (
                current_data["Correct"] if pd.notna(current_data["Correct"]) else ""
            )
            correct = st.selectbox(
                "Correct",
                options=["", "TRUE", "FALSE"],
                index=(
                    1
                    if str(correct_value).upper() == "TRUE"
                    else (2 if str(correct_value).upper() == "FALSE" else 0)
                ),
                help="Select TRUE or FALSE",
            )

            # Note field
            note = st.text_input(
                "Note",
                value=(
                    str(current_data["Note"]) if pd.notna(current_data["Note"]) else ""
                ),
            )

            # Use a container so submit/navigtion buttons are located here instead of bottom of form
            container = st.container(border=True)

        with col2:
            # Ref_Code field
            ref_code = st.text_area(
                "Ref_Code",
                value=(
                    str(current_data["Ref_Code"]).replace("\\n", "\n")
                    if pd.notna(current_data["Ref_Code"])
                    else ""
                ),
                height=200,
            )

            # Image viewer for Reference image
            row_num_display = st.session_state.current_row + 1
            image_id = f"{row_num_display:03d}.png"
            reference_path = os.path.join("reference", image_id)
            if os.path.exists(reference_path):
                st.image(reference_path, width="stretch")
            else:
                st.markdown("🖼️")

        with col3:
            # Gen_Code field
            gen_code = st.text_area(
                "Gen_Code",
                value=(
                    str(current_data["Gen_Code"]).replace("\\n", "\n")
                    if pd.notna(current_data["Gen_Code"])
                    else ""
                ),
                height=200,
            )

            # Image viewer for Generate image
            generated_path = os.path.join("generated", image_id)
            if os.path.exists(generated_path):
                st.image(generated_path, width="stretch")
            else:
                st.markdown("🖼️")

        # Validation
        date_valid, date_error = validate_date(date_str)
        correct_valid, correct_error = validate_boolean(correct)

        if not date_valid:
            st.error(f"Date Error: {date_error}")
        if not correct_valid:
            st.error(f"Correct Error: {correct_error}")

        # Get current form data
        def get_form_data():
            form_data = {
                "Number": st.session_state.current_row + 1,
                "Date": date_str if date_str else None,
                "Source": source if source else None,
                "Prompt": prompt if prompt else None,
                "Ref_Code": (ref_code.replace("\n", "\\n") if ref_code else None),
                "Gen_Tool": gen_tool if gen_tool else None,
                "Gen_Code": (gen_code.replace("\n", "\\n") if gen_code else None),
                "Correct": correct if correct else None,
                "Note": note if note else None,
            }
            return form_data

        # Navigation buttons
        navcol1, navcol2 = container.columns(2)
        with navcol1:
            if shortcut_form_submit_button("⬆ Previous", "pageup"):
                form_data = get_form_data()
                save_form(form_data, st.session_state.current_row)
                if st.session_state.current_row > 0:
                    # Navigate to the previous row
                    st.session_state.current_row -= 1
                    st.rerun()
        with navcol2:
            if shortcut_form_submit_button("⬇ Next", "pagedown"):
                form_data = get_form_data()
                save_form(form_data, st.session_state.current_row)
                if st.session_state.current_row < len(df) - 1:
                    # Navigate to the next row
                    st.session_state.current_row += 1
                    st.rerun()
                else:
                    # We are on the last row; add a new row if current row is complete
                    current = df.iloc[st.session_state.current_row]
                    date_filled = (
                        pd.notna(current.get("Date"))
                        and str(current.get("Date")).strip() != ""
                    )
                    prompt_filled = (
                        pd.notna(current.get("Prompt"))
                        and str(current.get("Prompt")).strip() != ""
                    )

                    if date_filled and prompt_filled:
                        # Build a new empty row with today's date
                        new_row = {col: None for col in form_data}
                        new_row["Number"] = len(df) + 1
                        new_row["Date"] = datetime.now().strftime("%Y-%m-%d")
                        if save_form(new_row, st.session_state.current_row + 1):
                            # Move to the newly added row
                            st.session_state.current_row += 1
                            st.rerun()


if __name__ == "__main__":
    main()
