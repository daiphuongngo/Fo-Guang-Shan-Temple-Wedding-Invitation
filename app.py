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

# Optional HEIC support. The app still works if pillow-heif is not installed.
try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
    HEIC_SUPPORTED = True
except Exception:
    HEIC_SUPPORTED = False

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

TIMELINE: List[Tuple[str, str, str]] = [
    ("16:00", "Gatherings", "Guests arrive, settle in, and prepare for the ceremony."),
    ("16:30", "Praying Services & Transfer of Merits", "A one-hour Buddhist prayer service and transfer of merits."),
    ("17:30", "Photo Shooting", "Family, friends, and couple photos."),
    ("18:00", "Vegetarian Banquet", "A vegetarian banquet to celebrate together."),
]

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
    ".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff", ".heic", ".heif"
}

# If you want the app to display only photos from assets/album, change this to [ALBUM_DIR].
ALBUM_SEARCH_LOCATIONS = [ALBUM_DIR, ASSETS_DIR, BASE_DIR]

# ============================================================
# 2. CSS: MOBILE + DESKTOP
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
        --line: rgba(181, 138, 69, 0.24);
        --gold: #b58a45;
        --text: #2a241e;
        --muted: #655545;
        --soft: #f4eadb;
    }

    html, body, .stApp {
        background: var(--bg) !important;
        color: var(--text) !important;
        scroll-behavior: smooth;
    }

    .stApp {
        background:
            radial-gradient(circle at 12% 0%, rgba(235,199,199,0.25), transparent 26%),
            radial-gradient(circle at 88% 0%, rgba(217,199,174,0.30), transparent 28%),
            linear-gradient(180deg, #fbf7ef 0%, #f6eddf 100%) !important;
    }

    .block-container {
        max-width: 1080px;
        padding-top: 1.2rem;
        padding-bottom: 4rem;
    }

    /* Force mobile Chrome/dark mode to keep text black. */
    h1, h2, h3, h4, h5, h6,
    p, span, div,
    .hero-name, .hero-amp,
    .section-heading, .subsection-heading,
    .center-text, .timeline-time, .timeline-title, .timeline-text,
    .swatch-name, .swatch-code, .story-text {
        color: var(--text) !important;
    }

    .center-text {
        text-align: center !important;
        color: var(--muted) !important;
        max-width: 800px;
        margin: 0.35rem auto 1.2rem auto;
        line-height: 1.75;
        font-size: 1.02rem;
    }

    .section-heading {
        text-align: center !important;
        font-family: Georgia, 'Times New Roman', serif;
        font-size: clamp(1.8rem, 5vw, 2.65rem);
        font-weight: 700;
        line-height: 1.2;
        letter-spacing: 0.02em;
        margin: 0.2rem auto 1rem auto;
    }

    .section-heading:before,
    .section-heading:after,
    .subsection-heading:before,
    .subsection-heading:after {
        content: "—";
        color: var(--gold) !important;
        margin: 0 0.45em;
        opacity: 0.9;
    }

    .subsection-heading {
        text-align: center !important;
        font-family: Georgia, 'Times New Roman', serif;
        font-size: clamp(1.35rem, 4vw, 2.0rem);
        font-weight: 700;
        margin: 1.8rem auto 1rem auto;
    }

    .hero-card {
        background: var(--card);
        border: 1px solid var(--line);
        border-radius: 30px;
        box-shadow: 0 18px 45px rgba(60, 42, 20, 0.08);
        padding: 44px 28px 34px;
        text-align: center !important;
        max-width: 900px;
        margin: 0.5rem auto 1.8rem auto;
        position: relative;
        overflow: hidden;
    }

    .hero-card:before,
    .hero-card:after {
        content: "✦";
        position: absolute;
        color: rgba(181, 138, 69, 0.30) !important;
        font-size: 4rem;
        line-height: 1;
    }

    .hero-card:before { left: 24px; bottom: 18px; }
    .hero-card:after { right: 24px; top: 18px; }

    .small-label {
        letter-spacing: 0.22em;
        text-transform: uppercase;
        color: #8d6d3f !important;
        font-size: 0.78rem;
        margin-bottom: 14px;
        font-weight: 700;
        text-align: center !important;
    }

    .hero-name {
        font-family: Georgia, 'Times New Roman', serif;
        font-size: clamp(2.05rem, 7vw, 4.25rem);
        font-weight: 700;
        line-height: 1.1;
        text-align: center !important;
        margin: 0;
    }

    .hero-amp {
        color: var(--gold) !important;
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
        max-width: 720px;
        margin: 24px auto 0;
    }

    .hero-detail {
        background: rgba(255, 255, 255, 0.62);
        border: 1px solid rgba(181, 138, 69, 0.18);
        border-radius: 18px;
        padding: 16px 18px;
        text-align: center !important;
        line-height: 1.5;
        font-size: 0.96rem;
    }

    div[data-testid="stVerticalBlockBorderWrapper"] {
        border-color: var(--line) !important;
        background: var(--card) !important;
        border-radius: 26px !important;
        box-shadow: 0 14px 34px rgba(60, 42, 20, 0.06);
    }

    .timeline-row {
        max-width: 760px;
        margin: 0 auto;
        padding: 1rem 0;
        border-bottom: 1px solid rgba(181, 138, 69, 0.18);
    }

    .timeline-time {
        font-family: Georgia, 'Times New Roman', serif;
        color: var(--gold) !important;
        font-size: 1.2rem;
        font-weight: 700;
        text-align: left;
        white-space: nowrap;
    }

    .timeline-title {
        font-weight: 800;
        font-size: 1.03rem;
        margin-bottom: 0.25rem;
    }

    .timeline-text {
        color: var(--muted) !important;
        line-height: 1.6;
    }

    .swatch-name {
        text-align: center !important;
        font-weight: 800;
        margin-top: 0.35rem;
        font-size: 0.96rem;
    }

    .swatch-code {
        text-align: center !important;
        color: var(--muted) !important;
        font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
        font-size: 0.82rem;
        margin-bottom: 0.6rem;
    }

    .note-box {
        background: rgba(217, 199, 174, 0.24);
        border-left: 4px solid var(--gold);
        border-radius: 16px;
        padding: 15px 17px;
        color: var(--muted) !important;
        line-height: 1.65;
        margin: 1.2rem auto 0;
        max-width: 800px;
    }

    .story-text {
        text-align: center !important;
        color: var(--muted) !important;
        line-height: 1.85;
        font-size: 1.03rem;
        max-width: 820px;
        margin: 0.75rem auto;
    }

    .story-placeholder {
        background: rgba(255,255,255,0.55);
        border: 1px dashed rgba(181, 138, 69, 0.45);
        border-radius: 18px;
        padding: 1.2rem 1rem;
        color: var(--muted) !important;
        text-align: center;
        max-width: 820px;
        margin: 1rem auto;
        line-height: 1.7;
    }

    .album-caption {
        text-align: center !important;
        color: var(--muted) !important;
        font-size: 0.88rem;
        margin-top: 0.35rem;
    }

    .footer-text {
        text-align: center !important;
        color: #7b684f !important;
        font-family: Georgia, 'Times New Roman', serif;
        font-size: 1.25rem;
        padding: 22px 8px 46px;
        line-height: 1.75;
    }

    @media (max-width: 700px) {
        .block-container {
            padding-left: 0.8rem;
            padding-right: 0.8rem;
            padding-top: 0.75rem;
        }

        .hero-card {
            border-radius: 24px;
            padding: 34px 18px 24px;
        }

        .hero-detail-grid {
            grid-template-columns: 1fr;
        }

        .section-heading {
            font-size: 2.0rem;
        }

        .subsection-heading {
            font-size: 1.5rem;
        }

        .timeline-row {
            padding: 0.85rem 0;
        }

        .timeline-time {
            font-size: 1.05rem;
        }

        .center-text, .story-text {
            font-size: 0.96rem;
        }
    }
</style>
""",
    unsafe_allow_html=True,
)

# ============================================================
# 3. SMALL UI HELPERS
# ============================================================

def section_heading(text: str) -> None:
    st.markdown(f'<h2 class="section-heading">{html.escape(text)}</h2>', unsafe_allow_html=True)


def subsection_heading(text: str) -> None:
    st.markdown(f'<h3 class="subsection-heading">{html.escape(text)}</h3>', unsafe_allow_html=True)


def centered_text(text: str) -> None:
    st.markdown(f'<p class="center-text">{html.escape(text)}</p>', unsafe_allow_html=True)


def safe_markdown_text(text: str, class_name: str) -> None:
    st.markdown(f'<div class="{class_name}">{html.escape(text)}</div>', unsafe_allow_html=True)

# ============================================================
# 4. IMAGE HELPERS
# ============================================================

def safe_open_image(path: Path) -> Optional[Image.Image]:
    try:
        with Image.open(path) as img:
            img = ImageOps.exif_transpose(img)
            return img.copy()
    except (FileNotFoundError, UnidentifiedImageError, OSError, ValueError):
        return None


def make_color_swatch(hex_code: str, size: int = 72) -> Image.Image:
    """Create a small elegant circular color swatch as an image, not HTML."""
    scale = 4
    canvas_size = size * scale
    margin = 6 * scale
    img = Image.new("RGBA", (canvas_size, canvas_size), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)

    # Shadow
    shadow_offset = 3 * scale
    draw.ellipse(
        (margin + shadow_offset, margin + shadow_offset, canvas_size - margin + shadow_offset, canvas_size - margin + shadow_offset),
        fill=(60, 42, 20, 28),
    )

    # Circle
    draw.ellipse(
        (margin, margin, canvas_size - margin, canvas_size - margin),
        fill=hex_code,
        outline=(120, 105, 85, 120),
        width=2 * scale,
    )

    # Inner highlight border
    inset = 3 * scale
    draw.ellipse(
        (margin + inset, margin + inset, canvas_size - margin - inset, canvas_size - margin - inset),
        outline=(255, 255, 255, 110),
        width=1 * scale,
    )

    return img.resize((size, size), Image.Resampling.LANCZOS)


def center_crop_to_portrait(img: Image.Image, ratio: Tuple[int, int] = (4, 5)) -> Image.Image:
    src = img.copy().convert("RGB")
    target_ratio = ratio[0] / ratio[1]
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


def normalized_image_hash(img: Image.Image) -> str:
    small = img.copy().convert("RGB")
    small.thumbnail((180, 180), Image.Resampling.LANCZOS)
    buffer = io.BytesIO()
    small.save(buffer, format="JPEG", quality=75)
    return hashlib.sha256(buffer.getvalue()).hexdigest()


def is_album_candidate(path: Path) -> bool:
    if not path.is_file():
        return False
    if path.suffix.lower() not in SUPPORTED_IMAGE_EXTENSIONS:
        return False
    lower_name = path.name.lower()
    if lower_name in {"main_shrine.jpg", "main_shrine.jpeg", "main_shrine.png"}:
        return False
    if "secrets" in lower_name:
        return False
    return True


@st.cache_data(show_spinner=False)
def discover_album_paths() -> List[str]:
    paths: List[Path] = []
    seen = set()

    for folder in ALBUM_SEARCH_LOCATIONS:
        if not folder.exists():
            continue
        for path in sorted(folder.glob("*"), key=lambda p: p.name.lower()):
            if not is_album_candidate(path):
                continue
            resolved = str(path.resolve())
            if resolved in seen:
                continue
            seen.add(resolved)
            paths.append(path)

    return [str(p) for p in paths]


def get_album_images() -> Tuple[List[Tuple[Path, Image.Image]], List[Path], int]:
    valid_images: List[Tuple[Path, Image.Image]] = []
    invalid_files: List[Path] = []
    duplicate_count = 0
    seen_hashes = set()

    for path_str in discover_album_paths():
        path = Path(path_str)
        if path.suffix.lower() in {".heic", ".heif"} and not HEIC_SUPPORTED:
            invalid_files.append(path)
            continue

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
# 5. GOOGLE SHEETS
# ============================================================

SHEETS_SCOPE = ["https://www.googleapis.com/auth/spreadsheets"]


def get_secret_value(section: str, key: str, default: Optional[str] = None) -> Optional[str]:
    try:
        section_obj = st.secrets.get(section, {})
        return section_obj.get(key, default)
    except Exception:
        return default


def google_sheets_config_status() -> Tuple[bool, str]:
    spreadsheet_url = get_secret_value("app", "spreadsheet_url")
    worksheet_name = get_secret_value("app", "worksheet_name")
    client_email = get_secret_value("google_service_account", "client_email")
    private_key = get_secret_value("google_service_account", "private_key")

    if not spreadsheet_url or "PASTE_YOUR_GOOGLE_SHEET_URL_HERE" in spreadsheet_url:
        return False, "Missing spreadsheet_url in Streamlit secrets."
    if not worksheet_name:
        return False, "Missing worksheet_name in Streamlit secrets."
    if not client_email:
        return False, "Missing google_service_account.client_email in Streamlit secrets."
    if not private_key:
        return False, "Missing google_service_account.private_key in Streamlit secrets."
    return True, "Google Sheets is configured."


@st.cache_resource(show_spinner=False)
def get_google_worksheet():
    import gspread
    from google.oauth2.service_account import Credentials

    spreadsheet_url = st.secrets["app"]["spreadsheet_url"]
    worksheet_name = st.secrets["app"].get("worksheet_name", "RSVP")
    credentials_info = dict(st.secrets["google_service_account"])

    # Handles both TOML formats: actual newlines and escaped \n.
    if "private_key" in credentials_info and isinstance(credentials_info["private_key"], str):
        credentials_info["private_key"] = credentials_info["private_key"].replace("\\n", "\n")

    credentials = Credentials.from_service_account_info(credentials_info, scopes=SHEETS_SCOPE)
    client = gspread.authorize(credentials)
    spreadsheet = client.open_by_url(spreadsheet_url)

    try:
        worksheet = spreadsheet.worksheet(worksheet_name)
    except gspread.WorksheetNotFound:
        worksheet = spreadsheet.add_worksheet(title=worksheet_name, rows=1000, cols=12)

    return worksheet


def ensure_google_sheet_header(worksheet) -> None:
    values = worksheet.get_all_values()
    if not values:
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
# 7. PAGE SECTIONS
# ============================================================

def render_hero() -> None:
    st.markdown(
        f'''<section class="hero-card">
<div class="small-label">Together with our families</div>
<h1 class="hero-name">{html.escape(GROOM_NAME)}<br><span class="hero-amp">&amp;</span><br>{html.escape(BRIDE_NAME)}</h1>
<div class="gold-line"></div>
<p class="center-text">We joyfully invite you to celebrate our wedding.</p>
<div class="hero-detail-grid">
<div class="hero-detail">💍 <strong>{html.escape(WEDDING_DATE)}</strong></div>
<div class="hero-detail">📍 <strong>{html.escape(VENUE_NAME)}</strong><br>{html.escape(VENUE_SHORT)}</div>
</div>
</section>''',
        unsafe_allow_html=True,
    )


def render_invitation_details() -> None:
    with st.container(border=True):
        section_heading("Invitation Details")
        centered_text(
            f"Please join us for a Buddhist wedding ceremony at {VENUE_NAME}. "
            "The celebration will include a prayer service, transfer of merits, photo session, and vegetarian banquet."
        )


def render_main_shrine() -> None:
    with st.container(border=True):
        section_heading("The Main Shrine")
        centered_text(
            "The main shrine has a warm gold, wood, and lantern atmosphere. "
            "The invitation color palette is inspired by this peaceful temple setting."
        )
        shrine_img = safe_open_image(MAIN_SHRINE_IMAGE)
        if shrine_img is None:
            st.warning("Add the main shrine photo as assets/main_shrine.jpg.")
        else:
            st.image(shrine_img, width="stretch")
            safe_markdown_text("Fo Guang Shan Temple Main Shrine", "album-caption")


def render_timeline() -> None:
    with st.container(border=True):
        section_heading("Wedding Timeline")
        centered_text("A peaceful temple ceremony followed by photos and a vegetarian banquet.")

        for time_text, title, description in TIMELINE:
            st.markdown('<div class="timeline-row">', unsafe_allow_html=True)
            time_col, text_col = st.columns([1, 4], vertical_alignment="top")
            with time_col:
                safe_markdown_text(time_text, "timeline-time")
            with text_col:
                safe_markdown_text(title, "timeline-title")
                safe_markdown_text(description, "timeline-text")
            st.markdown('</div>', unsafe_allow_html=True)


def render_color_palette(title: str, colors: List[Tuple[str, str]]) -> None:
    subsection_heading(title)

    # Streamlit-native cards. No generated HTML blocks, so no raw code can leak onto the page.
    per_row = 5 if len(colors) >= 5 else len(colors)
    for start in range(0, len(colors), per_row):
        row_colors = colors[start : start + per_row]
        cols = st.columns(len(row_colors), gap="medium", vertical_alignment="center")
        for col, (name, hex_code) in zip(cols, row_colors):
            with col:
                with st.container(border=True):
                    left, mid, right = st.columns([1, 1, 1])
                    with mid:
                        st.image(make_color_swatch(hex_code, size=62), width=62)
                    safe_markdown_text(name, "swatch-name")
                    safe_markdown_text(hex_code, "swatch-code")


def render_dress_code() -> None:
    with st.container(border=True):
        section_heading("Dress Code")
        centered_text(
            "Please choose soft, elegant colors that match the warm temple setting. "
            "Ivory and white are not included for guests so the bride's white dress remains visually distinct."
        )

        render_color_palette("Ladies", LADIES_COLORS)
        render_color_palette("Men", MEN_COLORS)
        render_color_palette("Groom Reference", GROOM_REFERENCE)

        st.markdown(
            '''<div class="note-box"><strong>Suggested guest style:</strong> Ladies may wear sand beige, warm taupe, pastel pink, muted dusty blue, or soft charcoal. Men may wear medium grey, deep navy, muted blue, or charcoal suits with a white shirt. The groom will wear a black suit, white shirt, and black tie. For the temple ceremony, modest and respectful outfits are recommended.</div>''',
            unsafe_allow_html=True,
        )


def render_our_story() -> None:
    with st.container(border=True):
        section_heading("Our Story of Love")
        st.markdown(
            '''<p class="story-text">This section is reserved for our love story. You can replace this placeholder with a few paragraphs about how you met, meaningful memories, your journey together, and what this wedding day means to both of you.</p>
<div class="story-placeholder">Write your story here later.<br>Example: how we met, our first memories, our proposal, our shared values, and why we chose Fo Guang Shan Temple for this special day.</div>''',
            unsafe_allow_html=True,
        )


def render_album() -> None:
    with st.container(border=True):
        section_heading("Our Album")
        centered_text("A few memories we would love to share with you.")

        valid_images, invalid_files, duplicate_count = get_album_images()
        if not valid_images:
            st.warning("No valid album photos found. Add JPG, PNG, WEBP, or converted HEIC photos into assets/album/.")
        else:
            # Use two columns on desktop. Streamlit will stack cleanly on narrow screens.
            for index in range(0, len(valid_images), 2):
                cols = st.columns(2, gap="medium")
                for offset, col in enumerate(cols):
                    photo_index = index + offset
                    if photo_index >= len(valid_images):
                        continue
                    path, img = valid_images[photo_index]
                    with col:
                        portrait_img = center_crop_to_portrait(img)
                        st.image(portrait_img, width="stretch")

        if invalid_files:
            names = ", ".join(p.name for p in invalid_files[:6])
            extra = "" if len(invalid_files) <= 6 else f" and {len(invalid_files) - 6} more"
            st.info(f"Skipped invalid or unsupported image file(s): {names}{extra}.")
        if duplicate_count:
            st.info(f"Skipped {duplicate_count} duplicate image file(s) to avoid repeated photos.")
        if not HEIC_SUPPORTED:
            st.caption("HEIC note: HEIC files require pillow-heif in requirements.txt, or convert them to JPG first.")


def render_rsvp_form() -> None:
    with st.container(border=True):
        section_heading("RSVP")
        centered_text("Please let us know who will attend and whether there are any allergies for the vegetarian banquet.")

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
                adults = st.number_input("Number of adults attending *", min_value=0, max_value=20, value=1, step=1)
            with col2:
                children = st.number_input("Number of children attending", min_value=0, max_value=20, value=0, step=1)

            allergies = st.text_area(
                "Any allergies or dietary notes for the vegetarian banquet?",
                placeholder="Example: peanut allergy, gluten-free request, no mushrooms, etc.",
            )
            message = st.text_area("Optional message to the couple", placeholder="Write a short blessing or message...")
            submitted = st.form_submit_button("Submit RSVP", use_container_width=True)

        if submitted:
            errors = validate_rsvp(guest_name, email, int(adults), int(children))
            if errors:
                for error in errors:
                    st.error(error)
                return

            configured, status_message = google_sheets_config_status()
            if not configured:
                st.error(f"The RSVP was not saved because Google Sheets is not configured. Fix this first: {status_message}")
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
                # Safe debug detail. It does not print the private key.
                st.exception(exc)


def render_footer() -> None:
    st.markdown(
        '''<div class="footer-text">With gratitude, we look forward to celebrating this special day with you.<br>感恩有您 · 見證幸福</div>''',
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
