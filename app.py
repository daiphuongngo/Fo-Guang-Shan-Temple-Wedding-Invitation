import hashlib
import html
import io
import re
from datetime import datetime
from pathlib import Path
from textwrap import dedent
from typing import Dict, List, Optional, Tuple

import streamlit as st
from PIL import Image, ImageDraw, ImageOps, UnidentifiedImageError


# ============================================================
# 1. APP CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Liam & Alice Wedding Invitation",
    page_icon="💍",
    layout="wide",
    initial_sidebar_state="collapsed",
)

BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "assets"
ALBUM_DIR = ASSETS_DIR / "album"
MAIN_SHRINE_IMAGE = ASSETS_DIR / "main_shrine.jpg"

GROOM_NAME = "Dai Phuong Ngo (Liam)"
BRIDE_NAME = "Alice Bui"
WEDDING_DATE = "Saturday, September 26, 2026"
VENUE_NAME = "Fo Guang Shan Temple Main Shrine"
VENUE_SHORT = "Fo Guang Shan Temple, Toronto"

# Use this for the story section above the album.
# Replace the placeholder paragraphs with your real story later.
OUR_STORY_PARAGRAPHS: List[str] = [
    "Write your first paragraph here. For example, you can share how you met, what brought you closer, or what you appreciate most about each other.",
    "Write your second paragraph here. You can describe a meaningful memory, your journey as a couple, or why this wedding day is special to both of you.",
    "Write your third paragraph here. You can close with gratitude to your family and friends for witnessing this important moment.",
]

TIMELINE: List[Tuple[str, str, str]] = [
    ("16:00", "Gatherings", "Guests arrive, settle in, and prepare for the ceremony."),
    ("16:30", "Praying Services & Transfer of Merits", "A one-hour Buddhist prayer service and transfer of merits."),
    ("17:30", "Photo Shooting", "Family, friends, and couple photos."),
    ("18:00", "Vegetarian Banquet", "A vegetarian banquet to celebrate together."),
]

# No ivory/white for guests, so the bride's white dress remains visually distinct.
LADIES_COLORS: List[Tuple[str, str]] = [
    ("Sand Beige", "#D9C7AE"),
    ("Warm Taupe", "#A69B8E"),
    ("Pastel Pink", "#EBC7C7"),
    ("Muted Dusty Blue", "#4D6A87"),
    ("Soft Charcoal", "#262626"),
]

MEN_COLORS: List[Tuple[str, str]] = [
    ("Medium Grey", "#7A7F86"),
    ("Deep Navy", "#1F2A44"),
    ("Muted Blue", "#4D6A87"),
    ("Charcoal", "#262626"),
]

GROOM_REFERENCE: List[Tuple[str, str]] = [
    ("Black Suit", "#000000"),
    ("White Shirt", "#FFFFFF"),
    ("Black Tie", "#111111"),
]

SUPPORTED_IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
    ".bmp",
    ".tif",
    ".tiff",
}

SHEETS_SCOPE = ["https://www.googleapis.com/auth/spreadsheets"]


# ============================================================
# 2. CSS: RESPONSIVE WEB + MOBILE DESIGN
# ============================================================

st.markdown(
    dedent(
        """
        <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}

            :root {
                --bg: #fbf7ef;
                --card: rgba(255, 252, 246, 0.94);
                --line: rgba(181, 138, 69, 0.26);
                --gold: #b58a45;
                --text: #2a241e;
                --muted: #6a5948;
                --soft: #f2eadc;
            }

            html, body, [class*="css"] {
                scroll-behavior: smooth;
                background: var(--bg);
            }

            .stApp {
                background:
                    radial-gradient(circle at 12% 0%, rgba(235,199,199,0.28), transparent 26%),
                    radial-gradient(circle at 88% 0%, rgba(217,199,174,0.32), transparent 28%),
                    linear-gradient(180deg, #fbf7ef 0%, #f6eddf 100%);
            }

            .block-container {
                max-width: 1040px;
                padding-top: 1.2rem;
                padding-bottom: 4rem;
            }

            /* Streamlit bordered containers become the card sections. */
            div[data-testid="stVerticalBlockBorderWrapper"] {
                background: var(--card) !important;
                border: 1px solid var(--line) !important;
                border-radius: 28px !important;
                box-shadow: 0 18px 45px rgba(60, 42, 20, 0.08) !important;
                padding: 1.35rem 1.45rem !important;
            }

            .hero-card {
                width: min(100%, 900px);
                margin: 0 auto 1.7rem auto;
                padding: 42px 28px 32px;
                text-align: center;
                background: var(--card);
                border: 1px solid var(--line);
                border-radius: 30px;
                box-shadow: 0 18px 45px rgba(60, 42, 20, 0.08);
                position: relative;
                overflow: hidden;
            }

            .hero-card::before,
            .hero-card::after {
                content: "✦";
                position: absolute;
                color: rgba(181, 138, 69, 0.28);
                font-size: 4.2rem;
                line-height: 1;
            }

            .hero-card::before { left: 22px; bottom: 18px; }
            .hero-card::after { right: 22px; top: 18px; }

            .small-label {
                letter-spacing: 0.22em;
                text-transform: uppercase;
                color: #8d6d3f;
                font-size: 0.78rem;
                margin-bottom: 14px;
                font-weight: 650;
            }

            .main-title {
                font-family: Georgia, 'Times New Roman', serif;
                color: var(--text);
                font-size: clamp(2.35rem, 7vw, 4.4rem);
                line-height: 1.08;
                letter-spacing: 0.01em;
                margin: 0;
            }

            .ampersand {
                color: var(--gold);
                font-style: italic;
                display: inline-block;
                margin: 8px 0;
            }

            .gold-line {
                width: 74px;
                height: 1px;
                background: var(--gold);
                margin: 22px auto;
            }

            .hero-detail-grid {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 14px;
                max-width: 700px;
                margin: 24px auto 0;
            }

            .hero-detail {
                background: rgba(255, 255, 255, 0.62);
                border: 1px solid rgba(181, 138, 69, 0.18);
                border-radius: 18px;
                padding: 16px 18px;
                color: #4e4032;
                line-height: 1.5;
                font-size: 0.96rem;
                text-align: center;
            }

            .section-title {
                font-family: Georgia, 'Times New Roman', serif;
                color: #3a2f24;
                text-align: center;
                font-size: clamp(1.62rem, 4.8vw, 2.15rem);
                letter-spacing: 0.04em;
                margin: 0 0 12px;
            }

            .section-title::before,
            .section-title::after {
                content: "—";
                color: var(--gold);
                margin: 0 11px;
                opacity: 0.75;
            }

            .section-subtitle {
                color: var(--muted);
                line-height: 1.7;
                text-align: center;
                max-width: 760px;
                margin: 0 auto 20px;
                font-size: 1rem;
            }

            .center-line {
                text-align: center;
                color: var(--muted);
                line-height: 1.7;
                max-width: 760px;
                margin: 0.25rem auto 1rem auto;
            }

            .timeline-time {
                font-family: Georgia, 'Times New Roman', serif;
                color: var(--gold);
                font-size: 1.22rem;
                font-weight: 700;
                text-align: center;
            }

            .timeline-title {
                color: var(--text);
                font-weight: 780;
                font-size: 1.04rem;
                margin-bottom: 5px;
            }

            .timeline-text {
                color: #665746;
                line-height: 1.55;
                font-size: 0.96rem;
            }

            .divider {
                height: 1px;
                background: rgba(181, 138, 69, 0.18);
                margin: 0.75rem auto;
                width: 86%;
            }

            .palette-title {
                font-family: Georgia, 'Times New Roman', serif;
                color: #3a2f24;
                text-align: center;
                font-size: 1.48rem;
                margin: 1.25rem 0 0.75rem;
                letter-spacing: 0.04em;
            }

            .palette-title::before,
            .palette-title::after {
                content: "—";
                color: var(--gold);
                margin: 0 9px;
                opacity: 0.75;
            }

            .color-name {
                text-align: center;
                font-size: 0.88rem;
                font-weight: 750;
                color: #352b22;
                margin-top: 0.45rem;
                margin-bottom: 0.05rem;
            }

            .color-code {
                text-align: center;
                font-size: 0.78rem;
                color: #6a5948;
                font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
                margin-bottom: 0.75rem;
            }

            .note-box {
                background: rgba(217, 199, 174, 0.23);
                border-left: 4px solid var(--gold);
                border-radius: 16px;
                padding: 15px 17px;
                color: #5a4a38;
                line-height: 1.65;
                margin: 22px auto 0;
                max-width: 800px;
                text-align: left;
            }

            .story-paragraph {
                color: #5a4a38;
                line-height: 1.85;
                font-size: 1.02rem;
                max-width: 760px;
                margin: 0.9rem auto;
                text-align: center;
            }

            .photo-caption {
                text-align: center;
                font-size: 0.86rem;
                color: var(--muted);
                margin-top: 10px;
            }

            .album-note {
                font-size: 0.85rem;
                color: #7b684f;
                text-align: center;
                line-height: 1.55;
                margin-top: 12px;
            }

            div[data-testid="stForm"] {
                background: rgba(255, 255, 255, 0.50);
                border: 1px solid rgba(181, 138, 69, 0.18);
                border-radius: 22px;
                padding: 20px;
            }

            .stTextInput input,
            .stNumberInput input,
            .stTextArea textarea {
                border-radius: 12px !important;
            }

            .stButton button {
                background: linear-gradient(90deg, #a8792e, #c59b54) !important;
                color: white !important;
                border: 0 !important;
                border-radius: 14px !important;
                min-height: 3rem;
                font-weight: 750 !important;
            }

            .footer-text {
                text-align: center;
                color: #7b684f;
                font-family: Georgia, 'Times New Roman', serif;
                font-size: 1.25rem;
                padding: 18px 8px 42px;
                line-height: 1.75;
            }

            @media (max-width: 700px) {
                .block-container {
                    padding-left: 0.85rem;
                    padding-right: 0.85rem;
                    padding-top: 0.75rem;
                }

                .hero-card {
                    border-radius: 24px;
                    padding: 34px 18px 24px;
                }

                .hero-detail-grid {
                    grid-template-columns: 1fr;
                }

                div[data-testid="stVerticalBlockBorderWrapper"] {
                    border-radius: 23px !important;
                    padding: 1.05rem 1rem !important;
                }

                div[data-testid="stForm"] {
                    padding: 16px;
                }
            }
        </style>
        """
    ),
    unsafe_allow_html=True,
)


# ============================================================
# 3. SIMPLE HTML HELPERS
# ============================================================

def html_markdown(markup: str) -> None:
    """Render small, dedented HTML safely without causing Markdown code blocks."""
    st.markdown(dedent(markup).strip(), unsafe_allow_html=True)


def section_title(text: str) -> None:
    html_markdown(f'<h2 class="section-title">{html.escape(text)}</h2>')


def center_text(text: str) -> None:
    html_markdown(f'<p class="section-subtitle">{text}</p>')


def story_paragraph(text: str) -> None:
    html_markdown(f'<p class="story-paragraph">{html.escape(text)}</p>')


def divider() -> None:
    html_markdown('<div class="divider"></div>')


# ============================================================
# 4. IMAGE HELPERS
# ============================================================

def safe_open_image(path: Path) -> Optional[Image.Image]:
    """Open an image safely and fix phone EXIF rotation."""
    try:
        with Image.open(path) as img:
            img = ImageOps.exif_transpose(img)
            return img.convert("RGB").copy()
    except (FileNotFoundError, UnidentifiedImageError, OSError, ValueError):
        return None


def normalized_image_hash(img: Image.Image) -> str:
    """Return a stable hash so exact duplicate images can be skipped."""
    small = img.copy().convert("RGB")
    small.thumbnail((256, 256), Image.Resampling.LANCZOS)
    buffer = io.BytesIO()
    small.save(buffer, format="JPEG", quality=80)
    return hashlib.sha256(buffer.getvalue()).hexdigest()


def center_crop_to_portrait(img: Image.Image, output_size: Tuple[int, int] = (900, 1125)) -> Image.Image:
    """Create a clean 4:5 portrait card image from any photo orientation."""
    target_w, target_h = output_size
    target_ratio = target_w / target_h
    src = img.copy().convert("RGB")
    w, h = src.size
    src_ratio = w / h

    if src_ratio > target_ratio:
        new_w = int(h * target_ratio)
        left = max((w - new_w) // 2, 0)
        src = src.crop((left, 0, left + new_w, h))
    else:
        new_h = int(w / target_ratio)
        top = max((h - new_h) // 2, 0)
        src = src.crop((0, top, w, top + new_h))

    return src.resize(output_size, Image.Resampling.LANCZOS)


def color_swatch(hex_code: str, size: int = 96) -> Image.Image:
    """Create a circular color swatch as an image, avoiding raw HTML color cards."""
    img = Image.new("RGBA", (size, size), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    margin = 8
    draw.ellipse(
        (margin, margin, size - margin, size - margin),
        fill=hex_code,
        outline=(120, 100, 75, 80),
        width=2,
    )
    return img


def get_album_images(album_dir: Path) -> Tuple[List[Tuple[Path, Image.Image]], List[Path], int]:
    """Return valid unique album images, invalid files, and duplicate count."""
    if not album_dir.exists():
        return [], [], 0

    candidates = sorted(
        [p for p in album_dir.iterdir() if p.is_file() and p.suffix.lower() in SUPPORTED_IMAGE_EXTENSIONS],
        key=lambda p: p.name.lower(),
    )

    valid_images: List[Tuple[Path, Image.Image]] = []
    invalid_files: List[Path] = []
    seen_hashes = set()
    duplicate_count = 0

    for path in candidates:
        img = safe_open_image(path)
        if img is None:
            invalid_files.append(path)
            continue

        img_hash = normalized_image_hash(img)
        if img_hash in seen_hashes:
            duplicate_count += 1
            continue

        seen_hashes.add(img_hash)
        valid_images.append((path, img))

    return valid_images, invalid_files, duplicate_count


# ============================================================
# 5. GOOGLE SHEETS HELPERS
# ============================================================

def read_secret(section: str, key: str, default: Optional[str] = None) -> Optional[str]:
    """Safely read Streamlit secrets."""
    try:
        value = st.secrets[section].get(key, default)
        if value is None:
            return default
        return str(value)
    except Exception:
        return default


def normalize_private_key(private_key: str) -> str:
    """Convert literal backslash-n sequences into real newlines if needed."""
    if "\\n" in private_key and "\n" not in private_key.replace("\\n", ""):
        return private_key.replace("\\n", "\n")
    return private_key


def google_sheets_config_status() -> Tuple[bool, str]:
    """Return whether Google Sheets is configured and a clear status message."""
    spreadsheet_url = read_secret("app", "spreadsheet_url", "") or ""
    worksheet_name = read_secret("app", "worksheet_name", "RSVP") or "RSVP"
    client_email = read_secret("google_service_account", "client_email", "") or ""
    private_key = read_secret("google_service_account", "private_key", "") or ""

    if not spreadsheet_url or "PASTE_YOUR_GOOGLE_SHEET_URL_HERE" in spreadsheet_url:
        return False, "Missing spreadsheet_url in .streamlit/secrets.toml."
    if "docs.google.com/spreadsheets" not in spreadsheet_url:
        return False, "spreadsheet_url does not look like a Google Sheets URL."
    if not worksheet_name:
        return False, "Missing worksheet_name in .streamlit/secrets.toml."
    if not client_email:
        return False, "Missing client_email in .streamlit/secrets.toml."
    if not private_key:
        return False, "Missing private_key in .streamlit/secrets.toml."
    return True, "Google Sheets secrets are present."


def get_google_worksheet():
    """Connect to the Google Sheet using the Streamlit secrets file."""
    import gspread
    from google.oauth2.service_account import Credentials

    spreadsheet_url = st.secrets["app"]["spreadsheet_url"]
    worksheet_name = st.secrets["app"].get("worksheet_name", "RSVP")

    credentials_info: Dict[str, str] = dict(st.secrets["google_service_account"])
    credentials_info["private_key"] = normalize_private_key(credentials_info["private_key"])

    credentials = Credentials.from_service_account_info(credentials_info, scopes=SHEETS_SCOPE)
    client = gspread.authorize(credentials)
    spreadsheet = client.open_by_url(spreadsheet_url)

    try:
        worksheet = spreadsheet.worksheet(worksheet_name)
    except gspread.WorksheetNotFound:
        worksheet = spreadsheet.add_worksheet(title=worksheet_name, rows=1000, cols=12)

    return worksheet


def ensure_google_sheet_header(worksheet) -> None:
    """Add the header row if the worksheet is empty."""
    header = [
        "Submitted At",
        "Guest Name",
        "Email",
        "Adults Attending",
        "Children Attending",
        "Total Guests",
        "Allergies",
        "Message",
        "Source",
    ]

    first_row = worksheet.row_values(1)
    if not first_row:
        worksheet.append_row(header, value_input_option="USER_ENTERED")


def save_to_google_sheet(
    guest_name: str,
    email: str,
    adults: int,
    children: int,
    allergies: str,
    message: str,
) -> None:
    """Save RSVP data to Google Sheets."""
    worksheet = get_google_worksheet()
    ensure_google_sheet_header(worksheet)

    worksheet.append_row(
        [
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            guest_name.strip(),
            email.strip(),
            adults,
            children,
            adults + children,
            allergies.strip(),
            message.strip(),
            "Wedding Invitation Streamlit App",
        ],
        value_input_option="USER_ENTERED",
    )


# ============================================================
# 6. VALIDATION
# ============================================================

def is_valid_email(email: str) -> bool:
    pattern = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
    return re.match(pattern, email.strip()) is not None


def validate_rsvp(guest_name: str, email: str, adults: int, children: int) -> List[str]:
    errors: List[str] = []

    if not guest_name.strip():
        errors.append("Please enter your full name.")
    if not email.strip():
        errors.append("Please enter your email.")
    elif not is_valid_email(email):
        errors.append("Please enter a valid email address.")
    if adults + children <= 0:
        errors.append("Please enter at least one adult or child attending.")

    return errors


# ============================================================
# 7. UI SECTIONS
# ============================================================

def render_hero() -> None:
    html_markdown(
        f"""
        <div class="hero-card">
            <div class="small-label">Together with our families</div>
            <h1 class="main-title">
                {html.escape(GROOM_NAME)}<br>
                <span class="ampersand">&amp;</span><br>
                {html.escape(BRIDE_NAME)}
            </h1>
            <div class="gold-line"></div>
            <p class="section-subtitle">We joyfully invite you to celebrate our wedding.</p>
            <div class="hero-detail-grid">
                <div class="hero-detail">💍 <strong>{html.escape(WEDDING_DATE)}</strong></div>
                <div class="hero-detail">📍 <strong>{html.escape(VENUE_NAME)}</strong><br>{html.escape(VENUE_SHORT)}</div>
            </div>
        </div>
        """
    )


def render_invitation_details() -> None:
    with st.container(border=True):
        section_title("Invitation Details")
        center_text(
            f'Please join us for a Buddhist wedding ceremony at <strong>{html.escape(VENUE_NAME)}</strong>. '
            "The celebration will include a prayer service, transfer of merits, photo session, and vegetarian banquet."
        )


def render_main_shrine() -> None:
    with st.container(border=True):
        section_title("The Main Shrine")
        center_text(
            "The main shrine has a warm gold, wood, and lantern atmosphere. "
            "The invitation color palette is inspired by this peaceful temple setting."
        )

        shrine_img = safe_open_image(MAIN_SHRINE_IMAGE)
        if shrine_img is None:
            st.warning("Add the main shrine photo as: assets/main_shrine.jpg")
        else:
            st.image(shrine_img, use_container_width=True)
            html_markdown('<div class="photo-caption">Fo Guang Shan Temple Main Shrine</div>')


def render_timeline() -> None:
    with st.container(border=True):
        section_title("Wedding Timeline")
        center_text("A peaceful temple ceremony followed by photos and a vegetarian banquet.")

        for index, (time_text, title, description) in enumerate(TIMELINE):
            col_time, col_text = st.columns([1, 4], vertical_alignment="top")
            with col_time:
                html_markdown(f'<div class="timeline-time">{html.escape(time_text)}</div>')
            with col_text:
                st.markdown(f"**{title}**")
                st.write(description)
            if index < len(TIMELINE) - 1:
                divider()


def render_color_group(title: str, colors: List[Tuple[str, str]]) -> None:
    html_markdown(f'<h3 class="palette-title">{html.escape(title)}</h3>')

    cols = st.columns(min(len(colors), 5))
    for col, (color_name, hex_code) in zip(cols, colors):
        with col:
            left, middle, right = st.columns([1, 2, 1])
            with middle:
                st.image(color_swatch(hex_code), use_container_width=True)
            html_markdown(f'<div class="color-name">{html.escape(color_name)}</div>')
            html_markdown(f'<div class="color-code">{html.escape(hex_code)}</div>')


def render_dress_code() -> None:
    with st.container(border=True):
        section_title("Dress Code")
        center_text(
            "Please choose soft, elegant colors that match the warm temple setting. "
            "Ivory and white are not included for guests so the bride's white dress remains visually distinct."
        )

        render_color_group("Ladies", LADIES_COLORS)
        render_color_group("Men", MEN_COLORS)
        render_color_group("Groom Reference", GROOM_REFERENCE)

        html_markdown(
            """
            <div class="note-box">
                <strong>Suggested guest style:</strong>
                Ladies may wear sand beige, warm taupe, pastel pink, muted dusty blue, or soft charcoal.
                Men may wear medium grey, deep navy, muted blue, or charcoal suits with a white shirt.
                The groom will wear a black suit, white shirt, and black tie. For the temple ceremony,
                modest and respectful outfits are recommended.
            </div>
            """
        )


def render_our_story() -> None:
    with st.container(border=True):
        section_title("Our Story of Love")
        center_text("A small space for us to share our journey before the wedding day.")

        for paragraph in OUR_STORY_PARAGRAPHS:
            story_paragraph(paragraph)

        st.info(
            "Edit OUR_STORY_PARAGRAPHS near the top of app.py to replace this placeholder text with your real story."
        )


def render_album() -> None:
    with st.container(border=True):
        section_title("Our Album")
        center_text("A few memories we would love to share with you.")

        valid_images, invalid_files, duplicate_count = get_album_images(ALBUM_DIR)

        if not valid_images:
            st.warning("No valid album photos found. Add JPG, PNG, or WEBP photos into assets/album/.")
        else:
            for i in range(0, len(valid_images), 2):
                cols = st.columns(2)
                for j, col in enumerate(cols):
                    image_index = i + j
                    if image_index >= len(valid_images):
                        continue
                    _, img = valid_images[image_index]
                    portrait_img = center_crop_to_portrait(img)
                    with col:
                        st.image(portrait_img, use_container_width=True)

        notes = []
        if invalid_files:
            invalid_names = ", ".join(p.name for p in invalid_files[:5])
            extra = "" if len(invalid_files) <= 5 else f" and {len(invalid_files) - 5} more"
            notes.append(
                f"Skipped invalid image file(s): {invalid_names}{extra}. Re-export or delete these files from assets/album/."
            )
        if duplicate_count:
            notes.append(f"Skipped {duplicate_count} duplicate image file(s) to avoid repeated photos.")

        if notes:
            html_markdown(f'<div class="album-note">{"<br>".join(html.escape(note) for note in notes)}</div>')


def render_rsvp_form() -> None:
    with st.container(border=True):
        section_title("RSVP")
        center_text(
            "Please let us know who will attend and whether there are any allergies for the vegetarian banquet."
        )

        configured, status_message = google_sheets_config_status()
        if not configured:
            st.warning(
                "Google Sheets is not fully configured yet. RSVP submissions will not be saved until this is fixed. "
                f"Current issue: {status_message}"
            )

        with st.form("rsvp_form", clear_on_submit=False):
            guest_name = st.text_input("Your full name *", placeholder="Enter your full name")
            email = st.text_input("Your email *", placeholder="Enter your email")

            col1, col2 = st.columns(2)
            with col1:
                adults = st.number_input(
                    "Number of adults attending *",
                    min_value=0,
                    max_value=20,
                    value=1,
                    step=1,
                )
            with col2:
                children = st.number_input(
                    "Number of children attending",
                    min_value=0,
                    max_value=20,
                    value=0,
                    step=1,
                )

            allergies = st.text_area(
                "Any allergies or dietary notes for the vegetarian banquet?",
                placeholder="Example: peanut allergy, gluten-free request, no mushrooms, etc.",
            )
            message = st.text_area(
                "Optional message to the couple",
                placeholder="Write a short blessing or message...",
            )

            submitted = st.form_submit_button("Submit RSVP", use_container_width=True)

        if submitted:
            errors = validate_rsvp(guest_name, email, int(adults), int(children))
            if errors:
                for error in errors:
                    st.error(error)
            elif not configured:
                st.error(
                    "The RSVP was not saved because Google Sheets is not configured. "
                    f"Fix this first: {status_message}"
                )
            else:
                try:
                    save_to_google_sheet(
                        guest_name=guest_name,
                        email=email,
                        adults=int(adults),
                        children=int(children),
                        allergies=allergies,
                        message=message,
                    )
                    st.success("Thank you! Your RSVP has been recorded in the Google Sheet.")
                except Exception as exc:
                    st.error(
                        "The RSVP could not be saved to Google Sheets. Check the Sheet URL, worksheet tab name, "
                        "Google Sheets API, service-account key, and sharing permission."
                    )
                    st.caption(f"Technical detail: {exc}")


def render_footer() -> None:
    html_markdown(
        """
        <div class="footer-text">
            With gratitude, we look forward to celebrating this special day with you.<br>
            感恩有您 · 見證幸福
        </div>
        """
    )


# ============================================================
# 8. MAIN APP
# ============================================================

def main() -> None:
    render_hero()
    render_invitation_details()
    render_main_shrine()
    render_timeline()
    render_dress_code()
    render_our_story()
    render_album()
    render_rsvp_form()
    render_footer()


if __name__ == "__main__":
    main()
