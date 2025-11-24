import streamlit as st
import pandas as pd
import altair as alt

# -----------------------------
# CORE MODELING LOGIC (FUNCTIONS)
# -----------------------------

def calculate_bleeding_risk(age, inr, anticoagulant, gi_bleed, high_bp, antiplatelet_use, gender, weight, smoking, alcohol_use, antibiotic_order, dietary_change, has_liver_disease, has_stroke):
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
    score += 20 if has_liver_disease else 0   
    score += 10 if dietary_change else 0  
    
    # Chronic / Management / Demographics Factors
    score += 10 if age > 70 else 0
    score += 10 if high_bp else 0
    score += 10 if smoking else 0
    score += 5 if gender == 'Female' else 0
    score += 15 if weight > 120 or weight < 50 else 0
    score += 15 if has_stroke else 0 
    
    return min(score, 100)

def calculate_hypoglycemia_risk(insulin_use, renal_status, high_hba1c, neuropathy_history, gender, weight, recent_dka):
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

def calculate_comorbidity_load(has_stroke, active_chemo, recent_dka, has_liver_disease, smoking, high_bp):
    """Calculates a composite score representing the patient's overall disease burden and clinical fragility."""
    load = 0
    load += 25 if has_stroke else 0
    load += 30 if active_chemo else 0
    load += 20 if recent_dka else 0
    load += 15 if has_liver_disease else 0
    load += 10 if smoking else 0
    load += 10 if high_bp else 0
    return min(load, 100)


# -----------------------------
# SIMPLE CHATBOT & INTERACTIONS
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

interaction_db = {
    ("warfarin", "amiodarone"): "Major: Amiodaride increases INR, high bleeding risk.",
    ("warfarin", "ibuprofen"): "Major: NSAIDs increase bleeding risk with Warfarin.",
    ("apixaban", "ibuprofen"): "Moderate: NSAIDs increase bleeding risk with Apixaban.",
    ("clopidogrel", "aspirin"): "Moderate: Dual antiplatelet therapy, increases bleed risk.",
    ("rivaroxaban", "fluconazole"): "Major: Fluconazole increases Rivaroxaban levels (CYP3A4 inhibitor); high bleeding risk.",
    ("lisinopril", "spironolactone"): "Major: Risk of severe hyperkalemia (high potassium).",
    ("ibuprofen", "lisinopril"): "Major: Severe AKI risk (Triple Whammy component).",
    ("furosemide", "lisinopril"): "Major: Diuretic + ACEi causes severe hypotension and AKI risk.",
    ("glipizide", "alcohol"): "Major: Increased risk of severe hypoglycemia.",
    ("trimethoprim/sulfamethoxazole", "metformin"): "Major: TMP/SMX increases Metformin levels, high hypoglycemia risk.",
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
# PAGE 0 – LIVE DASHBOARD (FINAL PATIENT SUMMARY VIEW)
# ---------------------------------------------------
if menu == "Live Dashboard":
    
    st.subheader("General Patient Risk Overview")

    col_metrics = st.columns(4)
    col_metrics[0].metric("Bleeding Risk", "60%", "MED")
    col_metrics[1].metric("Hypoglycemia Risk", "92%", "CRITICAL")
    col_metrics[2].metric("AKI Risk (Renal)", "80%", "HIGH")
    col_metrics[3].metric("Clinical Fragility Index", "75%", "HIGH")

    st.markdown("---")
    
    col_left, col_right = st.columns([3, 7])

    # --- LEFT COLUMN: THE "INBOX" (Patient Queue) ---
    with col_left:
        st.subheader("⚠️ Patient Queue")
        st.markdown("---")
        
        # 1. Critical Patient 
        st.markdown('<div style="background-color:#B30000; color:white; padding:10px; border-radius:5px;">'
                    '**Patient A** (Room 302)<br>'
                    '🔴 **Risk: 92% (CRITICAL)**<br>'
                    '*Issue: Hypoglycemia Risk*</div>', 
                    unsafe_allow_html=True)
        
        # 2. High Risk Patient
        st.markdown('<div style="background-color:#FF8C00; color:black; padding:10px; border-radius:5px;">'
                    '**Patient B** (Room 410)<br>'
                    '🟠 **Risk: 80% (HIGH)**<br>'
                    '*Issue: AKI Risk*</div>', 
                    unsafe_allow_html=True)
        
        # 3. Medium Risk Patient
        st.markdown('<div style="background-color:#A8D08D; color:black; padding:10px; border-radius:5px;">'
                    '**Patient C** (Room 105)<br>'
                    '🟡 **Risk: 60% (MED)**<br>'
                    '*Issue: Bleeding Risk*', 
                    unsafe_allow_html=True)


    # --- RIGHT COLUMN: THE "DEEP DIVE" (Analysis for Patient A - Hypoglycemia) ---
    with col_right:
        # Header Zone
        st.subheader("Analysis: Patient A (65F)")
        st.caption("Risk Factors: Uncontrolled Diabetes, Impaired Renal Status (Common US Risks)")
        
        # New Section: Summary of Chronic Diseases and Risk Factors
        st.markdown("#### 📋 Patient Profile & History")
        
        profile_col1, profile_col2 = st.columns(2)
        
        profile_col1.markdown("##### 🗂️ **Core Demographics**")
        profile_col1.markdown(f"**Age/Gender:** 65 / Female")
        profile_col1.markdown(f"**Weight:** 55 kg")
        profile_col1.markdown(f"**Race:** Non-Hispanic Black")

        profile_col2.markdown("##### ❤️ **Chronic Conditions**")
        profile_col2.markdown("❌ **History of Stroke/TIA**") 
        profile_col2.markdown("✅ **History of Liver Disease**")
        profile_col2.markdown("✅ **Active Chemotherapy**")
        profile_col2.markdown("✅ **Uncontrolled BP**")
        profile_col2.markdown("✅ **Current Smoker** 🚭")
        
        st.markdown("---")
        
        # The Big Score
        metric_col1, metric_col2 = st.columns([2, 4])
        with metric_col1:
            st.metric(label="Hypoglycemia Probability", value="92%", delta="CRITICAL")
        with metric_col2:
            st.markdown("#### 🚨 Primary Risk: Severe Hypoglycemia Event")
            st.markdown("Prediction window: Next 24 Hours")

        st.markdown("---")

        # The AI "Brain" (Feature Importance Chart)
        st.subheader("🔍 Why did the AI flag this?")
        st.caption("Top factors contributing to this risk score (Mockup of XGBoost Feature Importance)")
        
        # Creating dummy data for the chart visualization (Hypoglycemia factors)
        risk_data = pd.DataFrame({
            'Risk Factor': ['Impaired Renal Status', 'Insulin/High-Risk DM Meds', 'High HbA1c (>9.0%)', 'Low Body Weight (<60kg)'],
            'Contribution': [35, 30, 15, 10]
        })
        
        # Horizontal Bar Chart using Altair
        chart = alt.Chart(risk_data).mark_bar(color='#00BFFF').encode( 
            x='Contribution',
            y=alt.Y('Risk Factor', sort='-x'),
            tooltip=['Risk Factor', 'Contribution']
        ).properties(height=200)
        
        st.altair_chart(chart, use_container_width=True)

        st.markdown("---")

        # The Clinical Evidence
        st.subheader("📋 Live Clinical Context")
        
        evidence_col1, evidence_col2 = st.columns(2)
        with evidence_col1:
            st.markdown("**Active Medications:**")
            st.markdown("- **Insulin** (Sliding Scale)")
            st.markdown("- **Sulfonylurea** (Concurrent use)")
        
        with evidence_col2:
            st.markdown("**Relevant Labs (Last 4 hrs):**")
            st.markdown("- **Glucose:** 105 mg/dL (Dropping) ⬇️")
            st.markdown("- **Creatinine:** 2.8 mg/dL (Impaired Renal)")

        st.markdown("---")
        
        # Action Buttons
        st.subheader("Recommended Action")
        st.info("💡 Recommendation: Hold Sulfonylurea dose. Review insulin sliding scale due to renal impairment.")
        
        st.button("✅ Approve Intervention", type="primary")
        st.button("❌ Snooze Alert")

# ---------------------------------------------------
# PAGE 1 – Risk Calculator (Manual Input)
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
    
    # ICD Input Field
    icd_input = st.text_input("ICD-10 Diagnosis Codes (e.g., I63.9, K74.6)", value="I63.9, K74.6")
    icd_codes = [code.strip().upper() for code in icd_input.split(',') if code.strip()] # Process input string
    
    # Extract ICD booleans for use in calculations
    has_stroke = any(code.startswith('I63') for code in icd_codes)
    has_liver_disease = any(code.startswith('K74') for code in icd_codes)

    st.markdown("---")
    
    # --- ACUTE & CHRONIC INPUTS (CHECKBOXES MOVED HERE) ---
    input_col1, input_col2, input_col3 = st.columns(3)
    
    # Column 1: Bleeding & GI Factors (Consolidated)
    st.markdown("#### 🩸 Bleeding & GI Factors")
    prior_stroke_check = input_col1.checkbox("History of Stroke/TIA (Calculated via ICD-10)", value=has_stroke, disabled=True) 
    hist_gi_bleed = input_col1.checkbox("History of GI Bleed", value=True)
    on_anticoag = input_col1.checkbox("Anticoagulant Use", value=True)
    on_antiplatelet = input_col1.checkbox("Antiplatelet Use (Aspirin/Plavix)", value=True)
    
    # Lifestyle/Acute Factors (consolidated under Bleeding)
    uncontrolled_bp = input_col1.checkbox("Uncontrolled BP (Systolic > 140)", value=True) 
    smoking_calc = input_col1.checkbox("Current Smoker", value=True) 
    alcohol_use = input_col1.checkbox("Heavy Alcohol Use", value=True)
    antibiotic_order = input_col1.checkbox("New Antibiotic Order", value=True)
    dietary_change = input_col1.checkbox("Significant Dietary Change (Vit K)", value=False)
    liver_disease_check = input_col1.checkbox("History of Liver Disease (Calculated via ICD-10)", value=has_liver_disease, disabled=True)


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
    bleeding_risk = calculate_bleeding_risk(age_calc, inr_calc, on_anticoag, hist_gi_bleed, uncontrolled_bp, on_antiplatelet, gender_calc, weight_calc, smoking_calc, alcohol_use, antibiotic_order, dietary_change, has_liver_disease, has_stroke)
    hypoglycemia_risk = calculate_hypoglycemia_risk(on_insulin, impaired_renal, high_hba1c, neuropathy_history, gender_calc, weight_calc, recent_dka)
    aki_risk = calculate_aki_risk(age_calc, on_diuretic, on_acei_arb, uncontrolled_bp, active_chemo, gender_calc, weight_calc, race_calc, baseline_creat, contrast_exposure)
    comorbidity_load = calculate_comorbidity_load(has_stroke, active_chemo, recent_dka, has_liver_disease, smoking_calc, uncontrolled_bp)


    st.markdown("---")
    
    # --- OUTPUTS ---
    output_col1, output_col2, output_col3, output_col4 = st.columns(4)
    output_col1.metric("Bleeding Risk", f"{bleeding_risk}%", "CRITICAL ALERT")
    output_col2.metric("Hypoglycemia Risk", f"{hypoglycemia_risk}%", "CRITICAL ALERT")
    output_col3.metric("AKI Risk (Renal)", f"{aki_risk}%", "HIGH ALERT")
    output_col4.metric("Clinical Fragility Index", f"{comorbidity_load}%", "CRITICAL ALERT")


    # 2. Determine and Display Specific Alert
    max_risk = max(bleeding_risk, hypoglycemia_risk, aki_risk)
    
    if max_risk >= 70:
        if bleeding_risk == max_risk:
            alert_message = "🔴 CRITICAL ALERT: Highest threat is **Bleeding Risk** due to Anticoagulation/INR instability."
        elif hypoglycemia_risk == max_risk:
            alert_message = "🔴 CRITICAL ALERT: Highest threat is **Hypoglycemia Risk** due to Renal Impairment/High Insulin sensitivity."
        elif aki_risk == max_risk:
            alert_message = "🔴 CRITICAL ALERT: Highest threat is **AKI Risk** due to Nephrotoxic Drug Combination or Baseline Kidney Damage."
        else:
            alert_message = "HIGH RISK ALERT: Check specific patient risks." # Fallback for equality cases or if logic missed a path

        st.error(alert_message)
    else:
        st.success("Patient risk is manageable. Monitoring is sufficient.")
