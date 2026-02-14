import pandas as pd
from scipy.sparse import csr_matrix
from sklearn.neighbors import NearestNeighbors

# ---------------- GLOBALS ---------------- #
books = None
dataset1 = None
matrix = None
knn_model = None
loaded = False


# ---------------- LOAD MODEL ONLY ONCE ---------------- #
def load_model():
    global books, dataset1, matrix, knn_model, loaded

    if loaded:
        return

    print("Loading Pickle datasets...")

    # Load prepared pickle files
    books = pd.read_pickle("books.pkl")
    dataset1 = pd.read_pickle("dataset1.pkl")

    print("Training KNN model...")

    # Popularity threshold (reduce dataset size)
    popularity_threshold = 50

    data = dataset1.groupby("Book-Title")["Book-Rating"].count().reset_index()
    data = data.rename(columns={"Book-Rating": "Total-Rating"})

    result = pd.merge(data, dataset1, on="Book-Title")
    result = result[result["Total-Rating"] >= popularity_threshold]

    # Pivot table (User-Book matrix)
    matrix = result.pivot_table(
        index="Book-Title",
        columns="User-ID",
        values="Book-Rating"
    ).fillna(0)

    up_matrix = csr_matrix(matrix)

    # Train KNN
    knn_model = NearestNeighbors(metric="cosine", algorithm="brute")
    knn_model.fit(up_matrix)

    loaded = True
    print("KNN Model Loaded Successfully ✅")


# ---------------- FIND CLOSEST MATCH ---------------- #
def find_best_match(book_name, book_list):
    book_name = book_name.lower()

    matches = [title for title in book_list if book_name in title.lower()]

    if len(matches) == 0:
        return None

    return matches[0]


# ---------------- KNN RECOMMENDATION ---------------- #
def knn_recommend(book_name, n=10):
    load_model()

    best_match = find_best_match(book_name, matrix.index)

    if best_match is None:
        return []

    distances, indices = knn_model.kneighbors(
        matrix.loc[best_match].values.reshape(1, -1),
        n_neighbors=n + 1
    )

    recommendations = []
    for i in indices[0][1:]:
        recommendations.append(matrix.index[i])

    return recommendations


# ---------------- POPULARITY FALLBACK ---------------- #
def popularity_based(n=10):
    load_model()

    popular = (
        dataset1.groupby("Book-Title")["Book-Rating"]
        .count()
        .sort_values(ascending=False)
        .head(n)
        .index.tolist()
    )

    return popular


# ---------------- FINAL MAIN FUNCTION ---------------- #
def recommend_books(book_name, n=10):
    load_model()

    # First try KNN
    recs = knn_recommend(book_name, n)

    # If no match found → fallback to Popular books
    if len(recs) == 0:
        return popularity_based(n)

    return recs
