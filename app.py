import csv
import hashlib
import html
import io
import re
from datetime import datetime
from pathlib import Path
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

# Edit this section later with your real love story paragraphs.
OUR_STORY_PARAGRAPHS: List[str] = [
    "This section is reserved for our story of love. We will share a few meaningful moments about how we met, how our relationship grew, and what this wedding day means to us.",
    "We are grateful for the love, support, and blessings from our families and friends as we begin this new chapter together.",
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

# These direct folders are scanned for album images.
# Recommended: put guest-facing album photos inside assets/album.
# The app also checks assets/ and the project root for image files in case photos were uploaded there by mistake.
ALBUM_SEARCH_LOCATIONS = [ALBUM_DIR, ASSETS_DIR, BASE_DIR]

EXCLUDED_IMAGE_NAMES = {
    "main_shrine.jpg",
    "main_shrine.jpeg",
    "main_shrine.png",
    "main_shrine.webp",
}

MAX_ALBUM_PHOTOS: Optional[int] = None  # Set to an integer like 20 if you want to limit the album.


# ============================================================
# 2. CSS: RESPONSIVE MOBILE + DESKTOP WEB DESIGN
# ============================================================

st.markdown(
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
    }

    .stApp {
        background:
            radial-gradient(circle at 12% 0%, rgba(235,199,199,0.30), transparent 28%),
            radial-gradient(circle at 88% 0%, rgba(217,199,174,0.34), transparent 30%),
            linear-gradient(180deg, #fbf7ef 0%, #f6eddf 100%);
    }

    .block-container {
        max-width: 1040px;
        padding-top: 1.2rem;
        padding-bottom: 4rem;
    }

    div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlockBorderWrapper"] {
        background: var(--card);
        border: 1px solid var(--line);
        border-radius: 30px;
        box-shadow: 0 18px 45px rgba(60, 42, 20, 0.08);
    }

    .hero-card {
        background: var(--card);
        border: 1px solid var(--line);
        border-radius: 30px;
        box-shadow: 0 18px 45px rgba(60, 42, 20, 0.08);
        padding: 42px 28px 32px;
        text-align: center;
        position: relative;
        overflow: hidden;
        margin: 8px auto 26px;
        max-width: 900px;
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
        text-align: center;
    }

    .main-title {
        font-family: Georgia, 'Times New Roman', serif;
        color: var(--text);
        font-size: clamp(2.2rem, 6.4vw, 4.2rem);
        line-height: 1.08;
        letter-spacing: 0.01em;
        margin: 0;
        text-align: center;
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

    .center-text {
        text-align: center;
        color: #5a4a38;
        line-height: 1.72;
        max-width: 760px;
        margin-left: auto;
        margin-right: auto;
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

    .detail-pill {
        background: rgba(255, 255, 255, 0.62);
        border: 1px solid rgba(181, 138, 69, 0.18);
        border-radius: 18px;
        padding: 16px 18px;
        color: #4e4032;
        line-height: 1.5;
        font-size: 0.96rem;
        text-align: center;
    }

    .timeline-time {
        font-family: Georgia, 'Times New Roman', serif;
        color: var(--gold);
        font-size: 1.22rem;
        font-weight: 700;
        text-align: right;
        padding-top: 0.15rem;
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

    .color-label {
        text-align: center;
        color: #352b22;
        font-size: 0.90rem;
        font-weight: 750;
        margin-top: 0.2rem;
    }

    .color-code {
        text-align: center;
        color: #6a5948;
        font-size: 0.78rem;
        font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    }

    .note-box {
        background: rgba(217, 199, 174, 0.23);
        border-left: 4px solid var(--gold);
        border-radius: 16px;
        padding: 15px 17px;
        color: #5a4a38;
        line-height: 1.65;
        margin: 22px auto 0;
        max-width: 760px;
    }

    .story-paragraph {
        text-align: center;
        color: #5a4a38;
        line-height: 1.8;
        max-width: 780px;
        margin: 0.95rem auto;
        font-size: 1.02rem;
    }

    .photo-caption {
        text-align: center;
        font-size: 0.86rem;
        color: var(--muted);
        margin-top: 10px;
    }

    .album-note {
        text-align: center;
        color: #7b684f;
        line-height: 1.6;
        font-size: 0.90rem;
        margin-top: 1rem;
    }

    .footer-text {
        text-align: center;
        color: #7b684f;
        font-family: Georgia, 'Times New Roman', serif;
        font-size: 1.25rem;
        padding: 18px 8px 42px;
        line-height: 1.75;
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

    @media (max-width: 700px) {
        .block-container {
            padding-left: 0.85rem;
            padding-right: 0.85rem;
            padding-top: 0.75rem;
        }

        .hero-card {
            border-radius: 24px;
            padding: 34px 18px 24px;
            margin-top: 4px;
        }

        .timeline-time {
            text-align: left;
            font-size: 1.08rem;
        }
    }
</style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# 3. BASIC DISPLAY HELPERS
# ============================================================

def section_title(title: str) -> None:
    st.markdown(f'<h2 class="section-title">{html.escape(title)}</h2>', unsafe_allow_html=True)


def center_text(text: str) -> None:
    st.markdown(f'<p class="section-subtitle">{html.escape(text)}</p>', unsafe_allow_html=True)


def story_text(text: str) -> None:
    st.markdown(f'<p class="story-paragraph">{html.escape(text)}</p>', unsafe_allow_html=True)


def color_swatch(hex_code: str, size: int = 96) -> Image.Image:
    """Create a circular color swatch image so Streamlit never renders raw HTML."""
    hex_code = hex_code.strip()
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    margin = 6
    draw.ellipse(
        (margin, margin, size - margin, size - margin),
        fill=hex_code,
        outline=(116, 98, 72, 80),
        width=2,
    )
    return image


def show_color_palette(title: str, colors: List[Tuple[str, str]], columns_per_row: int = 5) -> None:
    st.markdown(f'<h3 class="section-title" style="font-size:1.55rem;">{html.escape(title)}</h3>', unsafe_allow_html=True)
    for start in range(0, len(colors), columns_per_row):
        row_colors = colors[start : start + columns_per_row]
        cols = st.columns(len(row_colors))
        for col, (name, code) in zip(cols, row_colors):
            with col:
                left, middle, right = st.columns([1, 1.25, 1])
                with middle:
                    st.image(color_swatch(code), width="stretch")
                st.markdown(f'<div class="color-label">{html.escape(name)}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="color-code">{html.escape(code)}</div>', unsafe_allow_html=True)


# ============================================================
# 4. IMAGE HELPERS
# ============================================================

def safe_open_image(path: Path) -> Optional[Image.Image]:
    """Open an image safely and fix phone rotation with EXIF metadata."""
    try:
        with Image.open(path) as img:
            img = ImageOps.exif_transpose(img)
            return img.copy()
    except (FileNotFoundError, UnidentifiedImageError, OSError, ValueError):
        return None


def normalized_image_hash(img: Image.Image) -> str:
    """Create a normalized image hash so exact duplicates are skipped."""
    small = img.copy().convert("RGB")
    small.thumbnail((220, 220), Image.Resampling.LANCZOS)
    buffer = io.BytesIO()
    small.save(buffer, format="JPEG", quality=75)
    return hashlib.sha256(buffer.getvalue()).hexdigest()


def center_crop_to_portrait(img: Image.Image, target_ratio: float = 4 / 5) -> Image.Image:
    """Crop image to portrait 4:5 ratio for a consistent album grid."""
    src = img.copy().convert("RGB")
    width, height = src.size
    current_ratio = width / height

    if current_ratio > target_ratio:
        new_width = int(height * target_ratio)
        left = (width - new_width) // 2
        src = src.crop((left, 0, left + new_width, height))
    elif current_ratio < target_ratio:
        new_height = int(width / target_ratio)
        top = max((height - new_height) // 2, 0)
        src = src.crop((0, top, width, top + new_height))

    src.thumbnail((900, 1125), Image.Resampling.LANCZOS)
    return src


def get_candidate_image_files() -> List[Path]:
    """Find album images from assets/album first, then assets, then project root."""
    seen_paths = set()
    candidates: List[Path] = []

    for directory in ALBUM_SEARCH_LOCATIONS:
        if not directory.exists():
            continue
        for path in sorted(directory.iterdir(), key=lambda p: p.name.lower()):
            if not path.is_file():
                continue
            if path.suffix.lower() not in SUPPORTED_IMAGE_EXTENSIONS:
                continue
            if path.name.lower() in EXCLUDED_IMAGE_NAMES:
                continue
            if path.resolve() in seen_paths:
                continue
            seen_paths.add(path.resolve())
            candidates.append(path)

    return candidates


@st.cache_data(show_spinner=False)
def get_album_image_file_names() -> Tuple[List[str], List[str], int]:
    """
    Return valid unique image paths as strings, invalid file names, and duplicate count.
    This is cached so the deployed app does not repeatedly scan files on every interaction.
    """
    valid_paths: List[str] = []
    invalid_files: List[str] = []
    seen_hashes = set()
    duplicate_count = 0

    for path in get_candidate_image_files():
        img = safe_open_image(path)
        if img is None:
            invalid_files.append(path.name)
            continue

        img_hash = normalized_image_hash(img)
        if img_hash in seen_hashes:
            duplicate_count += 1
            continue

        seen_hashes.add(img_hash)
        valid_paths.append(str(path))

    if MAX_ALBUM_PHOTOS is not None:
        valid_paths = valid_paths[:MAX_ALBUM_PHOTOS]

    return valid_paths, invalid_files, duplicate_count


# ============================================================
# 5. GOOGLE SHEETS HELPERS
# ============================================================

SHEETS_SCOPE = ["https://www.googleapis.com/auth/spreadsheets"]

REQUIRED_SERVICE_ACCOUNT_KEYS = [
    "type",
    "project_id",
    "private_key_id",
    "private_key",
    "client_email",
    "client_id",
    "auth_uri",
    "token_uri",
    "auth_provider_x509_cert_url",
    "client_x509_cert_url",
]


def get_secret(section: str, key: str, default: Optional[str] = None) -> Optional[str]:
    try:
        return st.secrets[section].get(key, default)
    except Exception:
        return default


def google_sheets_config_status() -> Tuple[bool, str]:
    spreadsheet_url = get_secret("app", "spreadsheet_url")
    worksheet_name = get_secret("app", "worksheet_name")

    if not spreadsheet_url:
        return False, "Missing spreadsheet_url in Streamlit Secrets under [app]."
    if "PASTE_YOUR_GOOGLE_SHEET_URL_HERE" in spreadsheet_url:
        return False, "spreadsheet_url is still the placeholder value. Replace it with the real Google Sheet URL."
    if not spreadsheet_url.startswith("https://docs.google.com/spreadsheets/d/"):
        return False, "spreadsheet_url does not look like a valid Google Sheets URL."
    if not worksheet_name:
        return False, "Missing worksheet_name in Streamlit Secrets under [app]."

    for key in REQUIRED_SERVICE_ACCOUNT_KEYS:
        value = get_secret("google_service_account", key)
        if not value:
            return False, f"Missing {key} in Streamlit Secrets under [google_service_account]."

    private_key = get_secret("google_service_account", "private_key", "") or ""
    if "BEGIN PRIVATE KEY" not in private_key or "END PRIVATE KEY" not in private_key:
        return False, "private_key does not look valid. Copy it exactly from the service-account JSON file."

    return True, "Google Sheets configuration is present."


@st.cache_resource(show_spinner=False)
def get_google_worksheet():
    import gspread
    from google.oauth2.service_account import Credentials

    spreadsheet_url = st.secrets["app"]["spreadsheet_url"]
    worksheet_name = st.secrets["app"].get("worksheet_name", "RSVP")

    credentials_info: Dict[str, str] = {}
    for key in REQUIRED_SERVICE_ACCOUNT_KEYS:
        credentials_info[key] = st.secrets["google_service_account"][key]
    credentials_info["universe_domain"] = st.secrets["google_service_account"].get("universe_domain", "googleapis.com")

    credentials = Credentials.from_service_account_info(credentials_info, scopes=SHEETS_SCOPE)
    client = gspread.authorize(credentials)
    spreadsheet = client.open_by_url(spreadsheet_url)

    try:
        worksheet = spreadsheet.worksheet(worksheet_name)
    except gspread.WorksheetNotFound:
        worksheet = spreadsheet.add_worksheet(title=worksheet_name, rows=1000, cols=12)

    return worksheet


def ensure_google_sheet_header(worksheet) -> None:
    existing_values = worksheet.get_all_values()
    if existing_values:
        return

    worksheet.append_row(
        [
            "Submitted At",
            "Guest Name",
            "Email",
            "Adults Attending",
            "Children Attending",
            "Total Guests",
            "Allergies",
            "Message",
            "Source",
        ],
        value_input_option="USER_ENTERED",
    )


def save_to_google_sheet(
    guest_name: str,
    email: str,
    adults: int,
    children: int,
    allergies: str,
    message: str,
) -> None:
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
# 6. RSVP VALIDATION
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
# 7. PAGE SECTIONS
# ============================================================

def render_hero() -> None:
    st.markdown(
        f'''
<div class="hero-card">
    <div class="small-label">Together with our families</div>
    <h1 class="main-title">
        {html.escape(GROOM_NAME)}<br>
        <span class="ampersand">&amp;</span><br>
        {html.escape(BRIDE_NAME)}
    </h1>
    <div class="gold-line"></div>
    <p class="center-text">We joyfully invite you to celebrate our wedding.</p>
</div>
        ''',
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f'<div class="detail-pill">💍 <strong>{html.escape(WEDDING_DATE)}</strong></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(
            f'<div class="detail-pill">📍 <strong>{html.escape(VENUE_NAME)}</strong><br>{html.escape(VENUE_SHORT)}</div>',
            unsafe_allow_html=True,
        )


def render_invitation_details() -> None:
    with st.container(border=True):
        section_title("Invitation Details")
        center_text(
            f"Please join us for a Buddhist wedding ceremony at {VENUE_NAME}. "
            "The celebration will include a prayer service, transfer of merits, photo session, and vegetarian banquet."
        )


def render_main_shrine() -> None:
    with st.container(border=True):
        section_title("The Main Shrine")
        center_text(
            "The main shrine has a warm gold, wood, and lantern atmosphere. "
            "The invitation color palette is inspired by this peaceful temple setting."
        )
        img = safe_open_image(MAIN_SHRINE_IMAGE)
        if img is None:
            st.warning("Add the main shrine photo as assets/main_shrine.jpg.")
        else:
            img = img.copy().convert("RGB")
            img.thumbnail((1600, 900), Image.Resampling.LANCZOS)
            st.image(img, width="stretch")
            st.markdown('<div class="photo-caption">Fo Guang Shan Temple Main Shrine</div>', unsafe_allow_html=True)


def render_timeline() -> None:
    with st.container(border=True):
        section_title("Wedding Timeline")
        center_text("A peaceful temple ceremony followed by photos and a vegetarian banquet.")

        for time_text, title, description in TIMELINE:
            col_time, col_detail = st.columns([1, 4])
            with col_time:
                st.markdown(f'<div class="timeline-time">{html.escape(time_text)}</div>', unsafe_allow_html=True)
            with col_detail:
                st.markdown(f'<div class="timeline-title">{html.escape(title)}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="timeline-text">{html.escape(description)}</div>', unsafe_allow_html=True)
            st.divider()


def render_dress_code() -> None:
    with st.container(border=True):
        section_title("Dress Code")
        center_text(
            "Please choose soft, elegant colors that match the warm temple setting. "
            "Ivory and white are not included for guests so the bride's white dress remains visually distinct."
        )
        show_color_palette("Ladies", LADIES_COLORS, columns_per_row=5)
        show_color_palette("Men", MEN_COLORS, columns_per_row=4)
        show_color_palette("Groom Reference", GROOM_REFERENCE, columns_per_row=3)
        st.markdown(
            '<div class="note-box"><strong>Suggested guest style:</strong> Ladies may wear sand beige, warm taupe, pastel pink, muted dusty blue, or soft charcoal. Men may wear medium grey, deep navy, muted blue, or charcoal suits with a white shirt. The groom will wear a black suit, white shirt, and black tie. For the temple ceremony, modest and respectful outfits are recommended.</div>',
            unsafe_allow_html=True,
        )


def render_our_story() -> None:
    with st.container(border=True):
        section_title("Our Story of Love")
        for paragraph in OUR_STORY_PARAGRAPHS:
            story_text(paragraph)
        st.info("Edit OUR_STORY_PARAGRAPHS near the top of app.py to replace this placeholder with your real story.")


def render_album() -> None:
    with st.container(border=True):
        section_title("Our Album")
        center_text("A few memories we would love to share with you.")

        valid_path_strings, invalid_files, duplicate_count = get_album_image_file_names()

        if not valid_path_strings:
            st.warning("No valid album photos found. Add JPG, JPEG, PNG, or WEBP photos into assets/album/.")
            return

        cols = st.columns(2)
        for index, path_string in enumerate(valid_path_strings):
            path = Path(path_string)
            img = safe_open_image(path)
            if img is None:
                continue
            portrait_img = center_crop_to_portrait(img)
            with cols[index % 2]:
                st.image(portrait_img, width="stretch")

        notes = []
        notes.append(f"Displayed {len(valid_path_strings)} album photo(s).")
        if invalid_files:
            preview = ", ".join(invalid_files[:5])
            more = "" if len(invalid_files) <= 5 else f" and {len(invalid_files) - 5} more"
            notes.append(f"Skipped invalid image file(s): {preview}{more}.")
        if duplicate_count:
            notes.append(f"Skipped {duplicate_count} duplicate image file(s).")
        st.markdown(f'<div class="album-note">{"<br>".join(html.escape(note) for note in notes)}</div>', unsafe_allow_html=True)


def render_rsvp_form() -> None:
    with st.container(border=True):
        section_title("RSVP")
        center_text(
            "Please let us know who will attend and whether there are any allergies for the vegetarian banquet."
        )

        config_ok, config_message = google_sheets_config_status()
        if not config_ok:
            st.warning(f"Google Sheets is not fully configured yet. RSVP submissions will not be saved until this is fixed. Current issue: {config_message}")

        with st.form("rsvp_form", clear_on_submit=False):
            guest_name = st.text_input("Your full name *", placeholder="Enter your full name")
            email = st.text_input("Your email *", placeholder="Enter your email")

            col1, col2 = st.columns(2)
            with col1:
                adults = st.number_input("Number of adults attending *", min_value=0, max_value=20, value=1, step=1)
            with col2:
                children = st.number_input("Number of children attending", min_value=0, max_value=20, value=0, step=1)

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
                return

            config_ok, config_message = google_sheets_config_status()
            if not config_ok:
                st.error(f"The RSVP was not saved because Google Sheets is not configured. Fix this first: {config_message}")
                return

            try:
                save_to_google_sheet(
                    guest_name=guest_name,
                    email=email,
                    adults=int(adults),
                    children=int(children),
                    allergies=allergies,
                    message=message,
                )
                st.success("Thank you! Your RSVP has been recorded in the Google Sheet. We look forward to celebrating with you.")
            except Exception as exc:
                st.error(
                    "The RSVP could not be saved to Google Sheets. Check the Sheet URL, worksheet tab name, "
                    "Google Sheets API, service-account key, and sharing permission."
                )
                st.exception(exc)


def render_footer() -> None:
    st.markdown(
        '<div class="footer-text">With gratitude, we look forward to celebrating this special day with you.<br>感恩有您 · 見證幸福</div>',
        unsafe_allow_html=True,
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
