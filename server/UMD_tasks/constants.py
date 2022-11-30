import re

DatasetMarker = "annotate"
FPSMarker = "fps"
OriginalFPSMarker = "originalFps"
OriginalFPSStringMarker = "originalFpsString"
ConfidenceFiltersMarker = "confidenceFilters"
validVideoFormats = {
    "mp4",
    "webm",
    "avi",
    "mov",
    "wmv",
    "mpg",
    "mpeg",
    "mp2",
    "ogg",
    "flv",
}

videoRegex = re.compile(r"(\." + r"|\.".join(validVideoFormats) + ')$', re.IGNORECASE)
zipRegex = re.compile(r"\.zip$", re.IGNORECASE)
