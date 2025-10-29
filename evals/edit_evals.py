import streamlit as st
import pandas as pd
import os
from datetime import datetime
import io
from streamlit_shortcuts import add_shortcuts, shortcut_button
from streamlit_js_eval import streamlit_js_eval

# Custom CSS to reduce header space
reduce_header_space = """
   <style>
       .block-container {
           padding-top: 1rem;
           padding-bottom: 0rem;
           padding-left: 5rem;
           padding-right: 5rem;
       }
   </style>
"""
st.markdown(reduce_header_space, unsafe_allow_html=True)

# Set page config
st.set_page_config(page_title="Edit Evals CSV", layout="wide")

# File paths
CSV_FILE = "evals.csv"
TEMP_ROW_FILE = ".temp_current_row"


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


def save_current_row_to_temp(current_row):
    """Save the current row number to a temporary file"""
    try:
        with open(TEMP_ROW_FILE, "w") as f:
            f.write(str(current_row))
        return True
    except Exception as e:
        st.error(f"Error saving current row: {e}")
        return False


def load_current_row_from_temp():
    """Load the current row number from temporary file if it exists, then delete the file"""
    if os.path.exists(TEMP_ROW_FILE):
        try:
            with open(TEMP_ROW_FILE, "r") as f:
                current_row = int(f.read().strip())
            # Delete the temporary file after reading
            os.remove(TEMP_ROW_FILE)
            return current_row
        except (ValueError, FileNotFoundError, Exception) as e:
            # If there's any error reading or parsing, clean up the temp file and return None
            try:
                os.remove(TEMP_ROW_FILE)
            except FileNotFoundError:
                pass
            return None
    return None


# Handle form submission
def save_form(form_data, current_row):
    # Load CSV
    df = load_csv()

    if current_row < len(df):
        # Update the DataFrame with form data
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
        return False


def main():
    # Load CSV
    df = load_csv()
    if df is None:
        return

    # Initialize session state
    if "current_row" not in st.session_state:
        # First check if there's a saved row from a reset operation
        saved_row = load_current_row_from_temp()
        if saved_row is not None and 0 <= saved_row < len(df):
            st.session_state.current_row = saved_row
        else:
            # Fallback to original behavior: go to last nonblank row
            st.session_state.current_row = find_last_nonblank_row(df)

    # Columns for eval selector and navigation buttons (outside form)
    col1, col2 = st.columns([4, 1])

    with col1:
        # Eval selector
        selected_row = st.selectbox(
            "Select Eval:",
            range(len(df)),
            index=st.session_state.current_row,
            format_func=lambda x: f"{df.iloc[x]['Number'] if pd.notna(df.iloc[x]['Number']) else 'N/A'}: {str(df.iloc[x]['Prompt'])[:150]}{'...' if len(str(df.iloc[x]['Prompt'])) > 150 else ''}",
        )
        # Change in row selector updates page
        if selected_row != st.session_state.current_row:
            st.session_state.current_row = selected_row
            st.rerun()

    with col2:
        # Navigation buttons
        navcol1, navcol2 = st.columns(2)
        with navcol1:
            if shortcut_button("⬆ Previous", "pageup", use_container_width=True):
                if st.session_state.current_row > 0:
                    # Navigate to the previous row
                    st.session_state.current_row -= 1
                    st.rerun()
        with navcol2:
            if shortcut_button("⬇ Next", "pagedown", use_container_width=True):
                if st.session_state.current_row < len(df) - 1:
                    # Navigate to the next row
                    st.session_state.current_row += 1
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

            # File field
            file = st.text_input(
                "File",
                value=(
                    str(current_data["File"])
                    if pd.notna(current_data["File"])
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
                options=["", "True", "False"],
                index=(
                    1
                    if str(correct_value).upper() == "TRUE"
                    else (2 if str(correct_value).upper() == "FALSE" else 0)
                ),
                help="Select True or False",
            )

            # Note field
            note = st.text_input(
                "Note",
                value=(
                    str(current_data["Note"]) if pd.notna(current_data["Note"]) else ""
                ),
            )

            # Use a container so submit/navigtion buttons are located here instead of bottom of form
            save_container = st.container(border=True)

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

            # Get image filename from current eval number
            current_number = current_data.get("Number")
            if pd.notna(current_number):
                try:
                    image_id = f"{int(current_number):03d}.png"
                except (ValueError, TypeError):
                    image_id = "000.png"  # Fallback for invalid numbers
            else:
                image_id = "000.png"  # Fallback for missing numbers
            # Image viewer for reference plot
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

            # Image viewer for generated plot
            generated_path = os.path.join("generated", image_id)
            if os.path.exists(generated_path):
                st.image(generated_path, width="stretch")
            else:
                st.markdown("🖼️")

        # Date validation
        date_valid, date_error = validate_date(date_str)
        if not date_valid:
            st.error(f"Date Error: {date_error}")

        # Get current form data
        def get_form_data():
            # Extract the Number from the current row in the CSV
            current_number = current_data.get("Number")
            form_data = {
                "Number": current_number,
                "Date": date_str if date_str else None,
                "Source": source if source else None,
                "File": file if file else None,
                "Prompt": prompt if prompt else None,
                "Ref_Code": (ref_code.replace("\n", "\\n") if ref_code else None),
                "Gen_Tool": gen_tool if gen_tool else None,
                "Gen_Code": (gen_code.replace("\n", "\\n") if gen_code else None),
                "Correct": correct == "True" if correct else None,
                "Note": note if note else None,
            }
            return form_data

        # For some reason Streamlit doesn't recognize a form submit button with only one column
        savecol1, savecol2, savecol3 = save_container.columns(3)
        with savecol1:
            if shortcut_form_submit_button("Save", "ctrl+s"):
                # Manual save button
                form_data = get_form_data()
                save_form(form_data, st.session_state.current_row)
                st.rerun()
        with savecol2:
            if shortcut_form_submit_button("Reset", "ctrl+r"):
                # Save current row to temporary file and reload page -
                # this actually resets the form data unlike st.rerun()
                save_current_row_to_temp(st.session_state.current_row)
                streamlit_js_eval(js_expressions="parent.window.location.reload()")
        with savecol3:
            if shortcut_form_submit_button("New", "ctrl+n"):
                # Build a new empty row with next eval number and today's date
                new_row = {col: None for col in df.columns}
                new_row["Number"] = df["Number"].max() + 1
                new_row["Date"] = datetime.now().strftime("%Y-%m-%d")
                if save_form(new_row, len(df)):
                    # Move to the newly added row
                    st.session_state.current_row = len(df)
                    st.rerun()


if __name__ == "__main__":
    main()
