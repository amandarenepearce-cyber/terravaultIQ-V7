/* ===== PAGE LAYOUT FIX ===== */

/* Give the whole app breathing room */
.block-container {
    max-width: 1200px;
    padding-left: 2rem;
    padding-right: 2rem;
    margin: auto;
}

/* Fix weird edge clipping */
.main {
    padding-top: 1rem;
}

/* Prevent right-side cutoff */
section.main > div {
    padding-right: 1rem;
}

/* Smooth container spacing */
div[data-testid="stHorizontalBlock"] {
    gap: 2rem !important;
}
