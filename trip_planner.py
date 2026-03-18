import hashlib
import random
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta

import pandas as pd
import plotly.express as px
import streamlit as st


@dataclass(frozen=True)
class TripConfig:
    origin_default: str = "Hyderabad (HYD)"
    destination_default: str = "Goa (GOI)"
    nights: int = 2


CFG = TripConfig()


def _seed_from_inputs(*parts: object) -> int:
    # Stable across runs (unlike Python's built-in hash()).
    s = "|".join(str(p) for p in parts).encode("utf-8")
    return int.from_bytes(hashlib.md5(s).digest()[:4], "big", signed=False)


def _fmt_time(t: time) -> str:
    return t.strftime("%I:%M %p").lstrip("0")


def _dt(d: date, t: time) -> datetime:
    return datetime.combine(d, t)


def _duration_mins(dep: time, arr: time) -> int:
    dummy = date(2000, 1, 1)
    a = _dt(dummy, dep)
    b = _dt(dummy, arr)
    if b < a:
        b += timedelta(days=1)
    return int((b - a).total_seconds() // 60)


def build_mock_flights(
    origin: str,
    destination: str,
    depart_date: date,
    return_date: date,
    passengers: int,
) -> pd.DataFrame:
    """
    Returns round-trip flight options as one row per itinerary.
    Prices are per passenger (base) + baggage/fee noise; total_price includes passengers.
    """
    rng = random.Random(_seed_from_inputs(origin, destination, depart_date, return_date, passengers))

    airlines = [
        "IndiGo",
        "Air India",
        "Akasa Air",
        "SpiceJet",
        "Vistara",
        "Go First",
    ]
    dep_slots = [time(5, 40), time(7, 15), time(9, 5), time(12, 20), time(15, 10), time(18, 25), time(21, 5)]
    ret_slots = [time(6, 10), time(8, 50), time(11, 35), time(14, 45), time(17, 30), time(20, 10), time(22, 40)]

    rows: list[dict] = []
    for i in range(18):
        airline = rng.choice(airlines)

        d_dep = rng.choice(dep_slots)
        d_dur = rng.randint(75, 105)  # HYD->GOI typical-ish
        d_arr_dt = _dt(depart_date, d_dep) + timedelta(minutes=d_dur)
        d_arr = d_arr_dt.time()

        r_dep = rng.choice(ret_slots)
        r_dur = rng.randint(75, 110)
        r_arr_dt = _dt(return_date, r_dep) + timedelta(minutes=r_dur)
        r_arr = r_arr_dt.time()

        base = rng.randint(3600, 9800)  # per passenger round-trip
        fee = rng.randint(150, 650)
        per_passenger = base + fee
        total_price = per_passenger * max(1, int(passengers))

        rows.append(
            {
                "itinerary_id": f"RT-{i+1:02d}",
                "origin": origin,
                "destination": destination,
                "airline": airline,
                "depart_date": depart_date.isoformat(),
                "depart_time": _fmt_time(d_dep),
                "depart_arrival_time": _fmt_time(d_arr),
                "depart_duration_mins": _duration_mins(d_dep, d_arr),
                "return_date": return_date.isoformat(),
                "return_time": _fmt_time(r_dep),
                "return_arrival_time": _fmt_time(r_arr),
                "return_duration_mins": _duration_mins(r_dep, r_arr),
                "price_per_passenger": per_passenger,
                "passengers": max(1, int(passengers)),
                "total_price": total_price,
            }
        )

    df = pd.DataFrame(rows).sort_values("total_price", ascending=True, kind="mergesort").reset_index(drop=True)
    return df


def build_mock_oneway_flights(origin: str, destination: str, travel_date: date, passengers: int, seed_tag: str) -> pd.DataFrame:
    """
    Returns one-way flight options as one row per flight.
    Prices are per passenger; total_price includes passengers.
    """
    rng = random.Random(_seed_from_inputs(origin, destination, travel_date, passengers, seed_tag))

    airlines = ["IndiGo", "Air India", "Akasa Air", "SpiceJet", "Vistara", "Go First"]
    slots = [time(5, 40), time(7, 15), time(9, 5), time(11, 25), time(13, 55), time(16, 15), time(18, 25), time(21, 5)]

    rows: list[dict] = []
    for i in range(16):
        airline = rng.choice(airlines)
        dep = rng.choice(slots)
        dur = rng.randint(75, 115)
        arr = (_dt(travel_date, dep) + timedelta(minutes=dur)).time()

        base = rng.randint(1700, 5200)  # per passenger one-way
        fee = rng.randint(120, 520)
        per_passenger = base + fee
        pax = max(1, int(passengers))
        total_price = per_passenger * pax

        rows.append(
            {
                "flight_id": f"{seed_tag}-{i+1:02d}",
                "origin": origin,
                "destination": destination,
                "airline": airline,
                "date": travel_date.isoformat(),
                "departure_time": _fmt_time(dep),
                "arrival_time": _fmt_time(arr),
                "duration_mins": _duration_mins(dep, arr),
                "price_per_passenger": per_passenger,
                "passengers": pax,
                "total_price": total_price,
            }
        )

    return pd.DataFrame(rows).sort_values("total_price", ascending=True, kind="mergesort").reset_index(drop=True)


@st.cache_data(show_spinner=False)
def cached_roundtrip(origin: str, destination: str, depart_date: date, return_date: date, passengers: int) -> pd.DataFrame:
    return build_mock_flights(origin, destination, depart_date, return_date, passengers)


@st.cache_data(show_spinner=False)
def cached_oneway(origin: str, destination: str, travel_date: date, passengers: int, seed_tag: str) -> pd.DataFrame:
    return build_mock_oneway_flights(origin, destination, travel_date, passengers, seed_tag)


@st.cache_data(show_spinner=False)
def cached_hotels(destination: str) -> pd.DataFrame:
    return build_mock_hotels(destination)


@st.cache_data(show_spinner=False)
def cached_restaurants(hotel_location: str) -> pd.DataFrame:
    return build_mock_restaurants(hotel_location)


def build_mock_hotels(destination: str) -> pd.DataFrame:
    hotels = [
        ("Casa Calangute", 1899, 4.1, "Calangute"),
        ("Baga Breeze Inn", 2199, 4.2, "Baga"),
        ("Panjim Heritage Stay", 2499, 4.4, "Panjim"),
        ("Candolim Coastline", 2899, 4.3, "Candolim"),
        ("Anjuna Studio Suites", 3099, 4.0, "Anjuna"),
        ("Morjim Sands Resort", 3499, 4.5, "Morjim"),
        ("Colva Beach Retreat", 3299, 4.2, "Colva"),
        ("Arpora Hillside Hotel", 2699, 4.1, "Arpora"),
        ("Vagator View Boutique", 3999, 4.6, "Vagator"),
        ("Miramar Bay Hotel", 2799, 4.2, "Miramar"),
    ]
    df = pd.DataFrame(hotels, columns=["hotel_name", "price_per_night", "rating", "location"])
    df.insert(0, "city", destination)
    return df


def build_mock_restaurants(hotel_location: str) -> pd.DataFrame:
    base = [
        ("Fisherman’s Wharf", "Seafood, Goan", 450, 4.4),
        ("Vinayak Family Restaurant", "Goan, Indian", 250, 4.3),
        ("Cafe Bodega", "Cafe, Continental", 350, 4.2),
        ("Ritz Classic", "Seafood, Indian", 400, 4.1),
        ("Gunpowder", "South Indian, Fusion", 500, 4.5),
        ("Mum’s Kitchen", "Goan", 480, 4.6),
        ("Pousada by the Beach", "Goan, Seafood", 520, 4.3),
        ("Kokni Kanteen", "Goan", 320, 4.4),
        ("Burger Factory", "Fast Food", 220, 4.0),
        ("The Tibetan Kitchen", "Tibetan, Asian", 300, 4.2),
        ("Delhi Darbar", "North Indian, Mughlai", 280, 4.1),
        ("Souza Lobo", "Goan, Seafood", 460, 4.3),
    ]
    df = pd.DataFrame(base, columns=["restaurant_name", "cuisine", "average_cost", "rating"])
    df.insert(0, "near", hotel_location)
    return df


def inject_modern_css() -> None:
    st.markdown(
        """
<style>
  .block-container { padding-top: 1.1rem; padding-bottom: 2rem; max-width: 1200px; }
  [data-testid="stSidebar"] > div:first-child { padding-top: 1.15rem; }
  .mmt-hero {
    border-radius: 18px;
    padding: 18px 18px 16px 18px;
    background:
      radial-gradient(1300px 420px at 15% 5%, rgba(64, 196, 255, 0.55), transparent 60%),
      radial-gradient(1000px 520px at 85% 35%, rgba(255, 214, 130, 0.60), transparent 60%),
      linear-gradient(135deg, rgba(40, 90, 170, 0.72), rgba(90, 160, 255, 0.70));
    border: 1px solid rgba(255,255,255,0.22);
  }
  .mmt-hero h1 { margin: 0 0 6px 0; letter-spacing: -0.02em; text-shadow: 0 6px 18px rgba(0,0,0,0.35); }
  .mmt-hero p { margin: 0; opacity: 0.96; text-shadow: 0 4px 12px rgba(0,0,0,0.35); }
  .mmt-badge {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 6px 10px;
    border-radius: 999px;
    background: rgba(255,255,255,0.10);
    border: 1px solid rgba(255,255,255,0.10);
    font-size: 12px;
  }
  .mmt-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
  @media (max-width: 760px) { .mmt-grid { grid-template-columns: 1fr; } }
  .mmt-card {
    border-radius: 16px;
    padding: 14px 14px 12px 14px;
    border: 1px solid rgba(255,255,255,0.10);
    background: rgba(255,255,255,0.04);
  }
  .mmt-card:hover { border-color: rgba(0, 184, 255, 0.40); }
  .mmt-card h3 { margin: 0 0 4px 0; font-size: 16px; }
  .mmt-muted { opacity: 0.78; font-size: 13px; }
  .mmt-row { display:flex; gap: 10px; align-items: baseline; flex-wrap: wrap; }
  .mmt-kpi { font-size: 22px; font-weight: 700; letter-spacing: -0.02em; }
  .mmt-chip {
    display:inline-flex; align-items:center; gap:6px;
    padding: 5px 10px; border-radius: 999px;
    background: rgba(255,255,255,0.08);
    border: 1px solid rgba(255,255,255,0.10);
    font-size: 12px;
  }
  .mmt-cheapest {
    border: 1px solid rgba(0, 255, 170, 0.35);
    background: linear-gradient(135deg, rgba(0, 255, 170, 0.10), rgba(255,255,255,0.03));
  }
  .mmt-cta {
    padding: 10px 12px;
    border-radius: 12px;
    background: linear-gradient(135deg, rgba(0, 184, 255, 0.75), rgba(0, 255, 170, 0.65));
    border: 0;
    color: #06121f;
    font-weight: 700;
    text-align:center;
  }
  .mmt-divider { height: 1px; background: rgba(255,255,255,0.10); margin: 10px 0; }
</style>
        """,
        unsafe_allow_html=True,
    )


def money(v: float | int) -> str:
    cur = st.session_state.get("currency", "INR")
    rates = st.session_state.get(
        "fx_rates",
        {
            "INR": {"symbol": "₹", "rate": 1.0},
            "USD": {"symbol": "$", "rate": 1 / 83.0},
            "EUR": {"symbol": "€", "rate": 1 / 90.0},
            "GBP": {"symbol": "£", "rate": 1 / 104.0},
            "AED": {"symbol": "د.إ", "rate": 1 / 22.6},
        },
    )
    symbol = rates.get(cur, rates["INR"])["symbol"]
    rate = float(rates.get(cur, rates["INR"])["rate"])
    val = float(v) * rate
    if cur == "INR":
        return f"{symbol}{int(round(val)):,}"
    return f"{symbol}{val:,.2f}"


def ensure_state() -> None:
    st.session_state.setdefault("selected_flight_id", None)
    st.session_state.setdefault("selected_outbound_id", None)
    st.session_state.setdefault("selected_return_id", None)
    st.session_state.setdefault("selected_hotel_name", None)
    st.session_state.setdefault("selected_restaurants", [])
    st.session_state.setdefault("currency", "INR")
    st.session_state.setdefault(
        "fx_rates",
        {
            "INR": {"symbol": "₹", "rate": 1.0},
            "USD": {"symbol": "$", "rate": 1 / 83.0},
            "EUR": {"symbol": "€", "rate": 1 / 90.0},
            "GBP": {"symbol": "£", "rate": 1 / 104.0},
            "AED": {"symbol": "د.إ", "rate": 1 / 22.6},
        },
    )
    st.session_state.setdefault("payment_status", None)
    st.session_state.setdefault("show_payment", False)


def section_banner(title: str, subtitle: str, image_url: str, icon: str) -> None:
    st.markdown(
        f"""
<div class="mmt-card" style="
  padding: 16px;
  background:
    linear-gradient(90deg, rgba(6,18,31,0.82), rgba(6,18,31,0.25)),
    url('{image_url}');
  background-size: cover;
  background-position: center;
">
  <div class="mmt-row" style="justify-content: space-between; align-items: center;">
    <div>
      <div class="mmt-muted">{icon} {subtitle}</div>
      <h3 style="margin-top:4px;">{title}</h3>
    </div>
    <div class="mmt-badge">Triptastic</div>
  </div>
</div>
        """,
        unsafe_allow_html=True,
    )


def payment_gateway(amount_in_inr: int) -> None:
    cur = st.session_state.get("currency", "INR")
    st.markdown("#### Payment gateway (demo)")
    st.caption("This is a mock checkout flow for UI demo purposes only.")
    st.markdown(f"**Amount to pay:** {money(amount_in_inr)} ({cur})")

    method = st.radio("Choose payment method", ["UPI", "Card", "NetBanking"], horizontal=True)
    ok = False

    if method == "UPI":
        upi = st.text_input("UPI ID", placeholder="name@bank")
        ok = bool(upi.strip())
    elif method == "Card":
        c1, c2 = st.columns(2)
        with c1:
            card = st.text_input("Card number", placeholder="1234 5678 9012 3456")
        with c2:
            exp = st.text_input("Expiry", placeholder="MM/YY")
        c3, c4 = st.columns(2)
        with c3:
            cvv = st.text_input("CVV", placeholder="123", type="password")
        with c4:
            name = st.text_input("Name on card")
        ok = all(x.strip() for x in [card, exp, cvv, name])
    else:
        bank = st.selectbox("Select bank", ["SBI", "HDFC", "ICICI", "Axis", "Kotak"])
        ok = bool(bank)

    if st.button("Pay now", type="primary", disabled=not ok):
        st.session_state["payment_status"] = "success"
        st.success("Payment successful. Booking confirmed (demo).")


def card_flight(row: pd.Series, cheapest_total: int) -> None:
    is_cheapest = int(row["total_price"]) == int(cheapest_total)
    classes = "mmt-card " + ("mmt-cheapest" if is_cheapest else "")

    st.markdown(
        f"""
<div class="{classes}">
  <div class="mmt-row">
    <h3>✈️ {row['airline']} <span class="mmt-muted">({row['itinerary_id']})</span></h3>
    {"<span class='mmt-badge'>🏷️ Cheapest</span>" if is_cheapest else ""}
  </div>
  <div class="mmt-row mmt-muted">
    <span class="mmt-chip">🛫 {row['origin']} → {row['destination']}</span>
    <span class="mmt-chip">📅 {row['depart_date']} · {_fmt_time(datetime.strptime(row['depart_time'], '%I:%M %p').time())}</span>
    <span class="mmt-chip">🕒 {row['depart_time']} → {row['depart_arrival_time']} · {int(row['depart_duration_mins'])}m</span>
  </div>
  <div class="mmt-row mmt-muted" style="margin-top:6px;">
    <span class="mmt-chip">🛬 {row['destination']} → {row['origin']}</span>
    <span class="mmt-chip">📅 {row['return_date']} · {_fmt_time(datetime.strptime(row['return_time'], '%I:%M %p').time())}</span>
    <span class="mmt-chip">🕒 {row['return_time']} → {row['return_arrival_time']} · {int(row['return_duration_mins'])}m</span>
  </div>
  <div class="mmt-divider"></div>
  <div class="mmt-row">
    <div>
      <div class="mmt-muted">Total for {int(row['passengers'])} passenger(s)</div>
      <div class="mmt-kpi">{money(row['total_price'])}</div>
      <div class="mmt-muted">({money(row['price_per_passenger'])} per passenger)</div>
    </div>
  </div>
</div>
        """,
        unsafe_allow_html=True,
    )


def card_hotel(row: pd.Series, cheapest_per_night: int, nights: int) -> None:
    is_cheapest = int(row["price_per_night"]) == int(cheapest_per_night)
    classes = "mmt-card " + ("mmt-cheapest" if is_cheapest else "")
    total = int(row["price_per_night"]) * nights
    st.markdown(
        f"""
<div class="{classes}">
  <div class="mmt-row">
    <h3>🏨 {row['hotel_name']}</h3>
    {"<span class='mmt-badge'>🏷️ Cheapest</span>" if is_cheapest else ""}
  </div>
  <div class="mmt-row mmt-muted">
    <span class="mmt-chip">📍 {row['location']}, Goa</span>
    <span class="mmt-chip">⭐ {float(row['rating']):.1f} / 5</span>
    <span class="mmt-chip">🛏️ {nights} nights</span>
  </div>
  <div class="mmt-divider"></div>
  <div class="mmt-row">
    <div>
      <div class="mmt-muted">Price per night</div>
      <div class="mmt-kpi">{money(row['price_per_night'])}</div>
      <div class="mmt-muted">Est. stay total: <b>{money(total)}</b></div>
    </div>
  </div>
</div>
        """,
        unsafe_allow_html=True,
    )


def card_restaurant(row: pd.Series, budget_threshold: int) -> None:
    is_budget = int(row["average_cost"]) <= int(budget_threshold)
    classes = "mmt-card " + ("mmt-cheapest" if is_budget else "")
    st.markdown(
        f"""
<div class="{classes}">
  <div class="mmt-row">
    <h3>🍽️ {row['restaurant_name']}</h3>
    {"<span class='mmt-badge'>💸 Budget</span>" if is_budget else ""}
  </div>
  <div class="mmt-row mmt-muted">
    <span class="mmt-chip">🍛 {row['cuisine']}</span>
    <span class="mmt-chip">⭐ {float(row['rating']):.1f} / 5</span>
    <span class="mmt-chip">📍 Near {row['near']}</span>
  </div>
  <div class="mmt-divider"></div>
  <div class="mmt-row">
    <div>
      <div class="mmt-muted">Average cost per person</div>
      <div class="mmt-kpi">{money(row['average_cost'])}</div>
    </div>
  </div>
</div>
        """,
        unsafe_allow_html=True,
    )


def main() -> None:
    st.set_page_config(page_title="Triptastic", page_icon="🧳", layout="wide")
    inject_modern_css()
    ensure_state()

    h1, h2 = st.columns([1.35, 0.65], vertical_alignment="center")
    with h1:
        st.markdown(
            f"""
<div class="mmt-hero">
  <div class="mmt-row" style="justify-content: space-between; align-items: center;">
    <div>
      <h1>🧳 Triptastic</h1>
      <p>Plan a <b>2 days / 2 nights</b> round-trip from <b>Hyderabad (HYD)</b> to <b>Goa (GOI)</b> — flights, hotels, restaurants, and a single trip summary.</p>
    </div>
    <div class="mmt-badge">✨ Modern booking UI · Multi-currency · Mock checkout</div>
  </div>
</div>
            """,
            unsafe_allow_html=True,
        )
    with h2:
        # Unsplash image (hotlinked) for a travel vibe; safe to remove if offline usage is needed.
        st.image(
            "https://images.unsplash.com/photo-1548013146-72479768bada?auto=format&fit=crop&w=1200&q=70",
            caption="Goa • beaches • sunsets",
            width="stretch",
        )
    st.write("")

    today = date.today()
    default_depart = today + timedelta(days=7)
    default_return = default_depart + timedelta(days=2)

    with st.sidebar:
        st.subheader("🔎 Trip Search")
        origin = st.selectbox("Departure city", [CFG.origin_default, "Bengaluru (BLR)", "Mumbai (BOM)", "Delhi (DEL)"], index=0)
        destination = st.selectbox("Destination city", [CFG.destination_default, "Mumbai (BOM)", "Delhi (DEL)", "Jaipur (JAI)"], index=0)

        depart_date = st.date_input("Departure date", value=default_depart, min_value=today)
        # Default return is +2 days, but user can override for one-way / flexible trips.
        return_date = st.date_input("Return date", value=depart_date + timedelta(days=CFG.nights), min_value=depart_date)

        passengers = st.slider("Passengers", min_value=1, max_value=6, value=2)

        st.divider()
        st.subheader("💱 Currency")
        st.session_state["currency"] = st.selectbox(
            "Display prices in",
            ["INR", "USD", "EUR", "GBP", "AED"],
            index=["INR", "USD", "EUR", "GBP", "AED"].index(st.session_state.get("currency", "INR")),
        )

        st.divider()
        st.subheader("🎛️ Filters")

        flight_price_max = st.slider("Flight total (max)", min_value=5000, max_value=70000, value=25000, step=500)
        flight_airlines = st.multiselect("Preferred airlines", options=["IndiGo", "Air India", "Akasa Air", "SpiceJet", "Vistara", "Go First"])

        hotel_price_max = st.slider("Hotel per night (max)", min_value=1000, max_value=15000, value=4500, step=100)
        hotel_rating_min = st.slider("Hotel rating (min)", min_value=3.0, max_value=5.0, value=4.0, step=0.1)

        restaurant_cost_max = st.slider("Restaurant average cost (max)", min_value=150, max_value=1200, value=450, step=10)
        restaurant_rating_min = st.slider("Restaurant rating (min)", min_value=3.5, max_value=5.0, value=4.0, step=0.1)

        st.divider()
        st.caption("Tip: use **Trip Summary** tab to review your selections and total cost.")

    flights_df = cached_roundtrip(origin, destination, depart_date, return_date, passengers)
    hotels_df = cached_hotels("Goa")

    # Apply filters
    flights_f = flights_df[flights_df["total_price"] <= int(flight_price_max)].copy()
    if flight_airlines:
        flights_f = flights_f[flights_f["airline"].isin(flight_airlines)].copy()
    flights_f = flights_f.sort_values("total_price", ascending=True, kind="mergesort").reset_index(drop=True)

    hotels_f = hotels_df[
        (hotels_df["price_per_night"] <= int(hotel_price_max)) & (hotels_df["rating"] >= float(hotel_rating_min))
    ].copy()
    hotels_f = hotels_f.sort_values(["price_per_night", "rating"], ascending=[True, False], kind="mergesort").reset_index(drop=True)

    selected_hotel_location = (
        hotels_df.loc[hotels_df["hotel_name"] == st.session_state["selected_hotel_name"], "location"].iloc[0]
        if st.session_state["selected_hotel_name"] in set(hotels_df["hotel_name"])
        else (hotels_f["location"].iloc[0] if len(hotels_f) else "Panjim")
    )
    restaurants_df = cached_restaurants(selected_hotel_location)
    restaurants_f = restaurants_df[
        (restaurants_df["average_cost"] <= int(restaurant_cost_max)) & (restaurants_df["rating"] >= float(restaurant_rating_min))
    ].copy()
    restaurants_f = restaurants_f.sort_values(["average_cost", "rating"], ascending=[True, False], kind="mergesort").reset_index(drop=True)

    tabs = st.tabs(["✈️ Flights", "🏨 Hotels", "🍽️ Restaurants", "🧾 Trip Summary"])

    # ---------------- Flights ----------------
    with tabs[0]:
        section_banner(
            title="Flights: pick outbound + return",
            subtitle="Cheapest first • round-trip planning",
            image_url="https://images.unsplash.com/photo-1436491865332-7a61a109cc05?auto=format&fit=crop&w=1600&q=70",
            icon="✈️",
        )
        st.write("")
        c1, c2 = st.columns([1.6, 1.0], gap="large")
        with c1:
            st.subheader("Return ticket booking options")
            st.caption("Select **outbound** and **return** flights separately (return-ticket options).")

            ow_out = cached_oneway(origin, destination, depart_date, passengers, seed_tag="OUT")
            ow_ret = cached_oneway(destination, origin, return_date, passengers, seed_tag="RET")

            ow_out_f = ow_out[ow_out["total_price"] <= int(flight_price_max)].copy()
            ow_ret_f = ow_ret[ow_ret["total_price"] <= int(flight_price_max)].copy()
            if flight_airlines:
                ow_out_f = ow_out_f[ow_out_f["airline"].isin(flight_airlines)].copy()
                ow_ret_f = ow_ret_f[ow_ret_f["airline"].isin(flight_airlines)].copy()
            ow_out_f = ow_out_f.sort_values("total_price", ascending=True, kind="mergesort").reset_index(drop=True)
            ow_ret_f = ow_ret_f.sort_values("total_price", ascending=True, kind="mergesort").reset_index(drop=True)

            st.markdown("#### 🛫 Outbound (HYD → GOI)")
            if ow_out_f.empty:
                st.info("No outbound flights match the current filters.")
            else:
                cheapest_out = int(ow_out_f["total_price"].min())
                for _, row in ow_out_f.head(8).iterrows():
                    is_cheapest = int(row["total_price"]) == cheapest_out
                    st.markdown(
                        f"""
<div class="mmt-card {'mmt-cheapest' if is_cheapest else ''}">
  <div class="mmt-row">
    <h3>✈️ {row['airline']} <span class="mmt-muted">({row['flight_id']})</span></h3>
    {"<span class='mmt-badge'>🏷️ Cheapest</span>" if is_cheapest else ""}
  </div>
  <div class="mmt-row mmt-muted">
    <span class="mmt-chip">🛫 {row['origin']} → {row['destination']}</span>
    <span class="mmt-chip">📅 {row['date']}</span>
    <span class="mmt-chip">🕒 {row['departure_time']} → {row['arrival_time']} · {int(row['duration_mins'])}m</span>
  </div>
  <div class="mmt-divider"></div>
  <div class="mmt-row">
    <div>
      <div class="mmt-muted">Total for {int(row['passengers'])} passenger(s)</div>
      <div class="mmt-kpi">{money(row['total_price'])}</div>
      <div class="mmt-muted">({money(row['price_per_passenger'])} per passenger)</div>
    </div>
  </div>
</div>
                        """,
                        unsafe_allow_html=True,
                    )
                    bcols = st.columns([1, 2, 2])
                    with bcols[0]:
                        if st.button("Book Outbound", key=f"book_out_{row['flight_id']}"):
                            st.session_state["selected_outbound_id"] = row["flight_id"]
                            st.toast("Outbound flight selected.", icon="🛫")
                    with bcols[1]:
                        if st.session_state.get("selected_outbound_id") == row["flight_id"]:
                            st.success("Selected")
                    st.write("")

            st.markdown("#### 🛬 Return (GOI → HYD)")
            if ow_ret_f.empty:
                st.info("No return flights match the current filters.")
            else:
                cheapest_ret = int(ow_ret_f["total_price"].min())
                for _, row in ow_ret_f.head(8).iterrows():
                    is_cheapest = int(row["total_price"]) == cheapest_ret
                    st.markdown(
                        f"""
<div class="mmt-card {'mmt-cheapest' if is_cheapest else ''}">
  <div class="mmt-row">
    <h3>✈️ {row['airline']} <span class="mmt-muted">({row['flight_id']})</span></h3>
    {"<span class='mmt-badge'>🏷️ Cheapest</span>" if is_cheapest else ""}
  </div>
  <div class="mmt-row mmt-muted">
    <span class="mmt-chip">🛬 {row['origin']} → {row['destination']}</span>
    <span class="mmt-chip">📅 {row['date']}</span>
    <span class="mmt-chip">🕒 {row['departure_time']} → {row['arrival_time']} · {int(row['duration_mins'])}m</span>
  </div>
  <div class="mmt-divider"></div>
  <div class="mmt-row">
    <div>
      <div class="mmt-muted">Total for {int(row['passengers'])} passenger(s)</div>
      <div class="mmt-kpi">{money(row['total_price'])}</div>
      <div class="mmt-muted">({money(row['price_per_passenger'])} per passenger)</div>
    </div>
  </div>
</div>
                        """,
                        unsafe_allow_html=True,
                    )
                    bcols = st.columns([1, 2, 2])
                    with bcols[0]:
                        if st.button("Book Return", key=f"book_ret_{row['flight_id']}"):
                            st.session_state["selected_return_id"] = row["flight_id"]
                            st.toast("Return flight selected.", icon="🛬")
                    with bcols[1]:
                        if st.session_state.get("selected_return_id") == row["flight_id"]:
                            st.success("Selected")
                    st.write("")

        with c2:
            st.subheader("Price comparison")
            if "ow_out" in locals() and len(ow_out_f):
                chart_df = ow_out_f.head(12).copy()
                fig = px.bar(
                    chart_df,
                    x="flight_id",
                    y="total_price",
                    color="airline",
                    title="Outbound options by total price",
                    labels={"total_price": "Total Price (₹)"},
                )
                fig.update_layout(height=360, margin=dict(l=10, r=10, t=45, b=10), legend_title_text="Airline")
                st.plotly_chart(fig, width="stretch")

                out_sel = st.session_state.get("selected_outbound_id")
                ret_sel = st.session_state.get("selected_return_id")
                if out_sel or ret_sel:
                    out_pick = ow_out.loc[ow_out["flight_id"] == out_sel].iloc[0] if out_sel in set(ow_out["flight_id"]) else None
                    ret_pick = ow_ret.loc[ow_ret["flight_id"] == ret_sel].iloc[0] if ret_sel in set(ow_ret["flight_id"]) else None
                    total = (int(out_pick["total_price"]) if out_pick is not None else 0) + (int(ret_pick["total_price"]) if ret_pick is not None else 0)
                    if total:
                        st.success(f"Selected (out+return): **{money(total)}**")

            with st.expander("View flights table (mock dataset)", expanded=False):
                if "ow_out" in locals():
                    st.markdown("**Outbound**")
                    st.dataframe(
                        ow_out_f[["airline", "departure_time", "arrival_time", "total_price"]],
                        width="stretch",
                        hide_index=True,
                    )
                    st.markdown("**Return**")
                    st.dataframe(
                        ow_ret_f[["airline", "departure_time", "arrival_time", "total_price"]],
                        width="stretch",
                        hide_index=True,
                    )
            st.caption("All prices are mock estimates for demo purposes.")

    # ---------------- Hotels ----------------
    with tabs[1]:
        section_banner(
            title="Hotels in Goa (2 nights)",
            subtitle="Pick your stay • cheapest highlighted",
            image_url="https://images.unsplash.com/photo-1542314831-068cd1dbfeeb?auto=format&fit=crop&w=1600&q=70",
            icon="🏨",
        )
        st.write("")
        c1, c2 = st.columns([1.6, 1.0], gap="large")
        with c1:
            st.subheader(f"Hotels in Goa ({CFG.nights} nights)")
            if hotels_f.empty:
                st.info("No hotels match the current filters. Try increasing max price or lowering minimum rating.")
            else:
                cheapest_pn = int(hotels_f["price_per_night"].min())
                for idx, row in hotels_f.head(10).iterrows():
                    card_hotel(row, cheapest_per_night=cheapest_pn, nights=CFG.nights)
                    bcols = st.columns([1, 1, 2])
                    with bcols[0]:
                        if st.button("Book Now", key=f"book_h_{row['hotel_name']}"):
                            st.session_state["selected_hotel_name"] = row["hotel_name"]
                            st.toast("Hotel selected for your trip.", icon="🏨")
                    with bcols[1]:
                        if st.button("Select", key=f"sel_h_{row['hotel_name']}"):
                            st.session_state["selected_hotel_name"] = row["hotel_name"]
                    st.write("")

        with c2:
            st.subheader("Hotel pricing")
            if not hotels_f.empty:
                fig = px.histogram(
                    hotels_f,
                    x="price_per_night",
                    nbins=10,
                    title="Price per night distribution",
                    labels={"price_per_night": "Price per night (₹)"},
                )
                fig.update_layout(height=360, margin=dict(l=10, r=10, t=45, b=10))
                st.plotly_chart(fig, width="stretch")

                sel = st.session_state.get("selected_hotel_name")
                if sel:
                    pick = hotels_df.loc[hotels_df["hotel_name"] == sel]
                    if len(pick):
                        st.success(
                            f"Selected hotel: **{sel}** · **{money(int(pick.iloc[0]['price_per_night']) * CFG.nights)}** est. stay total"
                        )

            with st.expander("View hotels table (mock dataset)", expanded=False):
                st.dataframe(
                    hotels_f[["hotel_name", "price_per_night", "rating", "location"]],
                    width="stretch",
                    hide_index=True,
                )
            st.caption("Hotel inventory is mock data.")

    # ---------------- Restaurants ----------------
    with tabs[2]:
        section_banner(
            title="Restaurants near your hotel",
            subtitle="Affordable picks • budget highlighted",
            image_url="https://images.unsplash.com/photo-1414235077428-338989a2e8c0?auto=format&fit=crop&w=1600&q=70",
            icon="🍽️",
        )
        st.write("")
        st.subheader("Affordable restaurants near your hotel")
        st.caption(f"Showing places near **{selected_hotel_location}** (based on your selected hotel, if any).")
        if restaurants_f.empty:
            st.info("No restaurants match the current filters. Try increasing max cost or lowering minimum rating.")
        else:
            budget_threshold = int(restaurant_cost_max)

            c1, c2 = st.columns([1.6, 1.0], gap="large")
            with c1:
                for idx, row in restaurants_f.head(10).iterrows():
                    card_restaurant(row, budget_threshold=budget_threshold)
                    cols = st.columns([1, 3])
                    with cols[0]:
                        if st.button("Add to plan", key=f"add_r_{row['restaurant_name']}"):
                            current = list(st.session_state.get("selected_restaurants", []))
                            if row["restaurant_name"] not in current:
                                current.append(row["restaurant_name"])
                            st.session_state["selected_restaurants"] = current[:5]
                            st.toast("Added to your trip plan.", icon="🍽️")
                    with cols[1]:
                        st.caption("Tip: pick 2–4 restaurants for a realistic itinerary.")
                    st.write("")

            with c2:
                st.subheader("Top budget picks")
                top_budget = restaurants_df.sort_values(["average_cost", "rating"], ascending=[True, False]).head(5)
                top_budget["budget"] = top_budget["average_cost"].apply(money)
                st.dataframe(
                    top_budget[["restaurant_name", "cuisine", "budget", "rating"]],
                    width="stretch",
                    hide_index=True,
                )
                st.caption("Budget picks are highlighted in green in the list.")

    # ---------------- Summary ----------------
    with tabs[3]:
        section_banner(
            title="Trip Summary",
            subtitle="Review selections • checkout securely (demo)",
            image_url="https://images.unsplash.com/photo-1500375592092-40eb2168fd21?auto=format&fit=crop&w=1600&q=70",
            icon="🧾",
        )
        st.write("")
        st.subheader("Trip Summary (2D/2N)")

        flight_pick = None
        hotel_pick = None

        # New: outbound + return picked separately.
        out_sel = st.session_state.get("selected_outbound_id")
        ret_sel = st.session_state.get("selected_return_id")
        ow_out = cached_oneway(origin, destination, depart_date, passengers, seed_tag="OUT")
        ow_ret = cached_oneway(destination, origin, return_date, passengers, seed_tag="RET")
        out_pick = ow_out.loc[ow_out["flight_id"] == out_sel].iloc[0] if out_sel in set(ow_out["flight_id"]) else None
        ret_pick = ow_ret.loc[ow_ret["flight_id"] == ret_sel].iloc[0] if ret_sel in set(ow_ret["flight_id"]) else None

        if st.session_state.get("selected_hotel_name"):
            p = hotels_df.loc[hotels_df["hotel_name"] == st.session_state["selected_hotel_name"]]
            if len(p):
                hotel_pick = p.iloc[0]

        # Smart defaults if user hasn't selected
        if out_pick is None and len(ow_out):
            out_pick = ow_out.sort_values("total_price", ascending=True).iloc[0]
        if ret_pick is None and len(ow_ret):
            ret_pick = ow_ret.sort_values("total_price", ascending=True).iloc[0]
        if hotel_pick is None and len(hotels_f):
            hotel_pick = hotels_f.iloc[0]

        restaurant_names = list(st.session_state.get("selected_restaurants", []))
        if not restaurant_names and len(restaurants_f):
            restaurant_names = list(restaurants_f.head(3)["restaurant_name"].tolist())

        restaurants_pick = restaurants_df[restaurants_df["restaurant_name"].isin(restaurant_names)].copy()
        restaurants_pick = restaurants_pick.sort_values(["average_cost", "rating"], ascending=[True, False]).reset_index(drop=True)

        flight_cost = (int(out_pick["total_price"]) if out_pick is not None else 0) + (int(ret_pick["total_price"]) if ret_pick is not None else 0)
        hotel_cost = int(hotel_pick["price_per_night"]) * CFG.nights if hotel_pick is not None else 0
        food_cost = int(restaurants_pick["average_cost"].sum()) if len(restaurants_pick) else 0
        total_cost = flight_cost + hotel_cost + food_cost

        # Cheapest package under filters
        cheapest_pkg_cost = None
        cheapest_pkg = None
        if len(ow_out) and len(ow_ret) and len(hotels_f):
            f_out0 = ow_out.sort_values("total_price", ascending=True).iloc[0]
            f_ret0 = ow_ret.sort_values("total_price", ascending=True).iloc[0]
            h0 = hotels_f.iloc[0]
            cheapest_pkg = (f_out0, f_ret0, h0)
            cheapest_pkg_cost = int(f_out0["total_price"]) + int(f_ret0["total_price"]) + int(h0["price_per_night"]) * CFG.nights

        k1, k2, k3, k4 = st.columns(4)
        k1.metric("✈️ Flights (total)", money(flight_cost) if flight_cost else "—")
        k2.metric(f"🏨 Hotel ({CFG.nights} nights)", money(hotel_cost) if hotel_cost else "—")
        k3.metric("🍽️ Food (avg sum)", money(food_cost) if food_cost else "—")
        k4.metric("🧾 Est. trip total", money(total_cost) if total_cost else "—")

        st.write("")
        c1, c2 = st.columns([1.2, 0.8], gap="large")

        with c1:
            st.markdown("#### Your selections")

            if out_pick is None or ret_pick is None:
                st.warning("Pick both **Outbound** and **Return** flights in the **Flights** tab to finalize return ticket booking.")
            else:
                st.markdown(
                    f"""
<div class="mmt-card">
  <div class="mmt-row"><h3>✈️ Flights</h3></div>
  <div class="mmt-muted">Outbound: <b>{out_pick['airline']} ({out_pick['flight_id']})</b> · {money(int(out_pick['total_price']))}</div>
  <div class="mmt-row mmt-muted" style="margin-top:8px;">
    <span class="mmt-chip">🛫 {out_pick['origin']} → {out_pick['destination']}</span>
    <span class="mmt-chip">📅 {out_pick['date']}</span>
    <span class="mmt-chip">🕒 {out_pick['departure_time']} → {out_pick['arrival_time']}</span>
  </div>
  <div class="mmt-divider"></div>
  <div class="mmt-muted">Return: <b>{ret_pick['airline']} ({ret_pick['flight_id']})</b> · {money(int(ret_pick['total_price']))}</div>
  <div class="mmt-row mmt-muted" style="margin-top:8px;">
    <span class="mmt-chip">🛬 {ret_pick['origin']} → {ret_pick['destination']}</span>
    <span class="mmt-chip">📅 {ret_pick['date']}</span>
    <span class="mmt-chip">🕒 {ret_pick['departure_time']} → {ret_pick['arrival_time']}</span>
  </div>
</div>
                    """,
                    unsafe_allow_html=True,
                )

            if hotel_pick is None:
                st.warning("Select a hotel in the **Hotels** tab to finalize booking.")
            else:
                st.markdown(
                    f"""
<div class="mmt-card">
  <div class="mmt-row"><h3>🏨 Hotel</h3></div>
  <div class="mmt-muted">{hotel_pick['hotel_name']} · {hotel_pick['location']} · ⭐ {float(hotel_pick['rating']):.1f}</div>
  <div class="mmt-row mmt-muted" style="margin-top:8px;">
    <span class="mmt-chip">🛏️ {CFG.nights} nights</span>
    <span class="mmt-chip">💳 {money(int(hotel_pick['price_per_night']))}/night</span>
    <span class="mmt-chip">🧾 {money(int(hotel_pick['price_per_night']) * CFG.nights)} est.</span>
  </div>
</div>
                    """,
                    unsafe_allow_html=True,
                )

            st.markdown("#### Restaurants")
            if restaurants_pick.empty:
                st.info("Add restaurants in the **Restaurants** tab, or loosen filters.")
            else:
                show = restaurants_pick.copy()
                show["avg_cost"] = show["average_cost"].apply(money)
                st.dataframe(
                    show[["restaurant_name", "cuisine", "avg_cost", "rating"]],
                    width="stretch",
                    hide_index=True,
                )

        with c2:
            st.markdown("#### Best deal")
            if cheapest_pkg_cost is None:
                st.info("Pick at least one matching flight and hotel to compute the cheapest package.")
            else:
                f_out0, f_ret0, h0 = cheapest_pkg
                st.markdown(
                    f"""
<div class="mmt-card mmt-cheapest">
  <div class="mmt-row"><h3>🏷️ Cheapest package</h3></div>
  <div class="mmt-muted">Outbound: <b>{f_out0['airline']} ({f_out0['flight_id']})</b></div>
  <div class="mmt-muted">Return: <b>{f_ret0['airline']} ({f_ret0['flight_id']})</b></div>
  <div class="mmt-muted">Hotel: <b>{h0['hotel_name']}</b> ({h0['location']})</div>
  <div class="mmt-divider"></div>
  <div class="mmt-row">
    <div>
      <div class="mmt-muted">Flights total</div>
      <div class="mmt-kpi">{money(int(f_out0['total_price']) + int(f_ret0['total_price']))}</div>
    </div>
    <div style="width:12px;"></div>
    <div>
      <div class="mmt-muted">Hotel ({CFG.nights} nights)</div>
      <div class="mmt-kpi">{money(int(h0['price_per_night']) * CFG.nights)}</div>
    </div>
  </div>
  <div class="mmt-divider"></div>
  <div class="mmt-row">
    <div class="mmt-muted">Package total (excl. food)</div>
    <div class="mmt-kpi">{money(int(cheapest_pkg_cost))}</div>
  </div>
</div>
                    """,
                    unsafe_allow_html=True,
                )

            st.markdown("#### Actions")
            if st.button("✅ Confirm trip plan", type="primary"):
                st.session_state["show_payment"] = True
            if st.button("🧹 Reset selections"):
                st.session_state["selected_outbound_id"] = None
                st.session_state["selected_return_id"] = None
                st.session_state["selected_hotel_name"] = None
                st.session_state["selected_restaurants"] = []
                st.session_state["payment_status"] = None
                st.session_state["show_payment"] = False
                st.toast("Selections cleared.", icon="🧹")

        st.write("")
        st.caption("Note: This app uses **mock datasets** (no external APIs) and is meant as a modern UI demo in Streamlit.")

        if st.session_state.get("show_payment"):
            st.write("")
            payment_gateway(amount_in_inr=int(total_cost))


if __name__ == "__main__":
    main()

