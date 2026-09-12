import json

with open("template_dump.json", encoding="utf-8") as f:
    data = json.load(f)

with open("slides_summary.txt", "w", encoding="utf-8") as out:
    for s in data:
        num = s["slide"]
        out.write(f"\n==================== SLIDE {num} ====================\n")
        for sh in s["shapes"]:
            txt = sh["text"].strip()
            if not txt:
                continue
            # Skip repetitive branding headers/footers
            if any(b in txt for b in ["MIT ACSC", "KURUKSHETRA 2.0", "HACKFEST 2026", "Sudarshan_MITAOE"]):
                continue
            out.write(f"\n--- Shape ID {sh['id']} ({sh['name']}) ---\n")
            out.write(txt + "\n")
print("Done writing slides_summary.txt")
