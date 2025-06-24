import streamlit as st
import pandas as pd
import re
from datetime import datetime, timedelta
import time
from datetime import datetime
from fpdf import FPDF
import random
import folium
from streamlit_folium import st_folium
from PIL import Image
#import pytesseract
import base64
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

st.set_page_config(page_title="Smart Traffic & Toll Management", layout="wide")

# --- Custom CSS Styling ---
custom_css = """
<style>
html, body, [data-testid="stAppViewContainer"] {
    background: linear-gradient(to right, #0f2027, #203a43, #2c5364);
    
    background-attachment: fixed;
    background-repeat: no-repeat;
    background-size: cover;
}
[data-testid="stAppViewContainer"] > .main {
    background-color: rgba(255, 255, 255, 0.92);
    padding: 2rem;
    border-radius: 16px;
    margin: 2rem;
    box-shadow: 0 8px 20px rgba(0, 0, 0, 0.1);
}
[data-testid="stSidebar"] {
    background: linear-gradient(to bottom, #4b6cb7, #182848);
    color: white;
}
[data-testid="stSidebar"] * {
    color: white !important;
}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# --- Constants ---
receipt_download = None
receipt_filename = ""
ROADS = ["Highway 1", "Highway 2", "Highway 3"]
LANES = ["Lane 1", "Lane 2", "Lane 3"]
VEHICLE_TYPES = {"Car": 50, "Bus": 100, "Truck": 150, "Emergency": 0}
PAYMENT_MODES = ["FASTag", "UPI", "Cash"]
TOLL_BOOTHS = ["Booth A", "Booth B", "Booth C"]
ROAD_SPEED_LIMIT = {"Highway 1": (60, 100), "Highway 2": (50, 90), "Highway 3": (60, 100)}
SIGNAL_DIRECTIONS = ["North", "South", "East", "West"]
SIGNAL_SEQUENCE = ["Red", "Green", "Yellow"]
INCIDENT_TYPES = ["Accident", "Construction", "Breakdown"]
SEVERITY_LEVELS = ["Low", "Moderate", "High"]

# --- Session State Init ---
for key in ["vehicles", "signals", "incidents", "toll_vehicles", "signal_log", "last_signal_change", "overspeed_alerts"]:
    if key not in st.session_state:
        if key == "signals":
            st.session_state[key] = {d: "Red" for d in SIGNAL_DIRECTIONS}
        elif key == "last_signal_change":
            st.session_state[key] = datetime.now()
        elif key == "overspeed_alerts":
            st.session_state[key] = []
        else:
            st.session_state[key] = []

# --- Sidebar Navigation ---
st.sidebar.title("🚦 Smart Highway System")
section = st.sidebar.radio("Choose Section", [
    "Traffic Signal Control", "Highway Vehicle Management",
    "Toll Plaza Management", "Incident Management", "Dashboard Summary"])

# --- Traffic Signal Module ---
if section == "Traffic Signal Control":
    st.title("🚦 Traffic Signal Management")
    auto_cycle = st.checkbox("Auto Cycle every 60 seconds")

    current_time = datetime.now()
    time_elapsed = (current_time - st.session_state.last_signal_change).total_seconds()

    if auto_cycle and time_elapsed >= 60:
        current_active = [d for d, s in st.session_state.signals.items() if s == "Green"]
        if not current_active:
            next_dir = SIGNAL_DIRECTIONS[0]
        else:
            curr_idx = SIGNAL_DIRECTIONS.index(current_active[0])
            next_dir = SIGNAL_DIRECTIONS[(curr_idx + 1) % len(SIGNAL_DIRECTIONS)]
        for d in SIGNAL_DIRECTIONS:
            st.session_state.signals[d] = "Red"
        st.session_state.signals[next_dir] = "Green"
        st.session_state.signal_log.append({
            "direction": next_dir,
            "new_state": "Green",
            "time": datetime.now().strftime("%H:%M:%S")
        })
        st.session_state.last_signal_change = datetime.now()

    with st.expander("🚨 Emergency Override (Ambulance/Fire)"):
        override_direction = st.selectbox("Override Direction", SIGNAL_DIRECTIONS)
        if st.button("Activate Emergency Green"):
            for d in SIGNAL_DIRECTIONS:
                st.session_state.signals[d] = "Red"
            st.session_state.signals[override_direction] = "Green"
            st.session_state.signal_log.append({
                "direction": override_direction,
                "new_state": "Green (Emergency)",
                "time": datetime.now().strftime("%H:%M:%S")
            })
            st.session_state.last_signal_change = datetime.now()
            st.success(f"Emergency override activated for {override_direction}")

    col1, col2 = st.columns(2)
    with col1:
        for direction in ["East", "West"]:
            st.subheader(f"{direction} Signal")
            current = st.session_state.signals[direction]
            next_idx = (SIGNAL_SEQUENCE.index(current) + 1) % len(SIGNAL_SEQUENCE)
            next_state = SIGNAL_SEQUENCE[next_idx]
            st.markdown(f"**Current:** `{current}`")
            if st.button(f"Change to {next_state}", key=direction):
                if next_state == "Green" and "Green" in st.session_state.signals.values():
                    st.error("Another signal is already Green")
                else:
                    st.session_state.signals[direction] = next_state
                    st.session_state.signal_log.append({
                        "direction": direction,
                        "new_state": next_state,
                        "time": datetime.now().strftime("%H:%M:%S")
                    })
                    st.session_state.last_signal_change = datetime.now()
            elapsed = (datetime.now() - st.session_state.last_signal_change).total_seconds()
            countdown = max(0, 60 - int(elapsed)) if current == "Green" else "-"
            st.info(f"⏳ Countdown: {countdown} seconds")

    with col2:
        for direction in ["North", "South"]:
            st.subheader(f"{direction} Signal")
            current = st.session_state.signals[direction]
            next_idx = (SIGNAL_SEQUENCE.index(current) + 1) % len(SIGNAL_SEQUENCE)
            next_state = SIGNAL_SEQUENCE[next_idx]
            st.markdown(f"**Current:** `{current}`")
            if st.button(f"Change to {next_state}", key=direction):
                if next_state == "Green" and "Green" in st.session_state.signals.values():
                    st.error("Another signal is already Green")
                else:
                    st.session_state.signals[direction] = next_state
                    st.session_state.signal_log.append({
                        "direction": direction,
                        "new_state": next_state,
                        "time": datetime.now().strftime("%H:%M:%S")
                    })
                    st.session_state.last_signal_change = datetime.now()
            elapsed = (datetime.now() - st.session_state.last_signal_change).total_seconds()
            countdown = max(0, 60 - int(elapsed)) if current == "Green" else "-"
            st.info(f"⏳ Countdown: {countdown} seconds")

    st.subheader("Signal Overview")
    overview_row1, overview_row2 = st.columns(2)
    with overview_row1:
        for direction in ["East", "West"]:
            state = st.session_state.signals[direction]
            color = {"Red": "#ff4b4b", "Green": "#4bff4b", "Yellow": "#fff44b"}[state]
            st.markdown(f"""
            <div style='padding:10px;border-radius:8px;background-color:{color};color:black;'>
            <strong>{direction}</strong>: {state}
            </div>
            """, unsafe_allow_html=True)
    with overview_row2:
        for direction in ["North", "South"]:
            state = st.session_state.signals[direction]
            color = {"Red": "#ff4b4b", "Green": "#4bff4b", "Yellow": "#fff44b"}[state]
            st.markdown(f"""
            <div style='padding:10px;border-radius:8px;background-color:{color};color:black;'>
            <strong>{direction}</strong>: {state}
            </div>
            """, unsafe_allow_html=True)

        st.subheader("🗺️ Live Junction Signal Map")

    # Netaji Subhash Chandra Bose Junction base location
    base_lat, base_lon = 12.9767, 77.5997

    # Custom spaced coordinates for signals around the junction
    JUNCTION_COORDS = {
        "North": [base_lat + 0.0007, base_lon],        # Slightly north
        "South": [base_lat - 0.0007, base_lon],        # Slightly south
        "East":  [base_lat, base_lon + 0.0007],        # Slightly east
        "West":  [base_lat, base_lon - 0.0007]         # Slightly west
    }

    m = folium.Map(location=[base_lat, base_lon], zoom_start=18, control_scale=True)

    for direction, coords in JUNCTION_COORDS.items():
        signal_state = st.session_state.signals[direction]
        color = {"Red": "red", "Green": "green", "Yellow": "orange"}[signal_state]
        folium.Marker(
            location=coords,
            popup=f"{direction} Signal: {signal_state}",
            icon=folium.Icon(color=color, icon="info-sign")
        ).add_to(m)

    folium.Marker(
        location=[base_lat, base_lon],
        popup="🛑 Netaji Subhash Chandra Bose Circle",
        icon=folium.Icon(color="blue", icon="star")
    ).add_to(m)

    st_folium(m, width=750, height=450)


    if st.session_state.signal_log:
        st.subheader("Signal Change Log")
        df = pd.DataFrame(st.session_state.signal_log[::-1])
        st.dataframe(df, use_container_width=True)
    st.session_state.current_signal = dict(st.session_state.signals)

    


# --- Highway Vehicle Management ---
if section == "Highway Vehicle Management":
    st.title("🛣️ Highway Vehicle Entry/Exit Management")

    with st.form("vehicle_entry_form"):
        plate = st.text_input("Vehicle Plate (e.g., KA01AB1234)").upper().strip()
        vtype = st.selectbox("Vehicle Type", list(VEHICLE_TYPES.keys()))
        road = st.selectbox("Select Road", ROADS)
        lane = st.selectbox("Select Lane", LANES)
        speed = st.slider("Speed (km/h)", 0, 150, 80)
        destination = st.text_input("Destination/Exit Point")
        emergency = st.checkbox("Is Emergency Vehicle?")
        image = st.file_uploader("Upload License Plate Image (optional)", type=["jpg", "jpeg", "png"])
        submit = st.form_submit_button("Register Vehicle")

    if submit:
        min_spd, max_spd = ROAD_SPEED_LIMIT[road]
        now = datetime.now()

        if not re.match(r'^[A-Z]{2}[0-9]{2}[A-Z]{1,2}[0-9]{4}$', plate):
            st.error("Invalid plate format.")
        elif any(v["plate"] == plate for v in st.session_state.vehicles):
            st.warning("Vehicle already exists.")
        else:
            st.session_state.vehicles.append({
                "plate": plate,
                "type": vtype,
                "road": road,
                "lane": lane,
                "speed": speed,
                "destination": destination,
                "entry_time": now,
                "emergency": "Yes" if emergency else "No"
            })

            if speed > max_spd and not emergency:
                st.session_state.overspeed_alerts.append({
                    "plate": plate,
                    "speed": speed,
                    "limit": max_spd,
                    "timestamp": now.strftime("%H:%M:%S")
                })
                

                beep_base64 = (
                    "UklGRiQAAABXQVZFZm10IBAAAAABAAEAQB8AAIA+AAACABAAZGF0YQAAADMzMzMzMzMzMzMzMzMz"
                    "MzMzMzMzMzMzMzMzMzMzMzMzMzMzMzMzMzMzMzMzMzMzMzMzMzMzMzMzMzMzMzMzMzMzMzMzMzMz"
                )

                audio_data = base64.b64decode(beep_base64)
                st.audio(audio_data, format="audio/wav", start_time=0)


                st.warning(f"Vehicle is overspeeding! Limit: {max_spd} km/h")

            elif speed < min_spd and not emergency:
                st.warning(f"Speed is below minimum {min_spd} km/h")

            st.success(f"Vehicle {plate} added successfully.")

            if image:
                st.image(image, caption="Uploaded Image", use_column_width=True)
               # st.info(f"OCR Result: {text}")
                #img = Image.open(image)
                #text = pytesseract.image_to_string(img)
                st.info("OCR is disabled in this deployment.")

    if st.session_state.vehicles:
        st.subheader("📋 Active Vehicles on Highway")
        df = pd.DataFrame(st.session_state.vehicles)
        df["entry_time"] = pd.to_datetime(df["entry_time"])
        df["duration"] = (datetime.now() - df["entry_time"]).apply(lambda x: str(timedelta(seconds=int(x.total_seconds()))))

        with st.expander("🔍 Filter Vehicles"):
            r_filter = st.selectbox("Filter by Road", ["All"] + ROADS)
            e_filter = st.selectbox("Show Emergency Only?", ["All", "Yes"])
            if r_filter != "All":
                df = df[df["road"] == r_filter]
            if e_filter == "Yes":
                df = df[df["emergency"] == "Yes"]

        st.dataframe(df.drop(columns=["entry_time"]))

        with st.expander("⚠️ Overspeeding Alerts"):
            if st.session_state.overspeed_alerts:
                st.warning("Some vehicles are overspeeding!")
                alert_df = pd.DataFrame(st.session_state.overspeed_alerts)
                st.dataframe(alert_df)
            else:
                st.success("No overspeeding detected.")

        st.subheader("📍 Live Vehicle Tracking Map")

        # Step 1: Store base lat/lon only once
        base_lat = 13.0315
        base_lon = 77.5390

        # Step 2: Create map only once and store it in session_state
        if "static_map" not in st.session_state:
            static_map = folium.Map(location=[base_lat, base_lon], zoom_start=16)
            
            # Optional: Add static labels like toll booth, highway entry, etc.
            folium.Marker(
                location=[base_lat, base_lon],
                popup="Highway Control Center",
                icon=folium.Icon(color="blue", icon="star")
            ).add_to(static_map)
            
            st.session_state.static_map = static_map

        # Step 3: Copy static map for rendering + add only dynamic vehicle markers
        from copy import deepcopy
        vehicle_map = deepcopy(st.session_state.static_map)

        # Step 4: Add updated vehicle markers (only these change)
        for v in st.session_state.vehicles:
            lat = base_lat + random.uniform(-0.001, 0.001)
            lon = base_lon + random.uniform(-0.001, 0.001)
            folium.CircleMarker(
                location=[lat, lon],
                radius=6,
                popup=f"{v['plate']} ({v['type']})\nSpeed: {v['speed']} km/h",
                color="red" if v['emergency'] == "Yes" else "blue",
                fill=True,
                fill_opacity=0.7
            ).add_to(vehicle_map)

        # Step 5: Display map cleanly (no flicker)
        st_folium(vehicle_map, width=750, height=450)


        st.subheader("📈 Traffic Analytics Dashboard")
        df_stats = pd.DataFrame(st.session_state.vehicles)
        df_stats["entry_time"] = pd.to_datetime(df_stats["entry_time"])
        df_stats["hour"] = df_stats["entry_time"].dt.hour

        per_hour = df_stats["hour"].value_counts().sort_index()
        st.markdown("**🚗 Vehicle Entries Per Hour**")
        st.bar_chart(per_hour)

        avg_speed = df_stats["speed"].mean()
        st.metric("📏 Average Speed", f"{avg_speed:.2f} km/h")

        peak_hour = per_hour.idxmax() if not per_hour.empty else "N/A"
        st.metric("⏰ Peak Traffic Hour", f"{peak_hour}:00 hrs")

# --- Toll Management ---
if section == "Toll Plaza Management":
    st.title("💳 Toll Plaza Management System")

    import os  # Ensure os is imported for file check

    booth_distances = {
        ("Booth A", "Booth B"): 25,
        ("Booth A", "Booth C"): 40,
        ("Booth B", "Booth C"): 15
    }

    VEHICLE_TYPES = {"Car": 50, "Bus": 100, "Truck": 150, "Emergency": 0}
    TOLL_BOOTHS = ["Booth A", "Booth B", "Booth C"]
    PAYMENT_MODES = ["FASTag", "UPI", "Cash"]

    if "toll_vehicles" not in st.session_state:
        st.session_state.toll_vehicles = []

    # Flags for receipt download
    receipt_download = False
    receipt_filename = ""

    # Toll Booth Form
    with st.form("toll_form"):
        plate = st.text_input("Plate Number").upper().strip()
        vtype = st.selectbox("Vehicle Type", list(VEHICLE_TYPES.keys()))
        entry_booth = st.selectbox("Entry Booth", TOLL_BOOTHS)
        exit_booth = st.selectbox("Exit Booth", TOLL_BOOTHS)
        pay_mode = st.radio("Payment Mode", PAYMENT_MODES)
        pay_now = st.checkbox("Pay Now")
        toll_submit = st.form_submit_button("Record Toll")

    if toll_submit:
        if entry_booth != exit_booth:
            distance = booth_distances.get((entry_booth, exit_booth)) or booth_distances.get((exit_booth, entry_booth), 0)
        else:
            distance = 0

        fee = distance * 2 if vtype != "Emergency" else 0
        status = "Paid" if pay_now else "Unpaid"

        entry = {
            "plate": plate,
            "type": vtype,
            "entry_booth": entry_booth,
            "exit_booth": exit_booth,
            "distance": distance,
            "fee": fee,
            "status": status,
            "payment_mode": pay_mode,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        st.session_state.toll_vehicles.append(entry)
        st.success(f"{plate} recorded: Rs. {fee} for {distance} km via {pay_mode} - {status}")

        # Generate receipt only if paid
        if pay_now:
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)
            pdf.cell(200, 10, txt="Toll Payment Receipt", ln=True, align='C')
            pdf.cell(200, 10, txt=f"Vehicle: {plate}", ln=True)
            pdf.cell(200, 10, txt=f"From: {entry_booth} To: {exit_booth}", ln=True)
            pdf.cell(200, 10, txt=f"Distance: {distance} km", ln=True)
            pdf.cell(200, 10, txt=f"Fee Paid: Rs. {fee}", ln=True)
            pdf.cell(200, 10, txt=f"Payment Mode: {pay_mode}", ln=True)

            receipt_filename = f"receipt_{plate}.pdf"
            pdf.output(receipt_filename)
            receipt_download = True

    # Show download button after form is processed
    if receipt_download and os.path.exists(receipt_filename):
        with open(receipt_filename, "rb") as f:
            st.download_button("⬇️ Download Toll Receipt", f, file_name=receipt_filename, mime="application/pdf")

   # Admin Dashboard
    if st.session_state.toll_vehicles:
        df = pd.DataFrame(st.session_state.toll_vehicles)

        st.subheader("📋 Toll Log")
        st.dataframe(df[["timestamp", "plate", "type", "entry_booth", "exit_booth", "distance", "fee", "status", "payment_mode"]], use_container_width=True)

        st.subheader("📊 Booth-wise Collection (Paid Only)")
        df_paid = df[df["status"] == "Paid"]
        summary = df_paid.groupby("entry_booth").agg({
            "fee": "sum",
            "plate": "count"
        }).rename(columns={"fee": "Total Collection (Paid)", "plate": "Paid Vehicles Passed"})

        st.dataframe(summary)
        st.metric("Total Paid Amount", f"Rs. {df_paid['fee'].sum()}")
        st.bar_chart(summary["Total Collection (Paid)"])

        # Congestion Indicator
        st.subheader("🚦 Booth Congestion Levels")
        booth_queues = df["entry_booth"].value_counts().to_dict()
        col1, col2 = st.columns(2)

        with col1:
            for booth in TOLL_BOOTHS:
                count = booth_queues.get(booth, 0)
                if count <= 3:
                    color = "green"
                elif count <= 6:
                    color = "orange"
                else:
                    color = "red"

                st.markdown(f"""
                    <div style="background-color:{color};padding:10px;border-radius:10px;">
                    <strong>{booth}</strong>: {count} vehicles in queue
                    </div>
                """, unsafe_allow_html=True)

        with col2:
            st.subheader("🚗 Queue Per Booth")
            for b in TOLL_BOOTHS:
                st.markdown(f"**{b} Queue:** {booth_queues.get(b, 0)} vehicles")

        with st.expander("🔍 Filter Entries"):
            f_type = st.selectbox("Filter by Type", ["All"] + list(VEHICLE_TYPES.keys()))
            f_status = st.selectbox("Filter by Status", ["All", "Paid", "Unpaid"])

            if f_type != "All":
                df = df[df["type"] == f_type]
            if f_status != "All":
                df = df[df["status"] == f_status]

        st.dataframe(df, use_container_width=True)

        # Summary
        paid_amt = sum(v["fee"] for v in st.session_state.toll_vehicles if v["status"] == "Paid")
        unpaid_count = sum(1 for v in st.session_state.toll_vehicles if v["status"] == "Unpaid")
        st.metric("Total Collection", f"Rs. {paid_amt}")
        st.metric("Unpaid Vehicles", unpaid_count)

        with st.expander("📊 Visual Summary"):
            vc = pd.DataFrame(df["type"].value_counts()).reset_index()
            vc.columns = ["Vehicle Type", "Count"]
            st.bar_chart(vc.set_index("Vehicle Type"))


## --- Incident Management ---
elif section == "Incident Management":
    st.title("🚧 Incident Logging & Response")

    def send_email_alert(subject, body):
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart

        sender_email = st.secrets["email"]["sender"]
        receiver_email = st.secrets["email"]["receiver"]
        password = st.secrets["email"]["password"]

        msg = MIMEMultipart()
        msg["From"] = sender_email
        msg["To"] = receiver_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        try:
            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.starttls()
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, msg.as_string())
            server.quit()
            st.success("📧 Email alert sent!")
        except Exception as e:
            st.warning(f"Failed to send email: {e}")

    with st.form("incident_form"):
        road = st.selectbox("Affected Road", ROADS)
        itype = st.selectbox("Incident Type", INCIDENT_TYPES)
        severity = st.selectbox("Severity Level", SEVERITY_LEVELS)
        description = st.text_area("Description / Additional Notes")
        reported_by = st.text_input("Reported By")
        uploaded_images = st.file_uploader(
            "Upload Incident Image(s)", type=["jpg", "jpeg", "png"], accept_multiple_files=True
        )

        submit_incident = st.form_submit_button("Report Incident")

    if submit_incident:
        # Assign random lat/lon based on road
        road_coords = {
            "Highway 1": [13.0315, 77.5390],
            "Highway 2": [13.0415, 77.5490],
            "Highway 3": [13.0215, 77.5290],
        }
        base_lat, base_lon = road_coords[road]
        incident_lat = base_lat + random.uniform(-0.0007, 0.0007)
        incident_lon = base_lon + random.uniform(-0.0007, 0.0007)

        # Add to session state
        st.session_state.incidents.append({
            "road": road,
            "type": itype,
            "severity": severity,
            "resolved": False,
            "description": description,
            "reported_by": reported_by,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "lat": incident_lat,
            "lon": incident_lon,
            "images": [img.getvalue() for img in uploaded_images] if uploaded_images else []
        })

        # Simulate severity-based notification
        if severity == "High":
            st.toast(f"🚨 High severity {itype} reported on {road}", icon="⚠️")
            st.error("⚠️ Critical incident reported!")

            # Compose email
            subject = f"🚨 HIGH Severity Alert: {itype} on {road}"
            body = f"""
            Incident Type: {itype}
            Road: {road}
            Severity: HIGH
            Reported By: {reported_by}
            Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            Description: {description}
            """

            send_email_alert(subject, body)

        elif severity == "Moderate":
            st.toast(f"⚠️ Moderate incident on {road}", icon="⚠️")

        st.success("Incident logged successfully.")

    # Show unresolved incidents
    unresolved = [i for i in st.session_state.incidents if not i['resolved']]
    if unresolved:
        st.subheader("🚨 Active Incidents")
        df_unres = pd.DataFrame(unresolved)
        st.dataframe(df_unres, use_container_width=True)

        road_res = st.selectbox("Resolve Incident on Road", [i['road'] for i in unresolved])
        if st.button("Mark Incident Resolved"):
            for i in st.session_state.incidents:
                if i['road'] == road_res and not i['resolved']:
                    i['resolved'] = True
            st.success(f"Incident on {road_res} marked as resolved.")
    else:
        st.success("✅ No active incidents.")

    # 📍 Incident Location Mapping
    st.subheader("🗺️ Incident Map View (Live)")
    incident_map = folium.Map(location=[13.0315, 77.5390], zoom_start=13)

    for inc in st.session_state.incidents:
        if not inc["resolved"]:
            color = {"Low": "green", "Moderate": "orange", "High": "red"}[inc["severity"]]
            folium.Marker(
                location=[inc["lat"], inc["lon"]],
                popup=f"<strong>{inc['type']} ({inc['severity']})</strong><br>{inc['road']}<br>{inc['description']}<br>Reported by: {inc['reported_by']}<br>Time: {inc['timestamp']}",
                icon=folium.Icon(color=color)
            ).add_to(incident_map)

    st_folium(incident_map, width=750, height=450)

    # 🕒 Incident History Timeline
    st.subheader("🕒 Incident History Timeline")
    if st.session_state.incidents:
        for i, incident in enumerate(st.session_state.incidents[::-1]):
            with st.expander(f"{incident['timestamp']} - {incident['type']} on {incident['road']}"):
                st.write(f"**Reported by:** {incident['reported_by']}")
                st.write(f"**Severity:** {incident['severity']}")
                st.write(f"**Description:** {incident['description']}")
                st.write(f"**Status:** {'Resolved' if incident['resolved'] else 'Active'}")
                if incident.get("images"):
                    for idx, img_bytes in enumerate(incident["images"]):
                        st.image(img_bytes, caption=f"Incident Image {idx+1}", use_column_width=True)
    else:
        st.info("No incidents reported yet.")

# --- Dashboard ---
elif section == "Dashboard Summary":
    st.title("📊 System Summary Dashboard")
     # 🚦 Show Current Traffic Signals
    st.subheader("🚦 Live Traffic Signal Status")
    if "current_signal" in st.session_state:
        signals = st.session_state["current_signal"]
        cols = st.columns(4)
        for i, dir in enumerate(["North", "South", "East", "West"]):
            color = signals[dir]
            icon = "🟥" if color == "Red" else "🟨" if color == "Yellow" else "🟩"
            with cols[i]:
                st.metric(label=f"{dir}", value=f"{icon} {color}")
    else:
        st.warning("⚠️ Signal data not available. Please open Traffic Signal Control module first.")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Vehicles on Highway", len(st.session_state.vehicles))
    with col2:
        paid = sum(v["fee"] for v in st.session_state.toll_vehicles if v["status"] == "Paid")
        st.metric("Toll Revenue", f"₹{paid}")
    with col3:
        st.metric("Unresolved Incidents", len([i for i in st.session_state.incidents if not i['resolved']]))

    st.subheader("📄 Recent Toll Records")
    if st.session_state.toll_vehicles:
        st.dataframe(pd.DataFrame(st.session_state.toll_vehicles)[-5:], use_container_width=True)

    st.subheader("🛑 Active Incidents")
    if any(not i['resolved'] for i in st.session_state.incidents):
        st.dataframe(pd.DataFrame([i for i in st.session_state.incidents if not i['resolved']]), use_container_width=True)
    else:
        st.success("No incidents active ✅")
    
