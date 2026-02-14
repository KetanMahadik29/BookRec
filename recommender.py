import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix
from sklearn.neighbors import NearestNeighbors
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
import operator

# ---------------- GLOBALS ---------------- #
books = None
dataset1 = None
matrix = None
knn_model = None
popular_books = None
cosine_sim = None

loaded = False


# ---------------- LOAD EVERYTHING ONLY ONCE ---------------- #
def load_model():
    global books, dataset1, matrix, knn_model, popular_books, cosine_sim, loaded

    if loaded:
        return

    print("Loading datasets...")

    # Load CSV files
    books = pd.read_csv("Datasets/Books.csv", sep=";", encoding="ISO-8859-1", on_bad_lines="skip")
    users = pd.read_csv("Datasets/Users.csv", sep=";", encoding="ISO-8859-1", on_bad_lines="skip")
    ratings = pd.read_csv("Datasets/Book-Ratings.csv", sep=";", encoding="ISO-8859-1", on_bad_lines="skip")

    # Safe drop
    books.drop(
    ['Image-URL-S', 'Image-URL-M', 'Image-URL-L'],
    axis=1,
    inplace=True,
    errors="ignore"
)

    # Merge dataset
    dataset = pd.merge(books, ratings, on="ISBN")
    dataset = pd.merge(dataset, users, on="User-ID")

    dataset1 = dataset[dataset["Book-Rating"] != 0].reset_index(drop=True)

    # ---------------- Train KNN Model ---------------- #
    print("Training KNN model...")

    popularity_threshold = 50

    data = dataset1.groupby("Book-Title")["Book-Rating"].count().reset_index()
    data = data.rename(columns={"Book-Rating": "Total-Rating"})

    result = pd.merge(data, dataset1, on="Book-Title")
    result = result[result["Total-Rating"] >= popularity_threshold]

    matrix = result.pivot_table(
        index="Book-Title",
        columns="User-ID",
        values="Book-Rating"
    ).fillna(0)

    up_matrix = csr_matrix(matrix)

    knn_model = NearestNeighbors(metric="cosine", algorithm="brute")
    knn_model.fit(up_matrix)

    # ---------------- Train Content Model ---------------- #
    print("Training Content model...")

    popularity_threshold = 80
    popular_books = dataset1.groupby("Book-Title").filter(
        lambda x: len(x) >= popularity_threshold
    )

    tf = TfidfVectorizer(stop_words="english")
    tfidf_matrix = tf.fit_transform(popular_books["Book-Title"])

    cosine_sim = cosine_similarity(tfidf_matrix, tfidf_matrix)

    loaded = True
    print("Model loaded successfully!")


# ---------------- FIND CLOSEST MATCH ---------------- #
def find_best_match(book_name, book_list):
    book_name = book_name.lower()

    matches = [title for title in book_list if book_name in title.lower()]

    if len(matches) == 0:
        return None

    return matches[0]


# ---------------- KNN RECOMMENDER ---------------- #
def knn_recommend(book_name, n=5):
    load_model()

    best_match = find_best_match(book_name, matrix.index)

    if best_match is None:
        return []

    distances, indices = knn_model.kneighbors(
        matrix.loc[best_match].values.reshape(1, -1),
        n_neighbors=n + 1
    )

    return [matrix.index[i] for i in indices[0][1:]]


# ---------------- CONTENT RECOMMENDER ---------------- #
def content_recommend(book_name, n=5):
    load_model()

    best_match = find_best_match(book_name, popular_books["Book-Title"].values)

    if best_match is None:
        return []

    idx = popular_books[popular_books["Book-Title"] == best_match].index[0]
    similar_indices = cosine_sim[idx].argsort()[::-1]

    rec_books = []
    for i in similar_indices:
        title = popular_books.iloc[i]["Book-Title"]
        if title != best_match and title not in rec_books:
            rec_books.append(title)

        if len(rec_books) >= n:
            break

    return rec_books


# ---------------- POPULARITY FALLBACK ---------------- #
def popularity_based(n=5):
    load_model()

    popular = (
        dataset1.groupby("Book-Title")["Book-Rating"]
        .count()
        .sort_values(ascending=False)
        .head(n)
        .index.tolist()
    )

    return popular


# ---------------- FINAL AUTO HYBRID RECOMMENDER ---------------- #
def recommend_books(book_name, n=10):
    load_model()

    final_scores = {}

    # 1️⃣ KNN Collaborative
    knn_list = knn_recommend(book_name, 5)
    weight = 1.0
    for b in knn_list:
        final_scores[b] = final_scores.get(b, 0) + weight
        weight -= 0.1

    # 2️⃣ Content Based
    content_list = content_recommend(book_name, 5)
    weight = 1.0
    for b in content_list:
        final_scores[b] = final_scores.get(b, 0) + weight
        weight -= 0.1

    # 3️⃣ Popularity Fallback
    popular_list = popularity_based(5)
    weight = 0.5
    for b in popular_list:
        final_scores[b] = final_scores.get(b, 0) + weight
        weight -= 0.05

    # Sort final list
    ranked = sorted(final_scores.items(), key=lambda x: x[1], reverse=True)

    # Return top N recommendations
    return [book for book, score in ranked[:n]]
