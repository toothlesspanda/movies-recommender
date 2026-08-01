# Emotion axes: mood (0=light, 100=dark) | energy (0=slow, 100=intense)
#               tension (0=relaxing, 100=suspenseful) | weight (0=light, 100=heavy)
# Tuples: (mood, energy, tension, weight)

EMOTION_MAP = {
    "joy":       (  5,  60,   5,   5),
    "surprise":  ( 30,  70,  50,  25),
    "neutral":   ( 50,  40,  30,  40),
    "sadness":   ( 80,  15,  30,  85),
    "anger":     ( 70,  90,  80,  60),
    "disgust":   ( 75,  50,  55,  65),
    "fear":      ( 80,  65,  90,  65),
}

GENRE_MAP = {
    "Action":          (40, 90, 70, 30),
    "Adventure":       (30, 75, 50, 25),
    "Animation":       (20, 60, 25, 20),
    "Comedy":          (15, 60, 15, 15),
    "Crime":           (75, 55, 75, 65),
    "Documentary":     (50, 25, 20, 50),
    "Drama":           (60, 35, 40, 75),
    "Family":          (15, 50, 15, 20),
    "Fantasy":         (35, 65, 45, 35),
    "History":         (55, 35, 40, 60),
    "Horror":          (90, 60, 95, 60),
    "Music":           (30, 55, 15, 40),
    "Mystery":         (65, 40, 80, 55),
    "Romance":         (35, 35, 25, 55),
    "Science Fiction": (50, 70, 60, 45),
    "TV Movie":        (40, 40, 30, 35),
    "Thriller":        (80, 70, 90, 55),
    "War":             (85, 70, 75, 85),
    "Western":         (55, 60, 60, 45),
}

DEFAULT_SCORES = {"mood": 50, "energy": 50, "tension": 50, "weight": 50}

SYNOPSIS_WEIGHT = 0.35
