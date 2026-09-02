INSERT INTO reviews (user_id, book_id, rating, comment)
SELECT
    first_user.id,
    books.id,
    5,
    'Default review created for an existing book'
FROM books
JOIN (SELECT MIN(id) AS id FROM users) AS first_user
    ON first_user.id IS NOT NULL
LEFT JOIN reviews
    ON reviews.user_id = first_user.id
    AND reviews.book_id = books.id
WHERE reviews.id IS NULL;
