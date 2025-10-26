import streamlit as st
import pandas as pd
import os
from datetime import datetime
import io
from streamlit_shortcuts import shortcut_button

# Set page config
st.set_page_config(page_title="Edit Examples CSV", layout="wide")

# File path
CSV_FILE = "examples.csv"


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


def save_csv(df):
    """Save the DataFrame to CSV file"""
    try:
        df.to_csv(CSV_FILE, index=False)
        return True
    except Exception as e:
        st.error(f"Error saving CSV: {e}")
        return False


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


def navigate_to_previous_row(df):
    """Navigate to the previous row"""
    if st.session_state.current_row > 0:
        # Save current form data before switching
        save_current_form_data(df)
        st.session_state.current_row -= 1
        st.session_state.form_data = {}
        st.rerun()


def navigate_to_next_row(df):
    """Navigate to the next row"""
    if st.session_state.current_row < len(df) - 1:
        # Save current form data before switching
        save_current_form_data(df)
        st.session_state.current_row += 1
        st.session_state.form_data = {}
        st.rerun()
    else:
        # We are on the last row; optionally add a new row if current row is complete
        save_current_form_data(df)

        current = df.iloc[st.session_state.current_row]
        date_filled = (
            pd.notna(current.get("Date")) and str(current.get("Date")).strip() != ""
        )
        prompt_filled = (
            pd.notna(current.get("Prompt")) and str(current.get("Prompt")).strip() != ""
        )

        if date_filled and prompt_filled:
            # Build a new empty row with today's date
            new_row = {col: None for col in df.columns}
            if "Number" in df.columns:
                new_row["Number"] = len(df) + 1
            new_row["Date"] = datetime.now().strftime("%Y-%m-%d")

            df_new = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            if save_csv(df_new):
                # Move to the newly added row
                st.session_state.current_row += 1
                st.session_state.form_data = {}
                st.rerun()


def save_current_form_data(df):
    """Save current form data to the DataFrame"""
    if "form_data" in st.session_state and st.session_state.form_data:
        for col, value in st.session_state.form_data.items():
            df.loc[st.session_state.current_row, col] = value
        save_csv(df)


def main():
    # Load CSV
    df = load_csv()
    if df is None:
        return

    # Initialize session state
    if "current_row" not in st.session_state:
        st.session_state.current_row = find_last_nonblank_row(df)
    if "form_data" not in st.session_state:
        st.session_state.form_data = {}

    # Create three columns for better layout
    col1, col2, col3 = st.columns(3)

    with col1:
        # Row selector
        selected_row = st.selectbox(
            "Select Row:",
            range(len(df)),
            index=st.session_state.current_row,
            format_func=lambda x: f"{x + 1}: {str(df.iloc[x]['Prompt'])[:50]}{'...' if len(str(df.iloc[x]['Prompt'])) > 50 else ''}",
        )

        # Save current form data
        if selected_row != st.session_state.current_row:
            for col in df.columns:
                if col in st.session_state.form_data:
                    df.loc[st.session_state.current_row, col] = (
                        st.session_state.form_data[col]
                    )

            if save_csv(df):
                st.success("Changes saved!")
            else:
                st.error("Failed to save changes!")
                return

            # Update current row
            st.session_state.current_row = selected_row
            st.session_state.form_data = {}
            # Force a rerun to update the selectbox display
            st.rerun()

        # Load current row data
        current_data = df.iloc[st.session_state.current_row].to_dict()

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
                str(current_data["Source"]) if pd.notna(current_data["Source"]) else ""
            ),
        )

        # Prompt field
        prompt = st.text_area(
            "Prompt",
            value=(
                str(current_data["Prompt"]) if pd.notna(current_data["Prompt"]) else ""
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
            value=str(current_data["Note"]) if pd.notna(current_data["Note"]) else "",
        )

        innercol1, innercol2 = st.columns(2)

        with innercol1:
            if shortcut_button("⬆ Previous", "pageup"):
                navigate_to_previous_row(df)
        with innercol2:
            if shortcut_button("⬇ Next", "pagedown"):
                navigate_to_next_row(df)

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

    # Update form data in session state
    st.session_state.form_data = {
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

    # Manual save button
    if st.button("Save Changes", type="primary"):
        # Update the DataFrame
        for col, value in st.session_state.form_data.items():
            df.loc[st.session_state.current_row, col] = value

        if save_csv(df):
            st.success("Changes saved successfully!")
        else:
            st.error("Failed to save changes!")


if __name__ == "__main__":
    main()
