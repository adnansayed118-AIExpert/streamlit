import streamlit as st
import plotly.graph_objects as go
from reportlab.pdfgen import canvas
import io
from dataclasses import dataclass

st.set_page_config(page_title="BMI Health App", layout="wide")

st.title("BMI Calculator & Health Report")
st.write("App designed and developed by **Sayed Mohammad Adnan**")

st.image(
    "https://img.freepik.com/free-vector/body-mass-index-illustration_1308-169294.jpg",
    width=250
)

# -----------------------------
# HELPERS + GUIDANCE
# -----------------------------

@dataclass(frozen=True)
class Guidance:
    title: str
    summary: str
    nutrition: list[str]
    activity: list[str]
    habits: list[str]
    seek_help: list[str]


def bmi_category(bmi: float) -> tuple[str, str]:
    if bmi < 18.5:
        return "Underweight", "lightblue"
    if bmi < 25:
        return "Normal weight", "green"
    if bmi < 30:
        return "Overweight", "orange"
    if bmi < 35:
        return "Obese (Class I)", "red"
    if bmi < 40:
        return "Obese (Class II)", "darkred"
    return "Obese (Class III)", "darkred"


def mifflin_st_jeor_bmr(gender: str, weight_kg: float, height_cm: float, age: int) -> float:
    base = 10 * weight_kg + 6.25 * height_cm - 1 * age
    return base + 1 if gender == "Male" else base - 161


def activity_multiplier(level: str) -> float:
    return {
        "Sedentary (little or no exercise)": 1.2,
        "Light (1–3 days/week)": 1.375,
        "Moderate (3–5 days/week)": 1.55,
        "Active (6–7 days/week)": 1.725,
        "Very active (hard training / physical job)": 1.9,
    }[level]


def healthy_weight_range_kg(height_m: float) -> tuple[float, float]:
    return 18.5 * (height_m**2), 24.9 * (height_m**2)


GUIDANCE: dict[str, Guidance] = {
    "Underweight": Guidance(
        title="Underweight",
        summary="Focus on safe weight gain: more calories + strength training + sleep.",
        nutrition=[
            "Add 300–500 calories/day using nutrient‑dense foods (milk/yogurt, nuts, peanut butter, eggs, rice, potatoes).",
            "Aim for protein with every meal (about 1.6–2.2 g/kg/day if you can).",
            "Eat 3 meals + 1–2 snacks; choose smoothies/shakes if appetite is low.",
            "If weight loss was unintentional, consider a medical check for thyroid/gut/stress causes.",
        ],
        activity=[
            "Do strength training 2–4x/week (squat, push, pull, hinge) to gain muscle.",
            "Keep cardio light/moderate; avoid excessive long-duration cardio if struggling to gain weight.",
        ],
        habits=[
            "Sleep 7–9 hours; poor sleep reduces appetite and muscle gain.",
            "Track body weight weekly and adjust calories if not gaining ~0.25–0.5 kg/week.",
        ],
        seek_help=[
            "If you have fatigue, dizziness, or rapid/unexplained weight loss.",
            "If you suspect an eating disorder or have persistent low appetite.",
        ],
    ),
    "Overweight": Guidance(
        title="Overweight",
        summary="Aim for slow fat loss: small calorie deficit + steps + strength training.",
        nutrition=[
            "Create a small deficit (~300–500 calories/day); prioritize protein and fiber.",
            "Build plates: 1/2 vegetables, 1/4 protein, 1/4 carbs; add healthy fats in small amounts.",
            "Limit sugary drinks, deep-fried snacks, and late-night ultra-processed foods.",
            "Use portion control; eat slowly and stop at 80% full.",
        ],
        activity=[
            "Target 7,000–10,000 steps/day and 150 min/week of brisk walking or cycling.",
            "Strength train 2–3x/week to keep muscle while losing fat.",
        ],
        habits=[
            "Weigh weekly; measure waist monthly (waist changes can show progress even when weight stalls).",
            "Plan sleep and stress management—both strongly affect hunger and cravings.",
        ],
        seek_help=[
            "If you have high BP, high sugar, fatty liver, or sleep apnea symptoms (snoring/daytime sleepiness).",
            "If weight keeps rising despite consistent healthy habits.",
        ],
    ),
    "Obese (Class I)": Guidance(
        title="Obese (Class I)",
        summary="Prioritize health markers: gradual weight loss, joint-friendly activity, and checkups.",
        nutrition=[
            "Start with a sustainable deficit; avoid crash diets (they often rebound).",
            "Protein + vegetables first; keep refined carbs and sweets occasional.",
            "Use consistent meal timing to reduce random snacking.",
            "If possible, meet a dietitian for a personalized plan (especially with diabetes/thyroid issues).",
        ],
        activity=[
            "Begin with low-impact options: walking, cycling, swimming; build up slowly.",
            "Strength training 2x/week helps joints, metabolism, and daily function.",
        ],
        habits=[
            "Track key habits (steps, protein, sleep) more than perfect calorie counting.",
            "Break sitting time every hour; even 2–3 minutes helps.",
        ],
        seek_help=[
            "Get screening (BP, lipids, HbA1c) and discuss safe weight-loss options with a doctor.",
            "If you get chest pain, shortness of breath, or joint pain limiting movement.",
        ],
    ),
    "Obese (Class II)": Guidance(
        title="Obese (Class II)",
        summary="Medical support can help: combine lifestyle + clinician guidance.",
        nutrition=[
            "Use structured meals and a consistent plan; avoid extreme restriction.",
            "Prioritize protein and fiber; keep calories mostly from whole foods.",
        ],
        activity=[
            "Low-impact cardio + strength training, scaled to comfort and joints.",
            "Start small (10–15 min/day) and progress weekly.",
        ],
        habits=[
            "Sleep and stress are non‑negotiable; they affect hunger hormones.",
            "Use a weekly check-in: weight, waist, steps, and energy level.",
        ],
        seek_help=[
            "Discuss medications/structured programs with a doctor if lifestyle alone isn’t enough.",
            "Screen for sleep apnea, prediabetes/diabetes, and high blood pressure.",
        ],
    ),
    "Obese (Class III)": Guidance(
        title="Obese (Class III)",
        summary="Strongly consider medical management; focus on safe progress and mobility.",
        nutrition=[
            "A clinician-guided plan is recommended; treat this as a medical condition, not willpower.",
            "Keep meals simple and consistent; choose minimally processed foods most of the time.",
        ],
        activity=[
            "Prioritize daily mobility (short walks, chair exercises) and joint-safe training.",
            "Progress slowly; pain-free consistency matters more than intensity.",
        ],
        habits=[
            "Set 1–2 habits at a time (e.g., steps + sugary drinks). Build momentum.",
            "Use support: family, coach, dietitian, or structured program.",
        ],
        seek_help=[
            "See a doctor for a comprehensive plan (medications, sleep apnea evaluation, and other options).",
            "Seek urgent care if you have severe shortness of breath, chest pain, or swelling in legs.",
        ],
    ),
}


def guidance_for(category: str) -> Guidance | None:
    if category == "Normal weight":
        return None
    if category.startswith("Obese"):
        return GUIDANCE.get(category) or GUIDANCE["Obese (Class I)"]
    return GUIDANCE.get(category)


def create_pdf(
    name: str,
    gender: str,
    age: int,
    bmi: float,
    category: str,
    height_cm: float,
    weight_kg: float,
    tdee: float | None,
    tips: list[str],
):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer)

    c.setFont("Helvetica-Bold", 16)
    c.drawString(170, 800, "BMI HEALTH REPORT")

    c.setFont("Helvetica", 12)
    y = 755
    lines = [
        f"Name: {name}",
        f"Gender: {gender}",
        f"Age: {age}",
        f"Height: {height_cm:.1f} cm",
        f"Weight: {weight_kg:.1f} kg",
        f"BMI Value: {bmi:.2f}",
        f"BMI Category: {category}",
        "Healthy BMI Range: 18.5 - 24.9",
    ]
    if tdee is not None:
        lines.append(f"Estimated daily calories (TDEE): ~{tdee:.0f} kcal/day")

    for line in lines:
        c.drawString(70, y, line)
        y -= 22

    y -= 10
    c.setFont("Helvetica-Bold", 12)
    c.drawString(70, y, "Personal guidance (summary):")
    y -= 20
    c.setFont("Helvetica", 11)
    for t in tips[:10]:
        if y < 80:
            c.showPage()
            y = 800
            c.setFont("Helvetica", 11)
        c.drawString(80, y, f"- {t}")
        y -= 18

    c.save()
    buffer.seek(0)
    return buffer


# -----------------------------
# USER INPUT SECTION (DYNAMIC)
# -----------------------------

with st.sidebar:
    st.subheader("Your details")
    unit = st.radio("Units", ["Metric (kg, cm)", "Imperial (lb, ft/in)"], horizontal=True)
    name = st.text_input("Name")
    gender = st.radio("Gender", ["Male", "Female"], horizontal=True)
    age = st.number_input("Age", min_value=0, max_value=120, value=22, step=1)

    if unit == "Metric (kg, cm)":
        weight = st.number_input("Weight (kg)", min_value=1.0, step=0.1, value=60.0)
        height_cm = st.number_input("Height (cm)", min_value=50.0, step=0.1, value=170.0)
    else:
        weight_lb = st.number_input("Weight (lb)", min_value=1.0, step=0.1, value=150.0)
        h_ft = st.number_input("Height (ft)", min_value=1, max_value=8, value=5, step=1)
        h_in = st.number_input("Height (in)", min_value=0, max_value=11, value=7, step=1)
        weight = weight_lb * 0.45359237
        height_cm = (h_ft * 12 + h_in) * 2.54

    activity_level = st.selectbox(
        "Activity level",
        [
            "Sedentary (little or no exercise)",
            "Light (1–3 days/week)",
            "Moderate (3–5 days/week)",
            "Active (6–7 days/week)",
            "Very active (hard training / physical job)",
        ],
    )

    calculate = st.button("Calculate BMI", use_container_width=True)

height_m = height_cm / 100

# -----------------------------
# BMI CALCULATION
# -----------------------------

if calculate:

    if name == "":
        st.error("Please enter your name")
        st.stop()

    if height_m <= 0:
        st.error("Height must be greater than zero")
        st.stop()

    bmi = weight / (height_m ** 2)
    category, _color = bmi_category(bmi)
    bmr = mifflin_st_jeor_bmr(gender=gender, weight_kg=weight, height_cm=height_cm, age=int(age))
    tdee = bmr * activity_multiplier(activity_level)
    hw_min, hw_max = healthy_weight_range_kg(height_m)
    bmi_prime = bmi / 25.0

    st.subheader(f"Hello {name}")

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("BMI", f"{bmi:.2f}", help="BMI = weight(kg) / height(m)^2")
    m2.metric("Category", category)
    m3.metric("Healthy weight range", f"{hw_min:.1f}–{hw_max:.1f} kg")
    m4.metric("Estimated daily calories", f"{tdee:.0f} kcal", help="TDEE estimate using Mifflin-St Jeor + activity multiplier.")

    # BMI Category
    if category == "Underweight":
        st.warning("You are Underweight")
        st.image(
            "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQq2p9cqSwYeMD0ZY1w9NzlpxoCIEjN0e0lNw&s",
            caption="Underweight BMI",
            width=300
        )

    elif category == "Normal weight":
        st.success("You have Normal weight")
        st.image(
            "https://cdn.vectorstock.com/i/1000v/67/61/cartoon-young-boy-thumbs-up-vector-47696761.jpg",
            caption="Normal BMI",
            width=300
        )

    elif category == "Overweight":
        st.info("You are Overweight")
        st.image(
            "https://previews.123rf.com/images/topvectors/topvectors2010/topvectors201000059/156320634-cute-overweight-boy-chubby-plump-kid-character-cartoon-style-vector-illustration.jpg",
            caption="Overweight BMI",
            width=300
        )

    else:
        st.error(f"You are {category}")
        st.image(
            "https://img.freepik.com/free-vector/overweight-man-eating-fast-food-table-isolated_1308-133546.jpg",
            caption="Obese BMI",
            width=300
        )

    # -----------------------------
    # BMI GAUGE METER
    # -----------------------------

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=bmi,
        title={'text': "BMI Gauge"},
        gauge={
            'axis': {'range': [10, 40]},
            'steps': [
                {'range': [10, 18.5], 'color': "lightblue"},
                {'range': [18.5, 24.9], 'color': "green"},
                {'range': [25, 29.9], 'color': "orange"},
                {'range': [30, 40], 'color': "red"}
            ]
        }
    ))

    st.plotly_chart(fig, use_container_width=True)

    # -----------------------------
    # INSIGHTS + GUIDANCE
    # -----------------------------

    left, right = st.columns([1.15, 0.85], gap="large")

    with left:
        st.subheader("Your quick insights")
        st.write(
            f"- **BMI prime**: **{bmi_prime:.2f}** (BMI / 25)\n"
            f"- **BMR estimate**: **{bmr:.0f} kcal/day**\n"
            f"- **Activity level**: **{activity_level}**"
        )
        st.caption(
            "BMI is a screening tool and does not measure body fat directly. If you are very muscular, pregnant, "
            "or have special medical conditions, BMI may be less accurate."
        )

    with right:
        st.subheader("BMI chart")
        if gender == "Male":
            st.image(
                "https://cdn.vectorstock.com/i/1000v/32/89/body-mass-index-chart-for-men-vector-20533289.jpg",
                caption="Male BMI Chart",
                width=350
            )
        else:
            st.image(
                "https://cdn.vectorstock.com/i/1000v/35/26/body-mass-index-chart-for-women-vector-20533526.jpg",
                caption="Female BMI Chart",
                width=350
            )

    g = guidance_for(category)
    tips_for_pdf: list[str] = []

    if g is not None:
        st.subheader("How to keep healthy (personal guidance)")
        st.write(f"**{g.summary}**")
        t1, t2, t3, t4 = st.tabs(["Nutrition", "Activity", "Habits", "When to seek help"])
        with t1:
            for x in g.nutrition:
                st.write(f"- {x}")
        with t2:
            for x in g.activity:
                st.write(f"- {x}")
        with t3:
            for x in g.habits:
                st.write(f"- {x}")
        with t4:
            for x in g.seek_help:
                st.write(f"- {x}")

        tips_for_pdf = g.nutrition[:3] + g.activity[:2] + g.habits[:2] + g.seek_help[:2]
    else:
        st.subheader("How to keep healthy (for normal BMI)")
        st.success("You are in a healthy BMI range. Keep it up with these habits:")
        normal_tips = [
            "Eat mostly whole foods: protein + vegetables + fruits + whole grains.",
            "Strength train 2–3x/week and aim for 7,000–10,000 steps/day.",
            "Sleep 7–9 hours and manage stress to keep appetite and energy stable.",
            "Get regular checkups (BP, sugar, lipids) especially if family history is strong.",
        ]
        for x in normal_tips:
            st.write(f"- {x}")
        tips_for_pdf = normal_tips

    # -----------------------------
    # PDF REPORT GENERATION
    # -----------------------------
    pdf = create_pdf(
        name=name,
        gender=gender,
        age=int(age),
        bmi=bmi,
        category=category,
        height_cm=height_cm,
        weight_kg=weight,
        tdee=tdee,
        tips=tips_for_pdf,
    )

    st.download_button(
        label="Download BMI Report",
        data=pdf,
        file_name="BMI_Report.pdf",
        mime="application/pdf"
    )