import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from db import get_connection

TAGS = {
    # Sci-Fi / Fantasia
    "Time Travel": "Time travel, characters traveling to the past or future, altering timelines",
    "Aliens": "Alien invasion, extraterrestrial beings, first contact with alien species",
    "Space": "Space exploration, astronauts, spaceships, missions in outer space",
    "Robots/AI": "Robots, artificial intelligence, cyborgs, sentient machines",
    "Cyberpunk": "Cyberpunk, neon-lit future, hackers, high tech low life, virtual reality",
    "Dystopian": "Dystopian society, totalitarian regime, oppressive government, controlled population",
    "Superhero": "Superpowers, masked vigilante, saving the world, comic book hero",
    "Anti-Hero": "Anti-hero protagonist, morally grey, flawed character doing bad things for good reasons",
    # Horror / Criaturas
    "Supernatural": "Ghosts, spirits, demons, haunted houses, paranormal events",
    "Zombie": "Zombie outbreak, undead horde, infection spreading, surviving the undead",
    "Vampire": "Vampires, blood drinking, immortal creatures of the night",
    "Werewolf": "Werewolves, lycanthropy, shapeshifting into wolf creature",
    "Witches": "Witches, witchcraft, spells, sorcery, covens",
    "Dinosaurs": "Dinosaurs, prehistoric creatures, giant reptiles",
    "Dragons": "Dragons, fire-breathing, mythical flying beasts",
    # Crime / Acção
    "Heist": "Robbery, bank heist, stealing, planning a theft, con artists",
    "Revenge": "Revenge, vengeance, payback, hunting down those who wronged you",
    "Chase": "Car chase, pursuit, fugitive on the run, being hunted",
    "Spy": "Espionage, secret agent, undercover mission, intelligence agency",
    "Prison": "Prison escape, inmates, locked up, life behind bars",
    "Gangster": "Organized crime, mafia, cartel, crime boss, underworld",
    "Conspiracy": "Government conspiracy, cover-up, secret organizations, hidden truth",
    "Courtroom": "Courtroom drama, trial, lawyer, justice system, legal battle",
    "Kidnapping": "Kidnapping, abduction, hostage situation, ransom",
    # Sobrevivência / Natureza
    "Apocalypse": "End of the world, post-apocalyptic wasteland, civilization collapse, extinction",
    "Disaster": "Natural disaster, earthquake, tornado, tsunami, catastrophe",
    "Survival": "Survival against nature, stranded, fighting to stay alive, endurance",
    "Underwater": "Underwater, deep sea, ocean creatures, submarines, diving",
    "Wilderness": "Wilderness, jungle, forest, mountains, isolated in nature",
    "Arctic": "Arctic, frozen tundra, ice, extreme cold, polar expedition",
    "Desert": "Desert, sand, scorching heat, arid wasteland",
    "Tropical Island": "Tropical island, paradise, castaways, remote island",
    # Social / Vida
    "Coming of Age": "Growing up, teenager finding identity, youth, transition to adulthood",
    "High School": "High school setting, prom, school life, teenage social drama",
    "Teenage": "Teenagers, teen problems, youth rebellion, young adult struggles",
    "Sports": "Sports competition, athletes, training, championship, athletic rivalry",
    "Road Trip": "Journey on the road, traveling across country, road adventure",
    "Treasure Hunt": "Treasure hunt, searching for lost artifact, adventure quest, hidden treasure",
    "Body Swap": "Body swap, characters switching bodies, identity exchange",
    "Amnesia": "Amnesia, memory loss, forgotten identity, recovering lost memories",
    # Setting / Época
    "Medieval": "Medieval setting, knights, castles, swords, middle ages",
    "Futuristic": "Futuristic setting, advanced technology, future civilization",
    "Small Town": "Small town, rural community, countryside, village life",
    "Big City": "Big city life, urban setting, metropolis, city lights",
    "Pirates": "Pirates, ships, sailing the seas, treasure, swashbuckling",
    # Combate / Acção extra
    "Martial Arts": "Martial arts, kung fu, karate, hand-to-hand combat training, fighting tournament",
    "Assassination": "Hired killer, hitman, contract to kill a specific target, assassin",
    "Racing": "Car racing, Formula 1, motorcycle race, speed competition on a track",
    # Horror / Thriller extra
    "Exorcism": "Demonic possession, exorcist priest, casting out demons from a body",
    "Cult": "Religious cult, brainwashing followers, fanatical charismatic leader, commune",
    # Sci-Fi extra
    "Time Loop": "Stuck repeating the same day over and over, groundhog day, time loop",
    "Pandemic": "Virus outbreak, plague spreading, contagion, global epidemic, quarantine",
    "Nuclear": "Nuclear bomb, atomic explosion, radiation fallout, nuclear war threat",
    "Parallel Universe": "Alternate dimension, multiverse, parallel reality, crossing between worlds",
    "Hacker": "Hacking into computer systems, digital break-in, cyber attack, cracking codes",
    # Social / Vida extra
    "Christmas": "Christmas holiday celebration, Santa Claus, festive season, presents under the tree",
    "Wedding": "Wedding ceremony, bride and groom, marriage preparation, wedding day",
    "Dance": "Dance competition, choreography, ballet performance, ballroom dancing",
    "Drug Trade": "Drug trafficking, narcotics smuggling, drug cartel operation, dealing drugs",
    # Estilo / Estética
    "Glamour": "Glamour, luxury, wealth, high society, lavish lifestyle",
    "Fashion": "Fashion, clothing design, runway, models, style industry",
}

TAG_NAMES = list(TAGS.keys())
TAG_DESCRIPTIONS = list(TAGS.values())

# Load model and encode tags using descriptions
print("Encoding tags...")
model = SentenceTransformer("all-mpnet-base-v2")
tag_vectors = model.encode(TAG_DESCRIPTIONS, normalize_embeddings=True).astype(np.float32)

# Load movie embeddings from Faiss
print("Loading Faiss index...")
index = faiss.read_index("movies.faiss")
ids = np.load("movies_faiss_ids.npy")

vectors = np.zeros((index.ntotal, index.d), dtype=np.float32)
for i in range(index.ntotal):
    vectors[i] = index.reconstruct(i)

# Normalize movie vectors (Faiss IndexFlatIP already has them normalized, but just in case)
faiss.normalize_L2(vectors)

# Compute cosine similarity: each movie against each tag
print(f"Computing similarities ({len(ids)} movies x {len(TAG_NAMES)} tags)...")
similarities = vectors @ tag_vectors.T  # shape: (n_movies, n_tags)

# Assign top 3 tags per movie
top3_indices = np.argsort(-similarities, axis=1)[:, :3]
top3_scores = np.take_along_axis(similarities, top3_indices, axis=1)

# Filter to English movies with votes for display
conn = get_connection()
en_ids = set(r[0] for r in conn.execute(
    "SELECT id FROM movies WHERE original_language = 'en' AND vote_count >= 50"
).fetchall())

# Build reverse lookup: movie_id -> index in ids array
id_to_idx = {int(mid): i for i, mid in enumerate(ids)}

# Show well-known movies (high vote count)
popular = [r[0] for r in conn.execute(
    "SELECT id FROM movies WHERE original_language = 'en' AND vote_count >= 5000 ORDER BY vote_count DESC LIMIT 200"
).fetchall()]
sample_ids = [mid for mid in popular if mid in id_to_idx]
placeholders = ",".join("?" * len(sample_ids))
rows = conn.execute(
    f"SELECT id, title FROM movies WHERE id IN ({placeholders})", sample_ids
).fetchall()
title_map = {r["id"]: r["title"] for r in rows}

print("\n=== Sample movies with tags ===")
shown = 0
for mid in sample_ids:
    if mid in title_map and mid in id_to_idx:
        idx = id_to_idx[mid]
        tags_above = [f"{TAG_NAMES[top3_indices[idx, j]]} ({top3_scores[idx, j]:.3f})" for j in range(3) if top3_scores[idx, j] >= 0.26]
        tags_below = [f"({TAG_NAMES[top3_indices[idx, j]]} {top3_scores[idx, j]:.3f})" for j in range(3) if top3_scores[idx, j] < 0.26]
        print(f"  {title_map[mid]}: {', '.join(tags_above)}  {' '.join(tags_below)}")
        shown += 1
        if shown >= 50:
            break

# Show tag distribution (count movies where tag score >= 0.30)
print("\n=== Tag distribution (score >= 0.30) ===")
for i, tag in enumerate(TAG_NAMES):
    count = np.sum(similarities[:, i] >= 0.26)
    print(f"  {tag}: {count} movies ({count/len(ids)*100:.1f}%)")
no_tag_count = np.sum(np.max(similarities, axis=1) < 0.26)
print(f"\n  Movies with no tag >= 0.30: {no_tag_count} ({no_tag_count/len(ids)*100:.1f}%)")

# Show some no-tag movies to understand what's missing
print("\n=== Sample movies WITHOUT any tag (score < 0.30) ===")
no_tag_mask = np.max(similarities, axis=1) < 0.26
no_tag_ids = ids[no_tag_mask]
sample_no_tag = [int(mid) for mid in no_tag_ids if int(mid) in en_ids][:100]
if sample_no_tag:
    placeholders = ",".join("?" * len(sample_no_tag))
    rows = conn.execute(
        f"SELECT id, title FROM movies WHERE id IN ({placeholders})", sample_no_tag
    ).fetchall()
    no_tag_titles = {r["id"]: r["title"] for r in rows}
    shown = 0
    for mid in sample_no_tag:
        if mid in no_tag_titles:
            idx = id_to_idx[mid]
            best = similarities[idx].max()
            best_tag = TAG_NAMES[similarities[idx].argmax()]
            print(f"  {no_tag_titles[mid]} (best: {best_tag} {best:.2f})")
            shown += 1
            if shown >= 20:
                break

conn.close()
