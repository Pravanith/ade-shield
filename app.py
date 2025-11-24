import streamlit as st
import pandas as pd
import altair as alt

# -----------------------------
# SESSION STATE INITIALIZATION
# -----------------------------
if 'patient_loaded' not in st.session_state:
    st.session_state['patient_loaded'] = False
    st.session_state['bleeding_risk'] = 0
    st.session_state['hypoglycemic_risk'] = 0
    st.session_state['aki_risk'] = 0
    st.session_state['fragility_index'] = 0
    st.session_state['patient_info'] = {'age': 70, 'gender': 'Male', 'weight': 75} # Default profile

# -----------------------------
# CORE MODELING LOGIC (FUNCTIONS - FINAL CORRECTED SIGNATURES)
# -----------------------------

def calculate_bleeding_risk(age, inr, anticoagulant, gi_bleed, high_bp, antiplatelet_use, gender, weight, smoking, alcohol_use, antibiotic_order, dietary_change, liver_disease, prior_stroke):
    """Predicts bleeding risk, factoring in underlying conditions and patient demographics."""
    score = 0
    # Acute / Drug Factors
    score += 35 if anticoagulant else 0
    score += 40 if inr > 3.5 else 0
    score += 30 if gi_bleed else 0
    score += 15 if antiplatelet_use else 0
    
    # New Acute/Lifestyle Factors
    score += 25 if antibiotic_order else 0 
    score += 15 if alcohol_use else 0     
    score += 20 if liver_disease else 0   
    score += 10 if dietary_change else 0  
    
    # Chronic / Management / Demographics Factors
    score += 10 if age > 70 else 0
    score += 10 if high_bp else 0
    score += 10 if smoking else 0
    score += 5 if gender == 'Female' else 0
    score += 15 if weight > 120 or weight < 50 else 0
    score += 15 if prior_stroke else 0 
    
    return min(score, 100)

def calculate_hypoglycemic_risk(insulin_use, renal_status, high_hba1c, neuropathy_history, gender, weight, recent_dka):
    """Predicts low blood sugar risk, factoring in diabetes control status and severe events."""
    score = 0
    score += 30 if insulin_use else 0
    score += 45 if renal_status else 0
    score += 20 if high_hba1c else 0
    score += 10 if neuropathy_history else 0
    score += 10 if weight < 60 else 0
    score += 20 if recent_dka else 0 
    return min(score, 100)

def calculate_aki_risk(age, diuretic_use, acei_arb_use, high_bp, active_chemo, gender, weight, race, baseline_creat, contrast_exposure):
    """Predicts Acute Kidney Injury (AKI) risk from drug classes and co-existing conditions, including acute events."""
    score = 0
    score += 30 if diuretic_use else 0
    score += 40 if acei_arb_use else 0
    score += 25 if contrast_exposure else 0 
    score += 20 if age > 75 else 0
    score += 10 if high_bp else 0
    score += 20 if active_chemo else 0
    score += 15 if race == 'Non-Hispanic Black' else 0
    score += 30 if baseline_creat > 1.5 else 0 
    return min(score, 100)

def calculate_comorbidity_load(prior_stroke, active_chemo, recent_dka, liver_disease, smoking, high_bp):
    """Calculates a composite score representing the patient's overall disease burden and clinical fragility."""
    load = 0
    load += 25 if prior_stroke else 0
    load += 30 if active_chemo else 0
    load += 20 if recent_dka else 0
    load += 15 if liver_disease else 0
    load += 10 if smoking else 0
    load += 10 if high_bp else 0
    return min(load, 100)

# ---------------------------------------------------
# NEW FUNCTION: GENERATE SPECIFIC ALERT TEXT (UNMODIFIED)
# ---------------------------------------------------

def generate_detailed_alert(risk_type, inputs):
    """Generates a detailed, action-oriented alert based on the highest risk type and active inputs."""
    
    # 1. Determine the highest scoring threat
    if risk_type == "Bleeding":
        base_message = "🔴 CRITICAL ALERT: Highest threat is **Bleeding Risk**. Primary factors:"
        factors = []
        if inputs['inr'] > 3.5: factors.append(f"High INR ({inputs['inr']})")
        if inputs['antibiotic_order']: factors.append("New Antibiotic Order (Metabolic Interference)")
        if inputs['on_antiplatelet']: factors.append("Dual Antiplatelet/Anticoagulant Therapy")
        if inputs['alcohol_use']: factors.append("Heavy Alcohol Use")
        if inputs['hist_gi_bleed']: factors.append("History of GI Bleed")
        if inputs['prior_stroke']: factors.append("History of Stroke/TIA (Complex Management)")
        
    elif risk_type == "Hypoglycemic":
        base_message = "🔴 CRITICAL ALERT: Highest threat is **Hypoglycemic Risk**. Primary factors:"
        factors = []
        if inputs['impaired_renal']: factors.append("Impaired Renal Status (Reduced Drug Clearance)")
        if inputs['high_hba1c']: factors.append("Poor DM Control (HbA1c > 9.0%)")
        if inputs['recent_dka']: factors.append("Recent DKA/HHS Admission (Metabolic Volatility)")
        if inputs['weight'] < 60: factors.append(f"Low Body Weight ({inputs['weight']} kg)")

    elif risk_type == "AKI":
        base_message = "🔴 CRITICAL ALERT: Highest threat is **AKI Risk (Renal)**. Primary factors:"
        factors = []
        if inputs['baseline_creat'] > 1.5: factors.append(f"Baseline CKD (Creatinine > 1.5)")
        if inputs['active_chemo']: factors.append("Active Chemotherapy (Nephrotoxic Agent)")
        if inputs['contrast_exposure']: factors.append("Recent Contrast Dye Exposure")
        if inputs['on_acei_arb'] and inputs['on_diuretic']: factors.append("Combined ACEi/Diuretic Therapy")

    else: # Should not happen if risk >= 70
        return "HIGH RISK ALERT: Check specific patient risks."
        
    # Join factors or provide default if no specific factor is > 0
    if factors:
        return base_message + " " + ", ".join(factors) + "."
    else:
        return base_message + " High risk due to combination of demographic factors."


# -----------------------------
# SIMPLE CHATBOT & INTERACTIONS (UNMODIFIED)
# -----------------------------
def chatbot_response(text):
    text = text.lower()
    responses = {
        "warfarin": "Warfarin interacts with several medications and increases bleeding risk.",
        "amiodarone": "Amiodarone can elevate INR when combined with Warfarin.",
        "aki": "Acute Kidney Injury risk is elevated by certain blood pressure medications (ACEi/ARBs) and diuretics.",
        "metformin": "Metformin is a first-line diabetes drug but is strictly avoided in severe kidney impairment.",
        "acei": "ACE inhibitors are critical for hypertension but increase the risk of AKI, especially when combined with diuretics.",
        "doac": "Direct Oral Anticoagulants (like Apixaban) are used for clotting, but their dose must be adjusted for impaired renal function.",
        "sulfonylurea": "Sulfonylureas stimulate insulin release and have a high risk of causing severe hypoglycemia.",
        "diabetes": "Diabetes requires strict blood sugar monitoring; poor control (high HbA1c) increases hypoglycemia risk.",
        "hypertension": "Uncontrolled hypertension increases cardiovascular risk and stresses kidney function.",
        "cancer": "Active chemotherapy treatment increases the risk of AKI and immune suppression.",
    }
    for key in responses:
        if key in text:
            return responses[key]
    
    return "I need more specific clinical context. Please refine your query using drug classifications, risk factors, or one of the major ADE categories (Bleeding, Hypoglycemia, AKI)."

# --- DRUG INTERACTION DATABASE (EXPANDED) ---
interaction_db = {
    # --- 1. Bleeding/Clotting Risks ---
    ("warfarin", "amiodarone"): "Major: Amiodaride increases INR, high bleeding risk.",
    ("warfarin", "ibuprofen"): "Major: NSAIDs increase bleeding risk with Warfarin.",
    ("apixaban", "ibuprofen"): "Moderate: NSAIDs increase bleeding risk with Apixaban.",
    ("clopidogrel", "aspirin"): "Moderate: Dual antiplatelet therapy, increases bleed risk.",
    ("rivaroxaban", "fluconazole"): "Major: Fluconazole increases Rivaroxaban levels (CYP3A4 inhibitor); high bleeding risk.",
    ("warfarin", "paracetamol"): "Major: Paracetamol increases Warfarin's effect; high bleeding risk.",
    ("sertraline", "warfarin"): "Moderate: SSRI (Sertraline) combined with Warfarin increases baseline bleeding risk.",

    # --- 2. AKI/Renal/Electrolyte Risks ---
    ("lisinopril", "spironolactone"): "Major: Risk of severe hyperkalemia (high potassium).",
    ("ibuprofen", "lisinopril"): "Major: Severe AKI risk (Triple Whammy component).",
    ("furosemide", "lisinopril"): "Major: Diuretic + ACEi causes severe hypotension and AKI risk.",
    ("prednisone", "furosemide"): "Major: Steroid + Diuretic increases risk of severe hypokalemia (low potassium).", # NEW
    ("lithium", "hydrochlorothiazide"): "Major: Diuretic (HCTZ) increases Lithium toxicity risk by slowing excretion.", # NEW
    ("allopurinol", "azathioprine"): "Major: Allopurinol dramatically increases Azathioprine toxicity and risk of severe bone marrow suppression.", # NEW
    
    # --- 3. Hypoglycemia/Diabetes Risks ---
    ("glipizide", "alcohol"): "Major: Increased risk of severe hypoglycemia.",
    ("metformin", "cimetidine"): "Moderate: Cimetidine increases Metformin levels, raising hypoglycemia risk.",
    ("trimethoprim/sulfamethoxazole", "metformin"): "Major: TMP/SMX increases Metformin levels, high hypoglycemia risk.",
    ("metoprolol", "insulin"): "Moderate: Beta-blocker (Metoprolol) can mask the warning signs of hypoglycemia.", # NEW

    # --- 4. Cardiotoxicity/Serotonin Risks ---
    ("sertraline", "sumatriptan"): "Major: Both increase serotonin levels; high risk of Serotonin Syndrome.", # NEW
    ("azithromycin", "amiodarone"): "Major: Both prolong QT interval; high risk of fatal arrhythmia.", # NEW
    ("metoprolol", "diltiazem"): "Major: Both slow heart rate; high risk of severe bradycardia and hypotension.", # NEW
}

def check_interaction(drug1, drug2):
    """Checks for simple predefined drug interactions."""
    d1, d2 = drug1.lower().strip(), drug2.lower().strip()
    if (d1, d2) in interaction_db:
        return interaction_db[(d1, d2)]
    if (d2, d1) in interaction_db:
        return interaction_db[(d2, d1)]
    return "No major interaction found."
# -----------------------------
# Page Setup & Navigation
# -----------------------------
st.set_page_config(page_title="ADE Shield", layout="wide")
st.title("Clinical Risk Monitor")

with st.sidebar:
    st.title("Risk Monitor Menu")
    menu = st.radio(
        "Select Application View",
        ["Live Dashboard", "Risk Calculator", "CSV Upload", "Medication Checker", "Chatbot"],
        index=0
    )

# ---------------------------------------------------
# PAGE 0 – LIVE DASHBOARD (DYNAMICALLY CONNECTED)
# ---------------------------------------------------
if menu == "Live Dashboard":
    
    # --- CHECK FOR DYNAMIC DATA (STEP 1: READ STATE) ---
    if st.session_state['patient_loaded']:
        # If dynamic data is available, use it
        br = st.session_state['bleeding_risk']
        hr = st.session_state['hypoglycemic_risk']
        ar = st.session_state['aki_risk']
        cfr = st.session_state['fragility_index']
        patient = st.session_state['patient_info']
        
        # Determine primary alert based on loaded data
        max_risk = max(br, hr, ar)
        
        if br == max_risk:
            primary_threat = "Bleeding Risk"
        elif hr == max_risk:
            primary_threat = "Hypoglycemic Risk"
        else:
            primary_threat = "AKI Risk"
        
        # Define alert color based on severity
        alert_color = "red" if max_risk >= 70 else "green"
        alert_label = "CRITICAL" if max_risk >= 90 else ("HIGH" if max_risk >= 70 else "LOW")
        
    else:
        # If no dynamic data, use the original hardcoded demo data
        br, hr, ar, cfr = 60, 92, 80, 75
        patient = {'age': 65, 'gender': 'Female', 'weight': 55, 'high_a1c': True, 'renal_status': True}
        primary_threat = "Hypoglycemic Risk"
        alert_color = "red"
        alert_label = "CRITICAL"


    st.subheader("General Patient Risk Overview")

    col_metrics = st.columns(4)
    col_metrics[0].metric("Bleeding Risk", f"{br}%", "MED" if br < 70 else "CRITICAL")
    col_metrics[1].metric("Hypoglycemic Risk", f"{hr}%", alert_label)
    col_metrics[2].metric("AKI Risk (Renal)", f"{ar}%", "HIGH" if ar >= 70 else "LOW")
    col_metrics[3].metric("Clinical Fragility Index", f"{cfr}%", "HIGH" if cfr >= 70 else "LOW")

    st.markdown("---")
    
    col_left, col_right = st.columns([3, 7])

    # --- LEFT COLUMN: THE "INBOX" (Simplified Queue based on session state) ---
    with col_left:
        st.subheader("⚠️ Patient Queue")
        
        # Queue item reflects the current session state risk
        st.markdown(f'<div style="background-color:#B30000; color:white; padding:10px; border-radius:5px;">'
                    f'**Current Session Patient**<br>'
                    f'🔴 **Risk: {max_risk}% ({alert_label})**<br>'
                    f'*Issue: {primary_threat}*</div>', 
                    unsafe_allow_html=True)
        st.markdown("---")
        st.info("The remaining queue shows historical alerts (hardcoded).")
        # Hardcoded items for visual context
        st.markdown(f'<div style="background-color:#FF8C00; color:black; padding:10px; border-radius:5px;">**Patient B** (Room 410)<br>🟠 **Risk: 80% (HIGH)**<br>*Issue: AKI Risk*</div>', unsafe_allow_html=True)
        st.markdown(f'<div style="background-color:#A8D08D; color:black; padding:10px; border-radius:5px;">**Patient C** (Room 105)<br>🟡 **Risk: 60% (MED)**<br>*Issue: Bleeding Risk*</div>', unsafe_allow_html=True)


    # --- RIGHT COLUMN: THE "DEEP DIVE" (Analysis based on Session State) ---
    with col_right:
        st.subheader(f"Analysis: Patient Profile (Age {patient['age']}/{patient['gender']})")
        st.caption(f"Risk Focus: {primary_threat}")
        
        # Patient Profile
        st.markdown("#### 📋 Patient Profile")
        profile_col1, profile_col2, profile_col3 = st.columns(3)
        profile_col1.markdown(f"**Age/Gender:** {patient['age']} / {patient['gender']}")
        profile_col1.markdown(f"**Weight:** {patient['weight']} kg")
        profile_col2.markdown(f"**Fragility Index:** {cfr}%")
        profile_col2.markdown(f"**INR:** (Not Calculated)")
        profile_col3.markdown(f"**Risk Focus:** {primary_threat}")
        
        st.markdown("---")

        # The Big Score
        metric_col1, metric_col2 = st.columns([2, 4])
        with metric_col1:
            st.metric(label=f"{primary_threat} Probability", value=f"{max_risk}%", delta=alert_label)
        with col_right:
            st.markdown(f"#### 🚨 Primary Threat: {primary_threat}")
            st.markdown("Prediction window: Next 24 Hours")

        st.markdown("---")
        
        st.info(f"**Note:** To see the Feature Importance Chart, calculate a patient's risk in the **Risk Calculator** menu.")


# ---------------------------------------------------
# PAGE 1 – Risk Calculator (Input/Calculation)
# ---------------------------------------------------
elif menu == "Risk Calculator":
    st.subheader("Manual Multiple-Risk Calculator (High-Detail)")
    st.caption("Adjust the patient factors below to see the predicted risk scores for multiple ADEs.")

    # --- DEMOGRAPHIC & CORE INPUTS ---
    st.markdown("#### 👤 Patient Demographics & Core Factors")
    
    # CORRECTED INPUT LAYOUT
    demo_col1, demo_col2, demo_col3 = st.columns(3)
    
    # Column 1: Core Identity
    age_calc = demo_col1.number_input("Age", 18, 100, 78)
    gender_calc = demo_col1.selectbox("Gender", ['Male', 'Female'], index=1)
    race_calc = demo_col1.selectbox("Race/Ethnicity", ['Non-Hispanic Black', 'Other'], index=1)

    # Column 2: Vitals & Key Labs 
    weight_calc = demo_col2.number_input("Weight (kg)", 30, 150, 55)
    height_calc = demo_col2.number_input("Height (cm)", 100, 220, 175)
    inr_calc = demo_col2.number_input("INR (if applicable)", 0.5, 10.0, 4.1, format="%.2f")

    # Column 3: Baseline Risks (Creatinine)
    baseline_creat = demo_col3.number_input("Baseline Creatinine (mg/dL)", 0.5, 5.0, 0.9, format="%.1f") 
    
    st.markdown("---")
    
    # --- ACUTE & CHRONIC INPUTS (CHECKBOXES MOVED HERE) ---
    input_col1, input_col2, input_col3 = st.columns(3)
    
    # Column 1: Bleeding & GI Factors (Consolidated)
    st.markdown("#### 🩸 Bleeding & GI Factors")
    prior_stroke = input_col1.checkbox("History of Stroke/TIA", value=True) 
    hist_gi_bleed = input_col1.checkbox("History of GI Bleed", value=True)
    on_anticoag = input_col1.checkbox("Anticoagulant Use", value=True)
    on_antiplatelet = input_col1.checkbox("Antiplatelet Use (Aspirin/Plavix)", value=True)
    
    # Lifestyle/Acute Factors (consolidated under Bleeding)
    uncontrolled_bp = input_col1.checkbox("Uncontrolled BP (Systolic > 140)", value=True) 
    smoking_calc = input_col1.checkbox("Current Smoker", value=True) 
    alcohol_use = input_col1.checkbox("Heavy Alcohol Use", value=True)
    antibiotic_order = input_col1.checkbox("New Antibiotic Order", value=True)
    dietary_change = input_col1.checkbox("Significant Dietary Change (Vit K)", value=False)
    liver_disease = input_col1.checkbox("History of Liver Disease", value=True) 


    # Column 2: Diabetes & Renal Factors (Unmodified)
    st.markdown("#### 🦠 Diabetes & Renal Factors")
    on_insulin = input_col2.checkbox("Insulin/High-Risk DM Meds", value=True)
    high_hba1c = input_col2.checkbox("HbA1c > 9.0% (Poor DM Control)", value=True)
    neuropathy_history = input_col2.checkbox("History of Neuropathy/Ulcer", value=False)
    impaired_renal = input_col2.checkbox("Impaired Renal Status", value=True)
    recent_dka = input_col2.checkbox("Recent DKA/HHS Admission", value=True)


    # Column 3: Cardiovascular & Cancer Factors (Unmodified)
    st.markdown("#### ❤️ Cardio & Other Risks")
    on_acei_arb = input_col3.checkbox("ACEi/ARB Therapy", value=False)
    on_diuretic = input_col3.checkbox("Diuretic Use", value=False)
    active_chemo = input_col3.checkbox("Active Chemotherapy", value=True)
    contrast_exposure = input_col3.checkbox("Recent Contrast Dye Exposure", value=False)


    # --- CALCULATIONS ---
    # Passing new demographic factors to the calculation functions
    bleeding_risk = calculate_bleeding_risk(age_calc, inr_calc, on_anticoag, hist_gi_bleed, uncontrolled_bp, on_antiplatelet, gender_calc, weight_calc, smoking_calc, alcohol_use, antibiotic_order, dietary_change, liver_disease, prior_stroke)
    hypoglycemic_risk = calculate_hypoglycemic_risk(on_insulin, impaired_renal, high_hba1c, neuropathy_history, gender_calc, weight_calc, recent_dka)
    aki_risk = calculate_aki_risk(age_calc, on_diuretic, on_acei_arb, uncontrolled_bp, active_chemo, gender_calc, weight_calc, race_calc, baseline_creat, contrast_exposure)
    comorbidity_load = calculate_comorbidity_load(prior_stroke, active_chemo, recent_dka, liver_disease, smoking_calc, uncontrolled_bp)


    st.markdown("---")
    
    # --- OUTPUTS ---
    output_col1, output_col2, output_col3, output_col4 = st.columns(4)
    output_col1.metric("Bleeding Risk", f"{bleeding_risk}%", "CRITICAL ALERT")
    output_col2.metric("Hypoglycemia Risk", f"{hypoglycemic_risk}%", "CRITICAL ALERT")
    output_col3.metric("AKI Risk (Renal)", f"{aki_risk}%", "HIGH ALERT")
    output_col4.metric("Clinical Fragility Index", f"{comorbidity_load}%", "CRITICAL ALERT")


    # 2. Determine and Display Specific Alert
    max_risk = max(bleeding_risk, hypoglycemic_risk, aki_risk)
    
    if max_risk >= 70:
        # Gather all inputs into a dictionary for easy passing to the alert function
        inputs = {
            'inr': inr_calc, 'antibiotic_order': antibiotic_order, 'on_antiplatelet': on_antiplatelet,
            'alcohol_use': alcohol_use, 'hist_gi_bleed': hist_gi_bleed, 'prior_stroke': prior_stroke,
            'impaired_renal': impaired_renal, 'high_hba1c': high_hba1c, 'recent_dka': recent_dka,
            'weight': weight_calc, 'baseline_creat': baseline_creat, 'active_chemo': active_chemo,
            'on_acei_arb': on_acei_arb, 'on_diuretic': on_diuretic, 'contrast_exposure': contrast_exposure
        }
        
        # Determine the highest risk type for generating the detailed alert
        if bleeding_risk == max_risk:
            risk_type = "Bleeding"
        elif hypoglycemic_risk == max_risk:
            risk_type = "Hypoglycemic"
        elif aki_risk == max_risk:
            risk_type = "AKI"
        else:
            risk_type = "General" 

        alert_message = generate_detailed_alert(risk_type, inputs)

        st.error(alert_message)
        
        # --- THE LOAD BUTTON LOGIC IS HERE ---
        if st.button("Load Patient to Dashboard"):
            # Save the calculated scores and core demographics
            st.session_state['patient_loaded'] = True
            st.session_state['bleeding_risk'] = bleeding_risk
            st.session_state['hypoglycemic_risk'] = hypoglycemic_risk
            st.session_state['aki_risk'] = aki_risk
            st.session_state['fragility_index'] = comorbidity_load
            st.session_state['patient_info'] = {'age': age_calc, 'gender': gender_calc, 'weight': weight_calc}
            st.toast("Patient data loaded! Switch to Live Dashboard.")
    else:
        st.success("Patient risk is manageable. Monitoring is sufficient.")
