import pandas as pd
import os

sites = pd.read_csv(r"C:\Users\ASUS\OneDrive - Sri Lanka Institute of Information Technology\Desktop\tourism_risk_system\data\tourist_sites.csv")
image_dir = "public/images"

def slugify(name):
    return name.lower().replace(" ", "_").replace("'", "")

missing = []
present = []
for _, row in sites.iterrows():
    slug = slugify(row["site_name"])
    found = False
    for ext in [".jpg", ".jpeg", ".png"]:
        if os.path.exists(os.path.join(image_dir, slug + ext)):
            found = True
            break
    if found:
        present.append(row["site_name"])
    else:
        missing.append(row["site_name"])

print(f"Present: {len(present)} / {len(sites)}")
print(f"Missing: {len(missing)} / {len(sites)}")
print()
print("=== MISSING SITES ===")
for name in missing:
    print(name)
