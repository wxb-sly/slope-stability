import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


# CONSTANTS
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
FIGURES_DIR = os.path.join(PROJECT_ROOT,'data', 'reports', 'figures')
os.makedirs(FIGURES_DIR, exist_ok=True)

gamma_water = 9.81  # kN/m3
k_drain = 0.05
alpha = 0.01
water_table = [0.0]


C_PRIME = 5.0
PHI = 30
SLOPE = 25
UNIT_WEIGHT = 18.0
DEPTH = 2.0

asset_type = 'HIGH' # LOW, MEDIUM OR HIGH

#SYN DATA
dates = pd.date_range(start='2023-01-01', end='2023-12-31', freq='D')
df = pd.DataFrame({'date': dates})
total_sim_days = len(df)
# usually done for one representative year

def calc_FoS(
        c_prime, gamma_soil, depth, slope_angle_degree, depth_water, phi_prime_degree
):
    i = np.radians(slope_angle_degree)
    x =    (gamma_soil*depth - gamma_water*depth_water)  *(np.cos(i)*np.cos(i))

    phi_prime_rad = np.radians(phi_prime_degree)
    strength = c_prime + (x * np.tan(phi_prime_rad))

    stress = (gamma_soil*depth*np.sin(i)*np.cos(i))
    FoS = strength/stress
    return FoS

def generate_rain(day_of_year):
    np.random.seed(42)
    if 150 < day_of_year < 260:
        return np.random.exponential(scale=20.0) * np.random.choice([0, 1], p=[0.3, 0.7])
    else:
        return np.random.exponential(scale=5.0) * np.random.choice([0, 1], p=[0.8, 0.2])

def bucket_model(df):
    for i in range(1, len(df)):
        prev_h = water_table[-1]
        rain_input = df.loc[i, 'rain_mm']
        new_h = prev_h * (1 - k_drain) + (rain_input * alpha)
        new_h = min(new_h, 2.0)
        water_table.append(new_h)

    # visualize
    df['water_height_m'] = water_table
    fig, ax1 = plt.subplots(figsize=(12, 6))
    ax1.set_xlabel('Date')
    ax1.set_ylabel('Rainfall (mm)', color='blue')
    ax1.bar(df['date'], df['rain_mm'], color='blue', alpha=0.3, label='Rain')

    ax2 = ax1.twinx()
    ax2.set_ylabel('Water Table Height (m)', color='brown')
    ax2.plot(df['date'], df['water_height_m'], color='brown', linewidth=2, label='Water Table')
    ax2.axhline(y=2.0, color='red', linestyle='--', label='Surface (Saturation)')

    plt.title('The Bucket Model: Rainfall vs Groundwater Response')
    plt.savefig(os.path.join(FIGURES_DIR, 'bucket_model.png'))
    print(f"Rainfall vs Groundwater Response Curve saved at {os.path.join(FIGURES_DIR, 'bucket_model.png')}.")
    return df

def plot_risk_profile(df):
    df['fos'] = df.apply(
    lambda row: calc_FoS(
            c_prime=C_PRIME,
            phi_prime_degree=PHI,
            slope_angle_degree=SLOPE,
            gamma_soil=UNIT_WEIGHT,
            depth=DEPTH,
            depth_water=row['water_height_m']
        ), axis=1
    )
    plt.figure(figsize=(12, 4))
    plt.plot(df['date'], df['fos'], color='green', label='Factor of Safety')
    plt.axhline(y=1.0, color='red', linestyle='--', linewidth=2, label='Critical Failure (FoS=1)')
    plt.ylabel('Factor of Safety')
    plt.title('The Risk Profile: Stability over Time')
    plt.legend()
    plt.savefig(os.path.join(FIGURES_DIR, 'risk_profile.png'))
    print(f"Risk Profile saved at {os.path.join(FIGURES_DIR, 'risk_profile.png')}.")
    failed_days = df[df['fos'] < 1.0].shape[0]
    probability_of_failure = (failed_days / total_sim_days) * 100
    print(f"\n---SLOPE STABILITY REPORT---")
    print(f"Total Days Simulated: {total_sim_days}")
    print(f"Total Days of Failure Conditions: {failed_days}")
    print(f"Annual Probability of Failure: {probability_of_failure:.3f}%.")
    return probability_of_failure



def eng_verdict(pf, asset_class="MEDIUM"): # makes default
# aligned with AGS 2007
    if asset_class == 'LOW':
        threshold = 1
    elif asset_class == "HIGH":
        threshold = 0.01
    else:
        threshold = 0.1

    if pf > threshold * 10: # risk categories are logarithmic
        return "CRITICAL - IMMINENT DANGER"
    elif pf > threshold:
        return "UNSAFE - MITIGATION REQUIRED"
    else:
        return "SAFE - ACCEPTABLE"


if __name__ == "__main__":
    df['day_of_year'] = df['date'].dt.dayofyear
    df['rain_mm'] = df['day_of_year'].apply(generate_rain).fillna(0)

    df_w = bucket_model(df)
    FoS = calc_FoS(c_prime=C_PRIME,
                   gamma_soil=UNIT_WEIGHT,
                   depth=DEPTH,
                   slope_angle_degree=SLOPE,
                   depth_water=df_w['water_height_m'], phi_prime_degree=PHI
                   )
    pff = plot_risk_profile(df_w)


    print(f"The engineering verdict for asset class {asset_type} is {eng_verdict(pff, asset_type)}.")
    print("Mission Complete.")



















