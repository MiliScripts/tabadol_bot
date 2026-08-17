#!/usr/bin/env python3
import os
import re

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def patch_parachi_price_updates():
    filepath = os.path.join(BASE_DIR, "parachi_price_updates.py")
    if not os.path.exists(filepath):
        print(f"⚠️ {filepath} not found, skipping.")
        return

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Add imports for arabic_reshaper and bidi
    imports_to_add = []
    if "import arabic_reshaper" not in content:
        imports_to_add.append("import arabic_reshaper")
    if "from bidi.algorithm import get_display" not in content:
        imports_to_add.append("from bidi.algorithm import get_display")

    if imports_to_add:
        content = "\n".join(imports_to_add) + "\n" + content

    # 2. Replace stamp_text function definition
    old_stamp_text_pattern = re.compile(
        r'def stamp_text\(draw, x, y, text, size, color="#ffffff", is_rtl=False, anchor="mm"\):.*?(?=\ndef |\Z)',
        re.DOTALL
    )

    new_stamp_text = '''def stamp_text(draw, x, y, text, size, color="#ffffff", is_rtl=False, anchor="mm"):
    font = get_font(size)
    text_str = str(text)
    if is_rtl or any('\\u0600' <= c <= '\\u06FF' for c in text_str):
        text_str = get_display(arabic_reshaper.reshape(text_str))
    
    draw.text(
        xy=(x, y),
        text=text_str,
        font=font,
        fill=color,
        anchor=anchor
    )

'''

    if old_stamp_text_pattern.search(content):
        # Passing lambda prevents re.sub backslash escape errors
        content = old_stamp_text_pattern.sub(lambda m: new_stamp_text, content)
    else:
        print("⚠️ Could not match stamp_text function in parachi_price_updates.py")

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"✅ Successfully patched {filepath}")


def patch_parachi_price_story_image():
    filepath = os.path.join(BASE_DIR, "parachi_price_story_image", "app.py")
    if not os.path.exists(filepath):
        print(f"⚠️ {filepath} not found, skipping.")
        return

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Add imports
    imports_to_add = []
    if "import arabic_reshaper" not in content:
        imports_to_add.append("import arabic_reshaper")
    if "from bidi.algorithm import get_display" not in content:
        imports_to_add.append("from bidi.algorithm import get_display")

    if imports_to_add:
        content = "\n".join(imports_to_add) + "\n" + content

    # 2. Replace stamp_text function
    old_stamp_text_pattern = re.compile(
        r'def stamp_text\(draw, x, y, text, size, color="#ffffff", anchor="mm"\):.*?(?=\ndef |\Z)',
        re.DOTALL
    )

    new_stamp_text = '''def stamp_text(draw, x, y, text, size, color="#ffffff", anchor="mm"):
    font = get_font(size)
    text_str = str(text)
    if any('\\u0600' <= c <= '\\u06FF' for c in text_str):
        text_str = get_display(arabic_reshaper.reshape(text_str))
    
    draw.text(
        (x, y),
        text_str,
        font=font,
        fill=color,
        anchor=anchor
    )

'''

    if old_stamp_text_pattern.search(content):
        # Passing lambda prevents re.sub backslash escape errors
        content = old_stamp_text_pattern.sub(lambda m: new_stamp_text, content)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"✅ Successfully patched {filepath}")


if __name__ == "__main__":
    print("🛠️ Applying fixes to Parachi services...")
    patch_parachi_price_updates()
    patch_parachi_price_story_image()
    print("🎉 All patches applied successfully!")