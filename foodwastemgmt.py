import streamlit as st

# ------------------------------------------------------------
# 1. CONSTANTS (tuples and lists)
# ------------------------------------------------------------
CATEGORIES = ("Cooked Food", "Fruits", "Vegetables", "Bakery", "Dairy", "Packaged Food")
UNITS = ["kg", "plates", "packets", "litres", "pieces"]
WASTE_REASONS = ["Expired", "Spoiled", "Over-cooked", "Leftover", "Damaged"]

# Approximate meals one unit can feed (dictionary)
MEALS_PER_UNIT = {
    "kg": 4,
    "plates": 1,
    "packets": 2,
    "litres": 3,
    "pieces": 1,
}

# ------------------------------------------------------------
# 2. SESSION STATE (our in-memory "database")
# Streamlit reruns the script on every click, so we store data
# in st.session_state so it is not lost.
# ------------------------------------------------------------
if "donations" not in st.session_state:
    # A list of dictionaries - each dictionary is one food donation
    st.session_state.donations = [
        {"id": 1, "donor": "Hotel Sunrise", "item": "Veg Biryani", "category": "Cooked Food",
         "quantity": 20, "unit": "plates", "hours_left": 5, "location": "Salt Lake", "status": "Available"},
        {"id": 2, "donor": "Fresh Mart", "item": "Bananas", "category": "Fruits",
         "quantity": 10, "unit": "kg", "hours_left": 30, "location": "Park Street", "status": "Available"},
    ]

if "waste_log" not in st.session_state:
    st.session_state.waste_log = []

if "next_id" not in st.session_state:
    st.session_state.next_id = 3


# ------------------------------------------------------------
# 3. HELPER FUNCTIONS
# ------------------------------------------------------------
def add_donation(donor, item, category, quantity, unit, hours_left, location):
    """Create a new donation dictionary and add it to the list."""
    new_donation = {
        "id": st.session_state.next_id,
        "donor": donor,
        "item": item,
        "category": category,
        "quantity": quantity,
        "unit": unit,
        "hours_left": hours_left,
        "location": location,
        "status": "Available",
    }
    st.session_state.donations.append(new_donation)
    st.session_state.next_id += 1


def get_available_donations():
    """Return only the donations that have not been claimed yet."""
    available = []
    for donation in st.session_state.donations:
        if donation["status"] == "Available":
            available.append(donation)
    return available


def claim_donation(donation_id, ngo_name):
    """Mark a donation as claimed by an NGO."""
    for donation in st.session_state.donations:
        if donation["id"] == donation_id:
            donation["status"] = "Claimed"
            donation["claimed_by"] = ngo_name
            return True
    return False


def get_urgency(hours_left):
    """Return an urgency label based on how many hours are left."""
    if hours_left <= 6:
        return "🔴 Urgent"
    elif hours_left <= 24:
        return "🟠 Soon"
    else:
        return "🟢 Fresh"


def estimate_meals(quantity, unit):
    """Estimate how many people this food can feed."""
    return quantity * MEALS_PER_UNIT.get(unit, 1)


def log_waste(item, category, quantity, unit, reason):
    """Record food that was thrown away."""
    entry = {
        "item": item,
        "category": category,
        "quantity": quantity,
        "unit": unit,
        "reason": reason,
    }
    st.session_state.waste_log.append(entry)


def count_by_key(records, key):
    """Count how many times each value of a key appears.
    Example: count_by_key(waste_log, 'reason') -> {'Expired': 2, 'Spoiled': 1}
    """
    counts = {}
    for record in records:
        value = record[key]
        if value in counts:
            counts[value] += 1
        else:
            counts[value] = 1
    return counts


def calculate_stats():
    """Calculate summary numbers for the dashboard."""
    total = len(st.session_state.donations)
    claimed = 0
    meals_saved = 0

    for donation in st.session_state.donations:
        if donation["status"] == "Claimed":
            claimed += 1
            meals_saved += estimate_meals(donation["quantity"], donation["unit"])

    wasted_entries = len(st.session_state.waste_log)

    return {
        "total": total,
        "available": total - claimed,
        "claimed": claimed,
        "meals_saved": meals_saved,
        "wasted": wasted_entries,
    }


# ------------------------------------------------------------
# 4. PAGES (each page is a function)
# ------------------------------------------------------------
def dashboard_page():
    st.header("📊 Dashboard")
    stats = calculate_stats()

    col1, col2, col3 = st.columns(3)
    col1.metric("Total donations", stats["total"])
    col2.metric("Available now", stats["available"])
    col3.metric("Claimed by NGOs", stats["claimed"])

    col4, col5 = st.columns(2)
    col4.metric("Meals saved (approx.)", stats["meals_saved"])
    col5.metric("Waste entries logged", stats["wasted"])

    st.subheader("Donations by category")
    category_counts = count_by_key(st.session_state.donations, "category")
    if category_counts:
        st.bar_chart(category_counts)
    else:
        st.info("No donations yet. Add one from the 'Donate food' page.")


def donate_page():
    st.header("🍱 Donate food")
    st.write("Restaurants, hotels, shops or households can list surplus food here.")

    donor = st.text_input("Donor name")
    item = st.text_input("Food item")
    category = st.selectbox("Category", CATEGORIES)

    col1, col2 = st.columns(2)
    quantity = col1.number_input("Quantity", min_value=1, value=1, step=1)
    unit = col2.selectbox("Unit", UNITS)

    hours_left = st.slider("Hours until food goes bad", 1, 72, 12)
    location = st.text_input("Pickup location")

    if st.button("Add donation"):
        # Simple validation using conditionals
        if donor.strip() == "" or item.strip() == "" or location.strip() == "":
            st.error("Fill in donor name, food item and pickup location.")
        else:
            add_donation(donor.strip(), item.strip(), category, int(quantity),
                         unit, hours_left, location.strip())
            meals = estimate_meals(int(quantity), unit)
            st.success(f"Donation added. It can feed about {meals} people.")


def available_food_page():
    st.header("📋 Available food")
    available = get_available_donations()

    if len(available) == 0:
        st.info("No food is available right now.")
        return

    # Filter options
    selected_category = st.selectbox("Filter by category", ["All"] + list(CATEGORIES))
    sort_urgent = st.checkbox("Show most urgent first", value=True)

    # Filter using a loop
    filtered = []
    for donation in available:
        if selected_category == "All" or donation["category"] == selected_category:
            filtered.append(donation)

    # Sort using a function as key
    if sort_urgent:
        filtered.sort(key=lambda d: d["hours_left"])

    # Build a table (list of dictionaries) for display
    table = []
    for d in filtered:
        table.append({
            "ID": d["id"],
            "Item": d["item"],
            "Category": d["category"],
            "Quantity": f"{d['quantity']} {d['unit']}",
            "Donor": d["donor"],
            "Location": d["location"],
            "Hours left": d["hours_left"],
            "Urgency": get_urgency(d["hours_left"]),
        })

    if table:
        st.table(table)
    else:
        st.warning("No food found in this category.")


def claim_page():
    st.header("🤝 Claim food (for NGOs)")
    available = get_available_donations()

    if not available:
        st.info("Nothing to claim right now.")
        return

    ngo_name = st.text_input("NGO / receiver name")

    # Build a dictionary to map readable labels -> donation id
    options = {}
    for d in available:
        label = f"#{d['id']} - {d['item']} ({d['quantity']} {d['unit']}) from {d['donor']}"
        options[label] = d["id"]

    choice = st.selectbox("Choose food to claim", list(options.keys()))

    if st.button("Claim food"):
        if ngo_name.strip() == "":
            st.error("Enter your NGO name before claiming.")
        else:
            if claim_donation(options[choice], ngo_name.strip()):
                st.success(f"Claimed by {ngo_name}. Please pick it up soon.")
            else:
                st.error("Could not find that donation.")

    # Show claimed history
    st.subheader("Claimed history")
    history = []
    for d in st.session_state.donations:
        if d["status"] == "Claimed":
            history.append({
                "Item": d["item"],
                "Quantity": f"{d['quantity']} {d['unit']}",
                "Donor": d["donor"],
                "Claimed by": d.get("claimed_by", "-"),
            })
    if history:
        st.table(history)
    else:
        st.write("No food claimed yet.")


def waste_log_page():
    st.header("🗑️ Waste log")
    st.write("Record food that had to be thrown away, so you can find patterns and reduce it.")

    item = st.text_input("Wasted item")
    category = st.selectbox("Category", CATEGORIES, key="waste_category")
    col1, col2 = st.columns(2)
    quantity = col1.number_input("Quantity", min_value=1, value=1, step=1, key="waste_qty")
    unit = col2.selectbox("Unit", UNITS, key="waste_unit")
    reason = st.selectbox("Reason", WASTE_REASONS)

    if st.button("Log waste"):
        if item.strip() == "":
            st.error("Enter the name of the wasted item.")
        else:
            log_waste(item.strip(), category, int(quantity), unit, reason)
            st.success("Waste logged.")

    if st.session_state.waste_log:
        st.subheader("All waste entries")
        st.table(st.session_state.waste_log)

        st.subheader("Waste by reason")
        reason_counts = count_by_key(st.session_state.waste_log, "reason")
        st.bar_chart(reason_counts)

        # Find the most common reason using a loop
        top_reason = ""
        top_count = 0
        for r, c in reason_counts.items():
            if c > top_count:
                top_reason = r
                top_count = c
        st.info(f"Most common reason: **{top_reason}** ({top_count} times). "
                f"See the Tips page for ideas to reduce it.")


def tips_page():
    st.header("💡 Tips to reduce food waste")
    tips = {
        "Expired": ["Use first-in, first-out (FIFO) storage.",
                    "Check expiry dates every morning."],
        "Spoiled": ["Store food at the right temperature.",
                    "Keep fruits and vegetables separate."],
        "Over-cooked": ["Cook in smaller batches.",
                        "Track how much is eaten each day and adjust."],
        "Leftover": ["Donate extra food within a few hours.",
                     "Reuse leftovers in new dishes the next day."],
        "Damaged": ["Handle and pack food carefully.",
                    "Check deliveries before accepting them."],
    }

    for reason, tip_list in tips.items():
        with st.expander(reason):
            for tip in tip_list:
                st.write(f"- {tip}")


# ------------------------------------------------------------
# 5. MAIN APP (navigation using a dictionary of functions)
# ------------------------------------------------------------
def main():
    st.set_page_config(page_title="Food Waste Management", page_icon="")
    st.title("🍲 Food Waste Management System")

    pages = {
        "Dashboard": dashboard_page,
        "Donate food": donate_page,
        "Available food": available_food_page,
        "Claim food": claim_page,
        "Waste log": waste_log_page,
        "Tips": tips_page,
    }

    choice = st.sidebar.radio("Go to", list(pages.keys()))
    pages[choice]()  # call the selected page function

    st.sidebar.markdown("---")
    st.sidebar.caption("Data is stored in memory and resets when the app restarts.")


main()
