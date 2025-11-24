import streamlit as st
import pandas as pd
import altair as alt
from fpdf import FPDF
import openai

# -----------------------------

# SESSION STATE INITIALIZATION

# -----------------------------

if 'patient_loaded' not in st.session_state:
st.session_state['patient_loaded'] = False
st.session_state['bleeding_risk'] = 0
st.session_state['hypoglycemic_risk'] = 0
st.session_state['aki_risk'] = 0
st.session_state['fragility_index'] = 0
st.session_state['patient_info'] = {'age': 70, 'gender': 'Male', 'weight': 75}

# -----------------------------

# RISK CALCULATION FUNCTIONS

# -----------------------------

def calculate_bleeding_risk(age, inr, anticoagulant, gi_bleed, high_bp, antiplatelet_use, gender, weight, smoking, alcohol_use, antibiotic_order, dietary_change, liver_disease, prior_stroke):
score = 0
score += 35 if anticoagulant else 0
score += 40 if inr > 3.5 else 0
score += 30 if gi_bleed else 0
score += 15 if antiplatelet_use else 0
score += 25 if antibiotic_order else 0
score += 15 if alcohol_use else 0
score += 20 if liver_disease else 0
score += 10 if dietary_change else 0
score += 10 if age > 70 else 0
score += 10 if high_bp else 0
score += 10 if smoking else 0
score += 5 if gender == 'Female' else 0
score += 15 if weight > 120 or weight < 50 else 0
score += 15 if prior_stroke else 0
return min(score, 100)

def calculate_hypoglycemia_risk(insulin_use, renal_status, high_hba1c, neuropathy_history, gender, weight, recent_dka):
score = 0
score += 30 if insulin_use else 0
score += 45 if renal_status else 0
score += 20 if high_hba1c else 0
score += 10 if neuropathy_history else 0
score += 10 if weight < 60 else 0
score += 20 if recent_dka else 0
return min(score, 100)

def calculate_aki_risk(age, diuretic_use, acei_arb_use, high_bp, active_chemo, gender, weight, race, baseline_creat, contrast_exposure):
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
load = 0
load += 25 if prior_stroke else 0
load += 30 if active_chemo else 0
load += 20 if recent_dka else 0
load += 15 if liver_disease else 0
load += 10 if smoking else 0
load += 10 if high_bp else 0
return min(load, 100)

# -----------------------------

# DETAILED ALERT FUNCTION

# -----------------------------

def generate_detailed_alert(risk_type, inputs):
alert = ""
if risk_type == "Bleeding":
alert += "⚠️ **CRITICAL BLEEDING RISK** detected.\n\n"
alert += "Key drivers of risk:\n"
if inputs['inr'] > 3.5: alert += f"- INR ({inputs['inr']}) high\n"
if inputs['on_antiplatelet']: alert += "- Antiplatelet therapy\n"
if inputs['hist_gi_bleed']: alert += "- Prior GI bleed\n"
if inputs['antibiotic_order']: alert += "- Recent antibiotic\n"
if inputs['alcohol_use']: alert += "- Alcohol use\n"
if inputs['prior_stroke']: alert += "- History of stroke/TIA\n"
if inputs['liver_disease']: alert += "- Liver disease\n"
alert += "\n▶ Suggested Action: Recheck INR, monitor bleeding, reassess meds."
elif risk_type == "Hypoglycemic":
alert += "⚠️ **CRITICAL HYPOGLYCEMIA RISK** detected.\n\n"
if inputs['impaired_renal']: alert += "- Impaired renal function\n"
if inputs['high_hba1c']: alert += "- Poor diabetes control\n"
if inputs['recent_dka']: alert += "- Recent DKA/HHS\n"
if inputs['weight'] < 60: alert += "- Low body weight\n"
alert += "\n▶ Suggested Action: Review insulin dose, monitor glucose, check renal panel."
elif risk_type == "AKI":
alert += "⚠️ **HIGH RISK OF AKI** detected.\n\n"
if inputs['baseline_creat'] > 1.5: alert += f"- Creatinine ({inputs['baseline_creat']}) elevated\n"
if inputs['active_chemo']: alert += "- Active chemotherapy\n"
if inputs['on_acei_arb']: alert += "- ACEi/ARB therapy\n"
if inputs['on_diuretic']: alert += "- Diuretics\n"
if inputs['contrast_exposure']: alert += "- Contrast dye\n"
alert += "\n▶ Suggested Action: Check BMP, hydrate, hold nephrotoxic meds."
else:
alert += "⚠️ High clinical risk detected."
return alert

# -----------------------------

# CHATBOT & DRUG INTERACTIONS

# -----------------------------

interaction_db = {
("warfarin", "amiodarone"): "Major: Amiodarone increases INR; high bleeding risk."
}

def check_interaction(drug1, drug2):
d1, d2 = drug1.lower().strip(), drug2.lower().strip()
if (d1, d2) in interaction_db: return interaction_db[(d1,d2)]
if (d2, d1) in interaction_db: return interaction_db[(d2,d1)]
return "No major interaction found."

def chatbot_response(text):
text = text.lower()
responses = {
"warfarin": "Warfarin interacts with medications; increases bleeding risk.",
"aki": "AKI risk is increased by ACEi/ARB, diuretics, and contrast.",
}
for key in responses:
if key in text: return responses[key]
return "Provide more clinical context."

# -----------------------------

# STREAMLIT APP

# -----------------------------

st.set_page_config(page_title="ADE Shield Enhanced", layout="wide")
st.title("🛡️ ADE Shield - Clinical Risk Monitor")

with st.sidebar:
menu = st.radio("Select View", ["Live Dashboard", "Risk Calculator", "CSV Upload", "Medication Checker", "Chatbot"], index=0)

# -----------------------------

# LIVE DASHBOARD

# -----------------------------

if menu == "Live Dashboard":
st.subheader("General Patient Risk Overview")
br, hr, ar, cfr = 60, 92, 80, 75
primary_threat = "Hypoglycemia Risk"
alert_color = "red"
alert_label = "CRITICAL"
col1, col2, col3, col4 = st.columns(4)
col1.metric("Bleeding Risk", f"{br}%", "MED" if br<70 else "CRITICAL")
col2.metric("Hypoglycemia Risk", f"{hr}%", alert_label)
col3.metric("AKI Risk", f"{ar}%", "HIGH" if ar>=70 else "LOW")
col4.metric("Clinical Fragility Index", f"{cfr}%", "HIGH" if cfr>=70 else "LOW")
st.markdown("---")

# -----------------------------

# RISK CALCULATOR

# -----------------------------

elif menu == "Risk Calculator":
st.subheader("Manual Risk Calculator")
# ... [The Risk Calculator code from previous block] ...

# -----------------------------

# CSV UPLOAD WITH BULK ANALYSIS

# -----------------------------

elif menu == "CSV Upload":
st.subheader("Bulk Patient Risk Analysis")
uploaded = st.file_uploader("Upload CSV File", type="csv")
if uploaded:
df = pd.read_csv(uploaded)
st.success(f"CSV loaded with {len(df)} patients")
# Apply risk calculations to each row
df['Bleeding Risk'] = df.apply(lambda x: calculate_bleeding_risk(
x.get('age',70), x.get('inr',1), x.get('on_anticoagulant',0), x.get('hist_gi_bleed',0),
x.get('uncontrolled_bp',0), x.get('on_antiplatelet',0), x.get('gender','Male'),
x.get('weight',70), x.get('smoking',0), x.get('alcohol_use',0), x.get('antibiotic_order',0),
x.get('dietary_change',0), x.get('liver_disease',0), x.get('prior_stroke',0)), axis=1)
df['Hypoglycemia Risk'] = df.apply(lambda x: calculate_hypoglycemia_risk(
x.get('on_insulin',0), x.get('impaired_renal',0), x.get('high_hba1c',0), x.get('neuropathy_history',0),
x.get('gender','Male'), x.get('weight',70), x.get('recent_dka',0)), axis=1)
df['AKI Risk'] = df.apply(lambda x: calculate_aki_risk(
x.get('age',70), x.get('on_diuretic',0), x.get('on_acei_arb',0), x.get('uncontrolled_bp',0),
x.get('active_chemo',0), x.get('gender','Male'), x.get('weight',70), x.get('race','Other'),
x.get('baseline_creat',1), x.get('contrast_exposure',0)), axis=1)
st.dataframe(df)

# -----------------------------

# MEDICATION CHECKER

# -----------------------------

elif menu == "Medication Checker":
st.subheader("Drug-Drug Interaction Checker")
d1 = st.text_input("Drug 1")
d2 = st.text_input("Drug 2")
if d1 and d2:
result = check_interaction(d1,d2)
if "Major" in result: st.error(result)
elif "Moderate" in result: st.warning(result)
else: st.success(result)

# -----------------------------

# CHATBOT

# -----------------------------

elif menu == "Chatbot":
st.subheader("Clinical Information Chatbot")
user_input = st.text_input("Ask a question")
if user_input:
response = chatbot_response(user_input)
st.info(response)
