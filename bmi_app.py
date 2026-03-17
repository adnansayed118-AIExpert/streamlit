import streamlit as st

st.title("BMI Calculator")

st.write("This is BMI calculator App to calculate your BMI!")
st.write("App design and developed by Sayed Mohammad Adnan")

st.image(
    "https://img.freepik.com/free-vector/body-mass-index-illustration_1308-169294.jpg",
    caption="BMI Chart",
    width=300
)

name = st.text_input("Enter your name")

weight = st.number_input("Enter your weight in Kgs", min_value=1.0)

height_cm = st.number_input("Enter your height in cm", min_value=50.0)

# Convert cm to meters
height_m = height_cm / 100

if st.button("Calculate BMI"):

    bmi = weight / (height_m ** 2)

    st.write(f"Hello {name}")
    st.write(f"Your BMI is: {bmi:.2f}")

    if bmi < 18.5:
        st.warning("You are underweight")
        st.image(
            "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQq2p9cqSwYeMD0ZY1w9NzlpxoCIEjN0e0lNw&s",
            caption="Underweight BMI",
            width=300
        )

    elif 18.5 <= bmi <= 24.9:
        st.success("You are normal weight")
        st.image(
            "https://cdn.vectorstock.com/i/1000v/67/61/cartoon-young-boy-thumbs-up-vector-47696761.jpg",
            caption="Normal BMI",
            width=300
        )

    elif 25 < bmi <= 30:
        st.info("You are overweight")
        st.image(
            "https://previews.123rf.com/images/topvectors/topvectors2010/topvectors201000059/156320634-cute-overweight-boy-chubby-plump-kid-character-cartoon-style-vector-illustration.jpg",
            caption="Overweight BMI",
            width=300
        )

    else:
        st.error("You are obese")
        st.image(
            "https://img.freepik.com/free-vector/overweight-man-eating-fast-food-table-isolated_1308-133546.jpg",
            caption="Obese BMI",
            width=300
        )