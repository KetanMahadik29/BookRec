import pandas as pd

print("Loading CSV files...")

books = pd.read_csv(
    "Datasets/Books.csv",
    sep=";",
    encoding="ISO-8859-1",
    on_bad_lines="skip"
)

users = pd.read_csv(
    "Datasets/Users.csv",
    sep=";",
    encoding="ISO-8859-1",
    on_bad_lines="skip"
)

ratings = pd.read_csv(
    "Datasets/Book-Ratings.csv",
    sep=";",
    encoding="ISO-8859-1",
    on_bad_lines="skip"
)

print("Dropping image URL columns...")

# Drop only if columns exist
books.drop(
    columns=["Image-URL-S", "Image-URL-M", "Image-URL-L"],
    errors="ignore",
    inplace=True
)

print("Merging datasets...")

dataset = pd.merge(books, ratings, on="ISBN")
dataset = pd.merge(dataset, users, on="User-ID")

# Explicit Ratings Only
dataset1 = dataset[dataset["Book-Rating"] != 0].reset_index(drop=True)

print("Saving Pickle files...")

books.to_pickle("books.pkl")
dataset1.to_pickle("dataset1.pkl")

print("Done! Pickle files created successfully ✅")
