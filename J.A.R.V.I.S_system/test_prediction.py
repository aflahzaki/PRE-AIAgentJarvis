
# Test script dengan bug yang akan diperbaiki oleh J.A.R.V.I.S
import math

def calculate_average(numbers):
    # Bug: variabel sum tidak di-inisialisasi dengan benar
    total = 0
    for num in numbers:
        total = total + num

    # Bug: division by zero jika list kosong
    average = total / len(numbers)
    return average

def predict_stroke_risk(age, blood_pressure):
    # Bug: variabel risk_score tidak terdefinisi
    if age > 60:
        risk_score = 0.7
    elif age > 45:
        risk_score = 0.5

    # Bug: referensi risk_score yang belum terdefinisi jika age <= 45
    if blood_pressure > 140:
        risk_score += 0.3

    return risk_score

# Main execution dengan bug
if __name__ == "__main__":
    numbers = [10, 20, 30, 40, 50]
    avg = calculate_average(numbers)
    print(f"Average: {avg}")

    # Ini akan error karena age=35 tidak memenuhi kondisi manapun
    risk = predict_stroke_risk(age=35, blood_pressure=130)
    print(f"Stroke Risk Score: {risk}")
