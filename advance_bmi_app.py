import streamlit as st
import plotly.graph_objects as go
from reportlab.pdfgen import canvas
import io

st.set_page_config(page_title="BMI Health App", layout="wide")

st.title("BMI Calculator & Health Report")
st.write("App designed and developed by **Sayed Mohammad Adnan**")

st.image(
    "https://img.freepik.com/free-vector/body-mass-index-illustration_1308-169294.jpg",
    width=250
)

# -----------------------------
# USER INPUT SECTION
# -----------------------------

col1, col2 = st.columns(2)

with col1:
    name = st.text_input("Enter your name")
    gender = st.radio("Select Gender", ["Male", "Female"])

with col2:
    weight = st.number_input("Enter your weight (kg)", min_value=1.0, step=0.1)
    height_cm = st.number_input("Enter your height (cm)", min_value=50.0, step=0.1)

height_m = height_cm / 100

# -----------------------------
# BMI CALCULATION
# -----------------------------

if st.button("Calculate BMI"):

    if name == "":
        st.error("Please enter your name")
        st.stop()

    if height_m <= 0:
        st.error("Height must be greater than zero")
        st.stop()

    bmi = weight / (height_m ** 2)

    st.subheader(f"Hello {name}")
    st.write(f"Your BMI is **{bmi:.2f}**")

    # BMI Category
    if bmi < 18.5:
        category = "Underweight"
        st.warning("You are Underweight")
        st.image(
            "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQq2p9cqSwYeMD0ZY1w9NzlpxoCIEjN0e0lNw&s",
            caption="Underweight BMI",
            width=300
        )

    elif bmi < 25:
        category = "Normal weight"
        st.success("You have Normal weight")
        st.image(
            "https://cdn.vectorstock.com/i/1000v/67/61/cartoon-young-boy-thumbs-up-vector-47696761.jpg",
            caption="Normal BMI",
            width=300
        )

    elif bmi < 30:
        category = "Overweight"
        st.info("You are Overweight")
        st.image(
            "https://previews.123rf.com/images/topvectors/topvectors2010/topvectors201000059/156320634-cute-overweight-boy-chubby-plump-kid-character-cartoon-style-vector-illustration.jpg",
            caption="Overweight BMI",
            width=300
        )

    else:
        category = "Obese"
        st.error("You are Obese")
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
    # GENDER SPECIFIC BMI CHART
    # -----------------------------

    st.subheader("BMI Chart")

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

    # -----------------------------
    # PDF REPORT GENERATION
    # -----------------------------

    def create_pdf(name, gender, bmi, category):

        buffer = io.BytesIO()
        c = canvas.Canvas(buffer)

        c.setFont("Helvetica-Bold", 16)
        c.drawString(180, 800, "BMI HEALTH REPORT")

        c.setFont("Helvetica", 12)
        c.drawString(100, 730, f"Name: {name}")
        c.drawString(100, 700, f"Gender: {gender}")
        c.drawString(100, 670, f"BMI Value: {bmi:.2f}")
        c.drawString(100, 640, f"BMI Category: {category}")

        c.drawString(100, 600, "Healthy BMI Range: 18.5 - 24.9")

        c.save()

        buffer.seek(0)
        return buffer

    pdf = create_pdf(name, gender, bmi, category)

    st.download_button(
        label="Download BMI Report",
        data=pdf,
        file_name="BMI_Report.pdf",
        mime="application/pdf"
    )